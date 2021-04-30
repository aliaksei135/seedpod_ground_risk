import numpy as np
from casex import AircraftSpecs

from seedpod_ground_risk.path_analysis.descent_models.descent_model import DescentModel, primitives_to_dist


class GlideDescentModel(DescentModel):

    def __init__(self, aircraft: AircraftSpecs, n_samples: int = 2000) -> None:
        super().__init__(aircraft, n_samples)

    def transform(self, altitude, velocity, heading, wind_vel_y, wind_vel_x, loc_x, loc_y):
        d_i = self.aircraft.glide_ratio * altitude  # Horizontal distance
        t_i = np.sqrt((d_i ** 2) + (altitude ** 2)) / self.aircraft.glide_speed  # 3D distance/airspeed
        a_i = np.arctan(1 / self.aircraft.glide_ratio)
        v_i = d_i / t_i

        return primitives_to_dist(a_i, d_i, heading, loc_x, loc_y, t_i, v_i, wind_vel_x, wind_vel_y)
