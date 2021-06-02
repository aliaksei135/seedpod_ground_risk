import numpy as np
from skimage.draw import line

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


def make_path(cost_grid, bounds_poly, start_latlon, end_latlon, algo='rt*', pathwise_cost=False, **kwargs):
    from seedpod_ground_risk.path_analysis.utils import snap_coords_to_grid
    from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
    import shapely.geometry as sg

    raster_shape = cost_grid.shape
    min_lat, min_lon, max_lat, max_lon = bounds_poly.bounds
    start_lat, start_lon = start_latlon
    end_lat, end_lon = end_latlon
    raster_indices = dict(Longitude=np.linspace(min_lon, max_lon, num=raster_shape[0]),
                          Latitude=np.linspace(min_lat, max_lat, num=raster_shape[1]))
    start_x, start_y = snap_coords_to_grid(raster_indices, start_lon, start_lat)
    end_x, end_y = snap_coords_to_grid(raster_indices, end_lon, end_lat)

    env = GridEnvironment(cost_grid, diagonals=False)
    if algo == 'ra*2':
        from seedpod_ground_risk.pathfinding.a_star import RiskGridAStar
        algo = RiskGridAStar()
    elif algo == 'ra*':
        from seedpod_ground_risk.pathfinding.a_star import RiskAStar
        algo = RiskAStar()
    elif algo == 'rt*':
        from seedpod_ground_risk.pathfinding.theta_star import RiskThetaStar
        algo = RiskThetaStar()
    elif algo == 'ga':
        from functools import partial
        from seedpod_ground_risk.pathfinding.moo_ga import fitness_min_risk
        from seedpod_ground_risk.pathfinding.moo_ga import fitness_min_manhattan_length
        from seedpod_ground_risk.pathfinding.moo_ga import GeneticAlgorithm
        max_dist = np.sqrt((cost_grid.shape[0] ** 2) + (cost_grid.shape[1] ** 2))
        fitness_funcs = [
            partial(fitness_min_risk, cost_grid, cost_grid.max()),
            partial(fitness_min_manhattan_length, max_dist)
        ]
        fitness_weights = [
            1e11,
            1
        ]
        algo = GeneticAlgorithm(fitness_funcs, fitness_weights)
    path = algo.find_path(env, Node((start_y, start_x)), Node((end_y, end_x)), **kwargs)

    if not path:
        print('Path not found')
        return None

    snapped_path = []
    for node in path:
        lat = raster_indices['Latitude'][min(node.position[0], raster_shape[1] - 1)]
        lon = raster_indices['Longitude'][min(node.position[1], raster_shape[0] - 1)]
        snapped_path.append((lon, lat))
    lla_path = sg.LineString(snapped_path)

    if pathwise_cost:
        path_cost = []
        for idx in range(len(path[:-1])):
            n0 = path[idx].position
            n1 = path[idx + 1].position
            l = line(n0[0], n0[1], n1[0], n1[1])
            path_cost.append(cost_grid[l[0], l[1]])
        return lla_path, path, path_cost
    else:
        return lla_path
