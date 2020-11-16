import sys

from PySide2 import QtCore
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import *

from plot_server import PlotServer
from ui_resources.mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.plot_server = PlotServer(progress_callback=self.update_progress,
                                      update_callback=self.update_layers_tree)
        self.plot_server.start()

        self.webview.load(self.plot_server.url)
        self.webview.show()

        self.layers_model = QStandardItemModel(self.treeView)
        self.layers_model.itemChanged.connect(self.layer_key_updated)
        self.treeView.setModel(self.layers_model)
        self.treeView.setEnabled(True)

    def update_progress(self, update_str: str):
        self.statusBar.showMessage(update_str)

    def update_layers_tree(self):
        self.layers_model.clear()
        append = self.layers_model.appendRow
        for k in self.plot_server.layers.keys():
            item = QStandardItem(k)
            if k is 'base':
                item.setEditable(False)
            append(item)

    def layer_key_updated(self, layer):
        pass


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
