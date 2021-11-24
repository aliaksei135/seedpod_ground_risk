import os

os.chdir('../..')
import unittest

from seedpod_ground_risk.layers.temporal_population_estimate_layer import TemporalPopulationEstimateLayer
from tests.layers.test_layer_base import BaseLayerTestCase


class UnbufferedTemporalPopulationEstimateLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.hour = 8
        self.plot_title = f'Spatiotemporal Population Density, t={self.hour}'
        self.layer = TemporalPopulationEstimateLayer('test')
        super().setUp()

    def test_make_4_plot(self) -> None:
        import matplotlib.pyplot as mpl
        import numpy as np

        hours = [1, 8, 13, 17]
        rasters = {}

        for hour in hours:
            _, raster, _ = self.layer.generate(self.test_bounds, self.raster_shape, hour=hour)
            rasters[hour] = raster

        gs = mpl.GridSpec(2, 2, hspace=0.2, wspace=0.3)
        fig = mpl.figure()

        font = dict(fontsize=10)

        ax0 = fig.add_subplot(gs[0, 0])
        ax0.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m0 = ax0.matshow(np.flipud(rasters[1]))
        m0.set_clim(0, 15000)
        ax0.set_title('Population Density at 1 AM', fontdict=font)
        fig.colorbar(m0).set_label('Population Density\n[people/km$^2$]', fontsize=7)

        ax1 = fig.add_subplot(gs[0, 1])
        ax1.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m1 = ax1.matshow(np.flipud(rasters[8]))
        m1.set_clim(0, 15000)
        ax1.set_title('Population Density at 8 AM', fontdict=font)
        fig.colorbar(m1).set_label('Population Density\n[people/km$^2$]', fontsize=7)

        ax2 = fig.add_subplot(gs[1, 0])
        ax2.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m2 = ax2.matshow(np.flipud(rasters[13]))
        m2.set_clim(0, 15000)
        ax2.set_title('Population Density at 1 PM', fontdict=font)
        fig.colorbar(m2).set_label('Population Density\n[people/km$^2$]', fontsize=7)

        ax3 = fig.add_subplot(gs[1, 1])
        ax3.tick_params(left=False, right=False,
                        bottom=False, top=False,
                        labelleft=False, labelbottom=False)
        m3 = ax3.matshow(np.flipud(rasters[17]))
        m3.set_clim(0, 15000)
        ax3.set_title('Population Density at 5 PM', fontdict=font)
        fig.colorbar(m3).set_label('Population Density\n[people/km$^2$]', fontsize=7)

        fig.tight_layout()
        fig.show()


class BufferedTemporalPopulationEstimateLayerTestCase(BaseLayerTestCase):

    def setUp(self) -> None:
        self.plot_title = 'Spatiotemporal Population Density, t=13'
        self.layer = TemporalPopulationEstimateLayer('test', buffer_dist=10)
        super().setUp()


if __name__ == '__main__':
    unittest.main()
