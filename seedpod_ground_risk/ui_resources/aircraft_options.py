import json

from seedpod_ground_risk.data.external_data_references import aircraft_list_filepath


def aircraft_list():
    json_file_path = aircraft_list_filepath()
    with open(json_file_path, 'r') as j:
        aircrafts = json.loads(j.read())
    return aircrafts


def add_aircraft(new_ac):
    ac_list = AIRCRAFT_LIST
    ac_list[f"{new_ac['name']}"] = new_ac
    json_file_path = aircraft_list_filepath()
    if 'name' in ac_list[f"{new_ac['name']}"]: del ac_list[f"{new_ac['name']}"]['name']
    with open(json_file_path, 'w') as f:
        json.dump(ac_list, f)


# Create aircraft list dictionary from UAV list found in static_data
AIRCRAFT_LIST = aircraft_list()
