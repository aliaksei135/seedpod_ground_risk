import unittest

from seedpod_ground_risk.layers.temporal_population_estimate_layer import TemporalPopulationEstimateLayer
from tests.layers.test_layer_base import BaseLayerTestCase


class UnbufferedTemporalPopulationEstimateLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.hour = 8
        self.plot_title = f'Spatiotemporal Population Density, t={self.hour}'
        self.layer = TemporalPopulationEstimateLayer('test')
        super().setUp()


class BufferedTemporalPopulationEstimateLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.plot_title = 'Spatiotemporal Population Density, t=13'
        self.layer = TemporalPopulationEstimateLayer('test', buffer_dist=10)
        super().setUp()


if __name__ == '__main__':
    unittest.main()
