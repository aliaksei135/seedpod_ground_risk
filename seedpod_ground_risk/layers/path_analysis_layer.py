from typing import NoReturn, List, Tuple, Dict

import casex
import geopandas as gpd
import numpy as np
from holoviews.element import Overlay

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.path_analysis.descent_models.ballistic_model import BallisticModel
from seedpod_ground_risk.path_analysis.harm_models.fatality_model import FatalityModel
from seedpod_ground_risk.path_analysis.harm_models.strike_model import StrikeModel
from seedpod_ground_risk.path_analysis.utils import snap_coords_to_grid, bearing_to_angle, velocity_to_kinetic_energy
from seedpod_ground_risk.pathfinding import bresenham


class PathAnalysisLayer(AnnotationLayer):

    def __init__(self, key: str, filepath: str = '', ac_width: float = 2, ac_length: float = 2,
                 ac_mass: float = 2, ac_glide_ratio: float = 12, ac_glide_speed: float = 15,
                 ac_glide_drag_coeff: float = 0.8, ac_ballistic_drag_coeff: float = 0.8,
                 ac_ballistic_frontal_area: float = 3, ac_failure_prob: float = 0.05, alt: float = 50, vel: float = 18,
                 wind_vel: float = 5, wind_dir: float = 45, **kwargs):
        super(PathAnalysisLayer, self).__init__(key)
        self.filepath = filepath

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

        import geopandas as gpd
        self.dataframe = gpd.GeoDataFrame()
        self.buffer_poly = None

    def preload_data(self) -> NoReturn:
        self.dataframe = gpd.read_file(self.filepath)
        self.endpoint = self.dataframe.iloc[0].geometry.coords[-1]

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 resolution=20, **kwargs) -> Overlay:
        import geoviews as gv
        import scipy.stats as ss
        import joblib as jl

        bounds = (raster_data[0]['Longitude'].min(), raster_data[0]['Latitude'].min(),
                  raster_data[0]['Longitude'].max(), raster_data[0]['Latitude'].max())

        line_coords = list(self.dataframe.iloc[0].geometry.coords)
        path_grid_points, headings = self._generate_all_path_coords(line_coords, raster_data[0])

        bm = BallisticModel(self.aircraft)

        samples = 1000
        # Conjure up our distributions for various things
        alt = ss.norm(self.alt, 5).rvs(samples)
        vel = ss.norm(self.vel, 2.5).rvs(samples)
        wind_vels = ss.norm(self.wind_vel, 1).rvs(samples)
        wind_dirs = bearing_to_angle(ss.norm(self.wind_dir, np.deg2rad(5)).rvs(samples))
        wind_vel_y = wind_vels * np.sin(wind_dirs)
        wind_vel_x = wind_vels * np.cos(wind_dirs)

        # Create grid on which to evaluate each point of path with its pdf
        raster_shape = raster_data[1].shape
        x, y = np.mgrid[0:raster_shape[0], 0:raster_shape[1]]
        eval_grid = np.vstack((x.ravel(), y.ravel())).T

        def wrap_hdg_dists(alt, vel, hdg, wind_vel_y, wind_vel_x):
            (mean, cov), v_i, a_i = bm.transform(alt, vel,
                                                 ss.norm(hdg, np.deg2rad(2)).rvs(samples),
                                                 wind_vel_y, wind_vel_x,
                                                 0, 0)
            return hdg, (mean / resolution, cov / resolution, v_i, a_i)

        njobs = 1 if len(headings) < 3 else -1

        # Hardcode backend to prevent Qt freaking out
        res = jl.Parallel(n_jobs=njobs, backend='threading', verbose=1)(
            jl.delayed(wrap_hdg_dists)(alt, vel, hdg, wind_vel_y, wind_vel_x) for hdg in headings)
        dists_for_hdg = dict(res)

        def point_distr(c):
            dist_params = dists_for_hdg[c[2]]
            pdf = np.array(
                ss.multivariate_normal(dist_params[0] + np.array([c[0], c[1]]), dist_params[1]).pdf(eval_grid),
                dtype=np.longdouble)
            return pdf

        sm = StrikeModel(raster_data[1].ravel(), resolution * resolution, self.aircraft.width)
        fm = FatalityModel(0.5, 1e6, 34)
        ac_mass = self.aircraft.mass

        def wrap_pipeline(path_point_state):
            impact_pdf = point_distr(path_point_state)
            impact_vel = dists_for_hdg[path_point_state[2]][2]
            impact_angle = dists_for_hdg[path_point_state[2]][3]
            impact_ke = velocity_to_kinetic_energy(ac_mass, impact_vel)

            strike_pdf = sm.transform(impact_pdf, impact_angle=impact_angle)
            fatality_pdf = fm.transform(strike_pdf, impact_ke=impact_ke)

            return fatality_pdf, fatality_pdf.max(), strike_pdf.max()

        res = jl.Parallel(n_jobs=-1, backend='threading', verbose=1)(
            jl.delayed(wrap_pipeline)(c) for c in path_grid_points)
        fatality_pdfs = [r[0] for r in res]
        # PDFs come out in input order so sorting not required
        pathwise_fatality_maxs = np.array([r[1] for r in res], dtype=np.longdouble)
        pathwise_strike_maxs = np.array([r[2] for r in res], dtype=np.longdouble)

        import matplotlib.pyplot as mpl
        import tempfile
        import subprocess
        fig, ax = mpl.subplots(1, 1)
        path_dist = self.dataframe.to_crs('EPSG:27700').iloc[0].geometry.length
        ax.set_yscale('log')
        ax.set_ylim(bottom=1e-18)
        x = np.linspace(0, path_dist, len(pathwise_fatality_maxs))
        ax.axhline(y=np.median(pathwise_fatality_maxs), c='y',
                   label='Fatality Median')  # This seems to be as stable as fsum
        ax.plot(x, pathwise_fatality_maxs[::-1], c='r', label='Fatality Risk')
        ax.axhline(y=np.median(pathwise_strike_maxs), c='g',
                   label='Strike Median')  # This seems to be as stable as fsum
        ax.plot(x, pathwise_strike_maxs[::-1], c='b', label='Strike Risk')
        ax.legend()
        ax.set_ylabel('Risk [$h^{-1}$]')
        ax.set_xlabel('Path Distance [m]')
        ax.set_title('Casualty Risk along path')

        tmppath = tempfile.mkstemp()[1] + '.png'
        fig.savefig(tmppath)
        subprocess.run("explorer " + tmppath)

        risk_map = np.sum(fatality_pdfs, axis=0).reshape(raster_shape) * self.event_prob

        risk_raster = gv.Image(risk_map, vdims=['fatality_risk'], bounds=bounds).options(alpha=0.7, cmap='viridis',
                                                                                         tools=['hover'],
                                                                                         clipping_colors={
                                                                                             'min': (0, 0, 0, 0)})
        risk_raster = risk_raster.redim.range(fatality_risk=(risk_map.min() + 1e-15, risk_map.max()))
        print('Max probability of fatality: ', risk_map.max())

        return Overlay([
            gv.Contours(self.dataframe).opts(line_width=4, line_color='magenta'),
            risk_raster
        ])

    def clear_cache(self) -> NoReturn:
        pass

    def _generate_all_path_coords(self, waypoints, raster_indices):
        # Snap the line string nodes to the raster grid
        snapped_points = [snap_coords_to_grid(raster_indices, *coords) for coords in waypoints]
        # Generate pairs of consecutive (x,y) coords
        path_pairs = list(map(list, zip(snapped_points, snapped_points[1:])))
        headings = []
        for i in range(1, len(waypoints)):
            prev = waypoints[i - 1]
            next = waypoints[i]
            x = np.sin(next[0] - prev[0]) * np.cos(next[1])
            y = np.cos(prev[1]) * np.sin(next[1]) - np.sin(prev[1]) * np.cos(next[1]) * np.cos(next[0] - prev[0])
            angle = (np.arctan2(x, y) + (2 * np.pi)) % (2 * np.pi)
            headings.append(angle)
        # Feed these pairs into the Bresenham algo to find the intermediate points
        path_grid_points = [bresenham.make_line(*pair[0], *pair[1]) for pair in path_pairs]
        for idx, segment in enumerate(path_grid_points):
            n = len(segment)
            point_headings = np.full(n, headings[idx])
            path_grid_points[idx] = np.column_stack((np.array(segment), point_headings))
        # Bring all these points together and remove duplicate coords
        # Flip left to right as bresenham spits out in (y,x) order
        path_grid_points = np.unique(np.concatenate(path_grid_points, axis=0), axis=0)
        return path_grid_points, headings
