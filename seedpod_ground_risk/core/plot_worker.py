from PySide2.QtCore import QObject, Signal, QRunnable, Slot


class PlotWorkerSignals(QObject):
    init = Signal(str)
    ready = Signal(str)
    stop = Signal()

    set_time = Signal(int)
    generate = Signal()
    update_status = Signal(str)
    update_layers = Signal(list)
    reorder_layers = Signal(list)
    add_geojson_layer = Signal(str, float)
    add_osm_layer = Signal(str, bool)


class PlotWorker(QRunnable):

    def __init__(self, *args, **kwargs):
        super(PlotWorker, self).__init__()

        self.signals = PlotWorkerSignals()
        self.signals.init.connect(self.init)
        self.signals.stop.connect(self.stop)
        self.signals.generate.connect(self.generate)
        self.signals.set_time.connect(self.set_time)
        self.signals.reorder_layers.connect(self.layers_reorder)
        self.signals.add_geojson_layer.connect(self.add_geojson_layer)
        self.signals.add_osm_layer.connect(self.add_osm_layer)

        self.plot_server = None
        self.stop = False

    @Slot()
    def run(self) -> None:
        import time
        while True:
            if self.stop:
                return
            time.sleep(0.1)

    @Slot(str, bool)
    def init(self, tiles='Wikipedia'):
        from seedpod_ground_risk.core.plot_server import PlotServer

        self.plot_server = PlotServer(tiles=tiles,
                                      progress_callback=self.status_update,
                                      update_callback=self.layers_update)
        self.plot_server.start()
        self.signals.ready.emit(self.plot_server.url)

    @Slot()
    def stop(self):
        self.stop = True

    @Slot()
    def generate(self):
        self.plot_server.generate_map()
        self.status_update("Update queued, move map to trigger")

    @Slot(str, float)
    def add_geojson_layer(self, path, buffer):
        if buffer and buffer > 10:
            self.plot_server.add_geojson_layer(path, buffer=buffer)
        else:
            self.plot_server.add_geojson_layer(path)

    @Slot(str, bool)
    def add_osm_layer(self, kv, blocking):
        self.plot_server.add_osm_layer(kv, blocking)

    @Slot(int)
    def set_time(self, hour):
        self.plot_server.set_time(hour)

    @Slot(list)
    def layers_reorder(self, layer_order):
        self.plot_server.set_layer_order(layer_order)

    def layers_update(self, layers):
        self.signals.update_layers.emit(layers)

    def status_update(self, status):
        self.signals.update_status.emit(status)
