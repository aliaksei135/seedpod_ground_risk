import os
import threading

import colorcet
import geopandas as gpd
import geoviews as gv
import pandas as pd
import panel as pn
import shapely.geometry as sg
from geoviews import tile_sources as gvts

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


class PlotServer:

    def __init__(self, tiles='Wikipedia', tools=None, active_tools=None, cmap='CET_L18', plot_size=(790, 750)):
        self.tools = ['hover', 'crosshair'] if tools is None else tools
        self.active_tools = ['wheel_zoom'] if active_tools is None else active_tools
        self.cmap = getattr(colorcet, cmap)
        self.layers = {'base': getattr(gvts, tiles)}
        self.callbacks = []
        self.plot_size = plot_size

        self.query_osm_landuse_polygons([50.77, -2.0, 51.18, -0.9])
        self.ingest_census_data()
        self.generate_static_map()

        self.current_plot = self.compose_overlay_plot()
        self.server = pn.serve(self.current_plot, start=False, show=False)
        self._server_thread = None
        self.url = 'http://localhost:{port}/{prefix}'.format(port=self.server.port, prefix=self.server.prefix) \
            if self.server.address is None else self.server.address

        self.census_wards = None
        self.landuse_polygons = None

        def move_callback(attr, old, new):
            pass

    def start(self):
        """
        Start the Panel Server and run its Tornado IOLoop in a daemon thread
        """
        assert self.server is not None
        if self._server_thread is None:
            self.server.start()
            self._server_thread = threading.Thread(target=self.server.io_loop.start, daemon=True)
        self._server_thread.start()

    def stop(self):
        assert self.server is not None
        if self._server_thread is not None:
            if self._server_thread.is_alive():
                self._server_thread.join()

    def compose_overlay_plot(self):
        """
        Compose all generated HoloViews layers in self.layers into a single overlayed plot.
        Overlaid in a first-on-the-bottom manner
        """
        plot = None
        for layer in self.layers.values():
            if plot is None:
                plot = layer
            else:
                plot = plot * layer
        return plot.opts(width=self.plot_size[0], height=self.plot_size[1])

    def generate_static_map(self):
        """
        Generate static landuse map from
        """
        # Required data to generate plot
        assert self.landuse_polygons is not None
        assert self.census_wards is not None
        # Polygons aren't much use without a base map context
        assert self.layers is not None

        # Find landuse polygons intersecting/within census wards and merge left
        census_df = gpd.overlay(self.landuse_polygons, self.census_wards, how='intersection').to_crs('EPSG:4326')
        # Estimate the population of landuse polygons from the density of the census ward they are within
        # EPSG:4326 is *not* an equal area projection so would give gibberish areas
        # Project geometries to an equidistant/equal are projection
        census_df['population'] = census_df['density'] * census_df['geometry'].to_crs('EPSG:4088').area

        # Scale to reduce error for smaller, less dense wards
        # This was found empirically minimising the population error in 10 random villaegs in Hampshire
        # TODO: Scale population in smaller area more robustly
        def scale_pop(x):
            if 0 < x < 7000:
                return (-0.0000001 * (x ** 2) + 6) * x
            else:
                return x

        # Actually perform the populations scaling
        census_df['population'] = census_df['population'].apply(scale_pop)
        # Construct the GeoViews Polygons
        residential_pop_polys = gv.Polygons(census_df, vdims=['name', 'population']).opts(tools=self.tools,
                                                                                          active_tools=self.active_tools,
                                                                                          cmap=self.cmap,
                                                                                          width=1600, height=800,
                                                                                          color='population',
                                                                                          colorbar=True, colorbar_opts={
                'title': 'Population'}, show_legend=False)
        # Store layer
        self.layers['residential'] = residential_pop_polys

    def query_osm_landuse_polygons(self, bbox, landuse='residential'):
        """
        Perform blocking query on OpenStreetMaps Overpass API for objects with the passed landuse.
        Retain only polygons and store in GeoPandas GeoDataFrame
        :param iterable[4] bbox:
        :param str landuse: OSM landuse key from https://wiki.openstreetmap.org/wiki/Landuse
        """
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
                   s_bound=bbox[0], w_bound=bbox[1], n_bound=bbox[2], e_bound=bbox[3])
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

            # Construct gdf
            # OSM uses Web Mercator so set CRS without projecting as CRS is known
        self.landuse_polygons = gpd.GeoDataFrame(df_list, columns=['geometry']).set_crs('EPSG:4326')

    def ingest_census_data(self):
        '''
        Ingest Census boundaries and density values and overlay/merge
        '''
        # Import Census boundaries in Ordnance Survey grid and reproject
        census_wards_df = gpd.read_file(os.sep.join(('static_data', 'england_wa_2011_clipped.shp'))).drop(
            ['altname', 'oldcode'], axis=1).set_crs(
            'EPSG:27700').to_crs('EPSG:4326')
        # Import census ward densities
        density_df = pd.read_csv(os.sep.join(('static_data', 'density.csv')), header=0)
        # TODO: Scale density more robustly
        density_df['area'] = density_df['area'] * 10000
        density_df['density'] = density_df['density'] / 10000
        # These share a common UID, so merge together on it and store
        self.census_wards = census_wards_df.merge(density_df, on='code')
