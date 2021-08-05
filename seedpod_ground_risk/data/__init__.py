import os


def aircraft_list_filepath():
    aircraft_list_fp = os.sep.join(("static_data", "aircraft_list.json"))
    return aircraft_list_fp


def england_wa_2011_clipped_filepath():
    england_wa_2011_clipped_fp = os.sep.join(('static_data', 'england_wa_2011_clipped.shp'))
    return england_wa_2011_clipped_fp


def nhaps_data_filepath():
    nhaps_data_fp = os.sep.join(('static_data', 'nhaps.json'))
    return nhaps_data_fp


def density_filepath():
    density_fp = os.sep.join(('static_data', 'density.csv'))
    return density_fp


def traffic_count_filepath():
    traffic_count_fp = os.sep.join(('static_data', 'dft_traffic_counts_aadf.csv'))
    return traffic_count_fp


def road_geometry_filepath():
    road_geometry_fp = os.sep.join(('static_data', '2018-MRDB-minimal.shp'))
    return road_geometry_fp


def relative_variation_filepath():
    relative_variation_fp = os.sep.join(('static_data', 'tra0307.ods'))
    return relative_variation_fp
