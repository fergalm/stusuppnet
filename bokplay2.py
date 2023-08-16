from ipdb import set_trace as idebug 
from bokeh.io import show,save
import numpy as np 

from bokeh.plotting import figure, output_file
from bokeh.models import CustomJS, ColorBar, LinearColorMapper, BasicTicker, Label, Div, Spacer, HoverTool
from bokeh.layouts import row, column
import bokeh.palettes 

from bokeh.models import CustomJS, RadioButtonGroup, SetValue
from bokeh.events import MouseEnter, MouseLeave

from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmbok.chloropleth as fbc 
import frmbok.roads as roads


#import bokeh_chlorpleth as bc 
import stio

"""
Todo 

x SNAP DC data 
x Fix colorbar range 
o Bigger buttons
x Better defaults
x Fix 42B
o no tooltip for roads 
x Legend label 
o Turn on council
o 
o Make controls bigger
o Add map background
x Add interaction for political districts
x Add highlights for political districts
x Overlay roads 
x Fix elementary heat map
x Add tooltips 
x Add multiline for political districts 
x Add colorbar
x Change cmap 
x Plot polygons with holes
"""

import pandas as pd 
def main():
    outfn = "snap.html"
    council_fn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    leg_fn = '/home/fergal/data/elections/shapefiles/md_lege_districts/2022/Maryland_Legislative_Districts_2022.kml'
    cong_fn = "/home/fergal/data/elections/shapefiles/congressional/Congress_2022/US_Congressional_Districts_2022.kml"

    output_file(outfn)

    # alicefn = "alice.csv"    
    # farmsfn = "farms0623.csv"
    povertyfn = "snap/snap.xlsx"
    loader = stio.load_alice_data
    loader = stio.alt_load_farms_data
    loader = stio.load_dc_data
    elem = loader(povertyfn, "Elementary")
    mid  = loader(povertyfn, "Middle")
    high = loader(povertyfn, "High")
    assert len(elem) > 0

    council = stio.load_council_districts(council_fn)
    leg = stio.load_leg_districts(leg_fn)
    cong = stio.load_cong_districts(cong_fn)

    tools = "pan,wheel_zoom,reset"
    fig = figure(
        tools=tools,
        frame_height=800, 
        frame_width=800,
        x_range=(-77, -76.25),
        y_range=(39.1, 39.8),
        toolbar_location='above',
    )

    label = Label(
        x=400, y=740,
        x_units='data', y_units='data', 
        text="EMPTY TEXT", 
        text_font_size="24px",
        background_fill_color='#EEEEDD'
    )
 

    palette = bokeh.palettes.YlOrRd4[::-1]  #Reverse order
    fmt = "{Name}: {Value:.0f}%"
    opts = {
        'palette': palette,
        'tooltip_fmt': fmt,
        'val_col': 'Value',

    }
    plat_elem = chloropleth_geom_df(fig, elem, **opts)
    plat_mid  = chloropleth_geom_df(fig, mid,  **opts)
    plat_high = chloropleth_geom_df(fig, high, **opts)
    plat_elem.visible = False
    plat_mid.visible= False

    sch_choice = RadioButtonGroup(labels="Elem Middle High".split(), active=2, align="center")
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

    #Do this before showing district lines 
    roads.plot_interstate(fig, annotate=True)

    fmt = "District {DistrictId}"
    # opts = {'line_color':'navy', 'tooltip_fmt':fmt}
    opts = {'line_color':'navy', 'tooltip_fmt':None}
    
    # This is where we plot geometry outlines
    plat_council = fbc.plot_geometry_outlines(fig, council, **opts)
    plat_leg = fbc.plot_geometry_outlines(fig, leg, None)
    plat_cong = fbc.plot_geometry_outlines(fig, cong, None)

    plat_council.visible = False 
    plat_leg.visible = False
    plat_cong.visible = False 

    leg_choice = RadioButtonGroup(labels="None Council Leg Cong".split(), active=0, align="center")
    callback = CustomJS(
        args=dict(
            p1=plat_council, 
            p2=plat_leg, 
            p3=plat_cong, 
            leg_choice=leg_choice,
            label=label,
        ),
        code="""
            label.visible = (leg_choice.active > 0);
            p1.visible = (leg_choice.active==1);
            p2.visible = (leg_choice.active==2);
            p3.visible = (leg_choice.active==3);
            console.log('radio_button_group: active=' + leg_choice.active, this.toString());
    """
    )
    leg_choice.js_on_event("button_click", callback)

    add_political_callout(fig, label, plat_council, plat_leg, plat_cong)
    cb = create_colour_bar(fig, palette, 10, 90)
    layout = create_layout(sch_choice, leg_choice, fig, cb)

    #Show tooltips for heatmap layers only
    hover = HoverTool()
    hover.tooltips = "@tooltip"
    hover.renderers = [plat_council, plat_leg, plat_cong, plat_elem, plat_mid, plat_high]
    fig.add_tools(hover)

    save(layout, outfn)


import frmplots.plotstyle as fps 
def create_layout(sch_choice, leg_choice, fig, cb):

    template = "<FONT size='12'>%s</FONT>"
    sch = column(
        Div(text=template % "School Type", align="center"),
        sch_choice,
        sizing_mode="stretch_width",
    )

    leg = column(
        Div(text=template % "Political Districts", align="center"),
        leg_choice,
    )

    controls = row(sch, leg, sizing_mode="stretch_width")
    note = Div(text="<P>Note: School catchment areas typically overlap with two or more political districts</P>")
    
    watermark = fps.create_watermark_text(0)
    wmark = Div(text=watermark)

    layout = column(controls, row(fig, cb), note, wmark)

    return layout


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
    # handle.js_on_event(MouseEnter, CustomJS())
    return handle 



def chloropleth_geom_df(fig, df, geom_col='geom', val_col='val', tooltip_fmt=None, **kwargs):
    """Plot outlines of every shape in df

    Deals with multi polygons, but not with holes in polygons

    kwargs are passed to p.line()

    Is this the best way to implement this? Probably not.
    """

    tooltip_fmt = tooltip_fmt or " "

    palette = kwargs.pop('palette', 'YlOrRd7')
    tooltips = df.apply(lambda row: tooltip_fmt.format(**row), axis=1)
    # idebug()

    poly_props = {
        'line_color': kwargs.get('line_color', None) or 'white',
        'line_width': kwargs.get('line_width', None) or 2
    }

    handle = fbc.chloropleth(
        fig, 
        df[geom_col], 
        df[val_col],
        tooltips,
        poly_props,
        palette=palette, 
    )
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


def create_colour_bar(fig, palette, low, high):
    mapper = LinearColorMapper(palette=palette, low=low, high=high)
    color_bar = ColorBar(
        color_mapper=mapper, 
        label_standoff=12,
        # ticker=BasicTicker(min_interval=30, max_interval=30),)
        ticker=BasicTicker(desired_num_ticks=7),
    )
    print(fig.height)
    color_bar_plot = figure(
        title="Eligible for SNAP (%)",
        title_location='right',
        height=fig.frame_height +11,
        width=120,
        toolbar_location=None,
        min_border=0,
    )
    color_bar_plot.add_layout(color_bar, 'right')
    color_bar_plot.title.align="center"
    color_bar_plot.title.text_font_size = '16pt'

    return color_bar_plot


def add_political_callout(fig, label, plat_council, plat_leg, plat_cong):
    """Add a label to indicate the political district under the mouse"""

    text = ""
    callback = CustomJS(
        args=dict(
            label=label,
            p1=plat_council, 
            p2=plat_leg, 
            p3=plat_cong, 
        ),
        code="""
            console.log("In poltical callout");
            var cds = null;
            if (p1.visible)
            {   cds = p1.data_source;
            }
            else if (p2.visible)
            {   cds = p2.data_source;
            }
            else if (p3.visible)
            {   cds = p3.data_source;
            }
            else
            {   return;
            }
            console.log("CDS selected");

            var indices = cds.inspected.indices;
            console.log(indices)
            if (indices.length > 0)
            {
                console.log("Object selected");
                var index = indices[0];
                var text = cds.data['DistrictId'][index];
                label.text= 'District ' + text;
                label.x = cds.data['cent_lng'][index];
                label.y = cds.data['cent_lat'][index];
                console.log(label.x, label.y)
            }
        """
    )
            # //assert (cds !== null);

    fig.add_layout(label)
    fig.js_on_event('mousemove',callback)
    return label
