from itertools import combinations
from typing import Tuple

import geopandas as gpd
import numpy as np
import requests
import shapely.geometry as sg
from holoviews.element import Geometry
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# TODO The below line is a symptom of us not varifying the SSL certs.
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from seedpod_ground_risk.layers.blockable_data_layer import BlockableDataLayer


def query_osm_polygons(osm_tag, bound_poly: sg.Polygon) -> gpd.GeoDataFrame:
    """
    Perform blocking query on OpenStreetMaps Overpass API for objects with the passed tag.
    Retain only polygons and store in GeoPandas GeoDataFrame
    :param osm_tag: OSM tag to query
    :param shapely.Polygon bound_poly: bounding box around requested area in EPSG:4326 coordinates
    """
    from time import time

    t0 = time()
    bounds = bound_poly.bounds
    overpass_urls = ["https://overpass.kumi.systems/api/interpreter", "https://lz4.overpass-api.de/api/interpreter",
                     "https://z.overpass-api.de/api/interpreter", "https://overpass.openstreetmap.ru/api/interpreter",
                     "https://overpass.openstreetmap.fr/api/interpreter",
                     "https://overpass.nchc.org.tw/api/interpreter"]
    for i, url in enumerate(overpass_urls):
        resp, data = query_request(overpass_urls[i], osm_tag, bounds)
        if resp.status_code == 200:
            break
        else:
            print(resp.status_code)

    print("OSM query took ", time() - t0)

    ways = {o['id']: o['nodes'] for o in data['elements'] if o['type'] == 'way'}
    nodes = {o['id']: (o['lon'], o['lat']) for o in data['elements'] if o['type'] == 'node'}
    relations = [o for o in data['elements'] if o['type'] == 'relation']

    used_ways = []
    df_list = []
    for rel in relations:
        # Get all the id and role (inner/outer) of all relation members that are ways
        rw = [(w['ref'], w['role']) for w in rel['members'] if w['type'] == 'way']
        rel_outer_rings = []
        rel_inner_rings = []

        unclosed_ways = []
        # Iterate each way in relation
        for way_id, role in rw:
            # Find the way ID in ways
            if way_id in ways:
                way = ways[way_id]
                # Find the vertices (AKA nodes) that make up each polygon
                locs = [nodes[i] for i in way]
                start = locs[0]
                end = locs[-1]
                # Check if way is already a closed ring
                if start == end:
                    # Simplest case where way is already valid ring
                    # Create linear ring from vertices and classify by role
                    ring = sg.LinearRing(locs)
                    if role == 'inner':
                        rel_inner_rings.append(ring)
                    else:
                        rel_outer_rings.append(ring)
                elif len(unclosed_ways) > 0:
                    consumed = False
                    # Way is not a valid ring
                    # Check if there are any matching dangling nodes in other unclosed ways
                    for _, uw in unclosed_ways:
                        uw_start = uw[0]
                        uw_end = uw[-1]
                        if uw_end == start:
                            # If the start of this way is the same as the end of the unclosed way
                            # Append this ways nodes with duplicate coord sliced off
                            uw += locs
                            consumed = True
                        elif uw_end == end:
                            # If the end of this way is the same as the end of the unclosed way
                            # Append this ways nodes reversed with the duplicate coord sliced off
                            uw += locs[::-1]
                            consumed = True
                        elif uw_start == end:
                            # If the end of this way is the same as the start of the unclosed way
                            # Prepend this ways nodes with the duplicate coord sliced off
                            uw[0:0] = locs
                            consumed = True
                        elif uw_start == start:
                            # If the start of this way is the same as the start of the unclosed way
                            # Prepend this ways nodes reversed with the duplicate coord sliced off
                            uw[0:0] = locs[::-1]
                            consumed = True

                        # Check if this way has been used
                        if consumed:
                            # uw_start/end may have changed by now
                            if uw[0] == uw[-1]:
                                # Made a closed ring
                                # Create linear ring from vertices and classify by role
                                ring = sg.LinearRing(uw)
                                if role == 'inner':
                                    rel_inner_rings.append(ring)
                                else:
                                    rel_outer_rings.append(ring)
                                # Remove from unclosed ways
                                unclosed_ways.remove((role, uw))
                            break

                    # unclosed_ways is never empty in this if block, therefore loop is always entered
                    # and consumed is always defined
                    if not consumed:
                        # This way is currently isolated so store as another unclosed way
                        unclosed_ways.append((role, locs))
                else:
                    unclosed_ways.append((role, locs))
                # Store used ways to prevent double processing later on
                # Do not pop them out as other relations could be using them!
                used_ways.append(way_id)
        # Link up remaining unclosed polys
        if unclosed_ways:
            for (r1, uw1), (r2, uw2) in combinations(unclosed_ways, 2):
                consumed = False
                uw1_start = uw1[0]
                uw1_end = uw1[-1]
                uw2_start = uw2[0]
                uw2_end = uw2[-1]
                if uw1_end == uw2_start:
                    # If the start of this way is the same as the end of the unclosed way
                    # Append this ways nodes with duplicate coord sliced off
                    uw1 += uw2[1:]
                    consumed = True
                elif uw1_end == uw2_end:
                    # If the end of this way is the same as the end of the unclosed way
                    # Append this ways nodes reversed with the duplicate coord sliced off
                    uw1 += uw2[:0:-1]
                    consumed = True
                elif uw1_start == uw2_end:
                    # If the end of this way is the same as the start of the unclosed way
                    # Prepend this ways nodes with the duplicate coord sliced off
                    uw1[0:0] = uw2[:-1]
                    consumed = True
                elif uw1_start == uw2_start:
                    # If the start of this way is the same as the start of the unclosed way
                    # Prepend this ways nodes reversed with the duplicate coord sliced off
                    uw1[0:0] = uw2[:0:-1]
                    consumed = True

                # Check if this way has been used
                if consumed:
                    unclosed_ways.remove((r2, uw2))
                    # uw_start/end may have changed by now
                    if uw1[0] == uw1[-1]:
                        # Made a closed ring
                        # Create linear ring from vertices and classify by role
                        ring = sg.LinearRing(uw1)
                        if r1 == 'inner':
                            rel_inner_rings.append(ring)
                        else:
                            rel_outer_rings.append(ring)
                        # Remove from unclosed ways
                        unclosed_ways.remove((r1, uw1))
                        if not unclosed_ways:
                            break

        # Combine outer rings to a single ring
        if len(rel_outer_rings) > 1:
            coords = []
            for c in rel_outer_rings:
                coords += c.coords
            outer_ring = sg.LinearRing(coords)
        elif len(rel_outer_rings) < 1:
            if len(unclosed_ways) == 1:
                outer_ring = sg.LinearRing(unclosed_ways[0][1])
            else:
                print("No outer rings in multipolygon")
                continue
        else:
            outer_ring = rel_outer_rings[0]
        poly = sg.Polygon(shell=outer_ring, holes=rel_inner_rings)
        df_list.append(poly)

    # Iterate polygons ways
    for way_id, element in ways.items():
        if way_id in used_ways:
            continue
        # Find the vertices (AKA nodes) that make up each polygon
        locs = [nodes[i] for i in element]
        # Not a polygon if less than 3 vertices, so ignore
        if len(locs) < 3:
            continue
        # Add Shapely polygon to list
        poly = sg.Polygon(locs)
        df_list.append(poly)
    # OSM uses Web Mercator so set CRS without projecting as CRS is known
    poly_df = gpd.GeoDataFrame(df_list, columns=['geometry']).set_crs('EPSG:4326')
    poly_df.drop_duplicates(subset='geometry', inplace=True, ignore_index=True)
    return poly_df


def query_request(overpass_url, osm_tag, bounds):
    headers = {'User-Agent': f'seedpod-ground-risk v0.13.0 (Python 3.8/requests v{requests.__version__};)',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
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
          """.format(tag=osm_tag,
                     s_bound=bounds[0], w_bound=bounds[1], n_bound=bounds[2], e_bound=bounds[3])
    resp = requests.post(overpass_url, data={'data': query}, headers=headers, verify=False)
    data = resp.json()
    return resp, data


class OSMTagLayer(BlockableDataLayer):

    def __init__(self, key, osm_tag, **kwargs):
        super(OSMTagLayer, self).__init__(key, **kwargs)
        self._osm_tag = osm_tag

    def preload_data(self):
        pass

    def generate(self, bounds_polygon: sg.Polygon, raster_shape: Tuple[int, int], from_cache: bool = False, **kwargs) -> \
            Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]:
        import geoviews as gv
        from holoviews.operation.datashader import rasterize

        bounds = bounds_polygon.bounds
        polys_df = self.query_osm_polygons(bounds_polygon)
        if polys_df.empty:
            return None
        if self.buffer_dist > 0:
            polys_df.geometry = polys_df.to_crs('EPSG:27700').buffer(self.buffer_dist).to_crs('EPSG:4326')
        polys = gv.Polygons(polys_df).opts(alpha=0.8, color=self._colour, line_color=self._colour)
        raster = rasterize(polys, width=raster_shape[0], height=raster_shape[1],
                           x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(np.float))
        if self.blocking:
            raster_grid[raster_grid != 0] = -1
        else:
            raster_grid = None

        return polys, raster_grid, polys_df

    def clear_cache(self):
        pass

    def query_osm_polygons(self, bounds_poly):
        return query_osm_polygons(self._osm_tag, bounds_poly)
