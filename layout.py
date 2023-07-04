from ipdb import set_trace as idebug 
from bokeh.io import show,save
import numpy as np 

from bokeh.plotting import figure
from bokeh.models import CustomJS, ColorBar, LinearColorMapper, BasicTicker, Label, Div, Spacer
from bokeh.layouts import row, column
import bokeh.palettes 

from bokeh.models import CustomJS, RadioButtonGroup, SetValue
from bokeh.events import MouseEnter, MouseLeave

from frmbase.support import npmap, lmap 
from frmgis.anygeom import AnyGeom
import frmbok.chloropleth as fbc 
import frmbok.roads as roads


def main():

    opts = {
        'styles': {
            'color': 'red',
        }, 
        'align':"center" ,
    }
        
    sch_choice = RadioButtonGroup(labels="Elem Middle High".split(), active=2, **opts)
    leg_choice = RadioButtonGroup(labels="None Council Leg Cong".split(), active=2, align="center")

    layout = create_layout(sch_choice, leg_choice)
    save(layout, 'farms.html')



def create_layout(sch_choice, leg_choice):

    template = "<FONT size='16'>%s</FONT>"
    sch = column(
        Div(text=template % "School Type", align="center"),
        sch_choice,
        sizing_mode="stretch_width",
    )

    leg = column(
        Div(text=template % "Political Districts", align="center"),
        leg_choice,
    )

    controls = row(sch, Spacer(), leg)
    layout = column(controls)
    return layout
