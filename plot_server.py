import os
import threading
from concurrent.futures import wait
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Union, Tuple, Iterable, Any, Callable, NoReturn, Optional

import colorcet
import geopandas as gpd
import geoviews as gv
import pandas as pd
import panel as pn
import shapely.geometry as sg
import shapely.ops as so
from bokeh.server.server import Server
from geoviews import tile_sources as gvts
from holoviews import DynamicMap, Overlay, Element
from holoviews.streams import RangeXY
from numpy import isnan

# import spatialpandas as spd
# import dask.dataframe as dd
# import datashader as ds
# import datashader.transfer_functions as dstf
# import datashader.spatial.points as dsp
# from holoviews.operation.datashader import datashade, shade, spread, dynspread, rasterize

gpd.options.use_pygeos = True

import shapely.speedups

shapely.speedups.enable()

import requests

gv.extension('bokeh')
gv.output(backend='bokeh')


def make_bounds_polygon(*args: Iterable[float]) -> sg.Polygon:
    if len(args) == 2:
        return sg.box(args[1][0], args[0][0], args[1][1], args[0][1])
    elif len(args) == 4:
        return sg.box(*args)


def is_null(values: Any) -> bool:
    try:
        for value in values:
            if value is None or isnan(value):
                return True
    except TypeError:
        if values is None or isnan(values):
            return True
    return False


class PlotServer:
    layers: Dict[str, Union[Overlay, Element]]
    server: Server
    _cached_area: sg.Polygon
    _census_wards: gpd.GeoDataFrame
    _landuse_polygons: Dict[str, gpd.GeoDataFrame]
    _current_bounds: sg.Polygon

    # noinspection PyTypeChecker
    def __init__(self, tiles: str = 'Wikipedia', tools: Optional[Iterable[str]] = None,
                 active_tools: Optional[Iterable[str]] = None,
                 cmap: str = 'CET_L18',
                 plot_size: Tuple[int, int] = (770, 740),
                 progress_callback: Optional[Callable[[str], None]] = None,
                 update_callback: Optional[Callable[[], None]] = None):
        self.tools = ['hover', 'crosshair'] if tools is None else tools
        self.active_tools = ['wheel_zoom'] if active_tools is None else active_tools
        self.cmap = getattr(colorcet, cmap)
        self._layers_lock = threading.Lock()
        self.layers = {'base': getattr(gvts, tiles)}
        self.callback_streams = [RangeXY()]
        self.plot_size = plot_size
        self._progress_callback = progress_callback
        self._update_callback = update_callback

        self._thread_pool = ThreadPoolExecutor()
        self._cached_area_lock = threading.Lock()
        self._cached_area = None
        self._census_wards_lock = threading.Lock()
        self._census_wards = None
        self._landuse_polygons_lock = threading.Lock()
        self._landuse_polygons = {}
        self._current_bounds = make_bounds_polygon(50.87, -1.5, 51.00, -1.3)

        self.generate_static_layers(self._current_bounds)

        self._current_plot = DynamicMap(self.compose_overlay_plot, streams=self.callback_streams)
        self.server = pn.serve(self._current_plot, start=False, show=False)
        self._server_thread = None
        self.url = 'http://localhost:{port}/{prefix}'.format(port=self.server.port, prefix=self.server.prefix) \
            if self.server.address is None else self.server.address

    def start(self) -> NoReturn:
        """
        Start the plot server in a daemon thread
        """
        assert self.server is not None
        if self._server_thread is None:
            self.server.start()
            self._server_thread = threading.Thread(target=self.server.io_loop.start, daemon=True)
        self._server_thread.start()
        self._progress_callback('Plot Server started')

    def stop(self) -> NoReturn:
        """
        Stop the plot server if running
        """
        assert self.server is not None
        if self._server_thread is not None:
            if self._server_thread.is_alive():
                self._server_thread.join()
                self._progress_callback('Plot Server stopped')

    def compose_overlay_plot(self, x_range: Optional[Tuple[float, float]] = (-1.6, -1.2),
                             y_range: Optional[Tuple[float, float]] = (50.8, 51.05)) \
            -> Union[Overlay, Element, DynamicMap]:
        """
        Compose all generated HoloViews layers in self.layers into a single overlay plot.
        Overlaid in a first-on-the-bottom manner.
        If plot bounds has moved outside of data bounds, generate more as required.
        :param tuple x_range: (min, max) longitude range in EPSG:4326 coordinates
        :param tuple y_range: (min, max) latitude range in EPSG:4326 coordinates
        :returns overlay plot of stored layers
        """
        if self._cached_area is not None:
            self._progress_callback('Cache exists')
            if not is_null(x_range) and not is_null(y_range):
                # Construct box around requested bounds
                bounds_poly = make_bounds_polygon(x_range, y_range)
                # Ensure bounds are small enough to render without OOM or heat death of universe
                if bounds_poly.area < 0.2:
                    self._progress_callback('Area renderable')
                    # If new bounds are contained within existing bounds do nothing
                    # as polygons are already rendered
                    if not self._current_bounds.contains(bounds_poly):
                        # Check if bounds box is *fully* contained within the cached area polygon,
                        # if so generate only from cache, otherwise generate new data
                        # TODO: Generating map synchronously won't scale with more layers
                        self.generate_static_layers(bounds_poly, from_cache=self._cached_area.contains(bounds_poly))
                        self._current_bounds = bounds_poly
                else:
                    self._progress_callback('Area too large to render')

        layers = list(self.layers.values())
        plot = Overlay(layers)
        self._progress_callback("Rendering new map...")
        self._update_callback()
        return plot.opts(width=self.plot_size[0], height=self.plot_size[1])

    def generate_static_layers(self, bounds_poly: sg.Polygon, from_cache: Optional[bool] = False) -> NoReturn:
        """
        Generate static layers of map
        """
        # Polygons aren't much use without a base map context
        assert self.layers is not None
        # TODO: Generalise for arbitrary landuse keys
        landuse = 'residential'

        bounds = bounds_poly.bounds
        if not from_cache:
            # TODO: Multiple duplicate statements weaving in and out of concurrency
            if self._census_wards is None:
                # Some gain in concurrently running these
                self._progress_callback('Ingesting Census Data')
                census_future = self._thread_pool.submit(self.ingest_census_data)
                self._progress_callback('Querying OSM Landuse')
                osm_future = self._thread_pool.submit(self.query_osm_landuse_polygons, bounds_poly, landuse=landuse)
                wait([census_future])
                assert self._census_wards is not None
                bounded_census_wards = self._census_wards.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]
                wait([osm_future])
                assert landuse in self._landuse_polygons
            else:
                self._progress_callback('Querying OSM Landuse')
                osm_future = self._thread_pool.submit(self.query_osm_landuse_polygons, bounds_poly, landuse=landuse)
                bounded_census_wards = self._census_wards.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]
                wait([osm_future])
                assert landuse in self._landuse_polygons
        else:
            bounded_census_wards = self._census_wards.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]

        self._progress_callback('Overlaying census and OSM polys')
        # Find landuse polygons intersecting/within census wards and merge left
        census_df = gpd.overlay(self._landuse_polygons[landuse],
                                bounded_census_wards,
                                how='intersection')
        # Estimate the population of landuse polygons from the density of the census ward they are within
        # EPSG:4326 is *not* an equal area projection so would give gibberish areas
        # Project geometries to an equidistant/equal areq projection
        census_df['population'] = census_df['density'] * census_df['geometry'].to_crs('EPSG:4088').area

        # Scale to reduce error for smaller, less dense wards
        # This was found empirically minimising the population error in 10 random villaegs in Hampshire
        def scale_pop(x):
            if 0 < x < 3000:
                return 0.998 * x + 6
            else:
                return x

        # Actually perform the populations scaling
        census_df['population'] = census_df['population'].apply(scale_pop)
        # Construct the GeoViews Polygons
        self._progress_callback('Constructing Polygons')
        gv_polys = gv.Polygons(census_df, vdims=['name', 'population']) \
            .opts(tools=self.tools,
                  active_tools=self.active_tools,
                  cmap=self.cmap,
                  color='population',
                  colorbar=True, colorbar_opts={'title': 'Population'}, show_legend=False)
        # Store layer
        with self._layers_lock:
            self.layers[landuse] = gv_polys
        try:
            self._progress_callback('Calling plot update')
            # Calling the stream event with None kwargs results into plot regenerating without firing bounds update
            self._current_plot.event(x_range=None, y_range=None)
        except AttributeError:
            pass

    def query_osm_landuse_polygons(self, bound_poly: sg.Polygon, landuse: Optional[str] = 'residential') -> NoReturn:
        """
        Perform blocking query on OpenStreetMaps Overpass API for objects with the passed landuse.
        Retain only polygons and store in GeoPandas GeoDataFrame
        :param shapely.Polygon bound_poly: bounding box around requested area in EPSG:4326 coordinates
        :param str landuse: OSM landuse key from https://wiki.openstreetmap.org/wiki/Landuse
        """
        if self._cached_area is not None:
            if self._cached_area.contains(bound_poly):
                # Requested bounds are fully inside the area that has been generated already
                return
            elif self._cached_area.intersects(bound_poly):
                # Some of the requested bounds are outside the generated area
                # Get only the area that needs to be generated
                bound_poly = bound_poly.difference(self._cached_area)

        bounds = bound_poly.bounds
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = """
            [out:json]
            [timeout:120]
            [bbox:{s_bound}, {w_bound}, {n_bound}, {e_bound}];
            (
                node[landuse={landuse}];
                way[landuse={landuse}];
                rel[landuse={landuse}];
            ); 
            out center body;
            >;
            out center qt;
        """.format(landuse=landuse,
                   s_bound=bounds[0], w_bound=bounds[1], n_bound=bounds[2], e_bound=bounds[3])
        resp = requests.get(overpass_url, params={'data': query})
        data = resp.json()

        ways = [o for o in data['elements'] if o['type'] == 'way']
        nodes = {o['id']: (o['lon'], o['lat']) for o in data['elements'] if o['type'] == 'node'}

        df_list = []
        # Iterate polygons ways
        for element in ways:
            # Find the vertices (AKA nodes) that make up each polygon
            locs = [nodes[id] for id in element['nodes']]
            # Not a polygon if less than 3 vertices, so ignore
            if len(locs) < 3:
                continue
            # Add Shapely polygon to list
            poly = sg.Polygon(locs)
            df_list.append([poly])
        # df_list = [sg.Polygon([nodes[id] for id in element['nodes']]) for element in ways]
        assert len(df_list) > 0
        # OSM uses Web Mercator so set CRS without projecting as CRS is known
        poly_df = gpd.GeoDataFrame(df_list, columns=['geometry']).set_crs('EPSG:4326')

        with self._landuse_polygons_lock:
            # Construct gdf
            if landuse not in self._landuse_polygons:
                self._progress_callback('Initialised landuse polygon cache')
                self._landuse_polygons[landuse] = poly_df
            else:
                self._landuse_polygons[landuse] = self._landuse_polygons[landuse].append(poly_df)
                self._landuse_polygons[landuse].drop_duplicates(subset='geometry', inplace=True, ignore_index=True)

        with self._cached_area_lock:
            if self._cached_area is None:
                self._cached_area = bound_poly
            else:
                self._cached_area = so.unary_union([self._cached_area, bound_poly])

    def ingest_census_data(self) -> NoReturn:
        """
        Ingest Census boundaries and density values and overlay/merge
        """
        # Import Census boundaries in Ordnance Survey grid and reproject
        census_wards_df = gpd.read_file(os.sep.join(('static_data', 'england_wa_2011_clipped.shp'))).drop(
            ['altname', 'oldcode'], axis=1).set_crs(
            'EPSG:27700').to_crs('EPSG:4326')
        # Import census ward densities
        density_df = pd.read_csv(os.sep.join(('static_data', 'density.csv')), header=0)
        # Scale from hectares to m^2
        density_df['area'] = density_df['area'] * 10000
        density_df['density'] = density_df['density'] / 10000

        with self._census_wards_lock:
            # These share a common UID, so merge together on it and store
            self._census_wards = census_wards_df.merge(density_df, on='code')
