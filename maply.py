
from ipdb import set_trace as idebug
# import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 


from frmgis.anygeom import AnyGeom

from frmbase.support import npmap, lmap 

import plotly.express as px 
import geopandas as gpd 
import fiona


"""
Todo:
o Bug in map labels?
o Map labels should try a few different placements before giving up
o Add roadmap


o Plotly of districts only 
o Plotly of districts + catchments
o Turn on/off some layers 
o Add heatmap base layer 
"""


"""
Trying to read all values from a kml 
Taken from https://gis.stackexchange.com/questions/446036/reading-kml-with-geopandas


    import fiona 
    gdf_list = []
    for layer in fiona.listlayers(distfn):    
        gdf = gpd.read_file(distfn, driver='KML', layer=layer)
        gdf_list.append(gdf)
    df = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
"""

def main():
    #  return plot_district_chloropleth()
    return plot_school_chloropleth()


def plot_school_chloropleth():
    school_type = 'High'
    sch_fn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    
    
    sch = load_school_geoms(sch_fn, school_type)
    district = load_district_geoms(distfn)
    

    fig = px.choropleth_mapbox(
        sch, 
        geojson=eval(sch.geometry.to_json()), 
        locations='id',
        featureidkey='id', 
        color="Name",
        mapbox_style='open-street-map',
        center={'lon':-76.6605822299999, 'lat':39.3800276340746},
        zoom=9
    )

    update_fig_with_district_outlines(fig, district)


    fig.update_layout(mapbox_bounds={"west": -180, "east": -50, "south": 20, "north": 90})
    fig.show()
    return sch, district

    # return plot_districts_as_chloro(dist)


def load_school_geoms(fn, school_type):
    #Read kml into geopandas. Drive can be KML or LIBKML
    driver = "KML"
    fiona.drvsupport.supported_drivers[driver] = 'rw'
    # gpd.io.file.fiona.drvsupport.supported_drivers[driver] = 'rw'
    df = gpd.read_file(fn, driver=driver)

    #Value gets replaced with the quantity you want to plot
    df['value'] = np.arange(len(df))
    df['id'] = np.arange(len(df))
    return df 


def load_district_geoms(fn):
     #Read kml into geopandas. Drive can be KML or LIBKML
    driver = 'LIBKML'  #KML | LIBKML

    fiona.drvsupport.supported_drivers[driver] = 'rw'
    df = gpd.read_file(fn, driver=driver)
    #Geopandas ignores everything but the shape itself. Define the names
    df['Name'] = "D1 D2 D3 D4 D5 D6 D7".split()
    df.index = df.Name

    #Magic! Remove this line and plotly fills outside the polygon!
    df['geom'] = df.geometry.apply(orient, args=(-1,))
 
    #Make shapes smaller for plotting purposes
    df['geom'] = df.geometry.simplify(1e-3)
    return df 



def update_fig_with_district_outlines(fig, dist):
    #Only works for simple polygons?
    def foo(df):
        _, arr = AnyGeom(df.geom).as_array()

        if isinstance(arr, list):
            arr = arr[0][0]

        out = pd.DataFrame()
        out['lng'] = arr[:,0]
        out['lat'] = arr[:,1]
        out['district'] = df.Name
        return out 
    
    dflist = dist.apply(foo, axis=1).tolist()
    df = pd.concat(dflist)

    # fig = px.line(
    #     df, x='lng', y='lat', color='district'
    # )
    fig.add_line(df, x='lng', y='lat')
    fig.show()
    return fig






def plot_district_chloropleth():
    distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'


    # from shapely.geometry import polygon, multipolygon    

    #Read kml into geopandas. Drive can be KML or LIBKML
    driver = 'LIBKML'
    # gpd.io.file.fiona.drvsupport.supported_drivers[driver] = 'rw'
    fiona.drvsupport.supported_drivers[driver] = 'rw'
    df = gpd.read_file(distfn, driver=driver)
    #Geopandas ignores everything but the shape itself. Define the names
    df['Name'] = "D1 D2 D3 D4 D5 D6 D7".split()
    df.index = df.Name

    #Magic! Remove this line and plotly fills outside the polygon!
    df['geometry'] = df.geometry.apply(orient, args=(-1,))
 
    #Make shapes smaller for plotting purposes
    df['geometry'] = df.geometry.simplify(1e-3)


    fig = px.choropleth_mapbox(
        df, 
        geojson=eval(df.geometry.to_json()), 
        locations='Name', 
        color="Name",
        mapbox_style='open-street-map',
        
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.show()
    return df








from shapely.geometry.base import BaseMultipartGeometry
from shapely.geometry.polygon import orient as orient_
from shapely.geometry import Polygon
def orient(geom, sign=1.0):
    """From 

    https://gis.stackexchange.com/questions/336477/how-to-apply-the-orient-function-on-the-geometry-of-a-geopandas-dataframe

    This function is in shapely 1.7.2 and above
    """
    if isinstance(geom, BaseMultipartGeometry):
        return geom.__class__(
            list(
                map(
                    lambda geom: orient(geom, sign),
                    geom.geoms,
                )
            )
        )
    if isinstance(geom, (Polygon,)):
        return orient_(geom, sign)
    return geom


def plot_districts_as_chloro(df):
    geojson = geom_to_json(df, 'COUNCILMANIC_DISTRICTS', 'geom')
    
    fig = px.choropleth(df, geojson=geojson, 
        color='COUNCILMANIC_DISTRICTS',
        locations='COUNCILMANIC_DISTRICTS', 
        featureidkey='name',
        # projection="mercator",
    )     
    fig.update_xaxes(range=[-79, -75])
    fig.update_yaxes(range=[30, 35]) 
    fig.show()
    return df, geojson






def worked_example():
    df = px.data.election()
    geojson = px.data.election_geojson()

    fig = px.choropleth(
        df,   #Dataframe containing the values to plot 
        geojson=geojson, #dict containing boundaries as json 
        color="Bergeron",  #Column in df to plot
        locations="district",  #Matching column in df 
        featureidkey="properties.district",  #Matching column in geojson
        projection="mercator"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()
    return df, geojson


import json 
def geom_to_json(df, name_col, geom_col):

    features = []
    for n, g in zip(df[name_col], df[geom_col]):

        feat = {
            'type': 'Feature',
            'name': n, 
            'geometry': json.loads(AnyGeom(g).as_json())
        }
        feat['geometry']['coordinates'] = feat['geometry']['coordinates'][:10]
        features.append(feat)
    return features



