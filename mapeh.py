
from ipdb import set_trace as idebug
# import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 
import json

from bokeh.models import GeoJSONDataSource
from bokeh.plotting import figure, show
from bokeh.sampledata.sample_geojson import geojson

from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmgis.get_geom as fgg 



"""
Trying Bokeh instead

x Add a tooltip
o Hide tooltip for district lines
o Make a layer appear/disappear
o Add a basemap
o Better colormap: https://docs.bokeh.org/en/latest/docs/reference/palettes.html
        YlOrRd?
"""


from bokeh.models import HoverTool

def main():
    school_type = 'High'
    sch_fn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'

    dist = fgg.load_geoms_as_df(distfn)
    dist['val'] = dist.COUNCILMANIC_DISTRICTS.astype(int)

    sch = fgg.load_geoms_as_df(sch_fn)
    sch['val'] = np.arange(len(sch))

    tools = "pan,wheel_zoom,box_zoom,reset"
    p = figure(background_fill_color="white", tools=tools) 
    # p.add_tools('hover')
    chloropleth_geom_df(p, sch, val_col='val', palette='Spectral11')
    plot_shape_outlines(p, dist, line_color='navy', line_width=4)
    
    hover = HoverTool(tooltips=[('Name1', "@tooltip"), ('Value', "@val")])
    p.add_tools(hover)
                      
    show(p)


def plot_shape_outlines(p, df, geom_col='geom', **kwargs):
    """Plot outlines of every shape in df

    Deals with multi polygons, but not with holes in polygons

    kwargs are passed to p.line()
    """

    for i in range(len(df)):
        d1 = df[geom_col].iloc[i]
        parts = AnyGeom(d1).as_array()[1]

        if isinstance(parts, list):
            for part in parts:
                df2 = pd.DataFrame(part[0], columns="x y".split())
                p.line(x='x', y='y', source=df2, **kwargs)
        else:
            df2 = pd.DataFrame(parts, columns="x y".split())
            p.line(x='x', y='y', source=df2, **kwargs)    


from bokeh.transform import linear_cmap

 
def chloropleth_geom_df(p, df, geom_col='geom', val_col='val', **kwargs):
    """Plot outlines of every shape in df

    Deals with multi polygons, but not with holes in polygons

    kwargs are passed to p.line()

    Is this the best way to implement this? Probably not.
    """

    vmin = kwargs.pop('vmin', df[val_col].min())
    vmax = kwargs.pop('vmax', df[val_col].max())
    palette = kwargs.pop('palette', 'Spectral7')
    print(vmin, vmax)
    cmap = linear_cmap(field_name='val', palette=palette, low=vmin, high=vmax)
    print(cmap)

    xs = [] 
    ys = []
    cval = []
    tooltip = []
    for i in range(len(df)):
        d1 = df[geom_col].iloc[i]
        clr = df[val_col].iloc[i]
        name = df.Name.iloc[i]
        parts = AnyGeom(d1).as_array()[1]

        if isinstance(parts, list):
            for part in parts:
                arr = part[0]
                xs.append(arr[:,0])
                ys.append(arr[:,1])
                cval.append(clr)
                tooltip.append(name)

        else:
            arr = parts
            xs.append(arr[:,0])
            ys.append(arr[:,1])
            cval.append(clr)
            tooltip.append(name)

    tmp = pd.DataFrame()
    tmp['xs'] = xs 
    tmp['ys'] = ys 
    tmp['val'] = cval 
    tmp['tooltip'] = tooltip
    p.patches('xs', 'ys', source=tmp, color=cmap)
