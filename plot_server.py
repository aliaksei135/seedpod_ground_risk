import threading
from concurrent.futures import wait, as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from itertools import chain
from typing import Dict, Union, Tuple, Iterable, Any, Callable, NoReturn, Optional

import colorcet
import geopandas as gpd
import geoviews as gv
import panel as pn
import shapely.geometry as sg
import shapely.ops as so
import shapely.speedups
from bokeh.server.server import Server
from geoviews import tile_sources as gvts
from holoviews import DynamicMap, Overlay, Element
from holoviews.element import Geometry
from holoviews.streams import RangeXY
from numpy import isnan

from layer import Layer
from layers.geojson_layer import GeoJSONLayer
from layers.residential_layer import ResidentialLayer
from layers.roads_layer import RoadsLayer

gpd.options.use_pygeos = True
shapely.speedups.enable()

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
    static_layers: Iterable[Layer]
    server: Server
    plot_size: Tuple[int, int]
    _current_bounds: sg.Polygon
    _cached_area: sg.Polygon
    _generated_layers: Dict[str, Geometry]

    # noinspection PyTypeChecker
    def __init__(self, tiles: str = 'Wikipedia', tools: Optional[Iterable[str]] = None,
                 active_tools: Optional[Iterable[str]] = None,
                 rasterise: bool = True,
                 cmap: str = 'CET_L18',
                 plot_size: Tuple[int, int] = (770, 740),
                 progress_callback: Optional[Callable[[str], None]] = None,
                 update_callback: Optional[Callable[[], None]] = None):
        """
        Initialise a Plot Server
        :param str tiles: a geoviews.tile_sources attribute string from http://geoviews.org/gallery/bokeh/tile_sources.html#bokeh-gallery-tile-sources
        :param List[str] tools: the bokeh tools to make available for the plot from https://docs.bokeh.org/en/latest/docs/user_guide/tools.html
        :param List[str] active_tools: the subset of `tools` that should be enabled by default
        :param bool rasterise: Whether to opportunistically raster layers
        :param cmap: a colorcet attribute string for the colourmap to use from https://colorcet.holoviz.org/user_guide/Continuous.html
        :param Tuple[int, int] plot_size: the plot size in (width, height) order
        :param progress_callback: an optional callable that takes a string updating progress
        :param update_callback: an optional callable that is called before an plot is rendered
        """
        self.tools = ['hover', 'crosshair'] if tools is None else tools
        self.active_tools = ['wheel_zoom'] if active_tools is None else active_tools
        self.rasterise = rasterise
        self.cmap = getattr(colorcet, cmap)
        self._layers_lock = threading.Lock()
        self._generated_layers = {'base': getattr(gvts, tiles)}
        self.static_layers = [GeoJSONLayer('static_data/test_path.json', rasterise=False),
                              ResidentialLayer(rasterise=rasterise),
                              RoadsLayer(rasterise=rasterise)]
        self.callback_streams = [RangeXY()]
        self.plot_size = plot_size
        self._progress_callback = progress_callback
        self._update_callback = update_callback

        self._thread_pool = ThreadPoolExecutor()
        self._cached_area_lock = threading.Lock()
        self._cached_area = sg.Polygon()
        self._current_bounds = make_bounds_polygon(50.87, -1.5, 51.00, -1.3)

        wait([self._thread_pool.submit(layer.preload_data) for layer in chain(self.static_layers)])
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
            self._progress_callback('Plot Server starting...')
            self.server.start()
            self._server_thread = threading.Thread(target=self.server.io_loop.start, daemon=True)
        self._server_thread.start()
        self._progress_callback('Preloading data')

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
        if not is_null(x_range) and not is_null(y_range):
            # Construct box around requested bounds
            bounds_poly = make_bounds_polygon(x_range, y_range)
            # Ensure bounds are small enough to render without OOM or heat death of universe
            if bounds_poly.area < 0.2:
                self._progress_callback('Area renderable')
                # If new bounds are contained within existing bounds do nothing
                # as polygons are already rendered
                # If rasterising layers this must be called each map update to avoud loss of raster resolution
                if self.rasterise or not self._current_bounds.contains(bounds_poly):
                    self.generate_static_layers(bounds_poly)
                    self._current_bounds = bounds_poly
                    self._progress_callback("Rendering new map...")
            else:
                self._progress_callback('Area too large to render')

        plot = Overlay(list(self._generated_layers.values())).collate()
        self._update_callback()
        return plot.opts(width=self.plot_size[0], height=self.plot_size[1],
                         tools=self.tools, active_tools=self.active_tools)

    def generate_static_layers(self, bounds_poly: sg.Polygon) -> NoReturn:
        """
        Generate static layers of map
        :param shapely.geometry.Polygon bounds_poly: the bounding polygon for which to generate the map
        """
        # Polygons aren't much use without a base map context
        assert self.static_layers is not None

        self._progress_callback('Generating layer data')
        layer_futures = [self._thread_pool.submit(self.generate_layer, layer, bounds_poly) for layer in
                         self.static_layers]
        # Store generated layers as they are completed
        for future in as_completed(layer_futures):
            layer_key, geom = future.result()
            # Store layer
            # Lock not needed as this loop is synchronous
            self._generated_layers[layer_key] = geom

        try:
            self._progress_callback('Calling plot update')
            # Calling the stream event with None kwargs results into plot regenerating without firing bounds update
            self._current_plot.event(x_range=None, y_range=None)
        except AttributeError:
            pass

    @staticmethod
    def generate_layer(layer: Layer, bounds_poly: sg.Polygon) -> Tuple[str, Geometry]:
        from_cache = False
        layer_bounds_poly = bounds_poly
        if bounds_poly.within(layer.cached_area):
            # Requested bounds are fully inside the area that has been generated already
            from_cache = True
        elif bounds_poly.intersects(layer.cached_area):
            # Some of the requested bounds are outside the generated area
            # Get only the area that needs to be generated
            layer_bounds_poly = bounds_poly.difference(layer.cached_area)
        layer.cached_area = so.unary_union([layer.cached_area, bounds_poly])
        return layer.key, layer.generate(layer_bounds_poly, from_cache=from_cache)
