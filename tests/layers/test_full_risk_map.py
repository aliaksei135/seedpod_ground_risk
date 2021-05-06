import unittest
from itertools import chain

import casex
import geopandas as gpd
import numpy as np
import scipy.stats as ss
from numba import njit, prange, float64

from seedpod_ground_risk.core.plot_server import PlotServer, make_bounds_polygon
from seedpod_ground_risk.path_analysis.descent_models.ballistic_model import BallisticModel
from seedpod_ground_risk.path_analysis.descent_models.glide_model import GlideDescentModel
from seedpod_ground_risk.path_analysis.harm_models.fatality_model import FatalityModel
from seedpod_ground_risk.path_analysis.harm_models.strike_model import StrikeModel
from seedpod_ground_risk.path_analysis.utils import velocity_to_kinetic_energy, bearing_to_angle, snap_coords_to_grid


def offset_window_row(arr, shape, offset):
    y, x = shape
    off_y, off_x = offset
    for j in range(y):
        start_y = off_y - j
        end_y = start_y + y
        # row_windows = []
        # app = row_windows.append
        for i in range(x):
            start_x = off_x - i
            end_x = start_x + x
            yield arr[start_y:end_y, start_x:end_x]
            # app(arr[start_y:end_y, start_x:end_x])
        # yield row_windows  # Dont return np array here, as it gets copied to contiguous memory and OOMs


# ~140sec for 567,630 elements
@njit(cache=True, nogil=True, fastmath=True, parallel=True)
def wrap_all_pipeline(shape, padded_pdf, pcy, pcx, sm_premult):
    nr = shape[0]
    nc = shape[1]

    # Numba seems not to be able to stick a type onto `shape`
    out = np.zeros((nr, nc), dtype=float64)

    for r in prange(nr):
        start_y = pcy - r
        end_y = start_y + nr
        for c in prange(nc):
            out[r, c] = np.sum(sm_premult * padded_pdf[start_y:end_y, (pcx - c):(pcx - c + nc)])
    return out


# ~570sec for 567,630 elements
@njit(cache=True, nogil=True, fastmath=True)
def wrap_row_pipeline(row, shape, padded_pdf, padded_centre, sm):
    pcy, pcx = padded_centre
    start_y = pcy - row
    end_y = start_y + shape[0]
    # Get func references
    sm_transform = sm.transform

    # return [
    #     np.einsum('ij->',
    #               sm_transform(
    #                   padded_pdf[start_y:end_y, (pcx - cx):(pcx - cx + shape[1])],
    #               )
    #               , optimize='optimal') for cx in np.arange(shape[1])
    # ]
    return [
        np.sum(
            sm_transform(
                padded_pdf[start_y:end_y, (pcx - cx):(pcx - cx + shape[1])],
            )
        ) for cx in range(shape[1])
    ]


class FullRiskMapTestCase(unittest.TestCase):
    ###
    # This can take upwards of 10mins to run
    ###

    def setUp(self) -> None:
        super().setUp()

        self.hour = 13
        self.test_bounds = make_bounds_polygon((-1.5, -1.3), (50.87, 51))

        self._setup_aircraft()

        import os
        os.chdir(
            os.sep.join((
                os.path.dirname(os.path.realpath(__file__)),
                '..', '..'))
        )

        ps = PlotServer()
        ps.set_time(self.hour)
        self.raster_shape = ps._get_raster_dimensions(self.test_bounds, 30)
        # ps.data_layers += [ArbitraryObstacleLayer('test', 'static_data/FRZs.json')]

        [layer.preload_data() for layer in chain(ps.data_layers, ps.annotation_layers)]
        ps.generate_layers(self.test_bounds, self.raster_shape)
        self.raster_indices = dict(Longitude=np.linspace(-1.5, -1.3, num=self.raster_shape[0]),
                                   Latitude=np.linspace(51, 50.87, num=self.raster_shape[1]))
        self.raster_grid = np.flipud(np.sum(
            [ps._remove_raster_nans(res[1]) for res in ps._generated_data_layers.values() if
             res[1] is not None],
            axis=0))
        self.raster_shape = self.raster_grid.shape
        del ps

        self.path_coords = list(gpd.read_file('path.geojson').iloc[0].geometry.coords)

    def test_full_risk_map(self):
        import matplotlib.pyplot as mpl
        fig1, ax1 = mpl.subplots(1, 1)
        ax1.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m1 = ax1.matshow(self.raster_grid)
        ax1.set_title(f'Population Density at t={self.hour}')
        fig1.colorbar(m1, label='Spatiotemporal Population Density [people/km$^2$]')
        fig1.show()

        bm = BallisticModel(self.aircraft)
        gm = GlideDescentModel(self.aircraft)
        fm = FatalityModel(0.5, 1e6, 34)
        ac_mass = self.aircraft.mass

        x, y = np.mgrid[0:self.raster_shape[0], 0:self.raster_shape[1]]
        eval_grid = np.vstack((x.ravel(), y.ravel())).T

        samples = 5000
        # Conjure up our distributions for various things
        alt = ss.norm(self.alt, 5).rvs(samples)
        vel = ss.norm(self.vel, 2.5).rvs(samples)
        wind_vels = ss.norm(self.wind_vel, 1).rvs(samples)
        wind_dirs = bearing_to_angle(ss.norm(self.wind_dir, np.deg2rad(5)).rvs(samples))
        wind_vel_y = wind_vels * np.sin(wind_dirs)
        wind_vel_x = wind_vels * np.cos(wind_dirs)

        (bm_mean, bm_cov), v_i, a_i = bm.transform(alt, vel,
                                                   ss.uniform(0, 360).rvs(samples),
                                                   wind_vel_y, wind_vel_x,
                                                   0, 0)
        (gm_mean, gm_cov), v_i, a_i = gm.transform(alt, vel,
                                                   ss.uniform(0, 360).rvs(samples),
                                                   wind_vel_y, wind_vel_x,
                                                   0, 0)
        sm = StrikeModel(self.raster_grid, 30 * 30, self.aircraft.width, a_i)

        offset_y, offset_x = self.raster_shape[0] // 2, self.raster_shape[1] // 2
        bm_pdf = ss.multivariate_normal(bm_mean + np.array([offset_y, offset_x]), bm_cov).pdf(eval_grid)
        gm_pdf = ss.multivariate_normal(gm_mean + np.array([offset_y, offset_x]), gm_cov).pdf(eval_grid)
        pdf = bm_pdf + gm_pdf
        pdf = pdf.reshape(self.raster_shape)

        padded_pdf = np.zeros(((self.raster_shape[0] * 3) + 1, (self.raster_shape[1] * 3) + 1))
        padded_pdf[self.raster_shape[0]:self.raster_shape[0] * 2, self.raster_shape[1]:self.raster_shape[1] * 2] = pdf
        padded_pdf = padded_pdf * self.event_prob
        padded_centre_y, padded_centre_x = self.raster_shape[0] + offset_y, self.raster_shape[1] + offset_x
        impact_ke = velocity_to_kinetic_energy(ac_mass, v_i)

        # Leaving parallelisation to Numba seems to be faster
        res = wrap_all_pipeline(self.raster_shape, padded_pdf, padded_centre_y, padded_centre_x, sm.premult_mat)

        # Alternative joblib parallelisation
        # res = jl.Parallel(n_jobs=-1, prefer='threads', verbose=1)(
        #     jl.delayed(wrap_row_pipeline)(c, self.raster_shape, padded_pdf, (padded_centre_y, padded_centre_x), sm)
        #     for c in range(self.raster_shape[0]))

        strike_pdf = np.vstack(res)
        snapped_points = [snap_coords_to_grid(self.raster_indices, *coords) for coords in self.path_coords]

        import matplotlib.pyplot as mpl
        fig1, ax1 = mpl.subplots(1, 1)
        ax1.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m1 = ax1.matshow(self.raster_grid)
        ax1.set_title(f'Population Density at t={self.hour}')
        fig1.colorbar(m1, label='Population Density [people/km$^2$]')
        fig1.show()

        # strike_pdf = sm.transform(impact_pdf, impact_angle=a_i)
        np.savetxt(f'strike_map_t{self.hour}', strike_pdf, delimiter=',')

        fig2, ax2 = mpl.subplots(1, 1)
        ax2.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m2 = ax2.matshow(strike_pdf)
        fig2.colorbar(m2, label='Strike Risk [h$^{-1}$]')
        ax2.set_title(f'Strike Risk Map at t={self.hour}')
        fig2.show()

        fatality_pdf = fm.transform(strike_pdf, impact_ke=impact_ke)
        np.savetxt(f'fatality_map_t{self.hour}', fatality_pdf, delimiter=',')

        fig3, ax3 = mpl.subplots(1, 1)
        ax3.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m3 = ax3.matshow(fatality_pdf)
        fig3.colorbar(m3, label='Fatality Risk [h$^{-1}$]')
        ax3.set_title(f'Fatality Risk Map at t={self.hour}')
        fig3.show()

    def _setup_aircraft(self, ac_width: float = 2, ac_length: float = 1.5,
                        ac_mass: float = 2, ac_glide_ratio: float = 12, ac_glide_speed: float = 15,
                        ac_glide_drag_coeff: float = 0.1, ac_ballistic_drag_coeff: float = 0.8,
                        ac_ballistic_frontal_area: float = 0.1, ac_failure_prob: float = 5e-3, alt: float = 120,
                        vel: float = 18,
                        wind_vel: float = 5, wind_dir: float = 45):
        self.aircraft = casex.AircraftSpecs(casex.enums.AircraftType.FIXED_WING, ac_width, ac_length, ac_mass)
        self.aircraft.set_ballistic_drag_coefficient(ac_ballistic_drag_coeff)
        self.aircraft.set_ballistic_frontal_area(ac_ballistic_frontal_area)
        self.aircraft.set_glide_speed_ratio(ac_glide_speed, ac_glide_ratio)
        self.aircraft.set_glide_drag_coefficient(ac_glide_drag_coeff)

        self.alt = alt
        self.vel = vel
        self.wind_vel = wind_vel
        self.wind_dir = np.deg2rad((wind_dir - 90) % 360)

        self.event_prob = ac_failure_prob


def plot_path_risk(hour):
    import matplotlib.pyplot as mpl
    import shapely.geometry as sg
    import numpy as np
    import geopandas as gpd

    # import os
    # os.chdir(
    #     os.sep.join((
    #         os.path.dirname(os.path.realpath(__file__)),
    #         '..', '..'))
    # )

    path = np.genfromtxt('fr_map_path.csv', delimiter=',').astype(int)
    raster_indices = dict(Longitude=np.genfromtxt('raster_indices_lon.csv', delimiter=','),
                          Latitude=np.genfromtxt('raster_indices_lat.csv', delimiter=','))
    lat = raster_indices['Latitude'][path[:, 1]]
    lon = raster_indices['Longitude'][path[:, 0]]
    ls = sg.LineString([sg.Point(lon, lat) for lon, lat in zip(lon, lat)])
    df = gpd.GeoDataFrame(geometry=[ls]).set_crs('EPSG:4326')

    fatality_pdf = np.genfromtxt(f'fatality_map_t{hour}', delimiter=',')
    strike_pdf = np.genfromtxt(f'strike_map_t{hour}', delimiter=',')
    fig3, ax3 = mpl.subplots(1, 1)
    ax3.tick_params(left=False, right=False,
                    bottom=False, top=False,
                    labelleft=False, labelbottom=False)
    m3 = ax3.matshow(fatality_pdf)
    ax3.plot(path[:, 0], path[:, 1], 'r')
    fig3.colorbar(m3, label='Fatality Risk [h$^{-1}$]')
    ax3.set_title(f'Fatality Risk Map at t={hour}')
    fig3.show()
    pathwise_strike_maxs = strike_pdf[path[:, 1], path[:, 0]]
    pathwise_fatality_maxs = fatality_pdf[path[:, 1], path[:, 0]]
    fig, ax = mpl.subplots(1, 1)
    path_dist = df.to_crs('EPSG:27700').iloc[0].geometry.length
    ax.set_yscale('log')
    x = np.linspace(0, path_dist, len(pathwise_fatality_maxs))
    ax.axhline(y=np.mean(pathwise_fatality_maxs), c='y',
               label='Fatality Mean')  # This seems to be as stable as fsum
    ax.plot(x, pathwise_fatality_maxs, c='r', label='Fatality Risk')
    ax.axhline(y=np.mean(pathwise_strike_maxs), c='g',
               label='Strike Mean')  # This seems to be as stable as fsum
    ax.plot(x, pathwise_strike_maxs, c='b', label='Strike Risk')
    ax.legend()
    ax.set_ylabel('Risk [$h^{-1}$]')
    ax.set_xlabel('Path Distance [m]')
    ax.set_title(f'Casualty Risk along path at t={hour}')
    fig.show()


if __name__ == '__main__':
    unittest.main()
