import abc


class HarmModel(abc.ABC):
    """
    The purpose of a harm model is to map between probability distributions of different harm variables
    """

    @abc.abstractmethod
    def transform(self, val):
        """

        :param val: input probability scalar or np.array
        """
        pass
