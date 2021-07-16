from PySide2 import QtWidgets
from PySide2.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from seedpod_ground_risk.pathfinding.moo_ga import *


class DataGraph(FigureCanvas):
    def __init__(self, parent, path, grid):
        fig = Figure(figsize=(10, 5), dpi=300)
        self.ax1 = fig.add_subplot(111)
        super(DataGraph, self).__init__(fig)

        ys = []
        for idx in range(len(path[:-1])):
            n0 = path[idx].position
            n1 = path[idx + 1].position
            l = line(n0[0], n0[1], n1[0], n1[1])
            ys.append(grid[l[0], l[1]])
        ys = np.hstack(ys)
        self.ax1.plot(ys)

        super().__init__(fig)
        self.setParent(parent)


class GraphPopup(QWidget):
    def __init__(self, path, grid):
        super().__init__(path, grid)
        self.resize(1600, 800)
        chart = DataGraph(path, grid)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(chart)

        self.show()
