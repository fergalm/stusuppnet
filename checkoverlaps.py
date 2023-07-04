from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

import frmbase.support as fsupport 
import frmplots.plots as fplots
import frmbase.meta as fmeta 
lmap = fsupport.lmap 

from frmpolitics.census import CensusQuery, TigerQueryAcs
from frmgis.geomcollect import GeomCollection
import frmgis.get_geom as fgg 

from frmgis.anygeom import AnyGeom
import frmgis.plots as fgplots 
import frmgis.mapoverlay as fmo
import getincome as gi 


"""Checking my overlap calculation make sense
"""

def main():
    alice = pd.read_csv('tmp-alice.csv')
    pattern = '/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    sch = gi.load_all_schools(pattern)
    overlap = pd.read_csv('overlap.csv', index_col=0)

    # name = 'Lansdowne MS'
    # name = 'Loch Raven Academy'
    name = 'Dumbarton MS'
    sch = sch[sch.Name == name]
    assert len(sch) > 0
    sch_geom = sch.geom.iloc[0]

    idx = overlap[name] > 0.02
    overlap = overlap[idx][name]

    bg = pd.merge(overlap, alice, left_index=True, right_on='fips')
    print(bg)

    plt.clf()
    fgplots.plot_shape(sch_geom, 'k-', lw=4)

    for num_alice, num_house, geom in zip(bg['Num_Alice'], bg['Num_Households'], bg.geom):
        fgplots.plot_shape(geom, 'r-', lw=1)
        cent = AnyGeom(geom).as_geometry().Centroid()
        x, y = cent.GetX(), cent.GetY()

        if num_house > 0:
            text = "%.0f%%\n(%i)" %(num_alice/num_house*100, num_house)
            plt.text(x, y, text, fontsize=8, ha="center", va="center")
    _, cb =fgplots.chloropleth(bg.geom, bg.Percent_Alice, cmap=plt.cm.RdYlGn_r, alpha=.3, vmin=10, vmax=60)
    cb.set_label("Percent Alice")

    fplots.add_watermark(loc='bottom')
    #YlOrRd

    fmo.drawMap()