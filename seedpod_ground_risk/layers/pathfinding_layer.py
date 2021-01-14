from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import numpy as np
from holoviews.element import Geometry

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer


class PathfindingLayer(AnnotationLayer):

    def __init__(self, key, rasterise: bool = True, start_coords: Tuple[float, float] = (0, 0),
                 end_coords: Tuple[float, float] = (0, 0)):
        super().__init__('Pathfinding', False)
        self.start_coords = start_coords
        self.end_coords = end_coords

    def preload_data(self) -> NoReturn:
        pass

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 **kwargs) -> Geometry:
        from seedpod_ground_risk.pathfinding import environment, a_star
        from seedpod_ground_risk.pathfinding import heuristic
        import geoviews as gv

        snapped_start_lat_idx = np.argmin(np.abs(raster_data[0]['Latitude'] - self.start_coords[1]))
        snapped_start_lon_idx = np.argmin(np.abs(raster_data[0]['Longitude'] - self.start_coords[0]))
        start_node = environment.Node(snapped_start_lon_idx, snapped_start_lat_idx)

        snapped_end_lat_idx = np.argmin(np.abs(raster_data[0]['Latitude'] - self.end_coords[1]))
        snapped_end_lon_idx = np.argmin(np.abs(raster_data[0]['Longitude'] - self.end_coords[0]))
        end_node = environment.Node(snapped_end_lon_idx, snapped_end_lat_idx)

        env = environment.GridEnvironment(raster_data[1], diagonals=True)
        algo = a_star.AStar(heuristic=heuristic.EuclideanRiskHeuristic(env))
        path = algo.find_path(env, start_node, end_node)
        print(len(path))

        snapped_path = []
        for node in path:
            lat = raster_data[0]['Latitude'][node.y]
            lon = raster_data[0]['Longitude'][node.x]
            snapped_path.append((lon, lat))

        return gv.Path(snapped_path)

    def clear_cache(self) -> NoReturn:
        pass
