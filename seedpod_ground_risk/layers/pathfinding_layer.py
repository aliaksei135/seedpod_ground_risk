from time import time
from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import matplotlib.pyplot as mpl
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
        from seedpod_ground_risk.pathfinding.heuristic import EuclideanRiskHeuristic
        import geoviews as gv

        snapped_start_lat_idx = np.argmin(np.abs(raster_data[0]['Latitude'] - self.start_coords[1]))
        snapped_start_lon_idx = np.argmin(np.abs(raster_data[0]['Longitude'] - self.start_coords[0]))
        start_node = environment.Node(snapped_start_lon_idx, snapped_start_lat_idx,
                                      raster_data[1][snapped_start_lat_idx, snapped_start_lon_idx])

        snapped_end_lat_idx = np.argmin(np.abs(raster_data[0]['Latitude'] - self.end_coords[1]))
        snapped_end_lon_idx = np.argmin(np.abs(raster_data[0]['Longitude'] - self.end_coords[0]))
        end_node = environment.Node(snapped_end_lon_idx, snapped_end_lat_idx,
                                    raster_data[1][snapped_end_lat_idx, snapped_end_lon_idx])

        mpl.matshow(np.flipud(raster_data[1]), cmap='jet')
        mpl.colorbar()
        mpl.show()

        env = environment.GridEnvironment(raster_data[1], diagonals=True, pruning=False)
        # algo = a_star.RiskGridAStar(
        #     heuristic=heuristic.EuclideanRiskHeuristic(env, risk_to_dist_ratio=1))
        algo = a_star.RiskJumpPointSearchAStar(EuclideanRiskHeuristic(env, risk_to_dist_ratio=1), jump_gap=0)
        t0 = time()
        path = algo.find_path(env, start_node, end_node)
        print('Path generated in ', time() - t0)

        snapped_path = []
        for node in path:
            lat = raster_data[0]['Latitude'][node.y]
            lon = raster_data[0]['Longitude'][node.x]
            snapped_path.append((lon, lat))

        return gv.EdgePaths(snapped_path)

    def clear_cache(self) -> NoReturn:
        pass
