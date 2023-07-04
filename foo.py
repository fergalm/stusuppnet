from ipdb import set_trace as idebug 
import matplotlib.pyplot as plt 
from pprint import pprint 
import pandas as pd 
import numpy as np



def main():
    def highlight_max(x, color):
        idebug()
        ret = np.where(x == np.nanmax(x.to_numpy()), f"color: {color};", None)
        return ret

    df = pd.DataFrame(np.random.randn(5, 2), columns=["A", "B"])
    # styler = df.style.apply(highlight_max, color='red')  
    styler =    df.style.apply(highlight_max, color='blue', axis=1)  
    # df.style.apply(highlight_max, color='green', axis=None)  

    styler.to_html('table.html')
    # df.to_html('table.html')