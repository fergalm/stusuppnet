from ipdb import set_trace as idebug 
from pprint import pprint 
import pandas as pd 

from frmbase.support import check_cols_in_df
from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmgis.get_geom as fgg 
import frmbase.dfpipeline as dfp 



class LoadGeom(dfp.AbstractStep):
    def __init__(self, fn):
        self.fn = fn 

    def apply(self, df=None):
        return fgg.load_geoms_as_df(self.fn)


def get_district_geom(df, name):
    wkt = df.geom[ df.DistrictId == name].iloc[0]
    geom = AnyGeom(wkt).as_geometry()
    return geom


def load_cong_districts(fn):

    bc_districts = "01 02 07".split()
    pipeline = [
        LoadGeom(fn),
        dfp.RenameCol({"DISTRICT":"DistrictId"}),
        dfp.SelectCol("DistrictId", "geom"),
        dfp.Filter(f"DistrictId.isin({bc_districts})"),
        dfp.AssertNotEmpty(),
    ]

    df = dfp.runPipeline(pipeline)
    # idebug()
    return df


def load_leg_districts(fn):
    bc_districts = "06 08 07A 10 11A 11B 42A 42B 43B 44A 44B".split()
    pipeline = [
        LoadGeom(fn),
        dfp.RenameCol({"DISTRICT":"DistrictId"}),
        dfp.SelectCol("DistrictId", "geom"),
        dfp.Filter(f"DistrictId.isin({bc_districts})"),
    ]
    df = dfp.runPipeline(pipeline)
    return df


def load_council_districts(fn):

    pipeline = [
        LoadGeom(fn),
        dfp.RenameCol({"COUNCILMANIC_DISTRICTS":"DistrictId"}),
        dfp.SelectCol("DistrictId", "geom"),
    ]
    df = dfp.runPipeline(pipeline)

    #Simplify. This works better than simplify, but is very slow
    for i in range(len(df)):
        geom = AnyGeom(df.loc[i, 'geom']).as_geometry()
        # tmp = geom.Buffer(-.002)
        # df.loc[i, 'geom'] = tmp.Buffer(.002)
    return df 



def alt_load_farms_data(farms_file, school_type):
    schshapefn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'

    return load_farms_data(farms_file, school_type, schshapefn)


def load_farms_data(farms_file, school_type, shape_file):
    pipeline = [
        dfp.Load(farms_file),
        dfp.Filter("Year == 'Y2223'"),
        dfp.SelectCol("Site_Num", 'Site_Name', "FRPercent"),
        dfp.RenameCol({'FRPercent': 'Value'})
    ]
    df1 = dfp.runPipeline(pipeline)

    pipeline = [
        LoadGeom(shape_file),
        dfp.SelectCol('Name', 'CODE', 'geom'),
        dfp.SetCol('CODE', 'CODE.astype(int)')
    ]
    
    df2 = dfp.runPipeline(pipeline)

    df = pd.merge(df1, df2, left_on='Site_Num', right_on='CODE')
    assert check_cols_in_df(df, "Name Value geom".split())
    return df


def load_dc_data(dc_file, school_type, shape_file=None):
    schshapefn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    
    names = {
        'Local Education Agency Name':'County',
        'Site Name': 'School',
        'Total Enrollment': 'TotalEnrollment',
        'Total DC Free & Reduced': 'FreeReducedCount',
        'Code': 'Site_Num',
    }

    pipeline = [
        dfp.Load(dc_file),
        dfp.RenameCol(names),
        dfp.Filter('County == "BALTIMORE COUNTY PUBLIC SCHOOLS"'),
        dfp.SelectCol(*names.values()),
        dfp.SetCol('Value', '100* FreeReducedCount / TotalEnrollment'),
        dfp.SetCol('Site_Num', 'Site_Num.astype(int)')
    ]
    df1 = dfp.runPipeline(pipeline)

    pipeline = [
        LoadGeom(schshapefn),
        dfp.SelectCol('Name', 'CODE', 'geom'),
        dfp.SetCol('CODE', 'CODE.astype(int)')
    ]
    
    df2 = dfp.runPipeline(pipeline)

    df = pd.merge(df1, df2, left_on='Site_Num', right_on='CODE')
    assert check_cols_in_df(df, "Name Value geom".split())
    return df


def load_alice_data(alice_file, school_type):
    assert school_type in "Elementary Middle High".split()
    pipeline = [
        dfp.Load(alice_file, index_col=0),
        dfp.SelectCol("CODE", 'Name', "school_type", "Alice_Percent", "geom"),
        dfp.RenameCol({'Alice_Percent': 'Value'}),
        dfp.SetCol('CODE', 'CODE.astype(int)'),
        # dfp.Debugger(),
        dfp.Filter(f'school_type == "{school_type}"'),
    ]
    df1 = dfp.runPipeline(pipeline)
    df1['geom'] = lmap(lambda x: AnyGeom(x).as_geometry(), df1.geom)
    assert check_cols_in_df(df1, "Name Value geom".split())  
    return df1
