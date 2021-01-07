import random
from typing import NoReturn

import geopandas as gpd
import shapely.geometry as sg
from holoviews.element import Geometry

from seedpod_ground_risk.layers.data_layer import DataLayer


class OSMTagLayer(DataLayer):
    _landuse_polygons: gpd.GeoDataFrame

    def __init__(self, key, rasterise: bool = False, osm_tag: str = 'landuse=residential'):
        super().__init__(key, rasterise)
        self._osm_tag = osm_tag
        # Set a random colour
        self._colour = "#" + ''.join([random.choice('0123456789ABCDEF') for i in range(6)])
        self._landuse_polygons = gpd.GeoDataFrame()

    def preload_data(self) -> NoReturn:
        pass

    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, **kwargs) -> Geometry:
        import geoviews as gv

        self.query_osm_polygons(bounds_polygon)
        if self._landuse_polygons.empty:
            return None
        return gv.Polygons(self._landuse_polygons).opts(style={'alpha': 0.8, 'color': self._colour})

    def clear_cache(self):
        self._landuse_polygons = gpd.GeoDataFrame()

    def query_osm_polygons(self, bound_poly: sg.Polygon) -> NoReturn:
        """
        Perform blocking query on OpenStreetMaps Overpass API for objects with the passed landuse.
        Retain only polygons and store in GeoPandas GeoDataFrame
        :param shapely.Polygon bound_poly: bounding box around requested area in EPSG:4326 coordinates
        :param str landuse: OSM landuse key from https://wiki.openstreetmap.org/wiki/Landuse
        """
        from time import time
        import requests

        t0 = time()
        bounds = bound_poly.bounds
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = """
                  [out:json]
                  [timeout:120]
                  [bbox:{s_bound}, {w_bound}, {n_bound}, {e_bound}];
                  (
                      node[{tag}];
                      way[{tag}];
                      rel[{tag}];
                  ); 
                  out center body;
                  >;
                  out center qt;
              """.format(tag=self._osm_tag,
                         s_bound=bounds[0], w_bound=bounds[1], n_bound=bounds[2], e_bound=bounds[3])
        resp = requests.get(overpass_url, params={'data': query})
        data = resp.json()
        print("OSM query took ", time() - t0)

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

        self._landuse_polygons = self._landuse_polygons.append(poly_df)
        self._landuse_polygons.drop_duplicates(subset='geometry', inplace=True, ignore_index=True)
