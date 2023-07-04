import geopandas as gpd
import plotly.express as px
import pandas as pd 
import numpy as np 

from frmgis.anygeom import AnyGeom

import plotly.express as px 
import geopandas as gpd 
import fiona


"""
This code plots districts as black outlines.

It isn't integrated with school choropleth
"""

def main():
    distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    df = load_district_geoms(distfn)
    # df = df[:5]
    fig = plot_districts_as_outlines(df)
    fig.show()
    return fig 


def plot_districts_as_outlines(dist):
    #Only works for simple polygons?
    def foo(df):
        _, arr = AnyGeom(df.geometry).as_array()

        if isinstance(arr, list):
            arr = arr[0][0]

        out = pd.DataFrame()
        out['lng'] = arr[:,0]
        out['lat'] = arr[:,1]
        out['district'] = df.Name
        out['dnum'] = int(df.Name[-1])
        out['clr'] = 'rgb(0,0,0)'
        return out 
    
    dflist = dist.apply(foo, axis=1).tolist()
    df = pd.concat(dflist)

    fig = px.line_mapbox(
        df, lat='lat', lon='lng', 
        line_group='district',
        color='dnum',
        mapbox_style='open-street-map',

    )
    fig.update_traces(line={'color': 'black', 'width':4})
    # fig = px.line(
    #     df, x='lng', y='lat', color='clr'
    # )
    return fig



def load_district_geoms(fn):
     #Read kml into geopandas. Drive can be KML or LIBKML
    driver = 'LIBKML'  #KML | LIBKML

    fiona.drvsupport.supported_drivers[driver] = 'rw'
    df = gpd.read_file(fn, driver=driver)
    #Geopandas ignores everything but the shape itself. Define the names
    df['Name'] = "D1 D2 D3 D4 D5 D6 D7".split()
    df.index = df.Name

    #Magic! Remove this line and plotly fills outside the polygon!
    df['geometry'] = df.geometry.apply(orient, args=(-1,))
 
    #Make shapes smaller for plotting purposes
    df['geometry'] = df.geometry.simplify(1e-3)
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
