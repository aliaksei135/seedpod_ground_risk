from PySide2.QtCore import Signal
from PySide2.QtWebEngineWidgets import QWebEngineView


class PlotWebview(QWebEngineView):
    resize = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super(PlotWebview, self).__init__(*args, **kwargs)

    def resize_event(self, event):
        super().resize_event(event)
        webview_size = self.size()
        self.resize.emit(webview_size.width(), webview_size.height())
