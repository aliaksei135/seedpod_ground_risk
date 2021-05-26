import numpy as np

from seedpod_ground_risk.core.utils import remove_raster_nans, reproj_bounds


def make_fatality_grid(aircraft, strike_grid, v_is):
    from seedpod_ground_risk.path_analysis.harm_models.fatality_model import FatalityModel
    from seedpod_ground_risk.path_analysis.utils import velocity_to_kinetic_energy

    fm = FatalityModel(0.3, 1e6, 34)
    ac_mass = aircraft.mass
    impact_ke_b = velocity_to_kinetic_energy(ac_mass, v_is[0])
    impact_ke_g = velocity_to_kinetic_energy(ac_mass, v_is[1])
    res = fm.transform(strike_grid, impact_ke=impact_ke_g) + fm.transform(strike_grid, impact_ke=impact_ke_b)
    return res


def make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution, wind_direction, wind_speed):
    from seedpod_ground_risk.path_analysis.descent_models.ballistic_model import BallisticModel
    from seedpod_ground_risk.path_analysis.descent_models.glide_model import GlideDescentModel
    from seedpod_ground_risk.path_analysis.harm_models.strike_model import StrikeModel
    from seedpod_ground_risk.layers.strike_risk_layer import wrap_all_pipeline, wrap_pipeline_cuda
    from seedpod_ground_risk.path_analysis.utils import bearing_to_angle
    import scipy.stats as ss
    import os

    bm = BallisticModel(aircraft)
    gm = GlideDescentModel(aircraft)
    raster_shape = pop_grid.shape
    x, y = np.mgrid[0:raster_shape[0], 0:raster_shape[1]]
    eval_grid = np.vstack((x.ravel(), y.ravel())).T
    samples = 5000
    # Conjure up our distributions for various things
    alt = ss.norm(altitude, 5).rvs(samples)
    vel = ss.norm(airspeed, 2.5).rvs(samples)
    wind_vels = ss.norm(wind_speed, 1).rvs(samples)
    wind_dirs = bearing_to_angle(ss.norm(wind_direction, np.deg2rad(5)).rvs(samples))
    wind_vel_y = wind_vels * np.sin(wind_dirs)
    wind_vel_x = wind_vels * np.cos(wind_dirs)
    (bm_mean, bm_cov), v_ib, a_ib = bm.transform(alt, vel,
                                                 ss.uniform(0, 360).rvs(samples),
                                                 wind_vel_y, wind_vel_x,
                                                 0, 0)
    (gm_mean, gm_cov), v_ig, a_ig = gm.transform(alt, vel,
                                                 ss.uniform(0, 360).rvs(samples),
                                                 wind_vel_y, wind_vel_x,
                                                 0, 0)
    sm_b = StrikeModel(pop_grid, resolution ** 2, aircraft.width, a_ib)
    sm_g = StrikeModel(pop_grid, resolution ** 2, aircraft.width, a_ig)
    premult = sm_b.premult_mat + sm_g.premult_mat
    offset_y, offset_x = raster_shape[0] // 2, raster_shape[1] // 2
    bm_pdf = ss.multivariate_normal(bm_mean + np.array([offset_y, offset_x]), bm_cov).pdf(eval_grid)
    gm_pdf = ss.multivariate_normal(gm_mean + np.array([offset_y, offset_x]), gm_cov).pdf(eval_grid)
    pdf = bm_pdf + gm_pdf
    pdf = pdf.reshape(raster_shape)
    padded_pdf = np.zeros(((raster_shape[0] * 3) + 1, (raster_shape[1] * 3) + 1))
    padded_pdf[raster_shape[0]:raster_shape[0] * 2, raster_shape[1]:raster_shape[1] * 2] = pdf
    padded_pdf = padded_pdf * failure_prob
    padded_centre_y, padded_centre_x = raster_shape[0] + offset_y, raster_shape[1] + offset_x

    # Check if CUDA toolkit available through env var otherwise fallback to CPU bound numba version
    if not os.getenv('CUDA_HOME'):
        print('CUDA NOT found, falling back to Numba JITed CPU code')
        # Leaving parallelisation to Numba seems to be faster
        res = wrap_all_pipeline(raster_shape, padded_pdf, padded_centre_y, padded_centre_x, premult)

    else:

        res = np.zeros(raster_shape, dtype=float)
        threads_per_block = (32, 32)  # 1024 max per block
        blocks_per_grid = (
            int(np.ceil(raster_shape[1] / threads_per_block[1])),
            int(np.ceil(raster_shape[0] / threads_per_block[0]))
        )
        print('CUDA found, using config <<<' + str(blocks_per_grid) + ',' + str(threads_per_block) + '>>>')
        wrap_pipeline_cuda[blocks_per_grid, threads_per_block](raster_shape, padded_pdf, padded_centre_y,
                                                               padded_centre_x, premult, res)
    return res, (v_ib, v_ig)


def make_pop_grid(bounds, hour, resolution):
    from seedpod_ground_risk.layers.temporal_population_estimate_layer import TemporalPopulationEstimateLayer
    import pyproj

    proj = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg('4326'),
                                       pyproj.CRS.from_epsg('3857'),
                                       always_xy=True)

    raster_shape = reproj_bounds(bounds, proj, resolution)
    layer = TemporalPopulationEstimateLayer('tpe')
    layer.preload_data()
    _, raster_grid, _ = layer.generate(bounds, raster_shape, hour=hour, resolution=resolution)

    return np.flipud(remove_raster_nans(raster_grid))
