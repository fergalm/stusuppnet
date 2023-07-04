from bokeh.io import show
from bokeh.models import Button, SetValue
import numpy as np 

from bokeh.plotting import figure
from bokeh.models import CustomJS, MultiLine
from bokeh.layouts import row, column

from bokeh.models import CustomJS, RadioButtonGroup, ColumnDataSource
from bokeh.transform import linear_cmap


from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmgis.get_geom as fgg 

import stio

"""
Todo 

x Fix elementary heat map
o Add tooltips 
o Add multiline for political districts 
o Add interaction for political districts
o Add colorbar
o Change cmap 
o Overlay roads 
o Add labels?
o Plot polygons with holes
"""

def step1():
    # button = Button(label="Foo", button_type="primary")
    # callback = SetValue(obj=button, attr="label", value="Bar")
    # button.js_on_event("button_click", callback)

    p = figure()
    props = dict(line_width=4, line_alpha=0.7)
    x = np.linspace(0, 4 * np.pi, 100)
    l0 = p.line(x, np.sin(x), **props)

    button = Button(label="Foo", button_type="primary")
    callback = SetValue(obj=l0, attr="visible", value=False)
    button.js_on_event("button_click", callback)

    layout = row(button, p)
    show(layout)


def step2():

    p = figure()
    props = dict(line_width=4, line_alpha=0.7)
    x = np.linspace(0, 4 * np.pi, 100)
    l0 = p.line(x, np.sin(x),  **props)
    l1 = p.line(x, 4 * np.cos(x),  **props)
    l2 = p.line(x, np.tan(x),  **props)


    rbg = RadioButtonGroup(labels="A B C".split(), active=0)
    callback = CustomJS(
        args=dict(
            l0=l0, 
            l1=l1, 
            l2=l2, 
            rbg=rbg,
        ),
        code="""
            l0.visible = (rbg.active==0);
            l1.visible = (rbg.active==1);
            l2.visible = (rbg.active==2);
            console.log('radio_button_group: active=' + rbg.active, this.toString());
    """
    )
    rbg.js_on_event("button_click", callback)

    layout = column(rbg, p)
    show(layout)


import pandas as pd 
def step3():
    alicefn = "alice.csv"    
    council_fn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    leg_fn = '/home/fergal/data/elections/shapefiles/md_lege_districts/2022/Maryland_Legislative_Districts_2022.kml'
    cong_fn = "/home/fergal/data/elections/shapefiles/congressional/Congress_2022/US_Congressional_Districts_2022.kml"

    elem = stio.load_alice_data(alicefn, "Elementary")
    mid = stio.load_alice_data(alicefn, "Middle")
    high = stio.load_alice_data(alicefn, "High")
    assert len(elem) > 0

    # council = stio.load_council_districts(council_fn)
    leg = stio.load_leg_districts(leg_fn)
    cong = stio.load_cong_districts(cong_fn)


    tools = "pan,wheel_zoom,box_zoom,reset,hover"
    # fig = figure(tools=[HoverTool()],tooltips="@tooltip")
    fig = figure(tools=tools,tooltips="@tooltip", frame_height=800, frame_width=800)
    plat_elem = chloropleth_geom_df(fig, elem, val_col='Value')
    plat_mid = chloropleth_geom_df(fig, mid, val_col='Value')
    plat_high = chloropleth_geom_df(fig, high, val_col='Value')
    plat_elem.visible = False
    plat_mid.visible= False

    sch_choice = RadioButtonGroup(labels="Elem Middle High".split(), active=2)
    callback = CustomJS(
        args=dict(
            p0=plat_elem, 
            p1=plat_mid, 
            p2=plat_high, 
            sch_choice=sch_choice,
        ),
        code="""
            p0.visible = (sch_choice.active==0);
            p1.visible = (sch_choice.active==1);
            p2.visible = (sch_choice.active==2);
            console.log('radio_button_group: active=' + sch_choice.active, this.toString());
    """
    )
    sch_choice.js_on_event("button_click", callback)


    opts = {'line_color':'black'}
    # plat_council = plot_outlines(fig, council, **opts)
    plat_leg = plot_outlines(fig, leg, name_col='DistrictId', **opts)
    plat_cong = plot_outlines(fig, cong, name_col='DistrictId', **opts)
    # plat_council.visible = False 
    plat_cong.visible = False 

    leg_choice = RadioButtonGroup(labels="Council Leg Cong".split(), active=1)
    callback = CustomJS(
        args=dict(
            # p0=plat_council, 
            p1=plat_leg, 
            p2=plat_cong, 
            leg_choice=leg_choice,
        ),
        code="""
            //p0.visible = (leg_choice.active==0);
            p1.visible = (leg_choice.active==1);
            p2.visible = (leg_choice.active==2);
            console.log('radio_button_group: active=' + leg_choice.active, this.toString());
    """
    )
    leg_choice.js_on_event("button_click", callback)

    layout = column(sch_choice, leg_choice, fig)
    show(layout)


def plot_outlines(fig, df, name_col='Name', geom_col='geom', **kwargs):

    df2 = convert_wkt_df_to_bokeh_friendly_df(df, name_col, geom_col)
    handle = MultiLine('xs', 'ys', source=df2, **kwargs)
    return handle


def chloropleth_geom_df(fig, df, geom_col='geom', val_col='val', **kwargs):
    """Plot outlines of every shape in df

    Deals with multi polygons, but not with holes in polygons

    kwargs are passed to p.line()

    Is this the best way to implement this? Probably not.
    """

    vmin = kwargs.pop('vmin', df[val_col].min())
    vmax = kwargs.pop('vmax', df[val_col].max())

    kwargs['line_color'] = kwargs.get('line_color', None) or 'white'
    kwargs['line_width'] = kwargs.get('line_width', None) or 2

    palette = kwargs.pop('palette', 'YlOrRd7')
    cmap = linear_cmap(field_name='val', palette=palette, low=vmin, high=vmax)

    tooltip_fmt = "{name}: {clr:.0f}%"
    tmp = convert_wkt_df_to_bokeh_friendly_df(df, 'Name', geom_col, val_col, tooltip_fmt)

    handle = fig.patches('xs', 'ys', source=tmp, color=cmap, **kwargs)
    return handle 



def convert_wkt_df_to_bokeh_friendly_df(df, name_col, geom_col, val_col, tooltip_fmt=None):
    """I think I can do better than this. I want to just
    convert the geom col to a column of lists
    """

    tooltip_fmt = tooltip_fmt or "{i}: {name}"

    xs = [] 
    ys = []
    cval = []
    tooltip = []

    for i in range(len(df)):
        d1 = df[geom_col].iloc[i]
        clr = df[val_col].iloc[i]
        name = df[name_col].iloc[i]
        ptype, parts = AnyGeom(d1).as_array()

        if ptype == 'MULTIPOLYGON':
            if isinstance(parts, list):
                for part in parts:
                    arr = part[0]
                    xs.append(arr[:,0])
                    ys.append(arr[:,1])
                    cval.append(clr)
                    tooltip.append(tooltip_fmt.format(**locals()))
            else:
                arr = parts
                xs.append(arr[:,0])
                ys.append(arr[:,1])
                cval.append(clr)
                tooltip.append(tooltip_fmt.format(**locals()))
        elif ptype == 'POLYGON':
            if isinstance(parts, list):
                print(f'Polygon {name} at position {i} has a hole. Ignoring for now')
            else:
                arr = parts
                xs.append(arr[:,0])
                ys.append(arr[:,1])
                cval.append(clr)
                tooltip.append(tooltip_fmt.format(**locals()))

    tmp = pd.DataFrame()
    tmp['xs'] = xs 
    tmp['ys'] = ys 
    tmp['val'] = cval 
    tmp['tooltip'] = tooltip
    return tmp
