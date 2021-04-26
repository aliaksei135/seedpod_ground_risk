import unittest

from seedpod_ground_risk.layers.residential_layer import ResidentialLayer
from tests.layers.test_layer_base import BaseLayerTestCase


class UnbufferedResidentialLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.plot_title = 'Full Residential Population Density'
        self.layer = ResidentialLayer('test')
        super().setUp()


class BufferedResidentialLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.plot_title = 'Full Residential Population Density'
        self.layer = ResidentialLayer('test', buffer_dist=30)
        super().setUp()


if __name__ == '__main__':
    unittest.main()
