import sys

from PySide2 import QtCore
from PySide2.QtWidgets import *

from plot_server import PlotServer
from ui_resources.mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        plot_server = PlotServer(progress_callback=self.update_progress)
        plot_server.start()

        self.webview.load(plot_server.url)
        self.webview.show()

    def update_progress(self, update_str: str):
        self.statusBar.showMessage(update_str)


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
