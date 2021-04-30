import unittest

import scipy.stats as ss
from casex import *

from seedpod_ground_risk.path_analysis.descent_models.glide_model import GlideDescentModel
from seedpod_ground_risk.path_analysis.utils import bearing_to_angle


class GlideModelNEDWindTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.ac = AircraftSpecs(enums.AircraftType.FIXED_WING,
                                1,  # width
                                0.3,  # length
                                3.75  # mass
                                )
        self.ac.set_ballistic_frontal_area(0.1)
        self.ac.set_glide_speed_ratio(16, 12)
        self.ac.set_glide_drag_coefficient(0.1)
        self.ac.set_ballistic_drag_coefficient(0.9)

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
        track_mean = 60
        track_std = 2

        # In degrees!
        wind_dir_mean = 120
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

        bm = GlideDescentModel(self.ac)
        (means, cov), v_i, a_i = bm.transform(alt, vel, track, wind_vel_y, wind_vel_x, loc_x, loc_y)
        dist = ss.multivariate_normal(mean=means, cov=cov)

        if make_plot:
            # Make a sampling grid for plotting
            x, y = np.mgrid[(loc_x - 10):(loc_x + 1200), (loc_y - 50):(loc_y + 250)]
            pos = np.vstack([x.ravel(), y.ravel()])
            # Sample KDE PDF on these points
            density = dist.pdf(pos.T)
            # Plot sampled KDE PDF
            import matplotlib.pyplot as mpl
            fig, ax = mpl.subplots(1, 1, figsize=(8, 8))
            sc = ax.scatter(x, y, c=density)
            cbar = fig.colorbar(sc)
            cbar.set_label('Probability')
            ax.set_xlabel('Distance [m]')
            ax.set_ylabel('Distance [m]')
            ax.set_title(f'Uncontrolled Glide Ground Impact Probability Density \n'
                         f' Altitude $\sim \mathcal{{N}}({alt_mean},{alt_std}^2)$m,'
                         f' Airspeed $\sim \mathcal{{N}}({vx_mean},{vx_std}^2)$m/s,'
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
