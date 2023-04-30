from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

import frmbase.support as fsupport 
import frmplots.plots as fplots

import frmbase.dfpipeline as dfp 
lmap = fsupport.lmap 

import frmbase.fitter.nlsf as nlsf 

"""
Comparing Poverty as measured by FARMS with test scores as measured by MCAP

TODO:
xMCAP school code is sometimes int, sometimes string
o Time series of all schools. Do a weighted average
"""


def main():
    for grade in [3,4,5]:
        combined_plot(grade)
        plt.savefig(f"MCAP_Math_Grade_{grade}_allyears.png")
        plt.pause(1)


def combined_plot(grade): 
    plt.clf()
    for year in [2018, 2019, 2021, 2022]:
        df = _plot_year(year, grade)

    plt.xlabel("Students on Free/Reduced Lunch (%)")
    plt.ylabel(f"Proficient Grade {grade} Math (%)")
    fplots.add_watermark()

    title = f"Baltimore County Schools"
    plt.title(title, fontsize=28)
    plt.legend()


def plot_year(year:int, grade:int):
    plt.clf()
    _plot_year(year, grade) 
    plt.xlabel("Students on Free/Reduced Lunch (%)")
    plt.ylabel(f"Proficient Grade {grade} Math (%)")
    fplots.add_watermark()

    title = f"Baltimore County Schools  (Year starting {year})" 
    plt.title(title)


def _plot_year(year:int, grade:int):
    
    # year = 2019

    #If you change the year you must change the code in 3 places!
    farms = "farms0623.csv"
    farms = load_farms(farms, year)                   

    mcap = "/home/fergal/data/politics/stusuppnet/MCAP/mcap_total.csv"
    mcap = load_mcap(mcap, year, grade)

    df = pd.merge(farms, mcap, left_on='Site_Num', right_on='School_Number')
    df = df.sort_values('FRPercent')
    x = df.FRPercent.values
    y = df.Proficient_Pct.values

    i0 = np.where(df.Site_Name.values == 'Stoneleigh Elementary')[0]
    #Fit a simple model
    pars = [40, -.2, 0]
    fobj = nlsf.Nlsf(x, y, None, param=pars, func=nlsf.nlExp)
    fobj.fit()

    # plt.clf()
    plt.gcf().set_size_inches((12,8))

    # import matplotlib.patheffects as meffect
    # shadow = [meffect.SimplePatchShadow(alpha=1, shadow_rgbFace='grey'), meffect.Normal()]
    clr = 'midnightblue'
    clr = f'C{year-2018}'
    plt.plot(x, y, 'o', color=clr)
    # plt.plot(x[i0], y[i0], 'C2o', ms=14, mec='yellow', mew=2)
    
    xx = np.arange(100)
    plt.plot(xx, fobj.getBestFitModel(xx), '-', color=clr, lw=4, label=year)

    plt.xlim(0, 100)
    plt.ylim(0, 100)
    return df 



def load_farms(fn, year):
    """Load FARMS data for a single year"""
    cols = ['Site_Num', 'Site_Name', 'FRPercent', 'Year', 'CEP']

    farms_year = year -2000
    farms_year = f"Y{farms_year}{farms_year+1}"
    pipeline = [
        dfp.Load(fn, index_col=0),
        dfp.Filter(f"Year == '{farms_year}'"),
        dfp.AssertNotEmpty(),
        dfp.SelectCol(*cols)
    ]
    farms = dfp.runPipeline(pipeline)
    return farms 


def load_mcap(fn:str, year:int, grade:int):
    cols = "School_Number School_Name Assessment Proficient_Pct".split()              
    pipeline = [
        dfp.Load(fn, index_col=0),
        dfp.Filter(f'Academic_Year == {year}'),
        dfp.Filter('Tested_Count > 50'),
        dfp.SelectCol(*cols),
        dfp.Filter(f"Assessment == 'Mathematics Grade {grade}'"),
        # dfp.Filter(f"Assessment == 'English/Language Arts Grade {grade}'"),
        dfp.AssertNotEmpty(),
        dfp.SetCol('School_Number', 'School_Number.astype(float).astype(int)'),
    ]

    mcap = dfp.runPipeline(pipeline)
    return mcap

import matplotlib.ticker as mticker
def plot_single_school_mcap(school_name):
    mcap = "/home/fergal/data/politics/stusuppnet/MCAP/mcap_total.csv"
    cols = "School_Number School_Name Assessment Proficient_Pct".split()              

    
    pipeline = [
        dfp.Load(mcap, index_col=0),
        dfp.Filter(f'School_Name == "{school_name}"'),
        dfp.Filter("Grade > 0"),
        dfp.AssertNotEmpty(),
    ]
    ses = dfp.runPipeline(pipeline)


    func = lambda df: plt.plot(df.Academic_Year, df.Proficient_Pct, 'o-', label=gen_label(df.name))
    plt.clf(); 
    plt.gcf().set_size_inches((12,8))
    ses. \
        sort_values('Academic_Year'). \
        groupby(['Grade', 'Subject']). \
        apply(func); 
    plt.legend()

    plt.ylim(0, 100)
    plt.xlabel("Year")
    plt.ylabel("Percent Proficient")
    plt.title(school_name)
    plt.gca().xaxis.set_major_locator(mticker.MaxNLocator(5))
    plt.gca().xaxis.set_major_locator(mticker.MaxNLocator(5))
    plt.gca().xaxis.set_tick_params(which='minor', length=0)
    fplots.add_watermark()

    school_name = "_".join(school_name.split())
    plt.savefig(f'Single_School_ts{school_name}.png')

def gen_label(tup):
    return f"Grade {tup[0]} {tup[1]}"