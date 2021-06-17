# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'coord_picker.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from .plot_webview import PlotWebview


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 840)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(1200, 836))
        MainWindow.setBaseSize(QSize(1200, 800))
        self.actionImport = QAction(MainWindow)
        self.actionImport.setObjectName(u"actionImport")
        self.actionExport = QAction(MainWindow)
        self.actionExport.setObjectName(u"actionExport")
        self.actionAbout_Static_Sources = QAction(MainWindow)
        self.actionAbout_Static_Sources.setObjectName(u"actionAbout_Static_Sources")
        self.actionAbout_App = QAction(MainWindow)
        self.actionAbout_App.setObjectName(u"actionAbout_App")
        self.actionRasterise = QAction(MainWindow)
        self.actionRasterise.setObjectName(u"actionRasterise")
        self.actionRasterise.setCheckable(True)
        self.actionGenerate = QAction(MainWindow)
        self.actionGenerate.setObjectName(u"actionGenerate")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QSize(1200, 757))
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setSizeConstraint(QLayout.SetMinimumSize)
        self.plotWebview = PlotWebview(self.centralwidget)
        self.plotWebview.setObjectName(u"plotWebview")
        sizePolicy.setHeightForWidth(self.plotWebview.sizePolicy().hasHeightForWidth())
        self.plotWebview.setSizePolicy(sizePolicy)
        self.plotWebview.setMinimumSize(QSize(800, 781))

        self.horizontalLayout_4.addWidget(self.plotWebview)


        self.gridLayout.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"SEEDPOD Ground Risk", None))
        self.actionImport.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.actionExport.setText(QCoreApplication.translate("MainWindow", u"Export .png", None))
        self.actionAbout_Static_Sources.setText(QCoreApplication.translate("MainWindow", u"About Static Data", None))
        self.actionAbout_App.setText(QCoreApplication.translate("MainWindow", u"About App", None))
        self.actionRasterise.setText(QCoreApplication.translate("MainWindow", u"Rasterise", None))
        self.actionGenerate.setText(QCoreApplication.translate("MainWindow", u"Generate", None))
#if QT_CONFIG(tooltip)
        self.actionGenerate.setToolTip(QCoreApplication.translate("MainWindow", u"Generate Map for current view", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

