from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np

import frmgis.geomcollect as fgc 
import frmbase.meta as fmeta 



import itertools
import stio 


def main(council=None):
    """
    Make a html-able table of each school and the districts
    it overlaps with
    """

    council_fn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    leg_fn = '/home/fergal/data/elections/shapefiles/md_lege_districts/2022/Maryland_Legislative_Districts_2022.kml'
    cong_fn = "/home/fergal/data/elections/shapefiles/congressional/Congress_2022/US_Congressional_Districts_2022.kml"
    schools_data = "alice.csv"
    outfile = "district_table.csv"
    fmeta.save_state(outfile + ".json")

    cong = stio.load_cong_districts(cong_fn)
    leg = stio.load_leg_districts(leg_fn)
    if council is None:   
        council = stio.load_council_districts(council_fn)
 
    alice = pd.read_csv(schools_data, index_col=0)
    gc = fgc.GeomCollection(alice, "Name", "geom")


    council = create_table(gc, council, "Council")
    cong = create_table(gc, cong, "Congressional")
    leg  = create_table(gc, leg, "Legislative")

    df = funny_merge(cong, leg, "School")
    df = funny_merge(df, council, "School")
    df.to_csv(outfile)
    return df

def create_table(sch_gc, pol, district_type):

    overlap = sch_gc.measure_overlap_with_df(pol, "DistrictId", "geom")

    #Cull out minor overlaps
    idx = (overlap < .05) | overlap.isna()
    overlap[idx] = 0

    out = []
    for c in overlap.columns:
        df = overlap[overlap[c] > 0]
        tups = itertools.product(df.index, [c])
        out.extend(tups)
    
    out = pd.DataFrame(out, columns=f"School {district_type}".split())
    return out
  
        


def funny_merge(df1, df2, on):
    """Merges two tables in a unique way

    Let `on` be the common key between df1 and df2, with
    df[on] being non-unique (i.e there may be duplicate
    values in df[on]).

    Suppose key 'foo' appears 4 times in df1 and 2 times
    in df2. The key foo will appear 4 times in the output.
    All the columns of df1 will appear in the output, as
    will all columns of df2. For key "foo" the entries
    for the columns of df2 for two of the rows will be Nan.::
    
        foo val11 val21
        foo val12 val22
        foo val13  Nan
        foo val14  Nan

    """

    gr1 = df1.groupby(on)
    gr2 = df2.groupby(on)
    count1 = gr1.count()
    count2 = gr2.count()


    # idebug()
    # count1 = count1[count1.columns[-1]]
    # count2 = count2[count2.columns[-1]]
    count1 = count1.max(axis=1)
    count2 = count2.max(axis=1)
    
    count = count1.copy()
    count[count2 > count1] = count2


    cols1 = set(df1.columns) - set([on])
    cols2 = set(df2.columns) - set([on])

    dflist = []
    for i in range(len(count)):
        name = count.index[i] 
        # if name == "Charlesmont ES":
        #     idebug()

        tmp = pd.DataFrame()
        tmp['drop'] = np.arange(int(count.iloc[i]))
        tmp[on] = name 

        c1 = int(count1[name])
        c2 = int(count2[name])
        # c1 = int(count1.iloc[i])
        # c2 = int(count2.iloc[i])
        # idebug()
        tmp.loc[ :c1-1, cols1] = gr1.get_group(name)[cols1].values
        tmp.loc[ :c2-1, cols2] = gr2.get_group(name)[cols2].values

        tmp = tmp.drop('drop', axis=1)
        dflist.append(tmp)
    return pd.concat(dflist)