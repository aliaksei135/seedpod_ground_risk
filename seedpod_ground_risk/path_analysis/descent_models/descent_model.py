import abc

from casex import AircraftSpecs


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
