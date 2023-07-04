
from ipdb import set_trace as idebug
# import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 
import json

from bokeh.models import GeoJSONDataSource
from bokeh.plotting import figure, show
from bokeh.sampledata.sample_geojson import geojson
from bokeh.models import CustomJS, RadioButtonGroup, MultiChoice

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
from bokeh.layouts import row, column


def worked_example():
# from bokeh.io import show
# from bokeh.models import CustomJS, MultiChoice

    OPTIONS = ["foo", "bar", "baz", "quux"]

    multi_choice = MultiChoice(value=["foo", "baz"], options=OPTIONS)
    # multi_choice.js_on_change("value", CustomJS(code="""
    #     console.log('multi_choice: value=' + this.value, this.toString())
    # """))
    multi_choice.js_on_change("value", CustomJS(code="""
        alert('multi_choice: value=' + this.value, this.toString())
    """))

    rbg = RadioButtonGroup(labels="A B C".split(), active=0)
    rbg.js_on_change(
        "button", 
        CustomJS(
            code="""alert('RBG: value=' + this.value, this.toString())
            """
        )
    )
    show(column(multi_choice, rbg))
    



def main():

    # data = np.random.randn(20).reshape(10, 2)
    # tools = "pan,wheel_zoom,box_zoom,reset"
    # p = figure(background_fill_color="white", tools=tools, frame_height=800) 
    # p.line(data[:,0], data[:,1],line_color='navy', line_width=4)

    pols = ["Council", "State", "Congress"]
    bg = RadioButtonGroup(labels=pols)

    bg.js_on_event(
        "button_click", 
        CustomJS(
            args=dict(btn=bg), 
            # code="console.log('radio_button_group: active=' + btn.active, this.toString())"
            #code="""alert('radio_button_group: active=' + btn.active, this.toString()))"""
            code="""alert("Hello");"""
        )
    )


    # page = column(bg, p)
    show(bg)


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
