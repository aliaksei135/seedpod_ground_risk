import matplotlib.pyplot as mpl
from PySide2.QtWidgets import QDialog, QVBoxLayout
from matplotlib import gridspec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from seedpod_ground_risk.pathfinding.moo_ga import *


# main window
# which inherits QDialog
class DataWindow(QDialog):

    # constructor
    def __init__(self, pathfinding_layer, grid, resolution, raster_grid, raster_indices, parent=None):
        super(DataWindow, self).__init__(parent)
        self.resize(1000, 500)
        self.figure = mpl.figure(figsize=(8, 4))
        self.pathfinding_layer = pathfinding_layer
        self.grid = grid
        self.resolution = resolution
        self.raster_grid = raster_grid
        self.raster_indices = raster_indices

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.setWindowTitle("Path Data")

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        gs = gridspec.GridSpec(1, 2, width_ratios=[2.5, 1])
        ax1 = self.figure.add_subplot(gs[0])
        ax2 = self.figure.add_subplot(gs[1])
        path = self.pathfinding_layer.path
        ys = []
        dist = []
        for idx in range(len(path[:-1])):
            n0 = path[idx].position
            n1 = path[idx + 1].position
            l = line(n0[0], n0[1], n1[0], n1[1])
            ys.append(grid[l[0], l[1]])
            # if len(dist) != 0:

        path_dist = self.pathfinding_layer.dataframe.to_crs('EPSG:27700').iloc[0].geometry.length
        ys = np.hstack(ys)
        x = np.linspace(0, path_dist, len(ys))
        ax1.plot(x, ys)
        ax1.set_xlabel('Distance [m]')
        ax1.set_ylabel('Risk of fatality [per hour]')

        p = self.create_info_patch(ys)
        data_txt = f"The total fatality risk over this path is \n{self.op_format(ys, sum)} per hour" \
                   f"\n\nThe average fatality risk over this path is \n{self.op_format(ys, np.average)} per hour" \
                   f"\n\nThe max fatality risk over this path is \n{self.op_format(ys, max)} per hour" \
                   f"\n\nThe min fatality risk over this path is \n{self.op_format(ys, min)} per hour"

        ax2.add_patch(p)
        ax2.axis('off')
        ax2.text(0.5, 0.5, data_txt,
                 horizontalalignment='center',
                 verticalalignment='center',
                 fontsize=10, color='black',
                 transform=ax2.transAxes, wrap=True)

        self.canvas.draw()
        self.show()

    def op_format(self, val, op):
        return "{:.2e}".format(op(val))

    def create_info_patch(self, ys):
        import matplotlib.patches as pch

        left, width = 0, 1
        bottom, height = 0, 1
        right = left + width
        top = bottom + height

        p = pch.Rectangle(
            (left, bottom), width, height, color="white",
            fill=False, clip_on=False
        )

        return p