import sys

from PySide2 import QtCore
from PySide2.QtCore import Qt
from PySide2.QtWidgets import *

from plot_server import PlotServer
from ui_resources.mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.plot_server = PlotServer(tiles='Wikipedia',
                                      rasterise=False,
                                      progress_callback=self.update_progress,
                                      update_callback=self.update_layers_tree)
        self.plot_server.start()

        self.webview.load(self.plot_server.url)
        self.webview.show()

        self.listWidget.setEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.itemDoubleClicked.connect(self.layer_edit)

    def update_progress(self, update_str: str):
        self.statusBar.showMessage(update_str)

    def update_layers_tree(self):
        self.listWidget.clear()
        for layer in self.plot_server._generated_layers.keys():
            item = QListWidgetItem(layer)
            item.setCheckState(Qt.CheckState.Checked)
            self.listWidget.addItem(item)

    def layer_edit(self, item):
        print('Editing ', item)
        pass


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
