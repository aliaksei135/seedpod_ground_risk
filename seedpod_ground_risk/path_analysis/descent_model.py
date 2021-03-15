from casex import AircraftSpecs


class DescentModel:

    def __init__(self, aircraft: AircraftSpecs, n_samples: int = 2000) -> None:
        self.aircraft = aircraft
        self.n_samples = n_samples
