import os
from pathlib import Path

from PySide2.QtCore import Property, Signal, Slot, Qt, QUrl, QRegExp
from PySide2.QtGui import QRegExpValidator
from PySide2.QtPositioning import QGeoCoordinate
from PySide2.QtQuickWidgets import QQuickWidget
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget, QLineEdit,
)


# TODO: Give the user feedback on where their coordinate is when clicked
class MapDialog(QDialog):
    def __init__(self, geo_widget):
        super().__init__(geo_widget)
        self.setWindowTitle("Map")
        self.map_widget = QQuickWidget(resizeMode=QQuickWidget.SizeRootObjectToView)
        self.map_widget.rootContext().setContextProperty("controller", geo_widget)
        filename = os.fspath(Path(__file__).resolve().parent / "coord_map.qml")
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


class PostDialog(QDialog):
    def __init__(self, geo_widget):
        super().__init__(geo_widget)
        self.setWindowTitle("Map")
        self.map_widget = QQuickWidget(resizeMode=QQuickWidget.SizeRootObjectToView)
        self.map_widget.rootContext().setContextProperty("controller", geo_widget)

        label = QLabel('Postcode')
        field = QLineEdit()
        field.setValidator(QRegExpValidator(QRegExp(
            '([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})')))

        button_box = QDialogButtonBox()
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        layout = QVBoxLayout
        label.setBuddy(field)
        self.registerField('Postcode' + '*', field)
        layout.addWidget(label)
        layout.addWidget(field)


class GeoWidget(QWidget):
    coordinate_changed = Signal(name="coordinateChanged")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._coordinate = QGeoCoordinate(0, 0)
        # The coordinate bounds below only bound England, they can be expanded if more countries are added
        self._lat_spinbox = QDoubleSpinBox(
            minimum=49.0, maximum=56.0
        )
        self._lng_spinbox = QDoubleSpinBox(
            minimum=-8, maximum=2
        )
        self.btn = QToolButton(text="Map", clicked=self.handle_clicked)
        self.map_view = MapDialog(self)

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
