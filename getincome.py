from ipdb import set_trace as idebug 
import pandas as pd 

import frmbase.support as fsupport 
import frmbase.meta as fmeta 
lmap = fsupport.lmap 

from frmpolitics.census import CensusQuery, TigerQueryAcs
from frmgis.geomcollect import GeomCollection
import frmgis.get_geom as fgg 

def main():
    """Compute fraction of ALICE household in school catchment area

    ALICE stands for Asset Limited, Income Constrained, and Employed.
    For our purposes we define a household as ALICE if its census reported
    income is <$50k/yr.

    We query the census for number of households in each employment bracket,
    for each block group, then added up all the block groups in a school district.
    A blockgroup partially within a school district is apportioned to that 
    school district in proportion to the fraction of its area inside the 
    school distrct.

    Note that some of the district 7 blockgroups are underweighted because 
    some of their area is listed as being in the bay. I should tidy that up.
    """

    outfn = "alice.csv"
    incomefile = "income.csv"
    pattern = '/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    fmeta.save_state(outfn +".json")

    sch = load_all_schools(pattern)
    sch = sch.reset_index(drop=True)

    # bg = query_census_for_income()
    bg = pd.read_csv(incomefile)
    alice = compute_alice_frac(bg)
    gc = GeomCollection(bg, 'fips')

    overlap = gc.measure_overlap_with_df(sch, name_col='Name')
    df = pd.merge(alice, overlap, left_on='fips', right_index=True, validate="1:1")
    idebug()
    sch['Alice_Percent'] = 0
    for i in range(len(sch)):
        name = sch.Name.iloc[i]
        numer = (df[name] * df['Num_Alice']).sum()
        denom = (df[name] * df['Num_Households']).sum()
        sch.loc[i, 'Alice_Percent'] = 100 * numer / denom
        assert sch.loc[i, 'Name'] == name

    cols = "Name CODE school_type Alice_Percent geom".split()
    sch = sch[cols].copy()
    sch.to_csv(outfn)
    return df, sch


def load_all_schools(pattern):

    stype = "Elementary Middle High".split()
    dflist = []
    for st in stype:
        df = fgg.load_geoms_as_df(pattern.format(school_type=st))
        df['school_type'] = st
        dflist.append(df) 
    df = pd.concat(dflist)
    return df 


def query_census_for_income():
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
    out['Num_Households'] = df.Num_Households
    out['fips'] = df.fips 
    out['Num_Alice'] = termA 
    out['Percent_Alice'] = 100 * termA / (termA + termB)
    out['geom'] = df.geom
    return out 


