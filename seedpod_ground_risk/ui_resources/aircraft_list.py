import typing

import PySide2
from PySide2.QtCore import QRegExp
from PySide2.QtWidgets import QWizard, QWizardPage, QLabel, QGridLayout, QComboBox

from seedpod_ground_risk.ui_resources.aircraft_options import AIRCRAFT_LIST
from seedpod_ground_risk.ui_resources.layer_options import *


class ListAircraftPage(QWizardPage):

    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent)
        self.setTitle('Show Aircraft Data')

    def initializePage(self) -> None:
        super().initializePage()
        layout = QGridLayout()

        label = QLabel('Choose Aircraft')
        field = QComboBox(self)
        field.addItems(dummy_aircraft_variable.keys())
        field.addItems(AIRCRAFT_LIST.keys())
        label.setBuddy(field)
        self.registerField('Choose Aircraft' + '*', field)
        layout.addWidget(label)
        layout.addWidget(field)

        self.setLayout(layout)


class ListAircraftWizard(QWizard):
    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...,
                 flags: PySide2.QtCore.Qt.WindowFlags = ...) -> None:
        super().__init__(parent, flags)

        self.addPage(ListAircraftPage(self))

        self.setWindowTitle('Show Aircraft')

        # TODO: Going back in wizard does not clear page fields.
        # Hook into back button click and remove and re add page.

    def accept(self) -> None:
        super().accept()

        self.d = list(AIRCRAFT_LIST.values())[self.field("Choose Aircraft") - 1]

        return self.d
