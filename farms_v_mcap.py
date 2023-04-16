from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

import frmbase.support as fsupport 
import frmplots.plots as fplots
import frmbase.meta as fmeta 
import frmbase.dfpipeline as dfp 
lmap = fsupport.lmap 

from frmpolitics.census import CensusQuery, TigerQueryAcs
from frmgis.geomcollect import GeomCollection
import frmgis.get_geom as fgg 

from frmgis.anygeom import AnyGeom
import frmgis.plots as fgplots 
import frmgis.mapoverlay as fmo
import getincome as gi 
import frmgis.roads as roads 

import frmbase.fitter.lsf as lsf 
import frmbase.fitter.nlsf as nlsf 

"""
Comparing Poverty as measured by FARMS with test scores as measured by MCAP
"""

def main():
    
    #If you change the year you must change the code in 3 places!
    title = "Bal. County 2021/22 School Year"
    cols = ['Site_Num', 'Site_Name', 'FRPercent', 'Year', 'CEP']
    pipeline = [
        dfp.Load("farms0623.csv", index_col=0),
        # dfp.Filter("school_type == 'Elementary'"),
        dfp.Filter("Year == 'Y2122'"),
        dfp.AssertNotEmpty(),
        dfp.SelectCol(*cols)
    ]
    farms = dfp.runPipeline(pipeline)
    # return farms
                   

    mcap = "/home/fergal/data/politics/stusuppnet/MCAP/mcap_total.csv"
    cols = "School_Number School_Name Assessment Proficient_Pct".split()              
    pipeline = [
        dfp.Load(mcap, index_col=0),
        dfp.Filter('Academic_Year == 2021'),
        dfp.Filter('Tested_Count > 50'),
        dfp.SelectCol(*cols),
        dfp.Filter("Assessment == 'Mathematics Grade 3'"),
        dfp.SetCol('School_Number', 'School_Number.astype(float).astype(int)'),
    ]

    mcap = dfp.runPipeline(pipeline)

    df = pd.merge(farms, mcap, left_on='Site_Num', right_on='School_Number')
    df = df.sort_values('FRPercent')
    x = df.FRPercent.values
    y = df.Proficient_Pct.values

    i0 = np.where(df.Site_Name.values == 'Stoneleigh Elementary')[0]
    #Fit a simple model
    pars = [40, -.2, 0]
    fobj = nlsf.Nlsf(x, y, None, param=pars, func=nlsf.nlExp)
    fobj.fit()

    plt.clf()
    plt.gcf().set_size_inches((12,8))

    # import matplotlib.patheffects as meffect
    # shadow = [meffect.SimplePatchShadow(alpha=1, shadow_rgbFace='grey'), meffect.Normal()]
    # plt.plot(x, y, 'ko', path_effects=shadow)
    plt.plot(x, y, 'o', color='midnightblue')
    # plt.plot(x[i0], y[i0], 'C2o', ms=14, mec='yellow', mew=2)
    
    plt.plot(x, fobj.getBestFitModel(), 'C1-', lw=4)

    plt.xlabel("Students on Free/Reduced Lunch (%)")
    plt.ylabel("Proficient 3rd Grade Math (%)")
    fplots.add_watermark()
    plt.xlim(0, 100)
    plt.title(title)

    return df 