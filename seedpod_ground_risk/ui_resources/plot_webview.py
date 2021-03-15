import PySide2
from PySide2.QtCore import Signal
from PySide2.QtWebEngineWidgets import QWebEngineView


class PlotWebview(QWebEngineView):
    resize = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super(PlotWebview, self).__init__(*args, **kwargs)

    def resizeEvent(self, event: PySide2.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        webview_size = self.size()
        self.resize.emit(webview_size.width() - 50, webview_size.height() - 30)
