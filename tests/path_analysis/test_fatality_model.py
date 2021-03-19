import unittest

import matplotlib.pyplot as mpl
import numpy as np
from labellines import labelLines

from seedpod_ground_risk.path_analysis.harm_models.fatality_model import prob_fatality


class FatalityModelTestCase(unittest.TestCase):

    def test_curve_means(self):
        """
        Test curves approx follow correct shape by testing mean values of each
        """
        alpha = 1e6
        beta = 34
        p_s = np.linspace(0, 1, 11)

        ke = np.logspace(0, 15)
        p_f = [prob_fatality(ke, alpha, beta, p) for p in p_s]
        means = [pf.mean() for pf in p_f]
        self.assertEqual(len(p_f), 11)
        np.testing.assert_almost_equal(means, [0.88,
                                               0.8315,
                                               0.7731,
                                               0.7147,
                                               0.6563,
                                               0.5979,
                                               0.5395,
                                               0.4812,
                                               0.4235,
                                               0.3670,
                                               0.3132],
                                       decimal=4)

    def test_ranges(self):
        """
        Ensure model range is always :math: \\in [0,1]
        """
        alpha = 1e6
        beta = 34
        p_s = np.linspace(0, 1, 11)

        ke = np.logspace(0, 15)
        p_f = np.array([prob_fatality(ke, alpha, beta, p) for p in p_s])
        self.assertLessEqual(p_f.max(), 1)
        self.assertGreaterEqual(p_f.min(), 0)

    def test_fatality_prob_curves(self):
        """
        Recreate the figure in Dalamagkidis et al.
        """
        alpha = 1e6
        beta = 34
        p_s = np.linspace(0, 1, 11)

        ke = np.logspace(0, 15)
        p_f = [prob_fatality(ke, alpha, beta, p) for p in p_s]

        fig, ax = mpl.subplots(1, 1, figsize=(8, 5))
        ax.set_xlim(1, 1e14)
        ax.set_ylim(0, 1.1)
        for idx, p in enumerate(p_f):
            ax.plot(ke, p, label=f'$p_s={p_s[idx]:1g}$')

        x_pos = np.logspace(1.6, 11.6, 11)
        labelLines(ax.get_lines(), xvals=x_pos)

        ax.set_xlabel('Impact Kinetic Energy [J]')
        ax.set_ylabel('Probability of Fatality')
        ax.set_xscale('symlog')
        ax.set_title(f'Probability of Fatality - Dalamagkidis Model\n $\\alpha={alpha:3g}$, $\\beta={beta:3g}$')
        fig.show()


if __name__ == '__main__':
    unittest.main()
