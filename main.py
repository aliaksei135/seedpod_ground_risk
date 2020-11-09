import os
import sys

import folium as fl
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.geometry as sg
from PySide2 import QtCore
from PySide2.QtCore import QRunnable, Slot, Signal, QObject, QUrl
from PySide2.QtWebEngineWidgets import QWebEngineSettings
from PySide2.QtWidgets import *
from folium.plugins import HeatMap

from plot_server import PlotServer
from ui_resources.mainwindow import Ui_MainWindow

gpd.options.use_pygeos = True
from matplotlib import cm
from matplotlib.colors import to_hex

import shapely.speedups

shapely.speedups.enable()

import requests


class Signaller(QObject):
    update_map = Signal(list)
    update_status = Signal(float, str)


class MainWindow(QMainWindow, Ui_MainWindow):
    map_callback_js = '''function onMapMove() {{ 
        backend.on_map_move(map_{0}.getCenter().lat,  map_{0}.getCenter().lng);
        alert("Move"); 
    }}; 
    map_{0}.on('move', onMapMove);
    onMapMove();'''

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.webview.page().settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        # self.map_temp_dir = tempfile.TemporaryDirectory()
        #
        # self.map = fl.Map(location=[51.1, -1.9], prefer_canvas=True)
        # self.map_layers = []
        # abspath_qwc_js = os.path.abspath('ui_resources' + os.sep + 'qwebchannel.js')
        # self.map.get_root().header.add_child(JavascriptLink(abspath_qwc_js))
        # abspath_mc_js = os.path.abspath('ui_resources' + os.sep + 'map_callback.js')
        # self.map.get_root().header.add_child(JavascriptLink(abspath_mc_js))
        # self.map.get_root().script.add_child(Element('var the_map = map_' + self.map._id + ';'))
        #
        # self.map.save(os.path.abspath(self.map_temp_dir.name + os.sep + 'map.html'))
        # self.webview.load(QUrl.fromLocalFile(os.path.abspath(self.map_temp_dir.name + os.sep + 'map.html')))
        # # self.webview.page().runJavaScript('$(document).ready( function() {$("script").append(' + self.map_callback_js.format(self.map._id) + ');});')
        #
        # channel = QWebChannel(self.webview.page())
        # self.webview.page().setWebChannel(channel)
        # channel.registerObject("backend", self)
        plot_server = PlotServer()
        plot_server.start()

        self.webview.load(plot_server.url)
        self.webview.show()

        # self.threadpool = QThreadPool()
        # self.create_map()

    def create_map(self):
        mapgen = MapWorker()
        mapgen.signals.update_map.connect(self.update_map)
        mapgen.signals.update_status.connect(self.update_status)
        self.threadpool.start(mapgen)

    @Slot(float, float)
    def on_map_move(self, lat, lng):
        print(lat, ' ', lng)
        pass

    @Slot(list)
    def update_map(self, map_objects):
        self.map_layers += map_objects
        for obj in map_objects:
            obj.add_to(self.map)

        # Workaround to https://bugreports.qt.io/browse/QTBUG-53414?page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel&showAll=true
        # Chromium refuses to load over 2MB from webview#setHtml
        # We load order(s) of magnitude more than that
        self.map.save(os.path.abspath(self.map_temp_dir.name + os.sep + 'map.html'))
        self.webview.load(QUrl.fromLocalFile(os.path.abspath(self.map_temp_dir.name + os.sep + 'map.html')))
        self.webview.show()
        self.update_status(1.0, 'Done')

    @Slot(float, str)
    def update_status(self, progress, text):
        self.statusBar.showMessage(text)


class MapWorker(QRunnable):

    def __init__(self, bounds=None):
        super().__init__()
        self.signals = Signaller()
        self.bounds = bounds

    def run(self):
        self.signals.update_status.emit(0.1, "Fetching OSM data")
        overpass_url = "http://overpass-api.de/api/interpreter"
        landuse = 'residential'
        query = """
                        [out:json]
                        [timeout:120]
                        [bbox:50.77, -2.0, 51.18, -0.9];
                        (

                          //Residential
                            node[landuse={landuse}];
                            way[landuse={landuse}];
                            rel[landuse={landuse}];

                        );

                        out center body;
                        >;
                        out center qt;
                    """.format(landuse=landuse)
        resp = requests.get(overpass_url, params={'data': query})
        data = resp.json()
        ways = [o for o in data['elements'] if o['type'] == 'way']
        nodes = {o['id']: (o['lon'], o['lat']) for o in data['elements'] if o['type'] == 'node'}

        df_list = []
        for element in ways:
            locs = [nodes[id] for id in element['nodes']]
            if len(locs) < 3:
                continue
            poly = sg.Polygon(locs)
            df_list.append([poly])

        self.signals.update_status.emit(0.15, 'Importing Census ward boundaries')
        raw_ways_df = gpd.GeoDataFrame(df_list, columns=['geometry']).set_crs('EPSG:4326')
        wards_df = gpd.read_file('static_data/england_wa_2011_clipped.shp').drop(['altname', 'oldcode'],
                                                                                 axis=1).set_crs(
            'EPSG:27700').to_crs('EPSG:4326')
        ways_df = gpd.overlay(raw_ways_df, wards_df, how='intersection').to_crs('EPSG:4326').cx[-2.15:-0.4, 50.77:51.28]

        density_df = pd.read_csv('static_data/density.csv', header=0)
        density_df['area'] = density_df['area'] * 10000
        density_df['density'] = density_df['density'] / 10000
        census_df = ways_df.merge(density_df, on='code')

        self.signals.update_status.emit(0.3, 'Estimating polygon population densities')
        matched_ways = []
        for idx, r in ways_df.iterrows():
            # Assume only single ward matches way
            try:
                contained_ward = census_df.loc[census_df.contains(r['geometry'])].iloc[0]
                matched_ways.append(
                    [contained_ward['name'], contained_ward['code'], contained_ward['density'], r['geometry']])
            except:
                continue

        def scale_pop(x):
            if x > 0 and x < 7000:
                return (-0.0000001 * (x ** 2) + 6) * x
            else:
                return x

        # TODO: Reproj to equal area proj to calc areas
        census_df['population'] = census_df['density'] * census_df['geometry'].area
        # Scale to reduce error for smaller less dense wards
        census_df['population'] = census_df['population'].apply(scale_pop)

        reproj_df = census_df.to_crs('EPSG:4326')
        xmin, ymin, xmax, ymax = reproj_df.total_bounds
        max_poly_size = 0.0005
        num_cols = int((xmax - xmin) / max_poly_size)
        num_rows = int((ymax - ymin) / max_poly_size)
        cols = np.linspace(xmin, xmax, num_cols).tolist()
        rows = np.linspace(ymin, ymax, num_rows).tolist()
        rows.reverse()

        self.signals.update_status.emit(0.7, 'Generating heatmap raster grid')
        grid_polys = []
        for x in cols:
            for y in rows:
                grid_polys.append(sg.Polygon(
                    [(x, y), (x + max_poly_size, y), (x + max_poly_size, y - max_poly_size), (x, y - max_poly_size)]))

        grid = gpd.GeoDataFrame({'geometry': grid_polys}).set_crs('EPSG:4326')
        grid_intersected_polys_df = gpd.overlay(reproj_df, grid, how='intersection')

        max_pop = census_df['population'].quantile(0.99)
        cmap = cm.get_cmap('viridis', 100)

        def get_colour(pop):
            return to_hex(cmap(pop / max_pop))

        result_objects = []

        self.signals.update_status.emit(0.85, 'Generating map objects')
        for idx, row in reproj_df.iterrows():
            if row['geometry'].geom_type == 'Polygon':
                result_objects.append(
                    fl.Polygon(list(map(list, map(reversed, row['geometry'].exterior.coords))),
                               tooltip=row['name'],
                               popup=('Estimated Population: ' + str(row['population'])),
                               # color=get_colour(row['population']),
                               # fill=True)
                               )
                )
            else:
                for p in row['geometry'].geoms:
                    result_objects.append(
                        fl.Polygon(list(map(list, map(reversed, p.exterior.coords))),
                                   tooltip=row['name'],
                                   popup=('Estimated Population: ' + str(row['population'])),
                                   # color=get_colour(row['population']),
                                   # fill=True)
                                   )
                    )

        flat_points = []
        for idx, row in grid_intersected_polys_df.iterrows():
            poly_centroid = list(map(list, map(reversed, row['geometry'].centroid.coords)))[0]
            poly_centroid.append(row['population'])
            flat_points.append(poly_centroid)

        hm = HeatMap(flat_points, max_val=max_pop, min_opacity=0.1, blur=25)
        result_objects.append(hm)

        self.signals.update_status.emit(0.99, 'Generating map (Map may lag)')
        self.signals.update_map.emit(result_objects)


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
