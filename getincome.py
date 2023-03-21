from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 

from glob import glob 

import frmbase.support as fsupport 
import frmbase.meta as fmeta 
lmap = fsupport.lmap 

from frmpolitics.census import CensusQuery, TigerQueryAcs

def main():
    """Download block-group level data on income in Baltimore County"""

    survey = "acs"
    table = "acs5"
    year = 2021
    county = 24005     #24005 is the FIPS code of Baltimore County

    #List of cols taken from 
    #https://api.census.gov/data/2021/acs/acs5/groups/B19001.html
    
    mapper = {
        'B19001_001E': 'Num_Households',
        'B19001_002E': 'Household_Inc_0k_10k',
        'B19001_003E': 'Household_Inc_10k_15k',
        'B19001_004E': 'Household_Inc_15k_20k',
        'B19001_005E': 'Household_Inc_20k_25k',
        'B19001_006E': 'Household_Inc_25k_30k',
        'B19001_007E': 'Household_Inc_30k_35k',
        'B19001_008E': 'Household_Inc_35k_40k',
        'B19001_009E': 'Household_Inc_40k_45k',
        'B19001_010E': 'Household_Inc_45k_50k',
        'B19001_011E': 'Household_Inc_50k_60k',
        'B19001_012E': 'Household_Inc_60k_75k',
        'B19001_013E': 'Household_Inc_75k_100k',
        'B19001_014E': 'Household_Inc_100k_125k',
        'B19001_015E': 'Household_Inc_125k_150k',
        'B19001_016E': 'Household_Inc_150k_200k',
        'B19001_017E': 'Household_Inc_200k',
    }
    outfn = "income.csv"
    fmeta.save_state(outfn + ".json")
   
    cols = list(mapper.keys())
   
    cli = CensusQuery()
    df = cli.query_block_group(year, survey, table,  county, cols)
    df = df.rename(mapper, axis=1)

    cache_path = "/home/fergal/data/elections/shapefiles/censusblockgroups"
    tq = TigerQueryAcs(cache_path)
    geoms = tq.query_block_group(year, county)
    geoms = geoms[ ['GEOID', 'geom'] ].reset_index(drop=True)

    df = pd.merge(df, geoms, left_on='fips', right_on='GEOID')
    df.to_csv(outfn)
    return df
    

def compute_alice_frac(df):
    """Compute fraction of population that are ALICE:
    Asset Limited, Income Constrained, Unemployed

    We define ALICE as household income < 50k/yr
    """

    termA = \
        df.Household_Inc_0k_10k.astype(int) + \
        df.Household_Inc_10k_15k.astype(int) + \
        df.Household_Inc_15k_20k.astype(int) + \
        df.Household_Inc_20k_25k.astype(int) + \
        df.Household_Inc_25k_30k.astype(int) + \
        df.Household_Inc_30k_35k.astype(int) + \
        df.Household_Inc_35k_40k.astype(int) + \
        df.Household_Inc_40k_45k.astype(int) + \
        df.Household_Inc_45k_50k.astype(int) 
    
    termB = \
        df.Household_Inc_50k_60k.astype(int) + \
        df.Household_Inc_60k_75k.astype(int) + \
        df.Household_Inc_75k_100k.astype(int)  + \
        df.Household_Inc_100k_125k.astype(int)  + \
        df.Household_Inc_125k_150k.astype(int)  + \
        df.Household_Inc_150k_200k.astype(int)  + \
        df.Household_Inc_200k.astype(int)      
    
    out = pd.DataFrame()
    out['Num_Household'] = df.Num_Household
    out['fips'] = df.fips 
    out['Num_Alice'] = termA 
    out['Percent_Alice'] = termA / (termA + termB)
    out['geom'] = geom
    return out 


