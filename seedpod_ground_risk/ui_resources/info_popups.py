import matplotlib.pyplot as mpl
from PySide2.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from seedpod_ground_risk.pathfinding.moo_ga import *


# main window
# which inherits QDialog
class DataWindow(QDialog):

    # constructor
    def __init__(self, path, grid, parent=None):
        super(DataWindow, self).__init__(parent)
        self.figure = mpl.figure()
        self.path = path
        self.grid = grid

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.setWindowTitle("Path Data")

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
        ys = []
        dist = []
        for idx in range(len(path[:-1])):
            n0 = self.path[idx].position
            n1 = self.path[idx + 1].position
            l = line(n0[0], n0[1], n1[0], n1[1])
            ys.append(grid[l[0], l[1]])
        ys = np.hstack(ys)
        ax1.plot(ys)
        ax1.set_xlabel('Distance (m)')
        ax1.set_ylabel('Risk of fatality (per hour)')
        ax1.set_title(f"The total fatality risk over this path = {self.total_risk(ys)} per hour", pad=20)

        ax2.add_patch(p)
        self.canvas.draw()
        self.show()

    def total_risk(self, ys):
        tot_risk = "{:.2e}".format(sum(ys))
        return tot_risk

    def create_info_patch(self):

        # build a rectangle in axes coords
        left, width = .25, .5
        bottom, height = .25, .5
        right = left + width
        top = bottom + height

        # axes coordinates: (0, 0) is bottom left and (1, 1) is upper right
        p = patches.Rectangle(
            (left, bottom), width, height,
            fill=False, clip_on=False
        )

        return p


