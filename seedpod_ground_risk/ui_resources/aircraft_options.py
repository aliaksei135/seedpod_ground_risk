import json


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


# Create aircraft list dictionary from UAV list found in static_data
AIRCRAFT_LIST = aircraft_list()
