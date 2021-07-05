import os
import typing

import PySide2
from PySide2.QtCore import QRegExp, Qt
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QWizard, QWizardPage, QLabel, QLineEdit, QComboBox, QCheckBox, QGridLayout, QColorDialog, \
    QPushButton, QFileDialog

from seedpod_ground_risk.ui_resources.coordbox import GeoWidget
from seedpod_ground_risk.ui_resources.layer_options import *


class BasicLayerInfoPage(QWizardPage):

    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent)
        self.setTitle('Basic Layer Info')
        layout = QGridLayout()

        nameLabel = QLabel('Name')
        nameEdit = QLineEdit()
        nameEdit.setValidator(QRegExpValidator(QRegExp('.{0,255}'), self))
        nameLabel.setBuddy(nameEdit)
        layout.addWidget(nameLabel)
        layout.addWidget(nameEdit)
        self.registerField('name*', nameEdit)

        typeLabel = QLabel('Type')
        typeSpinner = QComboBox(self)
        typeSpinner.addItems(LAYER_OPTIONS.keys())
        typeLabel.setBuddy(typeSpinner)
        layout.addWidget(typeLabel)
        layout.addWidget(typeSpinner)
        self.registerField('type*', typeSpinner)

        self.setLayout(layout)


class SpecificLayerInfoPage(QWizardPage):

    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent)
        self.setTitle('Layer Options')

    def initializePage(self) -> None:
        super().initializePage()
        layout = QGridLayout()
        layerType = self.field('type')
        for name, opt in list(LAYER_OPTIONS.values())[layerType].items():
            regex = opt[0]
            label = QLabel(name)
            if regex == 'path':
                path_field = QLineEdit()
                path_field.setReadOnly(True)

                def set_path(event):
                    filepath = QFileDialog.getOpenFileName(self, "Import GeoJSON geometry...", os.getcwd(),
                                                           "GeoJSON Files (*.json)")
                    if filepath[0]:
                        path_field.setText(filepath[0])

                button = QPushButton()
                button.setText('Browse')
                button.clicked.connect(set_path)

                label.setBuddy(path_field)
                self.registerField(name + '*', path_field)
                layout.addWidget(label)
                layout.addWidget(path_field)
                layout.addWidget(button)
                continue
            elif regex == 'colour':
                colour_field = QLineEdit()
                colour_field.setReadOnly(True)

                def set_colour(event):
                    dialog = QColorDialog()
                    colour = dialog.getColor(Qt.white, self, )
                    if colour.isValid():
                        colour_field.setText(colour.name())

                button = QPushButton()
                button.setText('Pick')
                button.clicked.connect(set_colour)

                label.setBuddy(colour_field)
                self.registerField(name + '*', colour_field)
                layout.addWidget(label)
                layout.addWidget(colour_field)
                layout.addWidget(button)
                continue
            elif regex == 'algos':
                label = QLabel(name)
                field = QComboBox(self)
                field.addItems(ALGORITHM_OBJECTS.keys())
                # algoLabel.setBuddy(algoSpinner)
                # layout.addWidget(algoLabel)
                # layout.addWidget(algoSpinner)
                # self.registerField('algo*', algoSpinner)
            elif regex is bool:
                field = QCheckBox()
            # TODO: Make the Start and End coordinate field mandatory. Currently the wizard is unable to be used if they are mandatory
            elif regex == 'coordinate':
                field = GeoWidget()
                self.registerField(name, field, "coordinate", "coordinate_changed")
                label.setBuddy(field)
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
                layout.addWidget(field)
                continue
            else:
                field = QLineEdit()
                field.setValidator(QRegExpValidator(QRegExp(regex)))
            label.setBuddy(field)
            self.registerField(name + '*', field)
            layout.addWidget(label)
            layout.addWidget(field)
        self.setLayout(layout)


class LayerWizard(QWizard):
    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...,
                 flags: PySide2.QtCore.Qt.WindowFlags = ...) -> None:
        super().__init__(parent, flags)

        self.addPage(BasicLayerInfoPage(self))
        self.addPage(SpecificLayerInfoPage(self))

        self.setWindowTitle('Add Layer')

        # TODO: Going back in wizard does not clear page fields.
        # Hook into back button click and remove and re add page.

    def accept(self) -> None:
        super().accept()

        self.layerKey = self.field('name')
        self.layerType = self.field('type')
        self.opts = {}
        for name, opt in list(LAYER_OPTIONS.values())[self.layerType].items():
            if opt[1] == 'algo':
                d = {opt[1]: list(ALGORITHM_OBJECTS.values())[self.field(name)]}
            elif opt[1] == 'coordinate':
                d = {opt[1]: (self.field(name).latitude(), self.field(name).longitude())}
            else:
                d = {opt[1]: opt[2](self.field(name))}
            self.opts.update(d)
