import typing

import PySide2
from PySide2.QtCore import QRegExp
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QWizard, QWizardPage, QLabel, QLineEdit, QComboBox, QCheckBox, QGridLayout

from seedpod_ground_risk.ui_resources.layer_options import LAYER_OPTIONS


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
                field = QLineEdit()
                # field.setDisabled(True)
                # filepath = QFileDialog.getOpenFileName(self, "Import GeoJSON geometry...", os.getcwd(),
                #                                        "GeoJSON Files (*.json)")
                # if filepath[0]:
                #     field.setText(filepath[0])
            elif regex == 'colour':
                field = QLineEdit()
                # field.setDisabled(True)
                # dialog = QColorDialog()
                # colour = dialog.getColor(Qt.white, self,)
                # if colour.isValid():
                #     field.setText(colour.getRgb())
            elif regex is bool:
                field = QCheckBox()
            else:
                field = QLineEdit()
                field.setValidator(QRegExpValidator(QRegExp(regex)))
            label.setBuddy(field)
            self.registerField(name, field)
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
        self.opts = {opt[1]: opt[2](self.field(name)) for name, opt in
                     list(LAYER_OPTIONS.values())[self.layerType].items()}
