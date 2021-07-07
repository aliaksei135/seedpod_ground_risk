import click

from seedpod_ground_risk.api.api import *
from seedpod_ground_risk.core.utils import make_bounds_polygon


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


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.option('--output-path', default='.', type=click.Path(exists=True, writable=True),
              help='Output file path for geoTiff file')
@click.option('--resolution', default=40, type=click.INT, help='Resolution in metres of each pixel in the raster')
@click.option('--hour', default=13, type=click.INT, help='Hour of the week to generate map for. Must be 0<=h<=168')
def pop_density(min_lat, max_lat, min_lon, max_lon, output_path, resolution, hour):
    """
    Temporal Population Density map

    Generate a geotiff raster file of the population density in the specified bounds.

    All coordinates should be in decimal degrees and form a non degenerate polygon.

    """
    bounds = make_bounds_polygon((min_lon, max_lon), (min_lat, max_lat))
    raster_grid = make_pop_grid(bounds, hour, resolution)

    out_name = f'pop_density_{hour}h.tif'
    _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, raster_grid)


map.add_command(pop_density)


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.option('--aircraft', default=None, type=click.File(lazy=True),
              help='Aircraft config file. Uses built in defaults if not specified.')
@click.option('--failure_prob', default=5e-3, type=click.FLOAT, help='Probability of aircraft failure per flight hour.')
@click.option('--output-path', default='.', type=click.Path(exists=True, writable=True),
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
    bounds = make_bounds_polygon((min_lon, max_lon), (min_lat, max_lat))
    pop_grid = make_pop_grid(bounds, hour, resolution)

    if not aircraft:
        aircraft = _setup_default_aircraft()
    else:
        aircraft = _import_aircraft(aircraft)

    res, _ = make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution,
                              wind_direction, wind_speed)

    out_name = f'strike_{hour}h.tif'
    _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, res)


map.add_command(strike)


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('min_lat', type=click.FLOAT, )
@click.argument('max_lat', type=click.FLOAT, )
@click.argument('min_lon', type=click.FLOAT, )
@click.argument('max_lon', type=click.FLOAT, )
@click.option('--aircraft', default=None, type=click.File(lazy=True),
              help='Aircraft config file. Uses built in defaults if not specified.')
@click.option('--failure_prob', default=5e-3, type=click.FLOAT, help='Probability of aircraft failure per flight hour.')
@click.option('--output-path', default='.', type=click.Path(exists=True, writable=True),
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
    bounds = make_bounds_polygon((min_lon, max_lon), (min_lat, max_lat))
    pop_grid = make_pop_grid(bounds, hour, resolution)

    if not aircraft:
        aircraft = _setup_default_aircraft()
    else:
        aircraft = _import_aircraft(aircraft)

    strike_grid, v_is = make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution,
                                         wind_direction, wind_speed)

    res = make_fatality_grid(aircraft, strike_grid, v_is)

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
@click.option('--output-path', default='.', type=click.Path(exists=True, writable=True),
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
@click.argument('algo_args', nargs=-1, type=click.UNPROCESSED)
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
    import geopandas as gpd
    import os

    bounds = make_bounds_polygon((min_lon, max_lon), (min_lat, max_lat))
    pop_grid = make_pop_grid(bounds, hour, resolution)
    if not aircraft:
        aircraft = _setup_default_aircraft()
    else:
        aircraft = _import_aircraft(aircraft)
    strike_grid, v_is = make_strike_grid(aircraft, airspeed, altitude, failure_prob, pop_grid, resolution,
                                         wind_direction, wind_speed)
    res = make_fatality_grid(aircraft, strike_grid, v_is)

    snapped_path = make_path(res, bounds, (start_lat, start_lon), (end_lat, end_lon), algo=algo)
    if snapped_path:
        dataframe = gpd.GeoDataFrame({'geometry': [snapped_path]}).set_crs('EPSG:4326')
        dataframe.to_file(os.path.join(output_path, f'path.geojson'), driver='GeoJSON')
    else:
        print('Path could not be found')


# path
############################


def _setup_default_aircraft(ac_width: float = 2, ac_length: float = 1.5,
                            ac_mass: float = 7, ac_glide_ratio: float = 12, ac_glide_speed: float = 15,
                            ac_glide_drag_coeff: float = 0.1, ac_ballistic_drag_coeff: float = 0.8,
                            ac_ballistic_frontal_area: float = 0.1):
    import casex
    aircraft = casex.AircraftSpecs(casex.enums.AircraftType.FIXED_WING, ac_width, ac_length, ac_mass)
    aircraft.set_ballistic_drag_coefficient(ac_ballistic_drag_coeff)
    aircraft.set_ballistic_frontal_area(ac_ballistic_frontal_area)
    aircraft.set_glide_speed_ratio(ac_glide_speed, ac_glide_ratio)
    aircraft.set_glide_drag_coefficient(ac_glide_drag_coeff)

    return aircraft


def _import_aircraft(aircraft):
    import json
    import casex

    params = json.load(aircraft)
    basic_params = params['basic']
    ballistic_params = params['ballistic']
    gliding_params = params['glide']

    aircraft = casex.AircraftSpecs(casex.enums.AircraftType.FIXED_WING, basic_params['width'], basic_params['length'],
                                   basic_params['mass'])
    aircraft.set_ballistic_drag_coefficient(ballistic_params['drag_coeff'])
    aircraft.set_ballistic_frontal_area(ballistic_params['frontal_area'])
    aircraft.set_glide_speed_ratio(gliding_params['airspeed'], gliding_params['glide_ratio'])
    aircraft.set_glide_drag_coefficient(gliding_params['drag_coeff'])

    return aircraft


def _write_geotiff(max_lat, max_lon, min_lat, min_lon, out_name, output_path, res):
    import rasterio
    import os
    raster_shape = res.shape
    trans = rasterio.transform.from_bounds(min_lon, min_lat, max_lon, max_lat, *raster_shape)
    rds = rasterio.open(os.path.join(output_path, out_name),
                        'w', driver='GTiff', count=1, dtype=rasterio.float64,
                        crs='EPSG:4326', transform=trans, compress='lzw',
                        width=raster_shape[0], height=raster_shape[1])
    rds.write(res, 1)
    rds.close()


if __name__ == '__main__':
    main()
