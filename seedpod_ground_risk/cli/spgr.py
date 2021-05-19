import os

import casex
import click
import geopandas as gpd
import numpy as np
import pyproj
import rasterio
import scipy.stats as ss
import shapely.geometry as sg
from rasterio import transform

from seedpod_ground_risk.core.utils import make_bounds_polygon, remove_raster_nans, reproj_bounds
from seedpod_ground_risk.layers.strike_risk_layer import wrap_all_pipeline, wrap_pipeline_cuda
from seedpod_ground_risk.layers.temporal_population_estimate_layer import TemporalPopulationEstimateLayer
from seedpod_ground_risk.path_analysis.descent_models.ballistic_model import BallisticModel
from seedpod_ground_risk.path_analysis.descent_models.glide_model import GlideDescentModel
from seedpod_ground_risk.path_analysis.harm_models.fatality_model import FatalityModel
from seedpod_ground_risk.path_analysis.harm_models.strike_model import StrikeModel
from seedpod_ground_risk.path_analysis.utils import bearing_to_angle, velocity_to_kinetic_energy, snap_coords_to_grid
from seedpod_ground_risk.pathfinding.a_star import RiskGridAStar
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.moo_ga import GeneticAlgorithm


@click.group()
def main():
    pass


###############################
# map
@click.group()
def map():
    """
    Generate various raster maps
    """
    pass


main.add_command(map)


@click.command()
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.option('--output-path', default='', type=click.Path(exists=True, writable=True),
              help='Output file path for geoTiff file')
@click.option('--resolution', default=40, type=click.INT, help='Resolution in metres of each pixel in the raster')
@click.option('--hour', default=13, type=click.INT, help='Hour of the week to generate map for. Must be 0<=h<=168')
def pop_density(min_lat, max_lat, min_lon, max_lon, output_path, resolution, hour):
    """
    Temporal Population Density map

    Generate a geotiff raster file of the population density in the specified bounds.

    All coordinates should be in decimal degrees and form a non degenerate polygon.

    """
    bounds = make_bounds_polygon((min_lon, min_lat), (max_lon, max_lat))
    raster_grid = _make_pop_grid(bounds, hour, resolution)

    out_name = f'pop_density_{hour}h.tif'
    _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, raster_grid)


map.add_command(pop_density)


@click.command()
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.option('--aircraft', default=None, type=click.File(lazy=True),
              help='Aircraft config file. Uses built in defaults if not specified.')
@click.option('--failure_prob', default=5e-3, type=click.FLOAT, help='Probability of aircraft failure per flight hour.')
@click.option('--output-path', default='', type=click.Path(exists=True, writable=True),
              help='Output file path for geoTiff file')
@click.option('--resolution', default=40, type=click.INT, help='Resolution in metres of each pixel in the raster')
@click.option('--hour', default=13, type=click.INT, help='Hour of the week to generate map for. Must be 0<=h<=168')
@click.option('--altitude', default=120, type=click.FLOAT, help='Aircraft Altitude in metres')
@click.option('--airspeed', default=20, type=click.FLOAT, help='Aircraft Airspeed in m/s')
@click.option('--wind-direction', default=90, type=click.INT,
              help='The wind bearing. This is the direction the wind is coming from.')
@click.option('--wind_speed', default=5, type=click.FLOAT, help='Wind speed at the flight altitude in m/s')
def strike(min_lat, max_lat, min_lon, max_lon, aircraft, failure_prob, output_path, resolution, hour, altitude,
           airspeed, wind_direction, wind_speed):
    """
    Strike Risk map

    Generate a geotiff raster file of the probability of striking a person with a specified aircraft in the specified
    bounds.

    If an aircraft config json file is not specified, a default aircraft with reasonable parameters is used.

    All coordinates should be in decimal degrees and form a non degenerate polygon.

    """
    bounds = make_bounds_polygon((min_lon, min_lat), (max_lon, max_lat))
    pop_grid = _make_pop_grid(bounds, hour, resolution)

    if not aircraft:
        aircraft = _setup_default_aircraft()
    else:
        aircraft = _import_aircraft(aircraft)

    res, _ = _make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution,
                               wind_direction, wind_speed)

    out_name = f'strike_{hour}h.tif'
    _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, res)


map.add_command(strike)


@click.command()
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.option('--aircraft', default=None, type=click.File(lazy=True),
              help='Aircraft config file. Uses built in defaults if not specified.')
@click.option('--failure_prob', default=5e-3, type=click.FLOAT, help='Probability of aircraft failure per flight hour.')
@click.option('--output-path', default='', type=click.Path(exists=True, writable=True),
              help='Output file path for geoTiff file')
@click.option('--resolution', default=40, type=click.INT, help='Resolution in metres of each pixel in the raster')
@click.option('--hour', default=13, type=click.INT, help='Hour of the week to generate map for. Must be 0<=h<=168')
@click.option('--altitude', default=120, type=click.FLOAT, help='Aircraft Altitude in metres')
@click.option('--airspeed', default=20, type=click.FLOAT, help='Aircraft Airspeed in m/s')
@click.option('--wind-direction', default=90, type=click.INT,
              help='The wind bearing. This is the direction the wind is coming from.')
@click.option('--wind_speed', default=5, type=click.FLOAT, help='Wind speed at the flight altitude in m/s')
def fatality(min_lat, max_lat, min_lon, max_lon, aircraft, failure_prob, output_path, resolution, hour, altitude,
             airspeed, wind_direction, wind_speed):
    """
    Fatality Risk map

    Generate a geotiff raster file of the probability of ground fatality with a specified aircraft in the specified
    bounds.

    If an aircraft config json file is not specified, a default aircraft with reasonable parameters is used.

    All coordinates should be in decimal degrees and form a non degenerate polygon.

    """
    bounds = make_bounds_polygon((min_lon, min_lat), (max_lon, max_lat))
    pop_grid = _make_pop_grid(bounds, hour, resolution)

    if not aircraft:
        aircraft = _setup_default_aircraft()
    else:
        aircraft = _import_aircraft(aircraft)

    strike_grid, v_is = _make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution,
                                          wind_direction, wind_speed)

    res = _make_fatality_grid(aircraft, strike_grid, v_is)

    out_name = f'fatality_{hour}h.tif'

    _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, res)


map.add_command(fatality)


# map
############################

############################
# path

@click.group()
def path():
    """
    Generate paths minimising risk measures
    """
    pass


main.add_command(path)


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.argument('start_lat', type=click.FLOAT, )
@click.argument('start_lon', type=click.FLOAT, )
@click.argument('end_lat', type=click.FLOAT, )
@click.argument('end_lon', type=click.FLOAT, )
@click.option('--aircraft', default=None, type=click.File(lazy=True),
              help='Aircraft config file. Uses built in defaults if not specified.')
@click.option('--failure_prob', default=5e-3, type=click.FLOAT, help='Probability of aircraft failure per flight hour.')
@click.option('--output-path', default='', type=click.Path(exists=True, writable=True),
              help='Output file path for geoTiff file')
@click.option('--resolution', default=40, type=click.INT, help='Resolution in metres of each pixel in the raster')
@click.option('--hour', default=13, type=click.INT, help='Hour of the week to generate map for. Must be 0<=h<=168')
@click.option('--altitude', default=120, type=click.FLOAT, help='Aircraft Altitude in metres')
@click.option('--airspeed', default=20, type=click.FLOAT, help='Aircraft Airspeed in m/s')
@click.option('--wind-direction', default=90, type=click.INT,
              help='The wind bearing. This is the direction the wind is coming from.')
@click.option('--wind_speed', default=5, type=click.FLOAT, help='Wind speed at the flight altitude in m/s')
@click.option('--algo', default='ra*', type=click.STRING,
              help='Pathfinding algorithm to use. Current options are ["ra*", "ga"]')
@click.argument('algorithm_args', nargs=-1, type=click.UNPROCESSED)
def make(min_lat, max_lat, min_lon, max_lon,
         start_lat, start_lon, end_lat, end_lon,
         aircraft, failure_prob, output_path, resolution, hour, altitude,
         airspeed, wind_direction, wind_speed,
         algo, algo_args):
    """
    Path minimising the fatality risk posed.

    Generate a path minimising the fatality risk posed by a specified aircraft in the specified
    bounds. The path is output as a GeoJSON file in the form of a LineString of EPSG:4326 coordinates in (lon, lat) order
    from start to end.

    If an aircraft config json file is not specified, a default aircraft with reasonable parameters is used.

    All coordinates should be in decimal degrees and form a non degenerate polygon.

    """
    bounds = make_bounds_polygon((min_lon, min_lat), (max_lon, max_lat))
    pop_grid = _make_pop_grid(bounds, hour, resolution)
    if not aircraft:
        aircraft = _setup_default_aircraft()
    else:
        aircraft = _import_aircraft(aircraft)
    strike_grid, v_is = _make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution,
                                          wind_direction, wind_speed)
    res = _make_fatality_grid(aircraft, strike_grid, v_is)

    raster_shape = res.shape
    raster_indices = dict(Longitude=np.linspace(min_lon, max_lon, num=raster_shape[0]),
                          Latitude=np.linspace(min_lat, max_lat, num=raster_shape[1]))
    start_x, start_y = snap_coords_to_grid(raster_indices, start_lat, start_lon)
    end_x, end_y = snap_coords_to_grid(raster_indices, end_lat, end_lon)

    env = GridEnvironment(res, diagonals=False)
    if algo == 'ra*':
        algo = RiskGridAStar(**algo_args)
    elif algo == 'ga':
        raise NotImplementedError("GA CLI not implemented yet")
        algo = GeneticAlgorithm([], **algo_args)
    path = algo.find_path(env, Node((start_y, start_x)), Node((end_y, end_x)))

    snapped_path = []
    for node in path:
        lat = raster_indices['Latitude'][node.position[0]]
        lon = raster_indices['Longitude'][node.position[1]]
        snapped_path.append((lon, lat))
    snapped_path = sg.LineString(snapped_path)
    dataframe = gpd.GeoDataFrame({'geometry': [snapped_path]}).set_crs('EPSG:4326')
    dataframe.to_file(os.path.join(output_path, f'path.geojson'), driver='GeoJSON')


# path
############################

def _make_fatality_grid(aircraft, strike_grid, v_is):
    fm = FatalityModel(0.3, 1e6, 34)
    ac_mass = aircraft.mass
    impact_ke_b = velocity_to_kinetic_energy(ac_mass, v_is[0])
    impact_ke_g = velocity_to_kinetic_energy(ac_mass, v_is[1])
    res = fm.transform(strike_grid, impact_ke=impact_ke_g) + fm.transform(strike_grid, impact_ke=impact_ke_b)
    return res


def _make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution, wind_direction, wind_speed):
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


def _make_pop_grid(bounds, hour, resolution):
    proj = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg('4326'),
                                       pyproj.CRS.from_epsg('3857'),
                                       always_xy=True)

    raster_shape = reproj_bounds(bounds, proj, resolution)
    layer = TemporalPopulationEstimateLayer('tpe')
    layer.preload_data()
    _, raster_grid, _ = layer.generate(bounds, raster_shape, hour=hour, resolution=resolution)

    return remove_raster_nans(raster_grid)


def _setup_default_aircraft(ac_width: float = 2, ac_length: float = 1.5,
                            ac_mass: float = 2, ac_glide_ratio: float = 12, ac_glide_speed: float = 15,
                            ac_glide_drag_coeff: float = 0.1, ac_ballistic_drag_coeff: float = 0.8,
                            ac_ballistic_frontal_area: float = 0.1):
    aircraft = casex.AircraftSpecs(casex.enums.AircraftType.FIXED_WING, ac_width, ac_length, ac_mass)
    aircraft.set_ballistic_drag_coefficient(ac_ballistic_drag_coeff)
    aircraft.set_ballistic_frontal_area(ac_ballistic_frontal_area)
    aircraft.set_glide_speed_ratio(ac_glide_speed, ac_glide_ratio)
    aircraft.set_glide_drag_coefficient(ac_glide_drag_coeff)

    return aircraft


def _import_aircraft(aircraft):
    pass


def _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, res):
    raster_shape = res.shape
    trans = transform.from_bounds((min_lon, min_lat), (max_lon, max_lat), *raster_shape)
    rds = rasterio.open(os.path.join(output_path, out_name),
                        'w', driver='GTiff', count=1, dtype=rasterio.float64,
                        crs='EPSG:4326', transform=trans, compress='lzw',
                        width=raster_shape[0], height=raster_shape[1])
    rds.write(res, 1)
    rds.close()


if __name__ == '__main__':
    main()
