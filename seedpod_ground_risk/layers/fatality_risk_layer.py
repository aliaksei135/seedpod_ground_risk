import geoviews as gv
import numpy as np

from seedpod_ground_risk.layers.blockable_data_layer import BlockableDataLayer
from seedpod_ground_risk.layers.strike_risk_layer import StrikeRiskLayer
from seedpod_ground_risk.path_analysis.harm_models.fatality_model import FatalityModel
from seedpod_ground_risk.ui_resources.aircraft_options import AIRCRAFT_LIST


class FatalityRiskLayer(BlockableDataLayer):

    def __init__(self, key, ac: str = 'Default',
                 wind_vel: float = 0, wind_dir: float = 0, colour: str = None, blocking=False, buffer_dist=0,
                 **kwargs):
        super().__init__(key, colour, blocking, buffer_dist)
        self.ac = ac
        self.wind_vel = wind_vel
        self.wind_dir = wind_dir
        self.ac_dict = AIRCRAFT_LIST[ac]
        self._strike_layer = StrikeRiskLayer(f'{key}_strike_', ac=self.ac_dict, wind_vel=self.wind_vel,
                                             wind_dir=self.wind_dir,
                                             buffer_dist=buffer_dist, **kwargs)
        delattr(self, '_colour')

    def preload_data(self):
        self._strike_layer.preload_data()

    def generate(self, bounds_polygon, raster_shape, hour=8, resolution=30, **kwargs):
        strike_risk, impact_kes = self._strike_layer.make_strike_map(bounds_polygon, hour, raster_shape, resolution)

        fm = FatalityModel(0.3, 1e6, 34)
        risk_map = np.sum([fm.transform(strike_risk, impact_ke=ke) for ke in impact_kes], axis=0)

        bounds = bounds_polygon.bounds
        flipped_bounds = (bounds[1], bounds[0], bounds[3], bounds[2])
        risk_raster = gv.Image(risk_map, vdims=['strike_risk'], bounds=flipped_bounds).options(
            alpha=0.7,
            colorbar=True, colorbar_opts={'title': 'Person Fatality Risk [h^-1]'},
            cmap='viridis',
            tools=['hover'],
            clipping_colors={
                'min': (0, 0, 0, 0)})
        # import rasterio
        # from rasterio import transform
        # trans = transform.from_bounds(*flipped_bounds, *raster_shape)
        # p = os.path.expanduser(f'~/GroundRiskMaps')
        # if not os.path.exists(p):
        #     os.mkdir(p)
        # rds = rasterio.open(
        #     os.path.expanduser(p + f'/fatality_risk_{hour}h_ac{hash(self._strike_layer.aircraft)}.tif'),
        #     'w', driver='GTiff', count=1, dtype=rasterio.float64, crs='EPSG:4326', transform=trans, compress='lzw',
        #     width=raster_shape[0], height=raster_shape[1])
        # rds.write(risk_map, 1)
        # rds.close()

        return risk_raster, risk_map, None

    def clear_cache(self):
        pass
