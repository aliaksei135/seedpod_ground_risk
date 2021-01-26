import multiprocessing
import os
import sys
import time

from seedpod_ground_risk.core.plot_worker import PlotWorker

print("Builtin modules imported")
from PySide2.QtCore import Qt, QRect, Slot, QThreadPool

print("QTCore imported")
from PySide2.QtGui import QPixmap, QCloseEvent

print("QtGUI imported")
from PySide2.QtWidgets import QDialog, QMainWindow, QApplication, QListWidgetItem, QSplashScreen, QMessageBox, QSlider, \
    QLabel, QAbstractItemView

print("Qt modules imported")
from seedpod_ground_risk.ui_resources.mainwindow import Ui_MainWindow
from seedpod_ground_risk.ui_resources.textdialog import Ui_TextAboutDialog

print("Layer modules imported")


class TextAboutDialog(QDialog):
    def __init__(self, title):
        super(TextAboutDialog, self).__init__()
        self.ui = Ui_TextAboutDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(title)


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        threadpool = QThreadPool.globalInstance()
        self.plot_worker = PlotWorker()
        self.plot_worker.signals.update_layers.connect(self.layers_update)
        self.plot_worker.signals.update_status.connect(self.status_update)
        self.plot_worker.signals.ready.connect(self.plot_ready)
        threadpool.start(self.plot_worker)
        print("Initialising Plot Server")
        self.plot_worker.signals.init.emit('Wikipedia', rasterise)

        self.listWidget.setEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.itemDropped.connect(self.layer_reorder)
        self.listWidget.itemDoubleClicked.connect(self.layer_edit)
        self.listWidget.rightClickAddOSMLayer.connect(self.layer_add_osm)

        self.timeSlider = QSlider(Qt.Horizontal)
        self.timeSlider.setObjectName(u"timeSlider")
        self.timeSlider.setGeometry(QRect(760, 0, 441, 22))
        self.timeSlider.setMaximum(167)
        self.timeSlider.setPageStep(3)
        self.timeSlider.setTickPosition(QSlider.TicksAbove)
        self.timeSlider.setTickInterval(12)
        self.toolBar.addWidget(self.timeSlider)
        self.timeSliderLabel = QLabel("Time of Week")
        self.timeSliderLabel.setObjectName(u"timeSliderLabel")
        self.timeSliderLabel.setGeometry(QRect(590, 0, 161, 20))
        self.toolBar.addWidget(self.timeSliderLabel)
        self.timeSlider.valueChanged.connect(self.time_changed)

        self.addOSMLayerButton.clicked.connect(self.layer_add_osm)
        # self.removeLayerButton.connect()

        self.actionRasterise.triggered.connect(self.menu_config_rasterise)
        self.actionImport.triggered.connect(self.menu_file_import)
        self.actionExport.triggered.connect(self.menu_file_export)
        self.actionAbout_Static_Sources.triggered.connect(self.menu_about_static_sources)
        self.actionAbout_App.triggered.connect(self.menu_about_app)
        self.actionGenerate.triggered.connect(self.plot_worker.signals.generate.emit)

    def menu_config_rasterise(self, checked):
        # TODO: Allow reliable on-the-fly rasterisation switching
        if not checked:
            msg_box = QMessageBox()
            msg_box.warning(self, "Warning", "Not rasterising increases generation and render times significantly!")

    def menu_file_import(self):
        from PySide2.QtWidgets import QFileDialog
        from PySide2.QtWidgets import QInputDialog

        filepath = QFileDialog.getOpenFileName(self, "Import GeoJSON geometry...", os.getcwd(),
                                               "GeoJSON Files (*.json)")
        if filepath[0]:
            buffer, ok = QInputDialog.getDouble(self, "Set Path Buffer", "Buffer in metres:", 0, 0, 1500, 1)
            if ok:
                self.plot_worker.signals.add_geojson_layer.emit(filepath[0], buffer)
            else:
                self.plot_worker.signals.add_geojson_layer.emit(filepath[0], 0)

    def menu_file_export(self):
        from PySide2.QtCore import QFile
        from PySide2.QtWidgets import QFileDialog

        file_dir = QFileDialog.getExistingDirectory(self, "Save plot image...", os.getcwd(), QFileDialog.ShowDirsOnly)
        if file_dir:
            file = QFile(os.path.join(file_dir, 'risk_plot.png'))
            self.webview.grab().save(file)

    def menu_about_static_sources(self):
        from PySide2.QtGui import QTextDocument
        self.dialog = TextAboutDialog('About Data')
        doc = QTextDocument()
        doc.setMarkdown(self._read_file('static_data/DATA_SOURCES.md'))
        self.dialog.ui.textEdit.setDocument(doc)
        self.dialog.show()

    def menu_about_app(self):
        from PySide2.QtGui import QTextDocument
        self.dialog = TextAboutDialog('About')
        doc = QTextDocument()
        doc.setMarkdown(self._read_file('README.md'))
        self.dialog.ui.textEdit.setDocument(doc)
        self.dialog.show()

    @Slot(str)
    def plot_ready(self, url):
        self.webview.load(url)
        self.webview.show()

    @Slot(str)
    def status_update(self, update_str: str):
        self.statusBar.showMessage(update_str)

    @Slot(list)
    def layers_update(self, layers):
        self.listWidget.clear()
        for layer in layers:
            item = QListWidgetItem(layer)
            item.setCheckState(Qt.CheckState.Checked)
            self.listWidget.addItem(item)

    def layer_add_osm(self):
        from PySide2.QtWidgets import QInputDialog
        import re

        kv_str, ok = QInputDialog.getText(self, "Set OSM key=value string", "Pair in key=value format")
        if ok:
            r = re.compile('(\w+=\w+)|(\w+)')
            if r.match(kv_str) is not None:
                self.plot_worker.signals.add_osm_layer.emit(kv_str, False)
            else:
                self.layer_add_osm()

    def layer_edit(self, item):
        print('Editing ', item)
        pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.plot_worker.signals.stop.emit()

    def layer_reorder(self):
        print('Layers reordered')
        self.plot_worker.signals.reorder_layers.emit(
            [self.listWidget.item(n).text() for n in range(self.listWidget.count())])

    def time_changed(self, value):
        try:
            labels = generate_week_timesteps()
        except NameError:
            from seedpod_ground_risk.layers.roads_layer import generate_week_timesteps
            labels = generate_week_timesteps()
        self.plot_worker.signals.set_time.emit(value)
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
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)
    pixmap = QPixmap('ui_resources/cascade_splash.png')
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint)
    splash.setEnabled(False)
    splash.setMask(pixmap.mask())
    splash.show()
    time.sleep(0.1)  # This seems to fix the splash mask displaying but not the actual image
    app.processEvents()

    msg_box = QMessageBox()
    msg_box.setDefaultButton(QMessageBox.Yes)
    button_clicked = msg_box.question(splash, "Use Rasterisation?",
                                      "Rasterising will reduce the resolution of the plot but generate significantly "
                                      "faster.",
                                      QMessageBox.Yes | QMessageBox.No,
                                      QMessageBox.Yes)
    app.processEvents()
    rasterise = (button_clicked == msg_box.Yes)

    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    splash.finish(window)
    sys.exit(app.exec_())
