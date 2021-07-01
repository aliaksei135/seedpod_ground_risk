import os
import sys
from pathlib import Path

from PySide2.QtCore import Property, Signal, Slot, Qt, QUrl
from PySide2.QtPositioning import QGeoCoordinate
from PySide2.QtQuickWidgets import QQuickWidget
from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

CURRENT_DIRECTORY = Path(__file__).resolve().parent


# TODO: Give the user feedback on where their coordinate is when clicked
class MapDialog(QDialog):
    def __init__(self, geo_widget):
        super().__init__(geo_widget)
        self.setWindowTitle("Map")
        self.map_widget = QQuickWidget(resizeMode=QQuickWidget.SizeRootObjectToView)
        self.map_widget.rootContext().setContextProperty("controller", geo_widget)
        filename = os.fspath(CURRENT_DIRECTORY / "coord_map.qml")
        url = QUrl.fromLocalFile(filename)
        self.map_widget.setSource(url)

        button_box = QDialogButtonBox()
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        lay = QVBoxLayout(self)
        lay.addWidget(self.map_widget)
        lay.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)


class GeoWidget(QWidget):
    coordinate_changed = Signal(name="coordinateChanged")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._coordinate = QGeoCoordinate(0, 0)

        self._lat_spinbox = QDoubleSpinBox(
            minimum=49.0, maximum=56.0  # , valueChanged=self.handle_value_changed,
        )
        self._lng_spinbox = QDoubleSpinBox(
            minimum=-8, maximum=2  # , valueChanged=self.handle_value_changed,
        )
        self.btn = QToolButton(text="Map", clicked=self.handle_clicked)
        self.map_view = MapDialog(self)

        # self.coordinate_changed.connect(self.handle_value_changed)
        # self.coordinate_changed.connect(self.handle_value_changed)
        lay = QHBoxLayout(self)
        lay.addWidget(QLabel("Latitude:"))
        lay.addWidget(self._lat_spinbox)
        lay.addWidget(QLabel("Longitude:"))
        lay.addWidget(self._lng_spinbox)
        lay.addWidget(self.btn)

    @Property(QGeoCoordinate, notify=coordinate_changed)
    def coordinate(self):
        return self._coordinate

    @coordinate.setter
    def coordinate(self, coordinate):
        if self.coordinate == coordinate:
            return
        self._coordinate = coordinate
        self.coordinate_changed.emit()

    def handle_value_changed(self):
        coordinate = QGeoCoordinate(
            self._lat_spinbox.value(), self._lng_spinbox.value()
        )
        self.coordinate = coordinate

    @Slot(QGeoCoordinate)
    def update_from_map(self, coordinate):
        self.coordinate = coordinate
        self._lat_spinbox.setValue(self.coordinate.latitude())
        self._lng_spinbox.setValue(self.coordinate.longitude())

    def handle_clicked(self):
        self.map_view.exec_()


# Rest of code is used to debug this coordinate box

class WizardPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.geo_widget1 = GeoWidget()
        self.geo_widget2 = GeoWidget()

        self.registerField("coordinate1", self.geo_widget1)
        self.registerField("coordinate2", self.geo_widget2)

        lay = QVBoxLayout(self)
        lay.addWidget(self.geo_widget1)
        lay.addWidget(self.geo_widget2)


def main():
    app = QApplication(sys.argv)

    w = QWizard()
    page = WizardPage()
    w.addPage(page)
    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
