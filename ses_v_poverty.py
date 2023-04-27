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
Plot the evolution of SES in the scores/poverty space

Puts the low SES score for SES in 2022 in perspective
"""


def main():

    pipeline = [
        dfp.Load("farms0623.csv", index_col=0),
        dfp.Filter('Site_Num == 905'),
        dfp.SetCol('IntYear', '2000 + Year.str[1:3].astype(int)'),
    ]

    farms = dfp.runPipeline(pipeline)
    # return farms

    grade = 3 
    mcap = "/home/fergal/data/politics/stusuppnet/MCAP/mcap_total.csv"
    cols = "School_Number School_Name Academic_Year Assessment Proficient_Pct".split()              
    pipeline = [
        dfp.Load(mcap, index_col=0),
        dfp.Filter('Tested_Count > 50'),
        dfp.SelectCol(*cols),
        dfp.Filter(f"Assessment == 'Mathematics Grade {grade}'"),
        dfp.Filter("School_Number == 905"),
        dfp.AssertNotEmpty(),
        dfp.SetCol('School_Number', 'School_Number.astype(float).astype(int)'),
    ]

    mcap = dfp.runPipeline(pipeline)

    df = pd.merge(farms, mcap, left_on='IntYear', right_on='Academic_Year')

    plt.clf()
    plt.plot(df.FRPercent.values, df.Proficient_Pct.values, '-', color='lightgrey')
    # plt.plot(df.FRPercent.values, df.Proficient_Pct.values, 'o', ms=18, color='midnightblue')

    for i, row in df.iterrows():
        sym = f'C{row.IntYear-2018}o'

        plt.plot(row.FRPercent, row.Proficient_Pct, sym, ms=18)
        plt.text(row.FRPercent, row.Proficient_Pct, f"  {row.IntYear}", fontsize=26)

    plt.xlabel("Students on Free/Reduced Lunch (%)")
    plt.ylabel(f"Proficient Grade {grade} Math (%)")
    fplots.add_watermark()

    title = f"Baltimore County Schools"
    plt.title(title, fontsize=28)
    plt.xlim(12, 22)


    # plt.scatter(df.FRPercent.values, df.Proficient_Pct.values, c=df.IntYear.values)
    # plt.colorbar()
    return df 