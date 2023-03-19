from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

from glob import glob 

import frmbase.support as fsupport 
import frmbase.meta as fmeta 
lmap = fsupport.lmap
"""

x Download docs from 
x Convert to text with pdftotext -layout
x Manually remove page headers from each file 
x Read in and convert to csv see parsefarms.bash
o Convert all caps to init caps for 2122
o Produce a grid of num schools in common between each set of files 
o Fox 2021 by using OCR to scan the document 
o Merge with MCAP stuff
"""

def create_master_file():
    pattern = "/home/fergal/data/politics/stusuppnet/farms/*.csv"
    outfn = "farms0623.csv"
    fmeta.save_state(outfn + ".json")

    flist = sorted(glob(pattern))
    #Remove 2021, which is garbled
    flist = list(filter(lambda x: x[-8:-4] != "2021", flist))

    dflist = []
    for f in flist:
        df = pd.read_csv(f)
        df['Year'] = "Y" + f[-8:-4]    
        df['Site_Name'] = df.Site_Name.str.title().str.lstrip().str.rstrip()
        dflist.append(df)
    df = pd.concat(dflist)
    df.to_csv(outfn)
    return df 

def main():

    df = pd.read_csv('farms0623.csv')
    #Check Free + Reduced == Total 
    idx = df.Free + df.Reduced != df.TotalFR
    print(df[idx])


    #Check percentage is correct 
    idx = np.isnan(df.TotalFR)
    print(df[idx])
    idx = np.isnan(df.FRPercent)
    print(df[idx])

    idx = ~ np.isclose(df.TotalFR, .01*(df.Enrollment * df.FRPercent), atol=1)
    print(df[idx])

    #Check each school shows up each time 
    #Elem <--> Elementary is the most common failing, but not the only one
    return df.groupby('Site_Name').Site_Name.count().sort_values()