import json

from seedpod_ground_risk.data import aircraft_list_filepath


def aircraft_list():
    with open(aircraft_list_filepath(), 'r') as j:
        aircrafts = json.loads(j.read())
    return aircrafts


def add_aircraft(new_ac):
    ac_list = AIRCRAFT_LIST
    ac_list[f"{new_ac['name']}"] = new_ac
    with open(aircraft_list_filepath(), 'w') as f:
        json.dump(ac_list, f)


# Create aircraft list dictionary from UAV list found in static_data
AIRCRAFT_LIST = aircraft_list()
