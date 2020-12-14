import os
import sys
import time

from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap, QTextDocument
from PySide2.QtWidgets import QDialog, QMainWindow, QApplication, QAbstractItemView, QListWidgetItem, QSplashScreen, \
    QMessageBox, QFileDialog

from seedpod_ground_risk.layers.roads_layer import generate_week_timesteps
from seedpod_ground_risk.ui_resources.mainwindow import Ui_MainWindow
from seedpod_ground_risk.ui_resources.textdialog import Ui_TextAboutDialog


class TextAboutDialog(QDialog):
    def __init__(self, title):
        super(TextAboutDialog, self).__init__()
        self.ui = Ui_TextAboutDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(title)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, rasterise=True):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.plot_server = PlotServer(tiles='Wikipedia',
                                      rasterise=rasterise,
                                      progress_callback=self.status_update,
                                      update_callback=self.layers_update)
        self.plot_server.start()

        self.webview.load(self.plot_server.url)
        self.webview.show()

        self.listWidget.setEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.itemDropped.connect(self.layer_reorder)
        self.listWidget.itemDoubleClicked.connect(self.layer_edit)

        self.timeSlider.valueChanged.connect(self.time_changed)

        self.actionRasterise.triggered.connect(self.menu_config_rasterise)
        self.actionImport.triggered.connect(self.menu_file_import)
        self.actionExport.triggered.connect(self.menu_file_export)
        self.actionAbout_Static_Sources.triggered.connect(self.menu_about_static_sources)
        self.actionAbout_App.triggered.connect(self.menu_about_app)

    def menu_config_rasterise(self, checked):
        # TODO: Allow reliable on-the-fly rasterisation switching
        # self.plot_server.set_rasterise(checked)
        if not checked:
            msg_box = QMessageBox()
            msg_box.warning(self, "Warning", "Not rasterising increases generation and render times significantly!")

    def menu_file_import(self):
        filepath = QFileDialog.getOpenFileName(self, "Import GeoJSON geometry...", os.getcwd(),
                                               "GeoJSON Files (*.json)")
        if filepath:
            self.plot_server.add_geojson_layer(filepath[0])

    def menu_file_export(self):
        from PySide2.QtCore import QFile

        file_dir = QFileDialog.getExistingDirectory(self, "Save plot image...", os.getcwd(), QFileDialog.ShowDirsOnly)
        file = QFile(os.path.join(file_dir, 'risk_plot.png'))
        self.webview.grab().save(file)

    def menu_about_static_sources(self):
        self.dialog = TextAboutDialog('About Data')
        doc = QTextDocument()
        doc.setMarkdown(self._read_file('static_data/DATA_SOURCES.md'))
        self.dialog.ui.textEdit.setDocument(doc)
        self.dialog.show()

    def menu_about_app(self):
        self.dialog = TextAboutDialog('About')
        doc = QTextDocument()
        doc.setMarkdown(self._read_file('README.md'))
        self.dialog.ui.textEdit.setDocument(doc)
        self.dialog.show()

    def status_update(self, update_str: str):
        self.statusBar.showMessage(update_str)

    def layers_update(self):
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

    def time_changed(self, value):
        labels = generate_week_timesteps()
        self.plot_server.set_time(value)
        self.timeSliderLabel.setText(labels[value])

    def _read_file(self, file_path: str) -> str:
        from PySide2.QtCore import QFile
        from PySide2.QtCore import QTextStream
        from PySide2.QtCore import QIODevice

        file = QFile(file_path)
        file.open(QIODevice.ReadOnly)
        ts = QTextStream(file)
        string = ts.readAll()
        return string


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pixmap = QPixmap('seedpod_ground_risk/ui_resources/cascade_splash.png')
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint)
    splash.setEnabled(False)
    splash.setMask(pixmap.mask())
    splash.show()
    time.sleep(0.1)  # This seems to fix the splash mask displaying but not the actual image
    app.processEvents()

    from seedpod_ground_risk.plot_server import PlotServer

    msg_box = QMessageBox()
    msg_box.setDefaultButton(QMessageBox.Yes)
    button_clicked = msg_box.question(splash, "Use Rasterisation?",
                                      "Rasterising will reduce the resolution of the plot but generate significantly "
                                      "faster.",
                                      QMessageBox.Yes | QMessageBox.No,
                                      QMessageBox.Yes)
    app.processEvents()
    rasterise = (button_clicked == msg_box.Yes)

    window = MainWindow(rasterise=rasterise)
    window.show()
    window.raise_()
    window.activateWindow()
    splash.finish(window)
    sys.exit(app.exec_())
