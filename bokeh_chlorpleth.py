from ipdb import set_trace as idebug 
from bokeh.io import show,save
from bokeh.models import Button, SetValue
import numpy as np 

from bokeh.plotting import figure
from bokeh.models import CustomJS, ColorBar, LinearColorMapper
from bokeh.layouts import row, column
import bokeh.palettes 

from bokeh.models import CustomJS, RadioButtonGroup, ColumnDataSource
from bokeh.transform import linear_cmap


from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmgis.get_geom as fgg 

from bokeh.models import ColumnDataSource, Grid, LinearAxis, MultiPolygons, Plot

from typing import Iterable, Union , List 

def chloropleth(
        fig: figure,
        polygons: Iterable, 
        values : Iterable, 
        tooltips: Iterable[str],
        poly_props:dict,
        palette: Union[List, str] = None,
        vmin:float =None,
        vmax:float =None,
        **kwargs
    ) -> figure :
    """Plot a chloropleth, or heatmap, in Bokeh


    Inputs
    --------
    fig
        A bokeh figure handle 
    polygons
        The shapes to draw. Can be anything from simple polygons to multi-polygons
        with holes. The format is anything that AnyGeom class will accept.
    values
        (list of floats) the numeric value associated with each polygon used
        to choose the colour.
    palette
        Either the string name of a palette (e.g "Viridis7") or a list of
        RGB value as ['#RRGGBB', ...]. Good choices can be found in `bokeh.palettes`

    Optional Inputs
    -----------------
    vmin, vmax
        (floats) The min and max values of the colourmap

    All other values are passed a ColumnDataSource object. I'm not sure
    what will happen with them. Other options should probably have the
    same length as `polygons`.
    
    Todo
    --------
    Currently the function assume a linear colourmap. It would be nice
    to do other normalisations.
    """

    assert len(polygons) == len(values) 
    assert 'colour' not in poly_props

    palette = palette or 'Viridis7'

    clr = apply_linear_colour_map(palette, values.astype(float), vmin, vmax)
    cds = create_cds_from_array(polygons, value=values, colour=clr, tooltip=tooltips, **kwargs) 

    # idebug()
    glyph = MultiPolygons(xs="xs", ys="ys", fill_color='colour', **poly_props)
    handle = fig.add_glyph(cds, glyph)
    return handle 

def apply_linear_colour_map(palette, values, vmin=None, vmax=None):
    if isinstance(palette, str):
        palette = bokeh.palettes.__dict__[palette]

    num = len(palette)
    vmin = vmin or np.min(values)
    vmax = vmax or np.max(values)

    index = ((num-1) * (values-vmin) / (vmax-vmin)).astype(int)
    clr = np.array(palette)[index]
    return clr 


def create_cds_from_array(polygons, **kwargs):
    obj = lmap(lambda x: AnyGeom(x).as_bokeh(), polygons)
    xs = lmap(lambda x: x[0], obj)
    ys = lmap(lambda x: x[1], obj)
    kwargs['xs'] = xs 
    kwargs['ys'] = ys 
    cds = ColumnDataSource(kwargs)
    return cds 

import stio 
def play(df = None):
    if df is None:
        council_fn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
        df = stio.load_council_districts(council_fn)
        return df

    tools = "pan,wheel_zoom,box_zoom,reset,hover"
    fig = figure(
        tools=tools,
        tooltips="@tooltip", 
        frame_height=800, 
        frame_width=800,
        x_range=(-77, -76.25),
        y_range=(39.1, 39.8),
        # title="Draft",
    )

    handle = chloropleth(fig, df.geom, df.DistrictId, 'Viridis8')
    show(fig)
    return handle