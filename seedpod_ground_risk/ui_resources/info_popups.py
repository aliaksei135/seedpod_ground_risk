import matplotlib as plt
import numpy as np
from PySide2.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class RiskDistanceGraph(FigureCanvas):
    def __init__(self, parent):
        fig, self.ax = plt.subplots(figsize=(5, 4), dpi=200)
        super().__init__(fig)
        self.setParent(parent)

        """ 
        Matplotlib Script
        """
        t = np.arange(0.0, 2.0, 0.01)
        s = 1 + np.sin(2 * np.pi * t)

        self.ax.plot(t, s)

        self.ax.set(xlabel='time (s)', ylabel='voltage (mV)',
                    title='About as simple as it gets, folks')
        self.ax.grid()


class RDGraphPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1600, 800)

        chart = RiskDistanceGraph(self)
