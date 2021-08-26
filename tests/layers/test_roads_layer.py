import unittest

from seedpod_ground_risk.layers.roads_layer import RoadsLayer
from tests.layers.test_layer_base import BaseLayerTestCase


class UnbufferedRoadsLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.plot_title = 'Full Roads Population Transiting Density'
        self.layer = RoadsLayer('test')
        super().setUp()


if __name__ == '__main__':
    unittest.main()
