from typing import Dict, Union, Tuple, Iterable, Any, Callable, NoReturn, Optional, List, Sequence

import geopandas as gpd
import numpy as np
import shapely.geometry as sg
from holoviews import Overlay, Element
from holoviews.element import Geometry

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.layers.data_layer import DataLayer
from seedpod_ground_risk.layers.layer import Layer


def make_bounds_polygon(*args: Iterable[float]) -> sg.Polygon:
    if len(args) == 2:
        return sg.box(args[1][0], args[0][0], args[1][1], args[0][1])
    elif len(args) == 4:
        return sg.box(*args)


def is_null(values: Any) -> bool:
    from numpy import isnan

    try:
        for value in values:
            if value is None or isnan(value):
                return True
    except TypeError:
        if values is None or isnan(values):
            return True
    return False


class PlotServer:
    data_layers: List[DataLayer]
    annotation_layers: List[AnnotationLayer]
    plot_size: Tuple[int, int]
    _cached_area: sg.Polygon
    _generated_data_layers: Dict[str, Geometry]

    # noinspection PyTypeChecker
    def __init__(self, tiles: str = 'Wikipedia', tools: Optional[Iterable[str]] = None,
                 active_tools: Optional[Iterable[str]] = None,
                 cmap: str = 'CET_L18',
                 plot_size: Tuple[int, int] = (760, 735),
                 progress_callback: Optional[Callable[[str], None]] = None,
                 update_callback: Optional[Callable[[str], None]] = None):
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

        import colorcet
        self.cmap = getattr(colorcet, cmap)

        from geoviews import tile_sources as gvts
        self._base_tiles = getattr(gvts, tiles)

        self._time_idx = 0

        from seedpod_ground_risk.layers.residential_layer import ResidentialLayer
        from seedpod_ground_risk.layers.roads_layer import RoadsLayer
        self._generated_data_layers = {}
        self.data_layer_order = []
        self.data_layers = [ResidentialLayer('Residential Population', buffer_dist=30),
                            RoadsLayer('Road Traffic Population per Hour')]

        self.annotation_layers = []

        self.plot_size = plot_size
        self._progress_callback = progress_callback if progress_callback is not None else lambda *args: None
        self._update_callback = update_callback if update_callback is not None else lambda *args: None

        self._x_range, self._y_range = [-1.45, -1.35], [50.85, 50.95]

        self._epsg3857_to_epsg4326_proj = None
        self._preload_started = False
        self._preload_complete = False

        from bokeh.io import curdoc
        from bokeh.server.server import Server

        self._current_plot = curdoc()
        self._server_thread = None
        self.server = Server({'/': self.plot}, num_procs=1)
        self.server.io_loop.spawn_callback(self._preload_layers)
        self.url = 'http://localhost:{port}/{prefix}'.format(port=self.server.port, prefix=self.server.prefix) \
            if self.server.address is None else self.server.address

    async def _preload_layers(self):
        from concurrent.futures.thread import ThreadPoolExecutor
        from tornado.gen import multi
        from itertools import chain

        with ThreadPoolExecutor() as pool:
            await multi([pool.submit(layer.preload_data) for layer in chain(self.data_layers, self.annotation_layers)])
            self._preload_complete = True
            self._progress_callback('Preload complete. First generation will take a minute longer')

    def start(self) -> NoReturn:
        """
        Start the plot server in a daemon thread
        """
        assert self.server is not None
        import threading

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

    def _reproject_ranges(self):
        import pyproj

        if self._epsg3857_to_epsg4326_proj is None:
            self._epsg3857_to_epsg4326_proj = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg('3857'),
                                                                          pyproj.CRS.from_epsg('4326'),
                                                                          always_xy=True)
        self._x_range[0], self._y_range[0] = self._epsg3857_to_epsg4326_proj.transform(self._x_range[0],
                                                                                       self._y_range[0])
        self._x_range[1], self._y_range[1] = self._epsg3857_to_epsg4326_proj.transform(self._x_range[1],
                                                                                       self._y_range[1])

    def plot(self, doc):
        import holoviews as hv

        if doc.roots:
            doc.clear()
            self._reproject_ranges()
        hvPlot = self.compose_overlay_plot(self._x_range, self._y_range)
        fig = hv.render(hvPlot, backend='bokeh')
        fig.output_backend = 'webgl'

        def update_range(n, val):
            if n == 'x0':
                self._x_range[0] = round(val, 2)
            elif n == 'x1':
                self._x_range[1] = round(val, 2)
            elif n == 'y0':
                self._y_range[0] = round(val, 2)
            elif n == 'y1':
                self._y_range[1] = round(val, 2)

        fig.x_range.on_change('start', lambda attr, old, new: update_range('x0', new))
        fig.x_range.on_change('end', lambda attr, old, new: update_range("x1", new))
        fig.y_range.on_change('start', lambda attr, old, new: update_range("y0", new))
        fig.y_range.on_change('end', lambda attr, old, new: update_range("y1", new))

        doc.add_root(fig)
        self._current_plot = doc

    def generate_map(self):
        self._current_plot.add_next_tick_callback(lambda *args: self.plot(self._current_plot))

    def compose_overlay_plot(self, x_range: Optional[Sequence[float]] = (-1.6, -1.2),
                             y_range: Optional[Sequence[float]] = (50.8, 51.05)) \
            -> Union[Overlay, Element]:
        """
        Compose all generated HoloViews layers in self.data_layers into a single overlay plot.
        Overlaid in a first-on-the-bottom manner.

        If plot bounds has moved outside of data bounds, generate more as required.

        :param tuple x_range: (min, max) longitude range in EPSG:4326 coordinates
        :param tuple y_range: (min, max) latitude range in EPSG:4326 coordinates
        :returns: overlay plot of stored layers
        """
        from itertools import chain

        try:
            if not self._preload_complete:
                # If layers aren't preloaded yet just return the map tiles
                self._progress_callback('Still preloading layer data...')
                plot = self._base_tiles
            else:
                # Construct box around requested bounds
                bounds_poly = make_bounds_polygon(x_range, y_range)
                # Ensure bounds are small enough to render without OOM or heat death of universe
                if bounds_poly.area < 0.2:
                    from time import time

                    t0 = time()
                    self.generate_layers(bounds_poly)
                    self._progress_callback("Rendering new map...")
                    plot = Overlay([res[0] for res in self._generated_data_layers.values()])
                    print("Generated all layers in ", time() - t0)
                    if self.annotation_layers:
                        import matplotlib.pyplot as mpl
                        plot = Overlay([res[0] for res in self._generated_data_layers.values()])
                        raw_datas = [res[2] for res in self._generated_data_layers.values()]
                        raster_indices = dict(Longitude=np.linspace(x_range[0], x_range[1], num=400),
                                              Latitude=np.linspace(y_range[0], y_range[1], num=400))
                        raster_grid = np.zeros((400, 400), dtype=np.float64)
                        for res in self._generated_data_layers.values():
                            layer_raster_grid = res[1]
                            nans = np.isnan(layer_raster_grid)
                            layer_raster_grid[nans] = 0
                            raster_grid += res[1]

                        annotations = []
                        for layer in self.annotation_layers:
                            annotation = layer.annotate(raw_datas, (raster_indices, raster_grid))
                            if annotation:
                                annotations.append(annotation)

                        annotation_overlay = Overlay(annotations)
                        plot = Overlay([self._base_tiles, plot, annotation_overlay]).collate()
                    else:
                        plot = Overlay([self._base_tiles, plot]).collate()

                else:
                    self._progress_callback('Area too large to render!')
                    if not self._generated_data_layers:
                        plot = self._base_tiles
                    else:
                        plot = Overlay([self._base_tiles, *list(self._generated_data_layers.values())])

                layers = []
                for layer in chain(self.data_layers, self.annotation_layers):
                    d = {'key': layer.key}
                    if hasattr(layer, '_colour'):
                        d.update(colour=layer._colour)
                    if hasattr(layer, '_osm_tag'):
                        d.update(dataTag=layer._osm_tag)
                    layers.append(d)

                self._update_callback(list(chain(self.data_layers, self.annotation_layers)))

        except Exception as e:
            # Catch-all to prevent plot blanking out and/or crashing app
            # Just display map tiles in case this was transient
            print(e)
            plot = self._base_tiles

        return plot.opts(width=self.plot_size[0], height=self.plot_size[1],
                         tools=self.tools, active_tools=self.active_tools)

    def generate_layers(self, bounds_poly: sg.Polygon) -> NoReturn:
        """
        Generate static layers of map

        :param shapely.geometry.Polygon bounds_poly: the bounding polygon for which to generate the map
        """
        # Polygons aren't much use without a base map context
        assert self.data_layers is not None
        from concurrent.futures import as_completed
        from concurrent.futures.thread import ThreadPoolExecutor

        layers = {}
        self._progress_callback('Generating layer data')
        with ThreadPoolExecutor() as pool:
            layer_futures = [pool.submit(self.generate_layer, layer, bounds_poly, self._time_idx) for layer in
                             self.data_layers]
        # Store generated layers as they are completed
        for future in as_completed(layer_futures):
            key, result = future.result()
            # Store layer
            # Lock not needed as this loop is synchronous
            if result:
                layers[key] = result

        # Remove layers with explicit ordering
        # so they are can be reinserted in the correct order instead of updated in place
        self._generated_data_layers.clear()
        if not self.data_layer_order:
            self._generated_data_layers.update(dict(list(layers.items())[::-1]))
        else:
            # Add layers in order
            self._generated_data_layers.update({k: layers[k] for k in self.data_layer_order if k in layers})
            # # Add any new layers last
            self._generated_data_layers.update(
                {k: layers[k] for k in layers.keys() if k not in self._generated_data_layers})

    @staticmethod
    def generate_layer(layer: DataLayer, bounds_poly: sg.Polygon, hour: int) -> Union[
        Tuple[str, Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]], Tuple[str, None]]:
        import shapely.ops as so

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
        try:
            result = layer.key, layer.generate(layer_bounds_poly, from_cache=from_cache, hour=hour)
            return result
        except Exception as e:
            print(e)
            return layer.key + ' FAILED', None

    def set_rasterise(self, val: bool) -> None:
        self.rasterise = val
        for layer in self.data_layers:
            layer.rasterise = val

    def set_time(self, hour: int) -> None:
        self._time_idx = hour

    def add_layer(self, layer: Layer):
        layer.preload_data()
        if isinstance(layer, DataLayer):
            self.data_layers.append(layer)
        elif isinstance(layer, AnnotationLayer):
            self.annotation_layers.append(layer)

    def remove_layer(self, layer):
        if layer in self.data_layers:
            self.data_layers.remove(layer)
        elif layer in self.annotation_layers:
            self.annotation_layers.remove(layer)

    def set_layer_order(self, layer_order):
        self.data_layer_order = layer_order

    def _get_raster_dimensions(self, bounds_poly: sg.Polygon, raster_resolution_m: float) -> Tuple[int, int]:
        """
        Return a the (x,y) shape of a raster grid given its EPSG4326 envelope and desired raster resolution
        :param bounds_poly: EPSG4326 Shapely Polygon specifying bounds
        :param raster_resolution_m: raster resolution in metres
        :return: 2-tuple of (width, height)
        """

        import pyproj

        if self._epsg4326_to_epsg3857_proj:
            self._epsg4326_to_epsg3857_proj = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg('4326'),
                                                                          pyproj.CRS.from_epsg('3857'),
                                                                          always_xy=True)
        bounds = bounds_poly.bounds

        min_x, min_y = self._epsg4326_to_epsg3857_proj.transform(bounds[1], bounds[0])
        max_x, max_y = self._epsg4326_to_epsg3857_proj.transform(bounds[3], bounds[2])
        raster_width = abs(max_x-min_x) % raster_resolution_m
        raster_height = abs(max_y - min_y) % raster_resolution_m
        return raster_width, raster_height
