from unittest import result
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display
import seaborn as sns
import plotly.graph_objects as go
from numpy.f2py.auxfuncs import throw_error
from scipy.interpolate import interp2d, RegularGridInterpolator
from scipy.ndimage import median_filter
from scipy.ndimage import uniform_filter
import math
import re
from dataclasses import dataclass
from pathlib import Path
import pyarrow as pa
from scipy.signal import savgol_filter, find_peaks
import numpy as np
import pyvista as pv
import vtk
import pickle
import sys, numpy as np, platform, psutil
from plotly.subplots import make_subplots
import streamlit
import pickle


'''
OCT_Signal_Mapper.ipynb
Updated: 20 July 2026

Description: A Jupyter notebook designed to build 3D maps from data
for later use. Methods will be stored in MnM_Experiment.py, but
this will be a place to visualize the maps and perform diagnostics.
'''


# —————————————————————————————————————————————————————————————————————————————————————
# Loading Data ————————————————————————————————————————————————————————————————————————
# —————————————————————————————————————————————————————————————————————————————————————

# Path information
folder = "Data/"
html_file = "DryKidneyHTMLs.pkl"
surface_file = "DryKidneySurface.pkl"

# Parsing file
print("\nLoading data...")

# Loading the HTML animations
with open(folder+"DryKidneyX.pkl", "rb") as file:
    X = pickle.load(file)

with open(folder+"DryKidneyY.pkl", "rb") as file:
    Y = pickle.load(file)

#with open(folder+"DryKidneyZ.pkl", "rb") as file:
#    Z = pickle.load(file)

# Loading the surface
with open(folder + surface_file, "rb") as file:
    fig = pickle.load(file)

fig.show()

display(X)

display(Y)