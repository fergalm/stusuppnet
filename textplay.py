from ipdb import set_trace as idebug 
from typing import Iterable
from osgeo import ogr
import numpy as np

from bokeh.models import CustomJS,  Label, HoverTool, MultiPolygons, ColumnDataSource
from bokeh.plotting import figure
from bokeh.io import show


def main():
    tools = "pan,wheel_zoom,box_zoom,reset"
    fig = figure(
        tools=tools,
        tooltips="@tooltip", 
    )

    text = "This is some text"
    label = Label(x=200, y=10,x_units='screen', y_units='screen', text=text)
    fig.add_layout(label)

    wkt1 = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
    wkt2= "POLYGON ((75 10, 85 45, 55 40, 50 20, 75 10), (60 30, 75 35, 70 20, 60 30))"
    handle = plot_geometry_outlines(fig, [wkt1, wkt2], ["WKT 1", " WKT 2"])

    callback = CustomJS(
        args=dict(
            label=label,
            polys=handle, 
        ),
        code="""
            var cds = polys.data_source;
            var selected = cds.inspected.indices;
            console.log(selected)
            if (selected.length > 0)
            {
                console.log("Object selected")
                var index = selected[0];
                var text = cds.data['tooltip'][index];
                label.text= text;
            }
        """
    )

    fig.js_on_event('mousemove',callback)

    show(fig)





def plot_geometry_outlines(fig, polygons: Iterable, tooltips: Iterable[str], **kwargs):
    assert len(polygons) == len(tooltips)

    #defaults
    props = {
        'line_color': '#000000',    
    }
    props.update(kwargs)

    #Create a column data source in the format expected by multipolygon
    #This function is a detail, not relevant to the question, I think
    cds = create_cds_from_array(polygons, tooltip=tooltips) 

    glyph = MultiPolygons(xs="xs", ys="ys", **props)
    handle = fig.add_glyph(cds, glyph)
    return handle 



def create_cds_from_array(polygons, **kwargs):
    lmap = lambda x, y: list(map(x, y))

    obj = lmap(lambda x: as_bokeh(x), polygons)
    xs = lmap(lambda x: x[0], obj)
    ys = lmap(lambda x: x[1], obj)
    kwargs['xs'] = xs
    kwargs['ys'] = ys
    cds = ColumnDataSource(kwargs)
    return cds 


def as_bokeh(obj):
    obj = ogr.CreateGeometryFromWkt(obj)
    lng = ogrGeometryToNestedList(obj, 0)
    lat = ogrGeometryToNestedList(obj, 1)
    return lng, lat 


def ogrGeometryToNestedList(geometry, dim):
    """Converter used for Bokeh

    Converts one dimension (lng or lat) of a polygon-type geometry to
    a nested list in a format bokeh will like
    """

    out = []

    name = geometry.GetGeometryName()
    if name == 'MULTIPOLYGON':
        for i in range(geometry.GetGeometryCount()):
            poly = geometry.GetGeometryRef(i)
            out.extend(ogrGeometryToNestedList(poly, dim))
    elif name == 'POLYGON':
        ringlist = []
        for i in range(geometry.GetGeometryCount()):
            ring = geometry.GetGeometryRef(i)
            points = np.atleast_2d(ring.GetPoints())
            points = points[:, dim]
            ringlist.append( points.tolist())
        out.append(ringlist)
    else:
        raise ValueError("Currently only polygons and multipolygons supported for Bokeh ")
    
    return out 
