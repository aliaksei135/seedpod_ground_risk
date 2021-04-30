from casex import *

from seedpod_ground_risk.path_analysis.descent_models.descent_model import DescentModel, primitives_to_dist


class BallisticModel(DescentModel):

    def __init__(self, aircraft: AircraftSpecs, n_samples: int = 2000) -> None:
        super().__init__(aircraft, n_samples)

        self.bm = BallisticDescent2ndOrderDragApproximation()
        self.bm.set_aircraft(aircraft)

    def transform(self, altitude, velocity, heading, wind_vel_y, wind_vel_x, loc_x,
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
        :return: a tuple of (means, covariances) of the distribution
        :rtype: tuple of np.arrays of shape (2,) for the means and (2,2) for the covariances
        """
        # Compute impact distances and times in the PAE frame
        # The velocity vector is assumed to be aligned with path vector, hence v_y is 0
        d_i, v_i, a_i, t_i = self.bm.compute_ballistic_distance(altitude, velocity, 0)

        return primitives_to_dist(a_i, d_i, heading, loc_x, loc_y, t_i, v_i, wind_vel_x, wind_vel_y)
