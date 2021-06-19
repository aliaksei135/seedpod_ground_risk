from time import time
from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import geoviews as gv
import numpy as np
import shapely.geometry as sg
from holoviews.element import Geometry

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.path_analysis.utils import snap_coords_to_grid
from seedpod_ground_risk.pathfinding.a_star import RiskGridAStar
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, ManhattanRiskHeuristic


class PathfindingLayer(AnnotationLayer):

    def __init__(self, key, start_lat: float = 0, start_lon: float = 0, end_lat: float = 0, end_lon: float = 0,
                 algo: Algorithm = RiskGridAStar, aircraft: dict = {},heuristic: Heuristic = ManhattanRiskHeuristic,
                 rdr: float = 0.2, **kwargs):
        super().__init__(key)
        self.start_coords = (start_lat, start_lon)
        self.end_coords = (end_lat, end_lon)
        self.algo = algo
        self.aircraft = aircraft
        self.heuristic = heuristic
        self.rdr = rdr

    def preload_data(self) -> NoReturn:
        pass

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 resolution=20, **kwargs) -> Geometry:

        raster_grid = np.flipud(raster_data[1])

        start_x, start_y = snap_coords_to_grid(raster_data[0], self.start_coords[1], self.start_coords[0])
        end_x, end_y = snap_coords_to_grid(raster_data[0], self.end_coords[1], self.end_coords[0])

        if raster_grid[start_y, start_x] < 0:
            print('Start node in blocked area, path impossible')
            return None
        elif raster_grid[end_y, end_x] < 0:
            print('End node in blocked area, path impossible')
            return None

        env = GridEnvironment(raster_grid, diagonals=False)
        algo = self.algo(heuristic=self.heuristic(env, risk_to_dist_ratio=self.rdr))
        t0 = time()
        path = algo.find_path(env, Node((start_y, start_x)), Node((end_y, end_x)))
        if path is None:
            print("Path not found")
            return None
        else:
            print('Path generated in ', time() - t0)

        # mpl.matshow(raster_data[1], cmap='jet')
        # mpl.colorbar()
        # mpl.plot([n.x for n in path], [n.y for n in path], color='red')
        # mpl.title(
        #     f'Costmap \n Start (x,y):({snapped_start_lon_idx}, {snapped_start_lat_idx})'
        #     f'\n End (x,y):({snapped_end_lon_idx}, {snapped_end_lat_idx})')
        # mpl.show()

        snapped_path = []
        for node in path:
            lat = raster_data[0]['Latitude'][node.position[0]]
            lon = raster_data[0]['Longitude'][node.position[1]]
            snapped_path.append((lon, lat))

        snapped_path = sg.LineString(snapped_path)
        self.dataframe = gpd.GeoDataFrame({'geometry': [snapped_path]}).set_crs('EPSG:4326')
        return gv.Contours(self.dataframe).opts(line_width=4, line_color='magenta')

    def clear_cache(self) -> NoReturn:
        pass
