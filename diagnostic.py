from ipdb import set_trace as idebug
import matplotlib.pyplot as plt 
import pandas as pd
import numpy as np

import frmbase.dfpipeline as dfp 


def main():

    cols = ["Academic_Year", "School_Name", "Tested_Count", "Proficient_Pct", "Level", "Subject"]
    pipeline = [
        dfp.Load('mcap_total.csv'),
        dfp.Filter('Level == "Elementary"'),
        dfp.Filter('Subject == "English/Language"'),
        dfp.Filter("Grade == 5"),
        dfp.SelectCol(*cols),
        dfp.Sort('Academic_Year'),
        dfp.GroupApply('School_Name', plot),
    ]

    plt.clf()
    df = dfp.runPipeline(pipeline)
    return df 


def susan():
    """Susan wanted to know which schools did best in the Covid year"""
    cols = ["Academic_Year", "School_Name", "Tested_Count", "Proficient_Pct", "Level", "Subject"]
    pipeline = [
        dfp.Load('mcap_total.csv'),
        dfp.Filter('Level == "Elementary"'),
        dfp.Filter('Subject == "English/Language"'),
        dfp.Filter("Grade == 5"),
        dfp.SelectCol(*cols),
        dfp.Filter('Academic_Year == 2021'),
        dfp.Sort('Proficient_Pct'),
    ]
    df = dfp.runPipeline(pipeline)
    return df 

def plot(df):
    plt.plot(df.Academic_Year, df.Proficient_Pct, 'o-')