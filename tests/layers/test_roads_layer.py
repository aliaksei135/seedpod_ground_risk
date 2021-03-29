import unittest

from seedpod_ground_risk.layers.roads_layer import RoadsLayer
from tests.layers.test_layer_base import BaseLayerTestCase


class UnbufferedRoadsLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.layer = RoadsLayer('test')
        super().setUp()


class BufferedRoadsLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.layer = RoadsLayer('test', buffer_dist=10)
        super().setUp()


if __name__ == '__main__':
    unittest.main()
