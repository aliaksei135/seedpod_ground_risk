from typing import NoReturn

import geopandas as gpd

from seedpod_ground_risk.data import england_wa_2011_clipped_filepath, nhaps_data_filepath, \
    density_filepath
from seedpod_ground_risk.layers.blockable_data_layer import BlockableDataLayer
from seedpod_ground_risk.layers.osm_tag_layer import query_osm_polygons

nhaps_category_groupings = [
    [0, 1],
    [5, 9],
    [7],
    [6, 8],
]

nhaps_group_tags = [
    ['landuse=residential'],
    ['landuse=industrial', 'landuse=commercial'],
    ['building=school', 'building=college', 'building=university', 'building=public', 'building=government',
     'building=civic', 'building=hospital'],
    ['landuse=retail']
]


class TemporalPopulationEstimateLayer(BlockableDataLayer):

    def __init__(self, key, colour: str = None, blocking=False, buffer_dist=0):
        super().__init__(key, colour, blocking, buffer_dist)
        delattr(self, '_colour')

    def preload_data(self):
        self._ingest_census_data()
        self._ingest_nhaps_proportions()

    def generate(self, bounds_polygon, raster_shape, from_cache: bool = False, hour: int = 8, **kwargs):
        import pandas as pd
        import numpy as np
        import geoviews as gv
        from copy import deepcopy
        from holoviews.operation.datashader import rasterize
        import colorcet
        import datashader as ds

        bounds = bounds_polygon.bounds
        # Hardcode residential tag in as this is always the first OSM query made to find the total area population
        residential_df = query_osm_polygons('landuse=residential', bounds_polygon)
        bounded_census_wards = self._census_wards.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]

        # Find landuse polygons intersecting/within census wards and merge left
        census_df = gpd.overlay(residential_df,
                                bounded_census_wards,
                                how='intersection')
        # Estimate the population of landuse polygons from the density of the census ward they are within
        # EPSG:4326 is *not* an equal area projection so would give gibberish areas
        # Project geometries to an equidistant/equal areq projection
        census_reproj_areas = census_df['geometry'].to_crs('EPSG:3395').area * 1e-6  # km^2
        census_df['population'] = census_df['density'] * census_reproj_areas
        total_population = census_df['population'].sum()

        df = None

        # Ensure we have a large enough population for this approximation to be valid
        if total_population > 200000:
            hour_categories = self.nhaps_df.iloc[:, hour % 24]
            nhaps_category_gdfs = []

            for idx, categories in enumerate(nhaps_category_groupings):
                group_proportion = hour_categories.iloc[categories].sum()
                group_population = total_population * group_proportion

                # Residential areas are handled separately as they depend upon census data
                # Otherwise, they would become uniform density, when we have census data providing us (unscaled) densities
                if idx == 0:
                    group_gdf = deepcopy(census_df)
                    group_gdf['population'] = group_gdf['population'] * group_proportion
                    group_gdf['density'] = group_gdf['population'] / census_reproj_areas
                    group_gdf['ln_density'] = np.log(group_gdf['density'])
                else:
                    group_gdfs = [query_osm_polygons(tag, bounds_polygon) for tag in nhaps_group_tags[idx]]
                    group_gdf = gpd.GeoDataFrame(pd.concat(group_gdfs, ignore_index=True), crs='EPSG:4326')
                    areas = group_gdf.to_crs(epsg=3395).geometry.area * 1e-6  # km^2
                    group_density = group_population / areas.sum()
                    group_gdf['density'] = group_density
                    group_gdf['ln_density'] = np.log(group_gdf['density'])
                    group_gdf['population'] = group_density * areas
                nhaps_category_gdfs.append(group_gdf)

            nhaps_category_gdf = gpd.GeoDataFrame(pd.concat(nhaps_category_gdfs, ignore_index=True), crs='EPSG:4326')
            # Construct the GeoViews Polygons
            gv_polys = gv.Polygons(nhaps_category_gdf, kdims=['Longitude', 'Latitude'],
                                   vdims=['population', 'ln_density', 'density']) \
                .opts(color='ln_density',
                      cmap=colorcet.CET_L18, alpha=0.6,
                      colorbar=True, colorbar_opts={'title': 'Log Population Density [ln(people/km^2)]'},
                      show_legend=False,
                      line_color='ln_density')

            if self.buffer_dist > 0:
                buffered_df = deepcopy(nhaps_category_gdf)
                buffered_df.geometry = buffered_df.to_crs('EPSG:27700') \
                    .buffer(self.buffer_dist).to_crs('EPSG:4326')
                buffered_polys = gv.Polygons(buffered_df, kdims=['Longitude', 'Latitude'], vdims=['density'])
                raster = rasterize(buffered_polys, aggregator=ds.max('density'), width=raster_shape[0],
                                   height=raster_shape[1], x_range=(bounds[1], bounds[3]),
                                   y_range=(bounds[0], bounds[2]),
                                   dynamic=False)
            else:
                raster = rasterize(gv_polys, aggregator=ds.max('density'), width=raster_shape[0],
                                   height=raster_shape[1],
                                   x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
            df = nhaps_category_gdf
        else:
            census_df['ln_density'] = np.log(census_df['density'])
            # Construct the GeoViews Polygons
            gv_polys = gv.Polygons(census_df, kdims=['Longitude', 'Latitude'],
                                   vdims=['population', 'ln_density', 'density']) \
                .opts(color='ln_density',
                      cmap=colorcet.CET_L18, alpha=0.8,
                      colorbar=True, colorbar_opts={'title': 'Log Population Density [ln(people/km^2)]'},
                      show_legend=False,
                      line_color='ln_density')

            if self.buffer_dist > 0:
                buffered_df = deepcopy(census_df)
                buffered_df.geometry = buffered_df.to_crs('EPSG:27700') \
                    .buffer(self.buffer_dist).to_crs('EPSG:4326')
                buffered_polys = gv.Polygons(buffered_df, kdims=['Longitude', 'Latitude'], vdims=['name', 'density'])
                raster = rasterize(buffered_polys, aggregator=ds.max('density'), width=raster_shape[0],
                                   height=raster_shape[1], x_range=(bounds[1], bounds[3]),
                                   y_range=(bounds[0], bounds[2]),
                                   dynamic=False)
            else:
                raster = rasterize(gv_polys, aggregator=ds.max('density'), width=raster_shape[0],
                                   height=raster_shape[1],
                                   x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
            df = census_df

        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(float))

        return gv_polys, raster_grid, gpd.GeoDataFrame(df)

    def clear_cache(self):
        pass

    def _ingest_census_data(self) -> NoReturn:
        """
        Ingest Census boundaries and density values and overlay/merge
        """
        import pandas as pd

        # Import Census boundaries in Ordnance Survey grid and reproject
        census_wards_df = gpd.read_file(england_wa_2011_clipped_filepath()).drop(['altname', 'oldcode'], axis=1)
        if not census_wards_df.crs:
            census_wards_df = census_wards_df.set_crs('EPSG:27700')
        census_wards_df = census_wards_df.to_crs('EPSG:4326')
        # Import census ward densities
        density_df = pd.read_csv(density_filepath(), header=0)
        # Scale from hectares to km^2
        density_df['area'] = density_df['area'] * 0.01
        density_df['density'] = density_df['density'] / 0.01

        # These share a common UID, so merge together on it and store
        self._census_wards = census_wards_df.merge(density_df, on='code')

    def _ingest_nhaps_proportions(self) -> NoReturn:
        """
        Ingest NHAPS serialised spatiotemporal population location proportions
        """
        import pandas as pd
        self.nhaps_df = pd.read_json(nhaps_data_filepath())
