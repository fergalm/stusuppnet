from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

from glob import glob 

import frmbase.support as fsupport 
import frmbase.meta as fmeta 
lmap = fsupport.lmap 

import frmplots.plots as fplots
from frmpolitics.census import CensusQuery, TigerQueryAcs
from frmgis.geomcollect import GeomCollection
import frmgis.get_geom as fgg 
import frmgis.plots as fgplots 

import getincome 

"""

Create 2 plots of income, one tesslated by blockgroup, the other by highschool
"""


def main():

    axl = (-77.03517201704334, -76.11767641144938, 39.17666732671425, 39.74419986081214)
    cmap = plt.cm.YlOrRd

    plt.figure('hs')
    plt.clf()
    alice = pd.read_csv('alice_high.csv', index_col=0)
    _, cb = fgplots.chloropleth(alice.geom, alice.Alice_Percent, cmap=cmap, ec='w')
    cb.set_label("ALICE (Percent)")
    plt.title("ALICE by High School")
    plt.axis(axl)
    fplots.add_watermark(loc='bottom')
    plt.savefig('bgorhs_hs.png')

    plt.figure('bg')
    plt.clf()
    inc = pd.read_csv('income.csv', index_col=0)
    inc = getincome.compute_alice_frac(inc)
    _, cb = fgplots.chloropleth(inc.geom, inc.Percent_Alice, cmap=cmap)
    cb.set_label("ALICE (Percent)")
    plt.title("ALICE by Block Group")    
    plt.axis(axl)
    fplots.add_watermark(loc='bottom')
    plt.savefig('bgorhs_bg.png')