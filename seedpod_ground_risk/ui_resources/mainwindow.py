# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtWidgets import *

from .maplayerslistwidget import MapLayersListWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1216, 818)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(1200, 800))
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
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setGeometry(QRect(0, 20, 1211, 761))
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setMinimumSize(QSize(1211, 761))
        self.splitter.setMaximumSize(QSize(0, 0))
        self.splitter.setOrientation(Qt.Horizontal)
        self.listWidget = MapLayersListWidget(self.splitter)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setEnabled(False)
        self.splitter.addWidget(self.listWidget)
        self.webview = QWebEngineView(self.splitter)
        self.webview.setObjectName(u"webview")
        self.webview.setMinimumSize(QSize(500, 0))
        self.splitter.addWidget(self.webview)
        self.timeSlider = QSlider(self.centralwidget)
        self.timeSlider.setObjectName(u"timeSlider")
        self.timeSlider.setGeometry(QRect(760, 0, 441, 22))
        self.timeSlider.setMaximum(167)
        self.timeSlider.setPageStep(3)
        self.timeSlider.setOrientation(Qt.Horizontal)
        self.timeSlider.setTickPosition(QSlider.TicksAbove)
        self.timeSlider.setTickInterval(12)
        self.timeSliderLabel = QLabel(self.centralwidget)
        self.timeSliderLabel.setObjectName(u"timeSliderLabel")
        self.timeSliderLabel.setGeometry(QRect(590, 0, 161, 20))
        font = QFont()
        font.setPointSize(11)
        self.timeSliderLabel.setFont(font)
        self.timeSliderLabel.setAlignment(Qt.AlignCenter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1216, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuImport_Export = QMenu(self.menubar)
        self.menuImport_Export.setObjectName(u"menuImport_Export")
        self.menuAbout = QMenu(self.menubar)
        self.menuAbout.setObjectName(u"menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuImport_Export.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())
        self.menuFile.addAction(self.actionRasterise)
        self.menuImport_Export.addAction(self.actionImport)
        self.menuImport_Export.addAction(self.actionExport)
        self.menuAbout.addAction(self.actionAbout_Static_Sources)
        self.menuAbout.addAction(self.actionAbout_App)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"SEEDPOD Ground Risk", None))
        self.actionImport.setText(QCoreApplication.translate("MainWindow", u"Import", None))
        self.actionExport.setText(QCoreApplication.translate("MainWindow", u"Export", None))
        self.actionAbout_Static_Sources.setText(QCoreApplication.translate("MainWindow", u"About Static Data", None))
        self.actionAbout_App.setText(QCoreApplication.translate("MainWindow", u"About App", None))
        self.actionRasterise.setText(QCoreApplication.translate("MainWindow", u"Rasterise", None))
        self.timeSliderLabel.setText(QCoreApplication.translate("MainWindow", u"Time of Week", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"Config", None))
        self.menuImport_Export.setTitle(QCoreApplication.translate("MainWindow", u"Data", None))
        self.menuAbout.setTitle(QCoreApplication.translate("MainWindow", u"About", None))
    # retranslateUi

