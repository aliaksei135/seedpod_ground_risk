import os


def aircraft_list_filepath():
    aircraft_list_fp = os.sep.join(("static_data", "aircraft_list.json"))
    return aircraft_list_fp


def england_wa_2011_clipped_filepath():
    england_wa_2011_clipped_fp = os.sep.join(('static_data', 'england_wa_2011_clipped.shp'))
    return england_wa_2011_clipped_fp


def traffic_count_filepath():
    traffic_count_fp = os.sep.join(('static_data', 'dft_traffic_counts_aadf.csv'))
    return traffic_count_fp
