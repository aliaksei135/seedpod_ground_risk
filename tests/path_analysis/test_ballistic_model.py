import unittest

import scipy.stats as ss
from casex import *

from seedpod_ground_risk.path_analysis.ballistic_model import BallisticModel


class BallisticModelPAEFTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.ac = AircraftSpecs(enums.AircraftType.FIXED_WING,
                                2,  # width
                                1.8,  # length
                                7  # mass
                                )
        self.ac.set_ballistic_frontal_area(2)
        self.ac.set_glide_speed_ratio(15, 12)
        self.ac.set_glide_drag_coefficient(0.3)
        self.ac.set_ballistic_drag_coefficient(1.1)

        self.bm = BallisticDescent2ndOrderDragApproximation()
        self.bm.set_aircraft(self.ac)

    def test_ballistic_dist(self):
        """
        Test ballistic model impact distance distributions in the Path Aligned Event frame
        """
        alt_mean = 50
        alt_std = 5
        vx_mean = 18
        vx_std = 2.5
        vy = 1
        samples = 2000

        # Compute ballistic distances in the path aligned LTP frame with origin at the directly below the event location
        # AKA PAEF
        d_i, v_i, a_i, t_i = self.bm.compute_ballistic_distance(ss.norm(alt_mean, alt_std).rvs(samples),
                                                                ss.norm(vx_mean, vx_std).rvs(samples), vy)

        di_mean, di_std = ss.norm.fit(d_i)
        self.assertAlmostEqual(di_mean, 13.4, delta=0.5)
        self.assertAlmostEqual(di_std, 1.5, delta=0.2)

    def test_ballistic_time(self):
        """
        Test ballistic model impact time distributions in the Path Aligned Event frame
        """
        alt_mean = 50
        alt_std = 5
        vx_mean = 18
        vx_std = 2.5
        vy = 1
        samples = 2000

        # Compute ballistic distances in the path aligned LTP frame with origin at the directly below the event location
        # AKA PAEF
        d_i, v_i, a_i, t_i = self.bm.compute_ballistic_distance(ss.norm(alt_mean, alt_std).rvs(samples),
                                                                ss.norm(vx_mean, vx_std).rvs(samples), vy)

        ti_mean, ti_std = ss.norm.fit(t_i)
        self.assertAlmostEqual(ti_mean, 7.4, delta=0.5)
        self.assertAlmostEqual(ti_std, 0.7, delta=0.2)

    def test_ballistic_vel(self):
        """
        Test ballistic model impact velocity distributions in the Path Aligned Event frame
        """
        alt_mean = 50
        alt_std = 5
        vx_mean = 18
        vx_std = 2.5
        vy = 1
        samples = 2000

        # Compute ballistic distances in the path aligned LTP frame with origin at the directly below the event location
        # AKA PAEF
        d_i, v_i, a_i, t_i = self.bm.compute_ballistic_distance(ss.norm(alt_mean, alt_std).rvs(samples),
                                                                ss.norm(vx_mean, vx_std).rvs(samples), vy)

        vi_mean, vi_std = ss.norm.fit(v_i)
        self.assertAlmostEqual(vi_mean, 7.1, delta=0.05)
        self.assertAlmostEqual(vi_std, 0.2, delta=0.2)


class BallisticModelNEDWindTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.ac = AircraftSpecs(enums.AircraftType.FIXED_WING,
                                2,  # width
                                1.8,  # length
                                7  # mass
                                )
        self.ac.set_ballistic_frontal_area(2)
        self.ac.set_glide_speed_ratio(15, 12)
        self.ac.set_glide_drag_coefficient(0.3)
        self.ac.set_ballistic_drag_coefficient(1.1)

        self.bm = BallisticDescent2ndOrderDragApproximation()
        self.bm.set_aircraft(self.ac)

    def test_ballistic_dist(self):
        """
        Profile ballistic model impact distance distributions in the North East Down frame with wind compensation
        """
        make_plot = False  # Set flag to plot result
        samples = 5000

        # Conjure up our distributions for various things
        alt_mean = 50
        alt_std = 5
        alt = ss.norm(alt_mean, alt_std).rvs(samples)
        vx_mean = 18
        vx_std = 2.5
        vel = ss.norm(vx_mean, vx_std).rvs(samples)
        heading_mean = np.deg2rad(270)
        heading_std = np.deg2rad(2)
        heading = ss.norm(heading_mean, heading_std).rvs(samples)

        loc_x, loc_y = 0, 50

        wind_vel_x = ss.norm(5, 1).rvs(samples)
        wind_vel_y = ss.norm(1, 1).rvs(samples)

        bm = BallisticModel(self.ac)
        means, cov = bm.impact_distance_dist_params_ned_with_wind(alt, vel, heading, wind_vel_y, wind_vel_x, loc_x,
                                                                  loc_y)
        pdf = ss.multivariate_normal(mean=means, cov=cov).pdf

        if make_plot:
            # Make a sampling grid for plotting
            x, y = np.mgrid[(loc_x - 100):(loc_x + 100), (loc_y - 100):(loc_y + 100)]
            pos = np.vstack([x.ravel(), y.ravel()])
            # Sample KDE PDF on these points
            density = pdf(pos.T)
            # Plot sampled KDE PDF
            import matplotlib.pyplot as mpl
            fig, ax = mpl.subplots(1, 1)
            sc = ax.scatter(x, y, c=density)
            fig.colorbar(sc)
            fig.show()


if __name__ == '__main__':
    unittest.main()
