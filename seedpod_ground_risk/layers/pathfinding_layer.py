from time import time
from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import matplotlib.pyplot as mpl
import numpy as np
import shapely.geometry as sg
from holoviews.element import Geometry

from seedpod_ground_risk.layers.geojson_layer import GeoJSONLayer
from seedpod_ground_risk.pathfinding.a_star import RiskGridAStar
from seedpod_ground_risk.pathfinding.heuristic import ManhattanRiskHeuristic


class PathfindingLayer(GeoJSONLayer):

    def __init__(self, key, start_coords: Tuple[float, float] = (0, 0),
                 end_coords: Tuple[float, float] = (0, 0), buffer: float = 0):
        super().__init__(key, '')
        self.start_coords = start_coords
        self.end_coords = end_coords
        self.buffer_dist = buffer

    def preload_data(self) -> NoReturn:
        pass

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 **kwargs) -> Geometry:
        from seedpod_ground_risk.pathfinding import environment

        snapped_start_lat_idx = np.argmin(np.abs(raster_data[0]['Latitude'] - self.start_coords[1]))
        snapped_start_lon_idx = np.argmin(np.abs(raster_data[0]['Longitude'] - self.start_coords[0]))
        start_node = environment.Node(snapped_start_lon_idx, snapped_start_lat_idx,
                                      raster_data[1][snapped_start_lat_idx, snapped_start_lon_idx])

        snapped_end_lat_idx = np.argmin(np.abs(raster_data[0]['Latitude'] - self.end_coords[1]))
        snapped_end_lon_idx = np.argmin(np.abs(raster_data[0]['Longitude'] - self.end_coords[0]))
        end_node = environment.Node(snapped_end_lon_idx, snapped_end_lat_idx,
                                    raster_data[1][snapped_end_lat_idx, snapped_end_lon_idx])

        if raster_data[1][snapped_start_lon_idx, snapped_start_lat_idx] < 0:
            print('Start node in blocked area, path impossible')
            return None
        elif raster_data[1][snapped_end_lon_idx, snapped_end_lat_idx] < 0:
            print('End node in blocked area, path impossible')
            return None

        mpl.matshow(raster_data[1], cmap='jet')
        mpl.colorbar()
        mpl.title(
            f'Costmap \n Start (x,y):({snapped_start_lon_idx}, {snapped_start_lat_idx})'
            f'\n End (x,y):({snapped_end_lon_idx}, {snapped_end_lat_idx})')
        mpl.show()

        env = environment.GridEnvironment(raster_data[1], diagonals=True, pruning=False)
        algo = RiskGridAStar(
            heuristic=ManhattanRiskHeuristic(env, risk_to_dist_ratio=1e-7))
        # algo = RiskJumpPointSearchAStar(ManhattanRiskHeuristic(env, risk_to_dist_ratio=1e-8), jump_gap=0,
        #                                 jump_limit=5)
        t0 = time()
        path = algo.find_path(env, start_node, end_node)
        if path is None:
            print("Path not found")
            return None
        else:
            print('Path generated in ', time() - t0)

        snapped_path = []
        for node in path:
            lat = raster_data[0]['Latitude'][node.y]
            lon = raster_data[0]['Longitude'][node.x]
            snapped_path.append((lon, lat))

        snapped_path = sg.LineString(snapped_path)
        self.dataframe = gpd.GeoDataFrame({'geometry': [snapped_path]}).set_crs('EPSG:4326')
        epsg27700_geom = self.dataframe.to_crs('EPSG:27700').geometry
        self.buffer_poly = gpd.GeoDataFrame(
            {'geometry': epsg27700_geom.buffer(self.buffer_dist).to_crs('EPSG:4326')}
        )

        return super(PathfindingLayer, self).annotate(data, raster_data, **kwargs)

    def clear_cache(self) -> NoReturn:
        pass
