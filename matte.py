from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

from frmgis.anygeom import AnyGeom 
import frmgis.mapoverlay as fmo 
import frmgis.plots as fgplots 
import frmgis.get_geom as fgg 

from matplotlib.patches import PathPatch
from matplotlib.path import Path



def example():
    distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    dist = fgg.load_geoms_as_df(distfn)

    geom = dist.geom.iloc[2]

    plt.clf()
    for g in dist.geom:
        fgplots.plot_shape(g, '--')
    # matte = make_matte_for_polygon(geom, bbox='axis', color='w', alpha=.8)
    # matte = make_matte_for_multipolygon(geom, bbox='axis')
    matte = make_matte(geom, 'axis', color='C0', alpha=.8)
    plt.gca().add_patch(matte)


def make_matte(poly, bbox=None, **kwargs):
    """Create a matte, i.e a large shape with the requsted shape cut out

    Can be useful to cut a shape out of a larger shape when plotting
    Inputs
    ----------
    poly
        AnyGeom The shape to cut out. Must be a polygon or a multipolygon.
        Any holes in the geometry will be ignored.
    bbox   
        The bounding box. A rectange from which the shape is cut out of.
        This can be
        An AnyGeom
            Will use this geometry
        **None**
            Use the envelope of `poly`
        "axis"
            Will use the extent of the current plotting window in plot
            coordinates
    reverse
        (boolean, default false). If the matte acts screwy, set this to True.
        It might help.

    Any other arguments are passed to the `matplotlib.patches.PathPatch` class 
    
    Returns
    ---------
    An matplotlib patch object 


    Todo
    -----
    * Matting sometimes fails for multi geoms, possibly when they've been
    formed by the union of smaller geometries
    * Properly account for holes

    """

    if 'zorder' not in kwargs:
        kwargs['zorder'] = 9999 

    bbox_geom = getBBoxGeom(bbox, poly)

    gtype, poly = AnyGeom(poly).as_array()

    if gtype.lower() == 'polygon':
        return make_matte_for_polygon(bbox_geom, poly, **kwargs)
    elif gtype.lower() == 'multipolygon':
        return make_matte_for_multipolygon(bbox_geom, poly, **kwargs)
    else:
        raise ValueError
    

def make_matte_for_multipolygon(bbox_geom, poly_arr, bbox=None, **kwargs):
    reverse = kwargs.pop('reverse', False)
    bbox = bbox_geom
    parts = poly_arr

    #coords is a list with a numpy array inside
    coords = [AnyGeom(bbox).as_array()[1][:,:2]]
    codes = [Path.LINETO] * len(coords[0])
    codes[0] = Path.MOVETO

    # co_coords = []
    # co_codes = []
    # parts = AnyGeom(poly).as_array()[1]
    for obj in parts:
        arr = obj[0]

        if reverse:
            arr = arr[::-1]
        coords.append(arr)
        co_code = [Path.LINETO] * len(arr) 
        co_code[0] = Path.MOVETO
        codes += co_code

    #Combine envelope and individual elements
    coords = np.concatenate(coords)
    codes[-1] = Path.CLOSEPOLY

    path = Path(coords, codes)
    patch = PathPatch(path, **kwargs)
    return patch 


def make_matte_for_polygon(bbox_geom, poly_arr, bbox=None, **kwargs):
    reverse = kwargs.pop('reverse', False)

    env_coords = AnyGeom(bbox_geom).as_array()[1][:,:2]
    env_code = [Path.LINETO] * len(env_coords)
    env_code[0] = Path.MOVETO

    co_coords = poly_arr
    if reverse:
        co_coords = co_coords[::-1]


    co_code = [Path.LINETO] * len(co_coords)
    co_code[0] = Path.MOVETO
    co_code[-1] = Path.CLOSEPOLY

    coords = np.concatenate([env_coords, co_coords])
    code = env_code + co_code
    path = Path(coords, code)
    patch = PathPatch(path, **kwargs)
    
    return patch     
    

def getBBoxGeom(bbox, geom):
    if bbox is None:
        bbox = getGeomEnvelopeAsGeom(geom)
    elif bbox == 'axis':
        axl = plt.axis()
        bbox = getEnvelopeAsGeometry(axl)
    return bbox 


def getGeomEnvelopeAsGeom(geom):
    """Get the envelope of a geometry as a polygon

    GDAL's GetEnvelope() function returns a 4-tuple of corner coordinates.
    I frequently want to convert those points to a rectangle, and store
    it in a geometry.

    Inputs
    ---------
    geom
        A gdal geometry object


    Returns
    ---------
    A gdal geometry object
    """

    return getEnvelopeAsGeometry(geom.GetEnvelope())


def getEnvelopeAsGeometry(env):
    x0, x1, y0, y1 = env

    data = [ [x0, y0],
             [x0, y1],
             [x1, y1],
             [x1, y0],
             [x0, y0]
           ]

#    debug()
    env = AnyGeom(data, "polygon").as_geometry()
    return env