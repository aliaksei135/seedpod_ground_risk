import os

import casex
import geoviews as gv
import numpy as np
import scipy.stats as ss
from numba import cuda, njit, float64, prange

from seedpod_ground_risk.core.utils import remove_raster_nans
from seedpod_ground_risk.layers.blockable_data_layer import BlockableDataLayer
from seedpod_ground_risk.layers.roads_layer import RoadsLayer
from seedpod_ground_risk.layers.temporal_population_estimate_layer import TemporalPopulationEstimateLayer
from seedpod_ground_risk.path_analysis.descent_models.ballistic_model import BallisticModel
from seedpod_ground_risk.path_analysis.descent_models.glide_model import GlideDescentModel
from seedpod_ground_risk.path_analysis.harm_models.strike_model import StrikeModel
from seedpod_ground_risk.path_analysis.utils import bearing_to_angle


# ~10sec for 567,630 elements
@cuda.jit(fastmath=True)
def wrap_pipeline_cuda(shape, padded_pdf, pcy, pcx, sm_premult, out):
    nr = shape[0]
    nc = shape[1]
    # Unique position of this thread in grid
    x, y = cuda.grid(2)

    # Array bounds check
    if x < nc and y < nr:
        arr = padded_pdf[(pcy - y):(pcy - y + nr), (pcx - x):(pcx - x + nc)]
        acc = 0
        for r in range(nr):
            for c in range(nc):
                acc += arr[r, c] * sm_premult[r, c]
        out[y, x] = acc


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

    # einsum not supported by numba
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


class StrikeRiskLayer(BlockableDataLayer):
    def __init__(self, key, colour: str = None, blocking=False, buffer_dist=0, ac_width: float = 2,
                 ac_length: float = 2,
                 ac_mass: float = 2, ac_glide_ratio: float = 12, ac_glide_speed: float = 15,
                 ac_glide_drag_coeff: float = 0.1, ac_ballistic_drag_coeff: float = 0.8,
                 ac_ballistic_frontal_area: float = 0.2, ac_failure_prob: float = 5e-3, alt: float = 120,
                 vel: float = 18,
                 wind_vel: float = 5, wind_dir: float = 45):
        super().__init__(key, colour, blocking, buffer_dist)
        delattr(self, '_colour')

        self._layers = [
            TemporalPopulationEstimateLayer(f'_strike_risk_tpe_{key}', buffer_dist=buffer_dist),
            RoadsLayer(f'_strike_risk_roads_{key}', buffer_dist=buffer_dist)]

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

        self.bm = BallisticModel(self.aircraft)
        self.gm = GlideDescentModel(self.aircraft)

    def preload_data(self):
        [layer.preload_data() for layer in self._layers]

    def generate(self, bounds_polygon, raster_shape, from_cache: bool = False, resolution=30, hour: int = 8, **kwargs):
        generated_layers = [
            layer.generate(bounds_polygon, raster_shape, from_cache=from_cache, hour=hour, resolution=resolution,
                           **kwargs) for layer in self._layers]

        raster_grid = np.flipud(np.sum(
            [remove_raster_nans(res[1]) for res in generated_layers if
             res[1] is not None],
            axis=0))
        raster_shape = raster_grid.shape

        x, y = np.mgrid[0:raster_shape[0], 0:raster_shape[1]]
        eval_grid = np.vstack((x.ravel(), y.ravel())).T

        samples = 5000
        # Conjure up our distributions for various things
        alt = ss.norm(self.alt, 5).rvs(samples)
        vel = ss.norm(self.vel, 2.5).rvs(samples)
        wind_vels = ss.norm(self.wind_vel, 1).rvs(samples)
        wind_dirs = bearing_to_angle(ss.norm(self.wind_dir, np.deg2rad(5)).rvs(samples))
        wind_vel_y = wind_vels * np.sin(wind_dirs)
        wind_vel_x = wind_vels * np.cos(wind_dirs)

        (bm_mean, bm_cov), v_ib, a_ib = self.bm.transform(alt, vel,
                                                          ss.uniform(0, 360).rvs(samples),
                                                          wind_vel_y, wind_vel_x,
                                                          0, 0)
        (gm_mean, gm_cov), v_ig, a_ig = self.gm.transform(alt, vel,
                                                          ss.uniform(0, 360).rvs(samples),
                                                          wind_vel_y, wind_vel_x,
                                                          0, 0)
        sm_b = StrikeModel(raster_grid, resolution ** 2, self.aircraft.width, a_ib)
        sm_g = StrikeModel(raster_grid, resolution ** 2, self.aircraft.width, a_ig)
        premult = sm_b.premult_mat + sm_g.premult_mat

        offset_y, offset_x = raster_shape[0] // 2, raster_shape[1] // 2
        bm_pdf = ss.multivariate_normal(bm_mean + np.array([offset_y, offset_x]), bm_cov).pdf(eval_grid)
        gm_pdf = ss.multivariate_normal(gm_mean + np.array([offset_y, offset_x]), gm_cov).pdf(eval_grid)
        pdf = bm_pdf + gm_pdf
        pdf = pdf.reshape(raster_shape)

        padded_pdf = np.zeros(((raster_shape[0] * 3) + 1, (raster_shape[1] * 3) + 1))
        padded_pdf[raster_shape[0]:raster_shape[0] * 2, raster_shape[1]:raster_shape[1] * 2] = pdf
        padded_pdf = padded_pdf * self.event_prob
        padded_centre_y, padded_centre_x = raster_shape[0] + offset_y, raster_shape[1] + offset_x

        # Check if CUDA toolkit available through env var otherwise fallback to CPU bound numba version
        if not os.getenv('CUDA_HOME'):
            print('CUDA NOT found, falling back to Numba JITed CPU code')
            # Leaving parallelisation to Numba seems to be faster
            risk_map = wrap_all_pipeline(raster_shape, padded_pdf, padded_centre_y, padded_centre_x, premult)

        else:

            risk_map = np.zeros(raster_shape, dtype=float)
            threads_per_block = (32, 32)  # 1024 max per block
            blocks_per_grid = (
                int(np.ceil(raster_shape[1] / threads_per_block[1])),
                int(np.ceil(raster_shape[0] / threads_per_block[0]))
            )
            print('CUDA found, using config <<<' + str(blocks_per_grid) + ',' + str(threads_per_block) + '>>>')
            wrap_pipeline_cuda[blocks_per_grid, threads_per_block](raster_shape, padded_pdf, padded_centre_y,
                                                                   padded_centre_x, premult, risk_map)

        bounds = bounds_polygon.bounds
        flipped_bounds = (bounds[1], bounds[0], bounds[3], bounds[2])
        risk_raster = gv.Image(risk_map, vdims=['strike_risk'], bounds=flipped_bounds).options(
            alpha=0.7,
            colorbar=True, colorbar_opts={'title': 'Person Strike Risk [h^-1]'},
            cmap='viridis',
            tools=['hover'],
            clipping_colors={
                'min': (0, 0, 0, 0)})
        import rasterio
        from rasterio import transform
        trans = transform.from_bounds(*flipped_bounds, *raster_shape)
        rds = rasterio.open(f'strike_risk_{hour}00h.tif', 'w', driver='GTiff', count=1, dtype=rasterio.float64,
                            crs='EPSG:4326', transform=trans, compress='lzw',
                            width=raster_shape[0], height=raster_shape[1])
        rds.write(risk_map, 1)
        rds.close()

        return risk_raster, risk_map, None

    def clear_cache(self):
        pass
