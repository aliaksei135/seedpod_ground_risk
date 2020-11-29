# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui',
# licensing of 'main.ui' applies.
#
# Created: Sun Nov 29 21:31:36 2020
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 800)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                           QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(1200, 800))
        MainWindow.setBaseSize(QtCore.QSize(1200, 800))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setGeometry(QtCore.QRect(0, 0, 1200, 775))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.listWidget = MapLayersListWidget(self.splitter)
        self.listWidget.setEnabled(False)
        self.listWidget.setObjectName("listWidget")
        self.webview = QWebEngineView(self.splitter)
        self.webview.setMinimumSize(QtCore.QSize(500, 0))
        self.webview.setObjectName("webview")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1200, 32))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuImport_Export = QtWidgets.QMenu(self.menubar)
        self.menuImport_Export.setObjectName("menuImport_Export")
        self.menuAbout = QtWidgets.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionImport = QtWidgets.QAction(MainWindow)
        self.actionImport.setObjectName("actionImport")
        self.actionExport = QtWidgets.QAction(MainWindow)
        self.actionExport.setObjectName("actionExport")
        self.actionAbout_Static_Sources = QtWidgets.QAction(MainWindow)
        self.actionAbout_Static_Sources.setObjectName("actionAbout_Static_Sources")
        self.actionAbout_App = QtWidgets.QAction(MainWindow)
        self.actionAbout_App.setObjectName("actionAbout_App")
        self.actionConfiguration = QtWidgets.QAction(MainWindow)
        self.actionConfiguration.setObjectName("actionConfiguration")
        self.menuFile.addAction(self.actionConfiguration)
        self.menuImport_Export.addAction(self.actionImport)
        self.menuImport_Export.addAction(self.actionExport)
        self.menuAbout.addAction(self.actionAbout_Static_Sources)
        self.menuAbout.addAction(self.actionAbout_App)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuImport_Export.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "SEEDPOD Ground Risk", None, -1))
        self.menuFile.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuImport_Export.setTitle(QtWidgets.QApplication.translate("MainWindow", "Data", None, -1))
        self.menuAbout.setTitle(QtWidgets.QApplication.translate("MainWindow", "About", None, -1))
        self.actionImport.setText(QtWidgets.QApplication.translate("MainWindow", "Import", None, -1))
        self.actionExport.setText(QtWidgets.QApplication.translate("MainWindow", "Export", None, -1))
        self.actionAbout_Static_Sources.setText(
            QtWidgets.QApplication.translate("MainWindow", "About Static Data", None, -1))
        self.actionAbout_App.setText(QtWidgets.QApplication.translate("MainWindow", "About App", None, -1))
        self.actionConfiguration.setText(QtWidgets.QApplication.translate("MainWindow", "Configuration", None, -1))

from PySide2.QtWebEngineWidgets import QWebEngineView
from .maplayerslistwidget import MapLayersListWidget
