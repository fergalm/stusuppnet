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
from frmbase.support import Timer 

import stio as io 
"""

Intersect district with schools
Create union geom 
create matte
select only schools with correct type AND in union geom for labeling
labels

"""

def main():
    for school_type in ["Elementary", "Middle", "High"]:
        for mtype in ["cong", "council", "leg", ]:
            do_school_type(school_type, mtype)

def do_school_type(school_type, mtype):
    council_fn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
    leg_fn = '/home/fergal/data/elections/shapefiles/md_lege_districts/2022/Maryland_Legislative_Districts_2022.kml'
    cong_fn = "/home/fergal/data/elections/shapefiles/congressional/Congress_2022/US_Congressional_Districts_2022.kml"
    # schshapefn = f'/home/fergal/data/elections/shapefiles/schools/{school_type}_School_Districts.kml'
    # alicefn = "alice.csv"
    farmsfn = "farms0623.csv"

    with Timer("Loading districts"):
        if mtype == "council":
            political_districts = io.load_council_districts(council_fn)
        elif mtype == "leg":
            political_districts = io.load_leg_districts(leg_fn)
        elif mtype == "cong":
            political_districts = io.load_cong_districts(cong_fn)
        else:
            assert False 


    # idebug()
    with Timer("Loading Schools Data"):
        # schools_df = io.load_alice_data(alicefn, school_type)
        schools_df = io.alt_load_farms_data(farmsfn, school_type) 

    for d in political_districts.DistrictId:
        plt.clf()
        labeler = plot(schools_df, political_districts, d)

        if mtype == 'cong' and school_type.lower() == 'elementary':
            labeler.render()

        if mtype == "council":
            plt.suptitle(f"Council District {d} {school_type} Schools")
            plt.savefig(f"Council{d}_{school_type}.png")
        elif mtype == "leg":
            plt.suptitle(f"Legislative {d} {school_type} Schools")
            plt.savefig(f"Legislative{d}_{school_type}.png")
        elif mtype == "cong":
            plt.suptitle(f"Congressional District {d}: {school_type} Schools")
            plt.savefig(f"cong{d}_{school_type}.png")
        else:
            assert False 

        print(f"Figure {d} complete")
        plt.pause(1)


# def load(political_districts=None):
#     """
#     TODO
#     x Add labels 
#     o Figure out what to do for two schools in same place
#     x Filter geoms to district shape 
#     o How to best zoom to a district
#     3. Add roads 
#     o Should I label shapes not school locations?
#     """

#     school_type = 'Middle'
#     # district_name= "4"
#     districtfn = '/home/fergal/data/elections/shapefiles/councildistricts/Councilmanic_Districts_2022.kml'
#     alicefn = "alice.csv"

#     if political_districts is None:
#         political_districts = load_council_districts(districtfn)

#     # with Timer("district geom"):
#     #     district_geom = get_district_geom(political_districts, district_name)
 
#     # base_layer = load_farms_data(farmsfn, schshapefn, masterfn)
#     schools_df = io.load_alice_data(alicefn, school_type)

#     #Find the in-district schools
#     return schools_df, political_districts



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
    assert len(district_sch_df) > 0
    district_sch_geom = union_collection(list(district_sch_df.geom))
    env = district_sch_geom.GetEnvelope()

    plt.clf()
    plt.axis(env)
    set_figure_size()

    cmap = plt.cm.YlOrRd
    fgplots.chloropleth(schools_df.geom, schools_df.Value, cmap=cmap, alpha=.1, wantCbar=False)
    _, cb = fgplots.chloropleth(district_sch_df.geom, district_sch_df.Value, ec='w', lw=2,  cmap=cmap, vmin=10, vmax=90, nstep=9)
    #cb.set_label("ALICE Households (%)")
    cb.set_label("School Lunch Eligible (%)")
    labeler = add_labels(district_sch_df)

    fgplots.plot_shape(district_geom, '-', color='ivory', lw=6, zorder=+19)
    fgplots.plot_shape(district_geom, '-', color='midnightblue', lw=4, zorder=+20)
    frmgis.roads.plot_interstate()
    fmo.drawMap(zoom_delta=-1)
    ax = plt.gca()
    plt.axis('off')
    fplots.add_watermark(loc='bottom')
    return labeler



def set_figure_size(baseline_inches=14):
    env = plt.axis()
    dlng = env[1] - env[0]
    dlat = env[3] - env[2] 

    cb_size_inches = 1
    ratio = dlat/dlng 
    if ratio > 1:
        print("gt")
        plt.gcf().set_size_inches( cb_size_inches + baseline_inches/ratio, baseline_inches)
    else:
        print("lt")
        plt.gcf().set_size_inches( cb_size_inches + baseline_inches, baseline_inches*ratio)


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



                                    