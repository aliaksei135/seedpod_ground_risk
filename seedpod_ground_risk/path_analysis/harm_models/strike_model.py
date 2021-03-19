import numpy as np

from seedpod_ground_risk.path_analysis.harm_models.harm_model import HarmModel


def get_lethal_area(theta: float, uas_width: float):
    """
    Calculate lethal area of UAS impact from impact angle

    Method from :cite: Smith, P.G. 2000

    :param theta: impact angle in radians
    :param uas_width: UAS width in metres
    :return:
    """
    r_person = 1  # radius of a person
    h_person = 1.8  # height of a person
    r_uas = uas_width / 2  # UAS halfspan

    return ((2 * (r_person + r_uas) * h_person) / np.tan(theta)) + (np.pi * (r_uas + r_person) ** 2)


class StrikeModel(HarmModel):

    def __init__(self, pop_density, pixel_area, impact_angle, uas_width) -> None:
        """
        :param pop_density: population density value or np.array
        :param pixel_area: area of a single pixel in the raster grid
        :param impact_angle: impact angle value or np.array
        :param uas_width: characteristic dimension of the UAS
        """
        super().__init__()
        self.pop_density = pop_density
        self.pix_area = pixel_area
        self.impact_angle = impact_angle
        self.uas_width = uas_width

    def transform(self, val):
        # Product of vars divided by pixel area to scale lethal area to proportion of pixel area
        return val * self.pop_density * get_lethal_area(self.impact_angle, uas_width=self.uas_width) / self.pix_area
