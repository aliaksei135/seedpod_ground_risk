import unittest

import postcodes_io_api as pst


class TestCoordinateBox(unittest.TestCase):

    def test_postcode_api(self):
        postcode = "SO173RZ"
        api = pst.Api()
        data = api.get_postcode(postcode)
        verified_data = {'postcode': 'SO17 3RZ', 'quality': 1, 'eastings': 442899, 'northings': 115194,
                         'country': 'England', 'nhs_ha': 'South Central', 'longitude': -1.390884, 'latitude': 50.934605,
                         'european_electoral_region': 'South East', 'primary_care_trust': 'Southampton City',
                         'region': 'South East', 'lsoa': 'Southampton 005F', 'msoa': 'Southampton 005', 'incode': '3RZ',
                         'outcode': 'SO17', 'parliamentary_constituency': 'Romsey and Southampton North',
                         'admin_district': 'Southampton', 'parish': 'Southampton, unparished area',
                         'admin_county': None, 'admin_ward': 'Swaythling', 'ced': None,
                         'ccg': 'NHS Hampshire, Southampton and Isle of Wight', 'nuts': 'Southampton',
                         'codes': {'admin_district': 'E06000045', 'admin_county': 'E99999999',
                                   'admin_ward': 'E05002469', 'parish': 'E43000036',
                                   'parliamentary_constituency': 'E14000901', 'ccg': 'E38000253', 'ccg_id': 'D9Y0V',
                                   'ced': 'E99999999', 'nuts': 'TLJ32', 'lsoa': 'E01032756', 'msoa': 'E02003553',
                                   'lau2': 'E06000045'}}
        self.assertEqual(data['result']['longitude'], verified_data['longitude'])
        self.assertEqual(data['result']['latitude'], verified_data['latitude'])


if __name__ == '__main__':
    unittest.main()
