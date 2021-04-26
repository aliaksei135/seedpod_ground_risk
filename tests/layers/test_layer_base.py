import unittest

from seedpod_ground_risk.core.plot_server import make_bounds_polygon


class BaseLayerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        if not hasattr(self, 'layer'):
            return
        import os
        os.chdir(
            os.sep.join((
                os.path.dirname(os.path.realpath(__file__)),
                '..', '..'))
        )
        self.layer.preload_data()
        self.test_bounds = make_bounds_polygon((-1.5, -1.3), (50.85, 50.95))
        self.raster_shape = (1500, 1500)

    def test_raster_bounds(self):
        # Do not test base class!
        if self.__class__ is BaseLayerTestCase:
            return
        _, raster, _ = self.layer.generate(self.test_bounds, self.raster_shape)
        self.assertEqual(raster.shape, self.raster_shape)

    def test_raster_max_same_as_data_max(self):
        # Do not test base class!
        if self.__class__ is BaseLayerTestCase:
            return
        import numpy as np
        _, raster, raw_data = self.layer.generate(self.test_bounds, self.raster_shape)
        self.assertAlmostEqual(np.nanmax(raster), raw_data['density'].max())

    def test_plot_raster(self):
        # Do not test base class!
        if self.__class__ is BaseLayerTestCase:
            return
        import matplotlib.pyplot as mpl
        import numpy as np

        _, raster, _ = self.layer.generate(self.test_bounds, self.raster_shape, hour=13)

        fig, ax = mpl.subplots(1, 1)
        m = ax.matshow(np.flipud(raster))
        ax.set_title(self.plot_title)
        fig.colorbar(m, label='Population Density [people/km$^2$]')
        fig.show()


if __name__ == '__main__':
    unittest.main()
