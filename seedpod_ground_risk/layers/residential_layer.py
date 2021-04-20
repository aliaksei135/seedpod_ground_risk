from typing import NoReturn, Tuple

import geopandas as gpd
import numpy as np
import shapely.geometry as sg
from holoviews.element import Geometry
from shapely import speedups

from seedpod_ground_risk.layers.osm_tag_layer import OSMTagLayer

gpd.options.use_pygeos = True  # Use GEOS optimised C++ routines
speedups.enable()  # Enable shapely speedups


class ResidentialLayer(OSMTagLayer):
    _census_wards: gpd.GeoDataFrame

    def __init__(self, key, **kwargs):
        super(ResidentialLayer, self).__init__(key, 'landuse=residential', **kwargs)
        delattr(self, '_colour')
        self._census_wards = gpd.GeoDataFrame()

    def preload_data(self):
        print("Preloading Residential Layer")
        self.ingest_census_data()

    def generate(self, bounds_polygon: sg.Polygon, raster_shape: Tuple[int, int], from_cache: bool = False, **kwargs) -> \
            Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]:
        import colorcet
        import datashader as ds
        from holoviews.operation.datashader import rasterize
        import geoviews as gv
        from copy import deepcopy

        bounds = bounds_polygon.bounds
        polys_df = self.query_osm_polygons(bounds_polygon)
        bounded_census_wards = self._census_wards.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]

        # Find landuse polygons intersecting/within census wards and merge left
        census_df = gpd.overlay(polys_df,
                                bounded_census_wards,
                                how='intersection')
        # Estimate the population of landuse polygons from the density of the census ward they are within
        # EPSG:4326 is *not* an equal area projection so would give gibberish areas
        # Project geometries to an equidistant/equal areq projection
        census_df['population'] = census_df['density'] * census_df['geometry'].to_crs('EPSG:3395').area
        census_df['ln_density'] = np.log(census_df['density'])

        # Construct the GeoViews Polygons
        gv_polys = gv.Polygons(census_df, kdims=['Longitude', 'Latitude'],
                               vdims=['population', 'ln_density', 'density']) \
            .opts(color='ln_density',
                  cmap=colorcet.CET_L18, alpha=0.8,
                  colorbar=True, colorbar_opts={'title': 'Log Population Density [ln(people/km^2)]'}, show_legend=False,
                  line_color='ln_density')

        if self.buffer_dist > 0:
            buffered_df = deepcopy(census_df)
            buffered_df.geometry = buffered_df.to_crs('EPSG:27700') \
                .buffer(self.buffer_dist).to_crs('EPSG:4326')
            buffered_polys = gv.Polygons(buffered_df, kdims=['Longitude', 'Latitude'], vdims=['name', 'density'])
            raster = rasterize(buffered_polys, aggregator=ds.max('density'), width=raster_shape[0],
                               height=raster_shape[1], x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]),
                               dynamic=False)
        else:
            raster = rasterize(gv_polys, aggregator=ds.max('density'), width=raster_shape[0], height=raster_shape[1],
                               x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)

        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(np.float))

        return gv_polys, raster_grid, gpd.GeoDataFrame(census_df)

    def ingest_census_data(self) -> NoReturn:
        """
        Ingest Census boundaries and density values and overlay/merge
        """
        import pandas as pd
        import os

        # Import Census boundaries in Ordnance Survey grid and reproject
        census_wards_df = gpd.read_file(
            os.sep.join(('static_data', 'england_wa_2011_clipped.shp'))).drop(
            ['altname', 'oldcode'], axis=1)
        if not census_wards_df.crs:
            census_wards_df = census_wards_df.set_crs('EPSG:27700')
        census_wards_df = census_wards_df.to_crs('EPSG:4326')
        # Import census ward densities
        density_df = pd.read_csv(os.sep.join(('static_data', 'density.csv')), header=0)
        # Scale from hectares to km^2
        density_df['area'] = density_df['area'] * 0.01
        density_df['density'] = density_df['density'] / 0.01

        # These share a common UID, so merge together on it and store
        self._census_wards = census_wards_df.merge(density_df, on='code')
