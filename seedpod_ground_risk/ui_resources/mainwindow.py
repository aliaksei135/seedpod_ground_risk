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
from PySide2.QtWidgets import *

from PySide2.QtWebEngineWidgets import QWebEngineView
from .maplayerslistwidget import MapLayersListWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1646, 1109)
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
        self.actionGenerate = QAction(MainWindow)
        self.actionGenerate.setObjectName(u"actionGenerate")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QSize(1216, 757))
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setMinimumSize(QSize(1221, 771))
        self.splitter.setOrientation(Qt.Horizontal)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.listWidget = MapLayersListWidget(self.verticalLayoutWidget)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setEnabled(False)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setMinimumSize(QSize(405, 490))

        self.verticalLayout.addWidget(self.listWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 5, -1, 5)
        self.addLayerButton = QPushButton(self.verticalLayoutWidget)
        self.addLayerButton.setObjectName(u"addLayerButton")

        self.horizontalLayout.addWidget(self.addLayerButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.splitter.addWidget(self.verticalLayoutWidget)
        self.webview = QWebEngineView(self.splitter)
        self.webview.setObjectName(u"webview")
        sizePolicy.setHeightForWidth(self.webview.sizePolicy().hasHeightForWidth())
        self.webview.setSizePolicy(sizePolicy)
        self.webview.setMinimumSize(QSize(800, 781))
        self.splitter.addWidget(self.webview)

        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.toolBar.addAction(self.actionAbout_App)
        self.toolBar.addAction(self.actionAbout_Static_Sources)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionExport)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionGenerate)
        self.toolBar.addSeparator()

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
        self.addLayerButton.setText(QCoreApplication.translate("MainWindow", u"Add Layer", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

