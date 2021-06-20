import typing

import PySide2
from PySide2.QtCore import QRegExp
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QWizard, QWizardPage, QLabel, QLineEdit, QGridLayout

from seedpod_ground_risk.ui_resources.layer_options import *


class NewAircraftInfoPage(QWizardPage):

    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent)
        self.setTitle('New Aircraft Configuration')

    def initializePage(self) -> None:
        super().initializePage()
        layout = QGridLayout()
        aircraftType = self.field('type')
        for name, opt in list(AIRCRAFT_PARAMETERS.values())[aircraftType].items():
            regex = opt[0]
            label = QLabel(name)
            field = QLineEdit()
            field.setValidator(QRegExpValidator(QRegExp(regex)))
            label.setBuddy(field)
            self.registerField(name + '*', field)
            layout.addWidget(label)
            layout.addWidget(field)
        self.setLayout(layout)


class AircraftWizard(QWizard):
    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...,
                 flags: PySide2.QtCore.Qt.WindowFlags = ...) -> None:
        super().__init__(parent, flags)

        self.addPage(NewAircraftInfoPage(self))

        self.setWindowTitle('Add Layer')

        # TODO: Going back in wizard does not clear page fields.
        # Hook into back button click and remove and re add page.

    def accept(self) -> None:
        super().accept()
        self.aircraftKey = self.field('name')
        self.aircraftType = self.field('type')
        self.opts = {}
        for name, opt in list(AIRCRAFT_PARAMETERS.values())[self.aircraftType].items():
            d = {opt[1]: opt[2](self.field(name))}
        add_aircraft(d)
