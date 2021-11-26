from typing import Dict, Union, Tuple, Iterable, Callable, NoReturn, Optional, List, Sequence

import geopandas as gpd
import joblib as jl
import numpy as np
import shapely.geometry as sg
from holoviews import Overlay, Element
from holoviews.element import Geometry

from seedpod_ground_risk.core.utils import make_bounds_polygon, remove_raster_nans, reproj_bounds
from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.layers.data_layer import DataLayer
from seedpod_ground_risk.layers.fatality_risk_layer import FatalityRiskLayer
from seedpod_ground_risk.layers.layer import Layer


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
                 raster_resolution: float = 40,
                 plot_size: Tuple[int, int] = (760, 735),
                 progress_callback: Optional[Callable[[str], None]] = None,
                 update_callback: Optional[Callable[[str], None]] = None,
                 progress_bar_callback: Optional[Callable[[int], None]] = None):
        """
        Initialise a Plot Server

        :param str tiles: a geoviews.tile_sources attribute string from http://geoviews.org/gallery/bokeh/tile_sources.html#bokeh-gallery-tile-sources
        :param List[str] tools: the bokeh tools to make available for the plot from https://docs.bokeh.org/en/latest/docs/user_guide/tools.html
        :param List[str] active_tools: the subset of `tools` that should be enabled by default
        :param cmap: a colorcet attribute string for the colourmap to use from https://colorcet.holoviz.org/user_guide/Continuous.html
        :param raster_resolution: resolution of a single square of the raster pixel grid in metres
        :param Tuple[int, int] plot_size: the plot size in (width, height) order
        :param progress_callback: an optional callable that takes a string updating progress
        :param update_callback: an optional callable that is called before an plot is rendered
        :param progress_bar_callback: an optional callback that takes an integer updating the progress bar
        """
        self.tools = ['crosshair'] if tools is None else tools
        self.active_tools = ['wheel_zoom'] if active_tools is None else active_tools

        import colorcet
        self.cmap = getattr(colorcet, cmap)

        from geoviews import tile_sources as gvts
        self._base_tiles = getattr(gvts, tiles)

        self._time_idx = 0

        self._generated_data_layers = {}
        self.data_layer_order = []
        self.data_layers = [
            # TemporalPopulationEstimateLayer('Temporal Pop. Est'),
            # RoadsLayer('Road Traffic Population/Hour')
            FatalityRiskLayer('Fatality Risk'),
            # ResidentialLayer('Residential Layer')
        ]

        self.annotation_layers = []

        self.plot_size = plot_size
        self._progress_callback = progress_callback if progress_callback is not None else lambda *args: None
        self._update_callback = update_callback if update_callback is not None else lambda *args: None
        self._progress_bar_callback = progress_bar_callback if progress_bar_callback is not None else lambda *args: None

        self._x_range, self._y_range = [-1.45, -1.35], [50.85, 50.95]

        self.raster_resolution_m = raster_resolution

        self._epsg4326_to_epsg3857_proj = None
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
            self._progress_bar_callback(0)

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
            self._progress_callback(10)
        hvPlot = self.compose_overlay_plot(self._x_range, self._y_range)
        if self._preload_complete:
            self._progress_bar_callback(100)
            self._progress_callback("Plotting complete")
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
        try:
            if not self._preload_complete:
                # If layers aren't preloaded yet just return the map tiles
                self._progress_callback('Still preloading layer data...')
                plot = self._base_tiles
            else:
                # Construct box around requested bounds
                bounds_poly = make_bounds_polygon(x_range, y_range)
                raster_shape = self._get_raster_dimensions(bounds_poly, self.raster_resolution_m)
                # Ensure bounds are small enough to render without OOM or heat death of universe
                if (raster_shape[0] * raster_shape[1]) < 7e5:
                    from time import time

                    t0 = time()
                    self._progress_bar_callback(10)
                    # TODO: This will give multiple data layers, these need to be able to fed into their relevent pathfinding layers
                    for annlayer in self.annotation_layers:
                        new_layer = FatalityRiskLayer('Fatality Risk', ac=annlayer.aircraft['name'])
                        self.add_layer(new_layer)
                    self.remove_duplicate_layers()
                    self._progress_bar_callback(20)
                    self.generate_layers(bounds_poly, raster_shape)
                    self._progress_bar_callback(50)
                    plt_lyr = list(self._generated_data_layers)[0]
                    plot = Overlay([self._generated_data_layers[plt_lyr][0]])
                    print("Generated all layers in ", time() - t0)
                    if self.annotation_layers:
                        plot = Overlay([self._generated_data_layers[plt_lyr][0]])
                        res = []
                        for dlayer in self.data_layers:
                            raster_indices = dict(Longitude=np.linspace(x_range[0], x_range[1], num=raster_shape[0]),
                                                  Latitude=np.linspace(y_range[0], y_range[1], num=raster_shape[1]))
                            raw_data = [self._generated_data_layers[dlayer.key][2]]
                            raster_grid = np.sum(
                                [remove_raster_nans(self._generated_data_layers[dlayer.key][1])],
                                axis=0)
                            raster_grid = np.flipud(raster_grid)
                            raster_indices['Latitude'] = np.flip(raster_indices['Latitude'])

                            for alayer in self.annotation_layers:
                                if alayer.aircraft == dlayer.ac_dict:
                                    res.append(alayer.annotate(raw_data, (raster_indices, raster_grid)))

                        self._progress_callback('Annotating Layers...')
                        # res = jl.Parallel(n_jobs=1, verbose=1, backend='threading')(
                        #     jl.delayed(layer.annotate)(raw_datas, (raster_indices, raster_grid)) for layer in
                        #     self.annotation_layers )
                        plot = Overlay(
                            [self._base_tiles, plot, *[annot for annot in res if annot is not None]]).collate()
                    else:
                        plot = Overlay([self._base_tiles, plot]).collate()
                    self._progress_bar_callback(90)

                else:
                    self._progress_callback('Area too large to render!')
                    if not self._generated_data_layers:
                        plot = self._base_tiles
                    else:
                        plot = Overlay([self._base_tiles, *list(self._generated_data_layers.values())])

            self._update_layer_list()
            self._progress_callback("Rendering new map...")

        except Exception as e:
            # Catch-all to prevent plot blanking out and/or crashing app
            # Just display map tiles in case this was transient
            import traceback
            traceback.print_exc()
            self._progress_callback(
                f'Plotting failed with the following error: {e}. Please attempt to re-generate the plot')
            print(e)
            plot = self._base_tiles

        return plot.opts(width=self.plot_size[0], height=self.plot_size[1],
                         tools=self.tools, active_tools=self.active_tools)

    def _update_layer_list(self):
        from itertools import chain
        layers = []
        for layer in chain(self.data_layers, self.annotation_layers):
            d = {'key': layer.key}
            if hasattr(layer, '_colour'):
                d.update(colour=layer._colour)
            if hasattr(layer, '_osm_tag'):
                d.update(dataTag=layer._osm_tag)
            layers.append(d)
        self._update_callback(list(chain(self.data_layers, self.annotation_layers)))

    def generate_layers(self, bounds_poly: sg.Polygon, raster_shape: Tuple[int, int]) -> NoReturn:
        """
        Generate static layers of map

        :param raster_shape: shape of raster grid
        :param shapely.geometry.Polygon bounds_poly: the bounding polygon for which to generate the map
        """

        layers = {}
        self._progress_callback('Generating layer data')
        res = jl.Parallel(n_jobs=-1, verbose=1, prefer='threads')(
            jl.delayed(self.generate_layer)(layer, bounds_poly, raster_shape, self._time_idx,
                                            self.raster_resolution_m) for layer in self.data_layers)
        for key, result in res:
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
    def generate_layer(layer: DataLayer, bounds_poly: sg.Polygon, raster_shape: Tuple[int, int], hour: int,
                       resolution: float) -> Union[
        Tuple[str, Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]], Tuple[str, None]]:

        try:
            if isinstance(layer, FatalityRiskLayer):
                layer.key = f'{layer.key} {layer.ac} {layer.wind_dir:03d}@{layer.wind_vel}kts'
            result = layer.key, layer.generate(bounds_poly, raster_shape, from_cache=False, hour=hour,
                                               resolution=resolution)
            return result
        except Exception as e:
            import traceback
            traceback.print_tb(e.__traceback__)
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

    def export_path_geojson(self, layer, filepath):
        import os
        if layer in self.annotation_layers:
            layer.dataframe.to_file(os.path.join(os.sep, f'{filepath}', 'path.geojson'), driver='GeoJSON')

    def generate_path_data_popup(self, layer):
        from seedpod_ground_risk.pathfinding.environment import GridEnvironment
        from seedpod_ground_risk.ui_resources.info_popups import DataWindow
        from seedpod_ground_risk.layers.fatality_risk_layer import FatalityRiskLayer
        for dlayer in self.data_layers:
            if isinstance(dlayer, FatalityRiskLayer) and layer.aircraft == dlayer.ac_dict:
                cur_layer = GridEnvironment(self._generated_data_layers[dlayer.key][1])
                grid = cur_layer.grid
                popup = DataWindow(layer, grid)
                popup.exec()
                break

    def remove_duplicate_layers(self):
        # TODO Make the list/set method work as the nested for loop is clunky
        # self.data_layers = list(set(self.data_layers))

        for i, layer1 in enumerate(self.data_layers):
            for j, layer2 in enumerate(self.data_layers):
                if layer1.ac_dict == layer2.ac_dict and i != j:
                    self.remove_layer(layer2)

    def _get_raster_dimensions(self, bounds_poly: sg.Polygon, raster_resolution_m: float) -> Tuple[int, int]:
        """
        Return a the (x,y) shape of a raster grid given its EPSG4326 envelope and desired raster resolution
        :param bounds_poly: EPSG4326 Shapely Polygon specifying bounds
        :param raster_resolution_m: raster resolution in metres
        :return: 2-tuple of (width, height)
        """

        import pyproj

        if self._epsg4326_to_epsg3857_proj is None:
            self._epsg4326_to_epsg3857_proj = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg('4326'),
                                                                          pyproj.CRS.from_epsg('3857'),
                                                                          always_xy=True)
        return reproj_bounds(bounds_poly, self._epsg4326_to_epsg3857_proj, raster_resolution_m)
