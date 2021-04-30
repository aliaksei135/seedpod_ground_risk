import abc

import numpy as np
from casex import AircraftSpecs
from numba import njit
from sklearn.mixture import GaussianMixture

from seedpod_ground_risk.path_analysis.utils import bearing_to_angle, rotate_2d


@njit(cache=True)
def paef_to_ned_with_wind(x):
    """
    Transform PAE frame distances to NED frame and transform with wind.
    This func is designed to be used in np apply, hence the single arg. The column ordering is very specific!
    :param x: array row with ordering [paef_y (always 0), paef_x, impact_time, theta (rad), wind_vel_x, wind_vel_y]
    :return:
    """
    paef_c = x[0:2]
    t_i = x[2]
    theta = x[3]
    wind_vect = x[4:6]
    return rotate_2d(paef_c, theta) + wind_vect * t_i


def primitives_to_dist(a_i, d_i, heading, loc_x, loc_y, t_i, v_i, wind_vel_x, wind_vel_y):
    # Compensate for x,y axes being rotated compared to bearings
    theta = bearing_to_angle(heading)
    # Form the array structure required and transform
    arr = np.vstack((np.zeros(d_i.shape), d_i, t_i, theta, wind_vel_x, wind_vel_y))
    transformed_arr = np.apply_along_axis(paef_to_ned_with_wind, 0, arr)
    # Remove nan rows
    transformed_arr = transformed_arr[:, ~np.isnan(transformed_arr).all(axis=0)]
    gm = GaussianMixture()
    gm.fit_predict(transformed_arr.T)
    # If there the event and NED origins match, no need to translate
    if not loc_x or not loc_y:
        means = gm.means_[0]
    else:
        means = gm.means_[0] + np.array([loc_x, loc_y])
    # Gaussian Mixture model can deal with up to 3D distributions, but we are only dealing with 2D here,
    # so take first index into the depth
    return (means, gm.covariances_[0]), v_i.mean(), a_i.mean()


class DescentModel(abc.ABC):
    """
    The purpose of the descent model is to map the UAS properties and instantaneous kinematic states
     to an impact location distribution on the ground.
    """

    def __init__(self, aircraft: AircraftSpecs, n_samples: int = 2000) -> None:
        self.aircraft = aircraft
        self.n_samples = n_samples

    @abc.abstractmethod
    def transform(self, altitude, velocity, heading, wind_vel_y, wind_vel_x, loc_x, loc_y):
        """
        :param altitude: the altitude in metres
        :type altitude: float or np.array
        :param velocity: the velocity over the ground of the aircraft in the direction of flight in m/s
        :type velocity: float or np.array
        :param heading: the ground track bearing of the aircraft in deg (North is 000)
        :type heading: float or np.array
        :param wind_vel_x: the x component of the wind in m/s
        :type wind_vel_x: float or nd.array
        :param wind_vel_y: the y component of the wind in m/s
        :type wind_vel_y: float or nd.array
        :param loc_x: event x location
        :type loc_x: int
        :param loc_y: event y location
        :type loc_y: int
        """
        pass
