import json
from seedpod_ground_risk.layers.arbitrary_obstacle_layer import ArbitraryObstacleLayer
from seedpod_ground_risk.layers.osm_tag_layer import OSMTagLayer
from seedpod_ground_risk.layers.path_analysis_layer import PathAnalysisLayer
from seedpod_ground_risk.layers.pathfinding_layer import PathfindingLayer
from seedpod_ground_risk.layers.residential_layer import ResidentialLayer
from seedpod_ground_risk.layers.roads_layer import RoadsLayer
from seedpod_ground_risk.pathfinding.a_star import *


LAYER_OBJECTS = {
    'Select a Layer': None,
    'Generic OSM': OSMTagLayer,
    'Residential - England': ResidentialLayer,
    'Road Traffic Flow - England': RoadsLayer,
    'Existing Path Analysis': PathAnalysisLayer,
    'External Obstacles': ArbitraryObstacleLayer,
    'Pathfinding': PathfindingLayer
}

ALGORITHM_OBJECTS = {
    'Select Pathfinding Algorithm': None,
    # 'Grid A*': GridAStar,
    'Risk Grid A*': RiskGridAStar,
    # 'Jump Point Search+ A*': JumpPointSearchAStar,
    # 'Risk Jump Point Search+ A*': RiskJumpPointSearchAStar
}

# Dictionary of available layers and their available options with validation regex or bool
LAYER_OPTIONS = {
    'Select a Layer': None,
    'Generic OSM': {
        'OSM Tag': (r'\w+=\w+', 'osm_tag', str),
        'Colour': ('colour', 'colour', str),
        'Buffer Distance [m]': (r'\d{0,3}', 'buffer_dist', int),
        'Blocking': (bool, 'blocking', bool)
    },
    'Residential - England': {
        'Buffer Distance [m]': (r'\d{0,3}', 'buffer_dist', int),
    },
    'Road Traffic Flow - England': {
    },
    'Existing Path Analysis': {
        'File': ('path', 'filepath', str),
        'Aircraft': ('aircraft', 'Aircraft', eval),
        'Wind Speed [m/s]': (r'-?\d{0,3}\.?\d+', 'wind_vel', float),
        'Wind Bearing [deg]': (r'-?\d{0,3}\.?\d+', 'wind_dir', float)
    },
    'External Obstacles': {
        'File': ('path', 'filepath', str),
        'Colour': ('colour', 'colour', str),
        'Buffer Distance [m]': (r'\d{0,3}', 'buffer_dist', int),
        'Blocking': (bool, 'blocking', bool),
    },
    'Pathfinding': {
        'Start Latitude [dd]': (r'-?\d{0,3}\.\d+', 'start_lat', float),
        'Start Longitude [dd]': (r'-?\d{0,3}\.\d+', 'start_lon', float),
        'End Latitude [dd]': (r'-?\d{0,3}\.\d+', 'end_lat', float),
        'End Longitude [dd]': (r'-?\d{0,3}\.\d+', 'end_lon', float),
        'Algorithm': ('algos', 'algo', eval),
        'Aircraft': ('aircraft', 'Aircraft', eval),
        'Risk-Distance Ratio': (r'\d{0,3}(\.\d+)?', 'rdr', float),
        'Wind Speed [m/s]': (r'-?\d{0,3}\.?\d+', 'wind_vel', float),
        'Wind Bearing [deg]': (r'-?\d{0,3}\.?\d+', 'wind_dir', float)
    }
}

# Create aircraft list dictionary from UAV list found in static_data

def aircraft_list(filepath = "static_data/aircraft_list.json"):
    json_file_path = filepath
    with open(json_file_path, 'r') as j:
        aircrafts = json.loads(j.read())
    return aircrafts

AIRCRAFT_LIST = aircraft_list()
