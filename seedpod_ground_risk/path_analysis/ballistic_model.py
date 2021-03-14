from casex import *
from numba import njit
from sklearn.mixture import GaussianMixture

from seedpod_ground_risk.path_analysis.descent_model import DescentModel
from seedpod_ground_risk.path_analysis.utils import rotate_2d


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


class BallisticModel(DescentModel):

    def __init__(self, aircraft: AircraftSpecs, n_samples: int = 2000) -> None:
        super().__init__(aircraft, n_samples)

        self.bm = BallisticDescent2ndOrderDragApproximation()
        self.bm.set_aircraft(aircraft)

    def impact_distance_dist_params_ned_with_wind(self, altitude, velocity, heading, wind_vel_y, wind_vel_x, loc_x,
                                                  loc_y):
        """
        Return the parameters to a multivariate normal distribution describing the ground impact probability under a
        ballistic descent.

        This function takes into account wind and returns the result in the NED frame with x, y corresponding to
         East and North respectively. The distribution takes in the location of the event in the existing NED frame
         and transforms the Path aligned event frame (PAEF) to the NED frame at the specified location.

         If passing an array, all other arrays must be the same shape. This is usually a single dimension of samples
         generated with scipy.stats.<some distribution>.rvs

        The method is as follows:
            1. The ballistic model return one dimensional results from the specified params, if these are arrays then
                a number of samples are created.
            2. The heading(s) are rotated into the NED frame
            3. A vectorised operation is performed to firstly rotate the PAEF results into the NED frame
            4. The second part of the vectorised operation then multiplies the wind vector (in NED) by the time
                taken to impact the ground. This is then added to the first part.
            5. The samples are used to fit a multivariate Gaussian from which the parameters are generated.

        :param altitude: the altitude in metres
        :type altitude: float or np.array
        :param velocity: the velocity over the ground of the aircraft in the direction of flight in m/s
        :type velocity: float or np.array
        :param heading: the ground track angle of the aircraf in deg
        :type heading: float or np.array
        :param wind_vel_x: the x component of the wind in m/s
        :type wind_vel_x: float or nd.array
        :param wind_vel_y: the y component of the wind in m/s
        :type wind_vel_y: float or nd.array
        :param loc_x: event x location
        :type loc_x: int
        :param loc_y: event y location
        :type loc_y: int
        :return: a tuple of (means, covariances) of the distribution
        :rtype: tuple of np.arrays of shape (2,) for the means and (2,2) for the covariances
        """
        # Compute impact distances and times in the PAE frame
        # The velocity vector is assumed to be aligned with path vector, hence v_y is 0
        d_i, _, _, t_i = self.bm.compute_ballistic_distance(altitude, velocity, 0)

        # Compensate for x,y axes being rotated compared to bearings
        theta = (heading - (np.pi / 2)) * (2 * np.pi)
        # Get angle distribution in between body and NED frame
        # Form the array structure required and transform
        arr = np.vstack((np.zeros(d_i.shape), d_i, t_i, theta, wind_vel_x, wind_vel_y))
        transformed_arr = np.apply_along_axis(paef_to_ned_with_wind, 0, arr)
        gm = GaussianMixture()
        gm.fit_predict(transformed_arr.T)
        # If there the event and NED origins match, no need to translate
        if not loc_x or not loc_y:
            means = gm.means_[0] + np.array([loc_x, loc_y])
        else:
            means = gm.means_[0]
        # Gaussian Mixture model can deal with up to 3D distributions, but we are only dealing with 2D here,
        # so take first index into the depth
        return means, gm.covariances_[0]
