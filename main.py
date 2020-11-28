import sys
import time

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import *

from ui_resources.mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.plot_server = PlotServer(tiles='Wikipedia',
                                      rasterise=False,
                                      progress_callback=self.update_progress,
                                      update_callback=self.update_layers_list)
        self.plot_server.start()

        self.webview.load(self.plot_server.url)
        self.webview.show()

        self.listWidget.setEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.itemDropped.connect(self.layer_reorder)
        self.listWidget.itemDoubleClicked.connect(self.layer_edit)

    def update_progress(self, update_str: str):
        self.statusBar.showMessage(update_str)

    def update_layers_list(self):
        self.listWidget.clear()
        for layer in self.plot_server._generated_layers.keys():
            item = QListWidgetItem(layer)
            item.setCheckState(Qt.CheckState.Checked)
            self.listWidget.addItem(item)

    def layer_edit(self, item):
        print('Editing ', item)
        pass

    def layer_reorder(self):
        print('Layers reordered')
        self.plot_server.layer_order = [self.listWidget.item(n).text() for n in range(self.listWidget.count())]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pixmap = QPixmap('ui_resources/cascade_splash.png')
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint)
    splash.setEnabled(False)
    splash.setMask(pixmap.mask())
    splash.show()
    time.sleep(0.1)  # This seems to fix the splash mask displaying but not the actual image
    app.processEvents()

    from plot_server import PlotServer

    window = MainWindow()
    window.show()
    splash.finish(window)
    sys.exit(app.exec_())
