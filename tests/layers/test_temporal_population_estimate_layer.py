import unittest

from seedpod_ground_risk.layers.temporal_population_estimate_layer import TemporalPopulationEstimateLayer
from tests.layers.test_layer_base import BaseLayerTestCase


class UnbufferedTemporalPopulationEstimateLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.layer = TemporalPopulationEstimateLayer('test')
        super().setUp()


class BufferedTemporalPopulationEstimateLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.layer = TemporalPopulationEstimateLayer('test', buffer_dist=10)
        super().setUp()


if __name__ == '__main__':
    unittest.main()
