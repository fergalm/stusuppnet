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
import frmgis.roads as roads 

"""
Compare maps for Alice levels and income
"""


def main():
    alice = pd.read_csv("alice.csv", index_col = 0)
    alice = alice[alice.school_type == 'High']

    codes = alice[ ["CODE", "geom"] ]

    # idebug()
    farms = pd.read_csv("farms0623.csv", index_col=0)
    farms = pd.merge(farms, codes, left_on="Site_Num", right_on="CODE")
    year = 'Y2122'
    assert year in set(farms.Year)
    farms = farms[ farms.Year == year]
    assert len(farms) > 0
    print(farms.iloc[0])

    opts = {
        'vmin': 0,
        'vmax': 80,
        'ec': 'w',
        'lw': 2,
        'cmap': plt.cm.YlOrRd,
    }
    axl = [-76.926, -76.26, 39.1, 39.8]
    plt.figure(1)
    plt.clf()
    plt.subplot(121)
    fgplots.chloropleth(alice.geom, alice.Alice_Percent, **opts)
    polish(axl)
    plt.title("ALICE Percent")

    plt.subplot(122)
    cmap = plt.cm.YlOrRd
    fgplots.chloropleth(farms.geom, farms.FRPercent, **opts)
    polish(axl)
    plt.title("FARMS Percent")
    fplots.add_watermark(loc='bottom')
    return alice, farms


def polish(axl):
    plt.axis(axl)
    fmo.drawMap(zoom_delta=-2)
    roads.plot_interstate(lw=2)
    ax = plt.gca()
    ax.xaxis.set_ticks([])
    ax.yaxis.set_ticks([])

