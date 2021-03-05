from typing import NoReturn, Tuple

import geopandas as gpd
import numpy as np
import shapely.geometry as sg
from holoviews.element import Geometry

from seedpod_ground_risk.layers.blockable_data_layer import BlockableDataLayer


class OSMTagLayer(BlockableDataLayer):
    _landuse_polygons: gpd.GeoDataFrame

    def __init__(self, key, osm_tag, **kwargs):
        super(OSMTagLayer, self).__init__(key, **kwargs)
        self._osm_tag = osm_tag
        self._landuse_polygons = gpd.GeoDataFrame()

    def generate(self, bounds_polygon: sg.Polygon, raster_shape: Tuple[int, int], from_cache: bool = False, **kwargs) -> \
            Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]:
        import geoviews as gv
        from holoviews.operation.datashader import rasterize

        bounds = bounds_polygon.bounds
        self.clear_cache()
        self.query_osm_polygons(bounds_polygon)
        if self._landuse_polygons.empty:
            return None
        if self.buffer_dist > 0:
            self._landuse_polygons.geometry = self._landuse_polygons.to_crs('EPSG:27700') \
                .buffer(self.buffer_dist).to_crs('EPSG:4326')
        polys = gv.Polygons(self._landuse_polygons).opts(style={'alpha': 0.8, 'color': self._colour})
        raster = rasterize(polys, width=raster_shape[0], height=raster_shape[1],
                           x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(np.float))
        if self.blocking:
            raster_grid[raster_grid != 0] = -1

        return polys, raster_grid, gpd.GeoDataFrame(self._landuse_polygons)

    def clear_cache(self):
        self._landuse_polygons = gpd.GeoDataFrame()

    def query_osm_polygons(self, bound_poly: sg.Polygon) -> NoReturn:
        """
        Perform blocking query on OpenStreetMaps Overpass API for objects with the passed tag.
        Retain only polygons and store in GeoPandas GeoDataFrame
        :param shapely.Polygon bound_poly: bounding box around requested area in EPSG:4326 coordinates
        """
        from time import time
        import requests

        t0 = time()
        bounds = bound_poly.bounds
        overpass_url = "https://overpass.kumi.systems/api/interpreter"
        query = """
                  [out:json]
                  [timeout:30]
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
        if resp.status_code != 200:
            print(resp)
        data = resp.json()
        print("OSM query took ", time() - t0)

        ways = {o['id']: o['nodes'] for o in data['elements'] if o['type'] == 'way'}
        nodes = {o['id']: (o['lon'], o['lat']) for o in data['elements'] if o['type'] == 'node'}
        relations = [o for o in data['elements'] if o['type'] == 'relation']

        related_way_ids = []
        for rel in relations:
            rw = [w['ref'] for w in rel['members']]
            related_way_ids += rw
            rel_nodes = []
            for way_id in rw:
                if way_id in ways:
                    rel_nodes += ways[way_id]
                    ways.pop(way_id)
            ways[rel['id']] = rel_nodes

        df_list = []
        # Iterate polygons ways
        for element in ways.values():
            # Find the vertices (AKA nodes) that make up each polygon
            locs = [nodes[id] for id in element]
            # Not a polygon if less than 3 vertices, so ignore
            if len(locs) < 3:
                continue
            # Add Shapely polygon to list
            poly = sg.Polygon(locs)
            df_list.append([poly])
        assert len(df_list) > 0
        # OSM uses Web Mercator so set CRS without projecting as CRS is known
        poly_df = gpd.GeoDataFrame(df_list, columns=['geometry']).set_crs('EPSG:4326')

        self._landuse_polygons = self._landuse_polygons.append(poly_df)
        self._landuse_polygons.drop_duplicates(subset='geometry', inplace=True, ignore_index=True)
