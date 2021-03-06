import multiprocessing
import os
import sys
import time

import PySide2

from seedpod_ground_risk.core.plot_worker import PlotWorker
from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.ui_resources.add_layer_wizard import LayerWizard
from seedpod_ground_risk.ui_resources.layer_options import LAYER_OBJECTS
from seedpod_ground_risk.ui_resources.layerlistdelegate import Ui_delegate

print("Builtin modules imported")
from PySide2.QtCore import Qt, QRect, Slot, QThreadPool

print("QTCore imported")
from PySide2.QtGui import QPixmap, QCloseEvent, QPalette, QColor

print("QtGUI imported")
from PySide2.QtWidgets import QDialog, QMainWindow, QApplication, QListWidgetItem, QSplashScreen, QMessageBox, QSlider, \
    QLabel, QAbstractItemView, QWidget, QColorDialog, QMenu

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


class LayerItemDelegate(QWidget):
    def __init__(self, layer, plot_worker):
        super(LayerItemDelegate, self).__init__()
        self.ui = Ui_delegate()
        self.ui.setupUi(self)
        self._layer = layer
        self._plot_worker = plot_worker
        self.colour_set = False
        self.ui.pushButton.setAutoFillBackground(True)
        self.ui.pushButton.clicked.connect(self.change_colour)

    @property
    def key(self):
        return self.ui.nameLabel.text()

    def set_name(self, name: str):
        self.ui.nameLabel.setText(name)

    def set_data_tag(self, text: str):
        self.ui.dataTagLabel.setText(text)

    def set_colour(self, colour: str):
        self.colour_set = True
        pal = QPalette()
        pal.setColor(QPalette.Button, QColor(colour))
        self.ui.pushButton.setPalette(pal)

    def change_colour(self):
        if self.colour_set:
            dialog = QColorDialog()
            colour = dialog.getColor(Qt.white, self, )
            if colour.isValid():
                self.set_colour(colour)
                self._layer._colour = colour.name()

    def delete_layer(self):
        self._plot_worker.remove_layer(self._layer)

    def export_path_json(self):
        from PySide2.QtWidgets import QFileDialog

        file_dir = QFileDialog.getExistingDirectory(self, "Save plot .json file...", os.getcwd(),
                                                    QFileDialog.ShowDirsOnly)
        if file_dir:
            self._plot_worker.export_path_json(self._layer, file_dir)

    def mousePressEvent(self, event: PySide2.QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            menu = QMenu()
            menu.addAction("Delete", self.delete_layer)
            if isinstance(self._layer, AnnotationLayer):
                menu.addAction("Export .GeoJSON", self.export_path_json)
            menu.exec_(event.globalPos())


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
        self.plot_worker.signals.init.emit('Wikipedia')

        self.listWidget.setEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.itemDropped.connect(self.layer_reorder)

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

        self.addLayerButton.clicked.connect(self.layer_add)

        self.actionRasterise.triggered.connect(self.menu_config_rasterise)
        # self.actionImport.triggered.connect(self.menu_file_import)
        self.actionExport.triggered.connect(self.menu_file_export)
        self.actionAbout_Static_Sources.triggered.connect(self.menu_about_static_sources)
        self.actionAbout_App.triggered.connect(self.menu_about_app)
        self.actionGenerate.triggered.connect(self.plot_worker.signals.generate.emit)

    def menu_config_rasterise(self, checked):
        # TODO: Allow reliable on-the-fly rasterisation switching
        if not checked:
            msg_box = QMessageBox()
            msg_box.warning(self, "Warning", "Not rasterising increases generation and render times significantly!")

    # def menu_file_import(self):
    #     from PySide2.QtWidgets import QFileDialog
    #     from PySide2.QtWidgets import QInputDialog
    #
    #     filepath = QFileDialog.getOpenFileName(self, "Import GeoJSON geometry...", os.getcwd(),
    #                                            "GeoJSON Files (*.json)")
    #     if filepath[0]:
    #

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
            item = QListWidgetItem(self.listWidget)
            self.listWidget.addItem(item)
            delegate = LayerItemDelegate(layer, self.plot_worker)
            item.setSizeHint(delegate.size())
            delegate.set_name(layer.key)
            if hasattr(layer, '_colour'):
                delegate.set_colour(layer._colour)
            if hasattr(layer, '_osm_tag'):
                delegate.set_data_tag(layer._osm_tag)
            self.listWidget.setItemWidget(item, delegate)

    def layer_add(self):
        wizard = LayerWizard(self, Qt.Window)
        wizard.exec_()  # Open wizard and block until result
        if wizard.result() == QDialog.Accepted:
            layerObj = list(LAYER_OBJECTS.values())[wizard.layerType]
            layer = layerObj(wizard.layerKey, **wizard.opts)
            self.plot_worker.add_layer(layer)

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

    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    splash.finish(window)
    sys.exit(app.exec_())
