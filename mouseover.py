
from ipdb import set_trace as idebug 
from bokeh.io import show,save
import pandas as pd
import numpy as np 

from bokeh.plotting import figure
from bokeh.models import CustomJS, ColorBar, LinearColorMapper
from bokeh.layouts import row, column
import bokeh.palettes 

from bokeh.models import CustomJS, RadioButtonGroup, SetValue
from bokeh.events import MouseEnter, MouseLeave

from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmbok.roads as roads

import bokeh_chlorpleth as bc 
import stio

import bokplay2

def main():
    leg_fn = '/home/fergal/data/elections/shapefiles/md_lege_districts/2022/Maryland_Legislative_Districts_2022.kml'
    leg = stio.load_leg_districts(leg_fn)

    tools = "pan,wheel_zoom,box_zoom,reset,hover"
    fig = figure(
        tools=tools,
        tooltips="@tooltip", 
        frame_height=800, 
        frame_width=800,
        x_range=(-77, -76.25),
        y_range=(39.1, 39.8),
        toolbar_location='above',
        title="Draft",
    )

    fmt = "District {DistrictId}"
    opts = {'line_color':'black', 'tooltip_fmt':fmt}
    plat_leg = bokplay2.plot_outlines(fig, leg, **opts)
    show(fig)


def plot_outlines(fig, df, geom_col='geom', tooltip_fmt=None, **kwargs):
    tooltip_fmt = tooltip_fmt or " "
    kwargs['line_color'] = kwargs.get('line_color', None) or 'white'
    kwargs['line_width'] = kwargs.get('line_width', None) or 2


    #Create a dataframe in the format bokeh wants
    # src = pd.concat(lmap(convert_shape_to_bokeh_patch_format, df[geom_col]))
    src = convert_df_to_bokeh_patch_format(df, 'geom')
    tooltip = df.apply(lambda x: tooltip_fmt.format(**x), axis=1)
    src['tooltip'] = tooltip
    handle = fig.multi_line(xs='xs', ys='ys', source=src, **kwargs)
    jscode = CustomJS(
        args=dict(
        borders=handle
        ),
        code = """
            handle.line_width.value = 4;
        """
    )
    handle.js_on_event(MouseEnter, jscode)
    return handle 



def convert_df_to_bokeh_patch_format(df, geom_col):

    index = []
    dflist = []
    for ind, row in df.iterrows():
        shape = row[geom_col]
        tmp = convert_shape_to_bokeh_patch_format(shape)
        dflist.append(tmp)
        index.extend( [ind] * len(tmp))

    out = pd.concat(dflist)
    out.index = index 
    return out 


def convert_shape_to_bokeh_patch_format(shape):

    xs = [] 
    ys = []
    ptype, parts = AnyGeom(shape).as_array()

    if ptype == 'MULTIPOLYGON':
        if isinstance(parts, list):
            for part in parts:
                arr = part[0]
                xs.append(arr[:,0])
                ys.append(arr[:,1])
        else:
            arr = parts
            xs.append(arr[:,0])
            ys.append(arr[:,1])
    elif ptype == 'POLYGON':
        if isinstance(parts, list):
            print(f'Polygon has a hole. Ignoring for now')

        else:
            arr = parts
            xs.append(arr[:,0])
            ys.append(arr[:,1])
    
    out = pd.DataFrame()
    out['xs'] = xs 
    out['ys'] = ys 
    return out
