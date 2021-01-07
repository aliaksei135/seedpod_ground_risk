from typing import NoReturn

import geopandas as gpd
import shapely.geometry as sg
from holoviews.element import Geometry
from shapely import speedups

from seedpod_ground_risk.layers.osm_tag_layer import OSMTagLayer

gpd.options.use_pygeos = True  # Use GEOS optimised C++ routines
speedups.enable()  # Enable shapely speedups


class ResidentialLayer(OSMTagLayer):
    _census_wards: gpd.GeoDataFrame

    def __init__(self, key, **kwargs):
        super(ResidentialLayer, self).__init__(key, osm_tag='landuse=residential', **kwargs)
        self._census_wards = gpd.GeoDataFrame()

    def preload_data(self):
        print("Preloading Residential Layer")
        self.ingest_census_data()

    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, **kwargs) -> Geometry:
        from time import time
        import colorcet
        import datashader as ds
        from holoviews.operation.datashader import rasterize
        import geoviews as gv

        t0 = time()
        print("Generating Residential Layer Data")

        bounds = bounds_polygon.bounds

        if not from_cache:
            self.query_osm_polygons(bounds_polygon)
        bounded_census_wards = self._census_wards.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]
        print("Residential: Bounded census wards cumtime ", time() - t0)

        # Find landuse polygons intersecting/within census wards and merge left
        census_df = gpd.overlay(self._landuse_polygons,
                                bounded_census_wards,
                                how='intersection')
        print("Residential: Overlaid geometries cumtime ", time() - t0)
        # Estimate the population of landuse polygons from the density of the census ward they are within
        # EPSG:4326 is *not* an equal area projection so would give gibberish areas
        # Project geometries to an equidistant/equal areq projection
        census_df['population'] = census_df['density'] * census_df['geometry'].to_crs('EPSG:3395').area

        # Scale to reduce error for smaller, less dense wards
        # This was found empirically minimising the population error in 10 random villaegs in Hampshire
        def scale_pop(x):
            if 0 < x < 3000:
                return 0.998 * x + 6
            else:
                return x

        # Actually perform the populations scaling
        census_df['population'] = census_df['population'].apply(scale_pop)
        # Construct the GeoViews Polygons
        gv_polys = gv.Polygons(census_df, vdims=['name', 'population']) \
            .opts(color='population',
                  cmap=colorcet.CET_L18,
                  colorbar=True, colorbar_opts={'title': 'Population'}, show_legend=False)

        print("Residential: Estimated and Scaled Populations cumtime ", time() - t0)
        if self.rasterise:
            raster = rasterize(gv_polys, aggregator=ds.sum('population'),
                               cmap=colorcet.CET_L18, dynamic=False).options(colorbar=True,
                                                                             cmap=colorcet.CET_L18,
                                                                             clipping_colors={'0': 'transparent',
                                                                                              'NaN': 'transparent',
                                                                                              '-NaN': 'transparent'})
            t1 = time()
            print('Residential with raster: ', t1 - t0)
            return raster
        else:
            t1 = time()
            print('Residential no raster: ', t1 - t0)
            return gv_polys

    def ingest_census_data(self) -> NoReturn:
        """
        Ingest Census boundaries and density values and overlay/merge
        """
        import pandas as pd
        import os

        # Import Census boundaries in Ordnance Survey grid and reproject
        census_wards_df = gpd.read_file(os.sep.join(('static_data', 'england_wa_2011_clipped.shp'))).drop(
            ['altname', 'oldcode'], axis=1)
        if not census_wards_df.crs:
            census_wards_df = census_wards_df.set_crs('EPSG:27700')
        census_wards_df = census_wards_df.to_crs('EPSG:4326')
        # Import census ward densities
        density_df = pd.read_csv(os.sep.join(('static_data', 'density.csv')), header=0)
        # Scale from hectares to m^2
        density_df['area'] = density_df['area'] * 10000
        density_df['density'] = density_df['density'] / 10000

        # These share a common UID, so merge together on it and store
        self._census_wards = census_wards_df.merge(density_df, on='code')
