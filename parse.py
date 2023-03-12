from ipdb import set_trace as idebug
from pprint import pprint
import pandas as pd 


from frmbase.support import lmap
import frmbase.dfpipeline as dfp 
from frmbase.parmap import parmap 
import frmbase.meta as fmeta
import requests 

from glob import glob 
import re 



def parse():
    """

    Collect statistics on school performance as measured by the MCAP.

    MCAP data files downloaded from 
    https://reportcard.msde.maryland.gov/Graphs/#/DataDownloads/datadownload/3/17/6/99/XXXX/2020

    and similar.

    In 2020, because of Covid(?), more limited testing was done. In any case
    the file format is different, so I omit it. 

    Naturally the dataset format differs from year to year (most notably
    during the switch from csv to xlsx). So I've had to make choices
    about what to keep.

    Notes
    --------
    Excel breaks down results by demographic groups. For consistency
    with the older csv files, I select only the "All students" rows

    In the earlier years, performance per test was broken down into 3 tiers,
    then expanded into 5. There's no way to compare performance across
    these tiers so I drop all that data.
    """

    path = "/home/fergal/data/politics/stusuppnet/MCAP/"
    flist_xlsx = glob(path + "20*_MCAP_*.xlsx")
    flist_csv = glob(path + "MCAP_ELA_MATH*.csv")
    outfn = 'mcap_total.csv'
    fmeta.save_state(outfn + ".json")

    dflist = []
    for f in flist_xlsx:
        print(f)
        df = dfp.Load(f).apply(None)
        df = parse_xlsx(df)
        dflist.append(df)

    for f in flist_csv:
        print(f)
        df = dfp.Load(f).apply(None)
        df = parse_csv(df)
        dflist.append(df)

    df = pd.concat(dflist)

    drops = """
    LSS_Number
    School_Number
    Level_1_Pct
    Level_2_Pct
    Level_3_Pct
    Level_4_Pct
    Level_5_Pct
    Proficient_Count""".split()
    df = dfp.DropCol(*drops).apply(df)
    df.to_csv(outfn)
    return df


def parse_xlsx(df):

    mapper = {
        'Year': 'Academic_Year', 
        'LEA': 'LSS_Number', 
        'LEA_Name': 'LSS_Name', 
        'School': 'School_Number', 
        # 'School_Name': '', 
        # 'Assessment': '',
        'Student_group': 'Student_Group',
        # 'Tested_Count': '', 
        # 'Proficient_Count': '', 
        # 'Proficient_Pct': '',
        # 'Level_1_Pct': '', 
        # 'Level_2_Pct': '', 
        # 'Level_3_Pct': '', 
        # 'Create_Date': '',
    }

    df.columns = lmap(lambda x: re.subn(" ", "_", x)[0], df.columns)

    pipeline = [
        dfp.RenameCol(mapper),
        dfp.Filter("LSS_Name == 'Baltimore County'"),
        dfp.Filter("Student_Group == 'All Students'"),
        dfp.Copy(),
    ]
    df = dfp.runPipeline(pipeline, df)

    df = set_bad_values(df)
    df = set_school_level(df)
    df = set_subject(df)
    df = get_grade(df)
    return df 

def parse_csv(df):

    df.columns = lmap(lambda x: re.subn(" ", "_", x)[0], df.columns)
    pipeline = [
        dfp.Filter("LSS_Name == 'Baltimore County'"),
        dfp.Copy(),
    ]
    df = dfp.runPipeline(pipeline, df)

    df = set_bad_values(df)
    df = set_school_level(df)
    df = set_subject(df)
    df = get_grade(df)
    return df


def set_bad_values(df):
    for c in df.columns:
        idx = df[c] == '*'
        idx |= df[c] == '<= 5.0'
        df.loc[idx, c] = -1

        idx = df[c] == '>= 95.0'
        df.loc[idx, c] = 100
        try:
            df[c] = df[c].astype(float)
        except ValueError:
            pass 
    return df 


def set_subject(df):
    subj = df.Assessment.str.split().str.get(0)
    df['Subject'] = subj 
    # idebug()
    return df 

def get_grade(df):
    df['Grade'] = -1 
    idx = df.Assessment.str.contains("Grade")
    grade = df.Assessment.str.split().str.get(-1)
    df.loc[idx, 'Grade'] = grade
    df['Grade'] = df['Grade'].astype(int)
    return df

def set_school_level(df):
    df['Level'] = "Unknown"
    idx = df['School_Name'].str.contains("Elementary")
    df.loc[idx, 'Level'] = "Elementary"

    idx = df['School_Name'].str.contains("Middle")
    df.loc[idx, 'Level'] = "Middle"

    idx = df['School_Name'].str[-6:] == "Middle"
    df.loc[idx, 'Level'] = "Middle"

    idx = df['School_Name'].str.contains("High")
    df.loc[idx, 'Level'] = "High"


    #Meadowood Education Center  15 student attendance
    #Extended Day Learning Program  Homeschooling
    #Home Assignments
    elems = [
        "Lutherville Laboratory", 
        'Halstead Academy',
        "Chatsworth School",
    ]

    mids = [
        'Loch Raven Technical Academy',
        "Northwest Academy of Health Sciences",
        "Southwest Academy",
        "Crossroads Center",  #Alternative Ed.  
    ]

    highs = [
        'George W. Carver Center for Arts & Technology',
        'White Oak School',
        "Milford Mill Academy",
        "Western School of Technology & Env. Science",
        "BCDC Educational Center",
        "Rosedale Center",  #Alternative Ed
        "Catonsville Center for Alternative Studies",
    ]

    idx = df.School_Name.isin(elems)
    df.loc[idx, 'Level'] = "Elementary"

    idx = df.School_Name.isin(mids)
    df.loc[idx, 'Level'] = "Middle"

    idx = df.School_Name.isin(highs)
    df.loc[idx, 'Level'] = "High"

    return df