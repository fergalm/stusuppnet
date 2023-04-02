from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 


from frmgis.union import union_collection
from frmgis.anygeom import AnyGeom
import frmgis.geomcollect as fgc 
import frmgis.mapoverlay as fmo 
import frmgis.plots as fgplots 
import frmgis.get_geom as fgg 
import frmgis.roads 

from frmplots.platlabels import PlatLabel
import frmplots.plots as fplots 

from frmbase.support import npmap, lmap 
import frmbase.dfpipeline as dfp 

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
    plt.axis('off')


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



                                    