import abc
from typing import NoReturn


class Layer(abc.ABC):
    """
    Abstract base class for a single layer
    """
    key: str
    is_dynamic: bool

    def __init__(self, key, rasterise: bool = True):
        self.key = key
        self.is_dynamic = False
        self.rasterise = rasterise

    @abc.abstractmethod
    def preload_data(self) -> NoReturn:
        """
        Load any data that is expected to remain static for the duration of the program execution.
        This is called when the application is first initialised.
        This method is guaranteed to complete execution before any requests for plot generation to this class.
        """
        pass

    @abc.abstractmethod
    def clear_cache(self) -> NoReturn:
        """
        Clear all cached dynamic data to the state AFTER `preload_data` was called.
        All statically preloaded data should remain intact after calls to this method
        """
        pass
