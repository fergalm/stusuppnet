from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np 


from frmgis.anygeom import AnyGeom
from frmgis.union import union_collection
import frmgis.geomcollect as fgc 
import frmgis.mapoverlay as fmo 
import frmgis.plots as fgplots 
import frmgis.get_geom as fgg 
import frmgis.roads 

from frmbase.support import npmap, lmap 
import frmbase.dfpipeline as dfp 

import matte
"""

Intersect district with schools
Create union geom 
create matte
select only schools with correct type AND in union geom for labeling
labels

"""
import frmgis.roads as road 

from frmbase.support import Timer 

def load(political_districts=None):
    """
    TODO
    x Add labels 
    o Figure out what to do for two schools in same place
    x Filter geoms to district shape 
    o How to best zoom to a district
    3. Add roads 
    o Should I label shapes not school locations?
    """

    school_type = 'Elementary'
    district_name= "4"
    masterfn = "masterlist.csv"
    districtfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    labelfn = "/home/fergal/data/elections/shapefiles/schools/Public_Schools.kml"
    schshapefn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    farmsfn = "farms0623.csv"
    alicefn = "alice_high.csv"

    if political_districts is None:
        political_districts = load_districts(districtfn)

    with Timer("district geom"):
        district_geom = get_district_geom(political_districts, district_name)
 
    # base_layer = load_farms_data(farmsfn, schshapefn, masterfn)
    schools_df = load_alice_data(alicefn, schshapefn, masterfn)

    #Find the in-district schools
    return schools_df, political_districts



def filterByGeom(df, master_geom, name_col='Name', geom_col='geom'):
    sch_collection = fgc.GeomCollection(df, name_col, geom_col)
    overlap = sch_collection.measure_overlap(master_geom)
    df = df[overlap.frac > 1e-2]
    df = df.copy()

    # idx = npmap(lambda x: x.Overlaps(master_geom), geoms)
    return df 
    


def plot(schools_df, political_df, district_name):
    """
    Inputs
    ---------
    base_layer
        (dataframe) The geometries, and values for the underlying choropleth. These
        are typically some index of poverty for the school. This should include
        all schools in the county at the given level (high, middle, elementary)
        These are plotting with low opacity. Must contain the keys 
        geom and Value. 
    district_sch_df
        (dataframe) Dataframe of the the schools that overlap the district of interest.
        Same keys as base_layer
    district_geom
        (AnyGeom) The district geometry is plotted as a thick black line
    """
    district_name = str(district_name)
    district_geom = political_df[ political_df.DistrictId == district_name].geom.iloc[0]
    district_sch_df = filterByGeom(schools_df, district_geom)
    district_sch_geom = union_collection(list(district_sch_df.geom))
    env = district_sch_geom.GetEnvelope()

    plt.clf()
    set_figure_size()
    plt.axis(env)


    cmap = plt.cm.YlOrRd
    fgplots.chloropleth(schools_df.geom, schools_df.Value, cmap=cmap, alpha=.1, wantCbar=False)
    _, cb = fgplots.chloropleth(district_sch_df.geom, district_sch_df.Value, ec='w', lw=2,  cmap=cmap, vmin=10, vmax=50)
    cb.set_label("ALICE Households (%)")
    add_labels(district_sch_df)

    fgplots.plot_shape(district_geom, 'k-', lw=4, zorder=+20)
    frmgis.roads.plot_interstate()
    fmo.drawMap(zoom_delta=-1)
    ax = plt.gca()
    make_axes_locatable(ax)
    plt.axis('off')


def set_figure_size():
    env = plt.axis()
    dlng = env[1] - env[0]
    dlat = env[3] - env[2] 

    cb_size_inches = 4 
    ratio = dlat/dlng 
    if ratio > 1:
        print("gt")
        plt.gcf().set_size_inches( cb_size_inches + 10/ratio, 10)
    else:
        print("lt")
        plt.gcf().set_size_inches( cb_size_inches + 10, 10/ratio)


def load_labels(labelfile):
    pipeline = [
        LoadGeom(labelfile),
        dfp.SelectCol("FACILITY_N", "FACILITY_T", "MAP_LABEL", "geom"),
        dfp.SetCol("FACILITY_N", "FACILITY_N.str.title()"),
        dfp.SetCol("MAP_LABEL", "MAP_LABEL.str.title()"),
    ]
    df = dfp.runPipeline(pipeline)
    return df 


import frmplots.plots as fplots 
from frmplots.platlabels import PlatLabel
def add_labels(locs):
    labeler = PlatLabel()
    # bbox = {'color':'silver', 'alpha':.9}
    effect = fplots.outline(clr='#EEEEEE', lw=4)
    label_level = npmap(lambda x: x.Centroid().GetX(), locs.geom)
    label_level *= -1
    
    
    for geom, name, level in zip(locs.geom, locs.Name, label_level):
        cent = geom.Centroid()
        # fgplots.plot_shape(point, 'C0o', ms=4, zorder=20)
        labeler.text(cent.GetX(), cent.GetY(), " " + name.title(),
                      color='k', 
                      path_effects=effect, 
                      level=level, 
                      zorder=20,
                      ha="center",
                      fontsize=10,
            )
    return labeler


def match_to_master_geom(geom_list, master_geom):
    master = AnyGeom(master_geom).as_geometry()

    geom_list = lmap(lambda x: AnyGeom(x).as_geometry(), geom_list)
    out = lmap(lambda x: master.Intersection(x), geom_list)
    return out 


def is_clockwise(shape):
    gtype, arr = AnyGeom(shape).as_array()
    if gtype.lower() != 'polygon':
        raise ValueError("Not a polygon")
    
    #Translate to origin
    arr = arr.copy()
    arr[:,0] -= np.mean(arr[:,0])
    arr[:,1] -= np.mean(arr[:,1])
    dx = np.diff(arr[:,0])
    dy = np.diff(arr[:,1])

    sgn = np.sign(np.arctan2(dy, dx))
    return - np.sum(sgn)


class LoadGeom(dfp.AbstractStep):
    def __init__(self, fn):
        self.fn = fn 

    def apply(self, df=None):
        return fgg.load_geoms_as_df(self.fn)


def get_district_geom(df, name):
    wkt = df.geom[ df.DistrictId == name].iloc[0]
    geom = AnyGeom(wkt).as_geometry()
    return geom


def load_districts(fn):
    pipeline = [
        LoadGeom(fn),
        dfp.RenameCol({"COUNCILMANIC_DISTRICTS":"DistrictId"}),
        dfp.SelectCol("DistrictId", "geom"),
    ]
    df = dfp.runPipeline(pipeline)

    #Simplify. This works better than simplify, but is very slow
    for i in range(len(df)):
        geom = AnyGeom(df.loc[i, 'geom']).as_geometry()
        tmp = geom.Buffer(-.002)
        df.loc[i, 'geom'] = tmp.Buffer(.002)
    return df 


def load_farms_data(farms_file, shape_file, master_file):
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
    return df


def load_alice_data(alice_file, shape_file, master_file):
    pipeline = [
        dfp.Load(alice_file, index_col=0),
        dfp.SelectCol("CODE", 'Name', "Alice_Percent", "geom"),
        dfp.RenameCol({'Alice_Percent': 'Value'}),
        dfp.SetCol('CODE', 'CODE.astype(int)'),
    ]
    df1 = dfp.runPipeline(pipeline)
    df1['geom'] = lmap(lambda x: AnyGeom(x).as_geometry(), df1.geom)

    return df1
                                    
def plot_base_layer(df, geom_col='geom', value_col='value', **kwargs):
    cmap = kwargs.pop('cmap', plt.cm.YlOrRd)
    label = kwargs.pop('label', "Value")
    ec = 'w'

    _, cb = fgplots.chloropleth(df[geom_col], df[value_col], cmap=cmap, ec=ec, )
    cb.set_label(label)


# def main():
#     school_type = 'High'
#     district= 3
#     masterfn = "masterlist.csv"
#     distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
#     locfn = "/home/fergal/data/elections/shapefiles/schools/Public_Schools.kml"
#     schfn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
#     farmsfn = "farms0623.csv"

#     master = pd.read_csv(masterfn)
#     farms = pd.read_csv(farmsfn)
#     sch = fgg.load_geoms_as_df(schfn)
#     dist = fgg.load_geoms_as_df(distfn)
#     locs = fgg.load_geoms_as_df(locfn)
#     locs['FACILITY_N'] = locs.FACILITY_N.str.title()

#     df = pd.merge(master, sch, left_on='AltName1', right_on='Name')

#     cols = "Site_Num Site_Name AltName1 AltName2 geom".split() # Site_Type Enrollment Free TotalFR FRPercent".split()
#     pipeline = [
#         dfp.SelectCol(*cols),
#     ]
#     df = dfp.runPipeline(pipeline, df)
                   
#     pipeline = [
#         dfp.Load(farmsfn),
#         dfp.Filter("Year == 'Y2223'"),
#         dfp.SelectCol("Site_Num", "Enrollment", "TotalFR", "FRPercent")
#     ]
#     farms = dfp.runPipeline(pipeline)                   
#     df = pd.merge(df, farms, on='Site_Num')

#     #Add in POINTs to show location of schools
#     cols = ['Site_Num', 'Site_Name', 'AltName1', 'AltName2', 'geom_x', 'Enrollment',
#        'TotalFR', 'FRPercent', 'geom_y',  'FACILITY_T', 'FACILITY_N',  'MAP_LABEL',
#     ]
#     df = pd.merge(df, locs, left_on='AltName2', right_on='FACILITY_N')
#     pipeline = [
#         dfp.SelectCol(cols),
#         dfp.RenameCol({'geom_x': 'area_geom', 'geom_y':'address_geom'}),
#         dfp.SetCol('MAP_LABEL', 'MAP_LABEL.str.title()'),
#     ]
#     df = dfp.runPipeline(pipeline, df)

#     from frmgis.union import union_collection
#     county_geom = union_collection(dist.geom.values)

#     #School geom boundaries are over water, district ones are not. Trim schools
#     #to match districts
#     df['area_geom'] = df.area_geom.apply( lambda x: county_geom.Intersection(x))
#     #Create a union geometry of districts, intersect each HS with it
#     plt.clf()
#     fgplots.plot_shape(county_geom, 'g-')
#     _, cb = fgplots.chloropleth(df.area_geom, df.FRPercent, cmap=plt.cm.YlOrRd, ec='w')

#     for g in dist.geom:
#         fgplots.plot_shape(g, 'c-', lw=2,)
#     cb.set_label("Percent Students on Free Lunch")
#     plt.axis([-77.22, -76.04, 39.15, 39.77])

#     import matte
#     district_geom = dist.geom.iloc[district-1]
#     overlay = matte.make_matte(
#         district_geom, 'axis', zorder=10, color='w', alpha=.8)
#     plt.gca().add_patch(overlay)

#     locs = filterByGeom(df, district_geom)
#     labeler = add_labels(locs)
#     # labeler.render()

#     fplots.add_watermark(loc='bottom')
#     return locs
