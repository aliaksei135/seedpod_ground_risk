# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layerListDelegate.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_delegate(object):
    def setupUi(self, delegate):
        if not delegate.objectName():
            delegate.setObjectName(u"delegate")
        delegate.resize(410, 50)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(delegate.sizePolicy().hasHeightForWidth())
        delegate.setSizePolicy(sizePolicy)
        delegate.setMinimumSize(QSize(200, 40))
        delegate.setMaximumSize(QSize(410, 50))
        delegate.setBaseSize(QSize(200, 40))
        self.horizontalLayoutWidget = QWidget(delegate)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 0, 411, 51))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.nameLabel = QLabel(self.horizontalLayoutWidget)
        self.nameLabel.setObjectName(u"nameLabel")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.nameLabel.sizePolicy().hasHeightForWidth())
        self.nameLabel.setSizePolicy(sizePolicy1)
        self.nameLabel.setMinimumSize(QSize(199, 22))
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.nameLabel.setFont(font)

        self.verticalLayout.addWidget(self.nameLabel)

        self.dataTagLabel = QLabel(self.horizontalLayoutWidget)
        self.dataTagLabel.setObjectName(u"dataTagLabel")
        sizePolicy1.setHeightForWidth(self.dataTagLabel.sizePolicy().hasHeightForWidth())
        self.dataTagLabel.setSizePolicy(sizePolicy1)
        self.dataTagLabel.setMinimumSize(QSize(199, 19))

        self.verticalLayout.addWidget(self.dataTagLabel)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.horizontalSpacer = QSpacerItem(178, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton = QPushButton(self.horizontalLayoutWidget)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy2)
        self.pushButton.setMinimumSize(QSize(25, 49))
        self.pushButton.setAutoFillBackground(True)
        self.pushButton.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButton)

        self.retranslateUi(delegate)

        QMetaObject.connectSlotsByName(delegate)

    # setupUi

    def retranslateUi(self, delegate):
        delegate.setWindowTitle(QCoreApplication.translate("delegate", u"Form", None))
        self.nameLabel.setText(QCoreApplication.translate("delegate", u"Key", None))
        self.dataTagLabel.setText(QCoreApplication.translate("delegate", u"data tag", None))
        self.pushButton.setText("")
    # retranslateUi
