import unittest

import scipy.stats as ss
from casex import *

from seedpod_ground_risk.path_analysis.ballistic_model import BallisticModel
from seedpod_ground_risk.path_analysis.utils import bearing_to_angle


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

        import matplotlib.pyplot as mpl
        x = np.linspace(d_i.min(), d_i.max())
        y = ss.norm(di_mean, di_std).pdf(x)
        fig, ax = mpl.subplots(1, 1)
        ax.hist(d_i, density=True)
        ax.plot(x, y, 'r')
        ax.set_title('Event to Impact 1D Distance')
        ax.set_ylabel('Probability Density')
        ax.set_xlabel('Distance to Impact [m]')
        fig.show()

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

        import matplotlib.pyplot as mpl
        x = np.linspace(t_i.min(), t_i.max())
        y = ss.norm(ti_mean, ti_std).pdf(x)
        fig, ax = mpl.subplots(1, 1)
        ax.hist(t_i, density=True)
        ax.plot(x, y, 'r')
        ax.set_title('Event to Impact Time')
        ax.set_ylabel('Probability Density')
        ax.set_xlabel('Time to Impact [sec]')
        fig.show()

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
        self.ac.set_glide_drag_coefficient(0.1)
        self.ac.set_ballistic_drag_coefficient(0.8)

        self.bm = BallisticDescent2ndOrderDragApproximation()
        self.bm.set_aircraft(self.ac)

    def test_ballistic_dist(self):
        """
        Profile ballistic model impact distance distributions in the North East Down frame with wind compensation
        """
        make_plot = True  # Set flag to plot result
        samples = 3000

        loc_x, loc_y = 0, 0

        # Conjure up our distributions for various things
        alt_mean = 50
        alt_std = 5

        vx_mean = 18
        vx_std = 2.5

        # In degrees!
        track_mean = 90
        track_std = 2

        # In degrees!
        wind_dir_mean = 135
        wind_dir_std = 5
        wind_vel_mean = 10
        wind_vel_std = 2

        alt = ss.norm(alt_mean, alt_std).rvs(samples)
        vel = ss.norm(vx_mean, vx_std).rvs(samples)
        track = np.deg2rad(ss.norm(track_mean, track_std).rvs(samples))
        wind_vel = ss.norm(wind_vel_mean, wind_vel_std).rvs(samples)
        wind_dir = bearing_to_angle(np.deg2rad(ss.norm(wind_dir_mean, wind_dir_std).rvs(samples)))

        wind_vel_x = wind_vel * np.cos(wind_dir)
        wind_vel_y = wind_vel * np.sin(wind_dir)

        bm = BallisticModel(self.ac)
        means, cov = bm.impact_distance_dist_params_ned_with_wind(alt, vel, track, wind_vel_y, wind_vel_x, loc_x,
                                                                  loc_y)
        pdf = ss.multivariate_normal(mean=means, cov=cov).pdf

        if make_plot:
            # Make a sampling grid for plotting
            x, y = np.mgrid[(loc_x - 10):(loc_x + 100), (loc_y - 100):(loc_y + 100)]
            pos = np.vstack([x.ravel(), y.ravel()])
            # Sample KDE PDF on these points
            density = pdf(pos.T)
            # Plot sampled KDE PDF
            import matplotlib.pyplot as mpl
            fig, ax = mpl.subplots(1, 1, figsize=(8, 8))
            sc = ax.scatter(x, y, c=density)
            cbar = fig.colorbar(sc)
            cbar.set_label('Probability')
            ax.set_xlabel('Distance [m]')
            ax.set_ylabel('Distance [m]')
            ax.set_title(f'Ground Impact Probability Density \n'
                         f' Altitude $\sim \mathcal{{N}}({alt_mean},{alt_std}^2)$m,'
                         f' Groundspeed $\sim \mathcal{{N}}({vx_mean},{vx_std}^2)$m/s,'
                         f' Track $\sim \mathcal{{N}}({track_mean},{track_std}^2)$deg,\n'
                         f' Wind speed $\sim \mathcal{{N}}({wind_vel_mean},{wind_vel_std}^2)$m/s,'
                         f' Wind bearing $\sim \mathcal{{N}}({wind_dir_mean},{wind_dir_std}^2)$deg')
            ax.arrow(loc_x, loc_y, vx_mean * np.cos(bearing_to_angle(np.deg2rad(track_mean))),
                     vx_mean * np.sin(bearing_to_angle(np.deg2rad(track_mean))), label='UAS Track', width=1,
                     color='blue')
            ax.arrow(loc_x, loc_y, wind_vel_mean * np.cos(bearing_to_angle(np.deg2rad(wind_dir_mean))),
                     wind_vel_mean * np.sin(bearing_to_angle(np.deg2rad(wind_dir_mean))), label='Wind Direction',
                     width=1, color='red')
            fig.show()


if __name__ == '__main__':
    unittest.main()
