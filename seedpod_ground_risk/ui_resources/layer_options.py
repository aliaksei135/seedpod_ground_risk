import json

from seedpod_ground_risk.layers.arbitrary_obstacle_layer import ArbitraryObstacleLayer
from seedpod_ground_risk.layers.osm_tag_layer import OSMTagLayer
from seedpod_ground_risk.layers.path_analysis_layer import PathAnalysisLayer
from seedpod_ground_risk.layers.pathfinding_layer import PathfindingLayer
from seedpod_ground_risk.layers.residential_layer import ResidentialLayer
from seedpod_ground_risk.layers.roads_layer import RoadsLayer
from seedpod_ground_risk.pathfinding.a_star import *
from seedpod_ground_risk.pathfinding.theta_star import *

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
    'Risk Grid Theta*': RiskThetaStar
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
        'Aircraft': ('aircraft', 'aircraft', eval),
        'Risk-Distance Ratio': (r'\d{0,3}(\.\d+)?', 'rdr', float),
        'Wind Speed [m/s]': (r'-?\d{0,3}\.?\d+', 'wind_vel', float),
        'Wind Bearing [deg]': (r'-?\d{0,3}\.?\d+', 'wind_dir', float)
    }
}

AIRCRAFT_PARAMETERS = {
    'Aircraft Name': (r'.*', 'name', str),
    'Aircraft Width [m]': (r'-?\d{0,3}\.?\d+', 'width', float),
    'Aircraft Length [m]': (r'-?\d{0,3}\.?\d+', 'length', float),
    'Aircraft Mass [kg]': (r'-?\d{0,3}\.?\d+', 'mass', float),
    'Aircraft Glide Ratio': (r'-?\d{0,3}\.?\d+', 'glide_ratio', float),
    'Aircraft Glide Speed [m/s]': (r'-?\d{0,3}\.?\d+', 'glide_speed', float),
    'Aircraft Glide Drag Coeff': (r'-?\d{0,3}\.?\d+', 'glide_drag_coeff', float),
    'Aircraft Ballistic Drag Coeff': (r'-?\d{0,3}\.?\d+', 'bal_drag_coeff', float),
    'Aircraft Ballistic Frontal Area [m^2]': (r'-?\d{0,3}\.?\d+', 'frontal_area', float),
    'Aircraft Failure Probability [0-1]': (r'-?\d{0,3}\.?\d+', 'failure_prob', float),
    'Flight Altitude [m]': (r'-?\d{0,3}\.?\d+', 'alt', float),
    'Flight Airspeed [m/s]': (r'-?\d{0,3}\.?\d+', 'vel', float)
}


# Create aircraft list dictionary from UAV list found in static_data

def aircraft_list(filepath="static_data/aircraft_list.json"):
    json_file_path = filepath
    with open(json_file_path, 'r') as j:
        aircrafts = json.loads(j.read())
    return aircrafts


def add_aircraft(new_ac):
    ac_list = AIRCRAFT_LIST
    ac_list[f"{new_ac['name']}"] = new_ac
    if 'name' in ac_list[f"{new_ac['name']}"]: del ac_list[f"{new_ac['name']}"]['name']
    with open("static_data/aircraft_list.json", 'w') as f:
        json.dump(ac_list, f)

AIRCRAFT_LIST = aircraft_list()
