import numpy as np

from seedpod_ground_risk.path_analysis.harm_models.harm_model import HarmModel


def prob_fatality(ke_impact, alpha, beta, p_s):
    """
    Method from
    :cite: Dalamagkidis et al. ‘On Unmanned Aircraft Systems Issues, Challenges and
    Operational Restrictions Preventing Integration into the National Airspace System’
     https://doi.org/10.1016/j.paerosci.2008.08.001.

    This effectively maps the impact kinetic energy to probability of fatality in the form of a parameterised logistic growth curve.

    :param ke_impact: Kinetic energy of impact in Joules
    :param alpha: KE required at 0.5 p_s for 50% lethality probability
    :param beta: Fatal KE of direct impact (0 p_s)
    :param p_s: probability of sheltering [0-1]
    :return: probability of fatality [0-1]
    """
    return 1 / (1 + (np.sqrt(alpha / beta)) * np.power(beta / ke_impact, 1 / (4 * p_s)))


class FatalityModel(HarmModel):

    def __init__(self, impact_ke, shelter_prob, alpha, beta) -> None:
        """
        All params can either be a scalar or np.array.

        All np.array must share a common shape.

        :param impact_ke: Kinetic energy of impact in Joules
        :param alpha: KE required at 0.5 p_s for 50% lethality probability
        :param beta: Fatal KE of direct impact (0 p_s)
        :param shelter_prob: probability of sheltering [0-1]
        """
        super().__init__()
        self.impact_ke = impact_ke
        self.shelter_prob = shelter_prob
        self.alpha = alpha
        self.beta = beta

    def transform(self, val):
        return val * prob_fatality(self.impact_ke, self.alpha, self.beta, self.shelter_prob)
