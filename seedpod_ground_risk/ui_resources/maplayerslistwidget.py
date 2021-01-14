from PySide2.QtCore import Signal
from PySide2.QtWidgets import QListWidget


class MapLayersListWidget(QListWidget):
    itemDropped = Signal()
    rightClickAddOSMLayer = Signal()

    def __init__(self, *args, **kwargs):
        super(MapLayersListWidget, self).__init__(*args, **kwargs)

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        event.acceptProposedAction()

    def dropEvent(self, event):
        super().dropEvent(event)
        event.acceptProposedAction()
        self.itemDropped.emit()
