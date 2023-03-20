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

from frmbase.support import npmap, lmap 
import frmbase.dfpipeline as dfp 
"""

Intersect district with schools
Create union geom 
create matte
select only schools with correct type AND in union geom for labeling
labels

"""

def main():
    school_type = 'High'
    district= 3
    masterfn = "masterlist.csv"
    distfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    locfn = "/home/fergal/data/elections/shapefiles/schools/Public_Schools.kml"
    schfn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    farmsfn = "farms0623.csv"

    master = pd.read_csv(masterfn)
    farms = pd.read_csv(farmsfn)
    sch = fgg.load_geoms_as_df(schfn)
    dist = fgg.load_geoms_as_df(distfn)
    locs = fgg.load_geoms_as_df(locfn)
    locs['FACILITY_N'] = locs.FACILITY_N.str.title()

    df = pd.merge(master, sch, left_on='AltName1', right_on='Name')

    cols = "Site_Num Site_Name AltName1 AltName2 geom".split() # Site_Type Enrollment Free TotalFR FRPercent".split()
    pipeline = [
        dfp.SelectCol(*cols),
    ]
    df = dfp.runPipeline(pipeline, df)
                   
    pipeline = [
        dfp.Load(farmsfn),
        dfp.Filter("Year == 'Y2223'"),
        dfp.SelectCol("Site_Num", "Enrollment", "TotalFR", "FRPercent")
    ]
    farms = dfp.runPipeline(pipeline)                   
    df = pd.merge(df, farms, on='Site_Num')

    #Add in POINTs to show location of schools
    cols = ['Site_Num', 'Site_Name', 'AltName1', 'AltName2', 'geom_x', 'Enrollment',
       'TotalFR', 'FRPercent', 'geom_y',  'FACILITY_T', 'FACILITY_N',  'MAP_LABEL',
    ]
    df = pd.merge(df, locs, left_on='AltName2', right_on='FACILITY_N')
    pipeline = [
        dfp.SelectCol(cols),
        dfp.RenameCol({'geom_x': 'area_geom', 'geom_y':'address_geom'}),
        dfp.SetCol('MAP_LABEL', 'MAP_LABEL.str.title()'),
    ]
    df = dfp.runPipeline(pipeline, df)

    from frmgis.union import union_collection
    county_geom = union_collection(dist.geom.values)

    #School geom boundaries are over water, district ones are not. Trim schools
    #to match districts
    df['area_geom'] = df.area_geom.apply( lambda x: county_geom.Intersection(x))
    #Create a union geometry of districts, intersect each HS with it
    plt.clf()
    fgplots.plot_shape(county_geom, 'g-')
    _, cb = fgplots.chloropleth(df.area_geom, df.FRPercent, cmap=plt.cm.YlOrRd, ec='w')

    for g in dist.geom:
        fgplots.plot_shape(g, 'c-', lw=2,)
    cb.set_label("Percent Students on Free Lunch")
    plt.axis([-77.22, -76.04, 39.15, 39.77])

    import matte
    district_geom = dist.geom.iloc[district-1]
    overlay = matte.make_matte(
        district_geom, 'axis', zorder=10, color='w', alpha=.8)
    plt.gca().add_patch(overlay)

    locs = filterByGeom(df, district_geom)
    labeler = add_labels(locs)
    # labeler.render()

    fplots.add_watermark(loc='bottom')
    return locs


def filterByGeom(df, master_geom):
    sch_collection = fgc.GeomCollection(df, "MAP_LABEL", "area_geom")
    overlap = sch_collection.measure_overlap(master_geom)
    df = df[overlap.frac > 1e-2]

    # idx = npmap(lambda x: x.Overlaps(master_geom), geoms)
    return df 


import frmplots.plots as fplots 
from frmplots.platlabels import PlatLabel
def add_labels(locs):
    labeler = PlatLabel()
    # bbox = {'color':'silver', 'alpha':.9}
    effect = fplots.outline(clr='w', lw=4)
    label_level = npmap(lambda x: x.GetX(), locs.address_geom)
    label_level *= -1
    
    
    for point, name, level in zip(locs.address_geom, locs.MAP_LABEL, label_level):
        fgplots.plot_shape(point, 'C0o', ms=4, zorder=20)
        labeler.text(point.GetX(), point.GetY(), " " + name.title(),
                      color='k', path_effects=effect, level=level, zorder=20)
    return labeler


#     idebug()

#     dist_geom = dist.geom.iloc[district-1]
#     sch_collection = fgc.GeomCollection(sch, "Name")
#     overlap = sch_collection.measure_overlap(dist_geom)
    
#     sch = sch[overlap.frac > 1e-2]
#     school_union = union_collection(sch.geom.values)
#     idx = npmap(lambda x: school_union.Contains(x), locs.geom)
#     locs = locs[idx] 

#     plt.clf()
#     for shp in sch.geom:
#         fgplots.plot_shape(shp, 'k-')

#     for shp in dist.geom:
#         fgplots.plot_shape(dist_geom, 'C1-', lw=4)

#     plt.pause(.01)


#     from frmplots.platlabels import PlatLabel
#     labeler = PlatLabel()
#     bbox = {'color':'silver', 'alpha':.9}
#     label_level = npmap(lambda x: x.GetX(), locs.geom)
#     label_level *= -1
#     for point, name, level in zip(locs.geom, locs.MAP_LABEL, label_level):
#         fgplots.plot_shape(point, 'C0s')
#         labeler.text(point.GetX() + .004, point.GetY(),  name.title(), bbox=bbox, level=level, zorder=+9999)
   
    
#     # geom = get_matte(dist.geom.iloc[2])
#     # fgplots.pplot_shape(geom, '--')
#     # patches = AnyGeom(geom).as_patch(alpha=.4)
#     # for pa in patches:
#     #     plt.gca().add_patch(pa)

#     # fgplots.plot_shape(school_union, 'C2--')

#     fmo.drawMap('light', zoom_delta=-1)

#     #Futzing
#     ax = plt.gca()
#     ax.axis('off')
#     ax.set_position([.01, .01, .99, .99])

#     plt.pause(.1)
#     labeler.render()

#     return locs, sch

# # import frmbase.dfpipeline as dfp
# # def load_school_locs(locfn, sch_type_fn):

# #     pipeline = [ 
# #         dfp.SelectCls(

# #     pipeline = [
# #         dfp.Load(sch_type_fn, index_col=0),
# #         dfp.SelectCol("School_Name", "Level"),
# #         dfp.GroupBy('School_Name', '.head(1)')
# #     ]
# #     sch_types = dfp.runPipeline(pipeline)

# #     df = pd.merge(
# #     idebug()

# def get_matte(shp):
#     lng = [-76.99, -76.99, -76.2, -76.2, -76.99]
#     lat = [39.1, 39.8, 39.8, 39.1, 39.1]

#     env = np.zeros((5,2))
#     env[:,0] = lng[::-1]
#     env[:,1] = lat[::-1]

#     env_geom = AnyGeom(env, gtype="POLYGON").as_geometry()
#     shp_geom = AnyGeom(shp).as_geometry()
#     geom = env_geom.SymDifference(shp_geom)
#     return geom 