import pickle
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dry Kidney", layout="wide")

# Resolve Data/ relative to this file so it works locally and on Streamlit Cloud
DATA = Path(__file__).parent / "Data"


@st.cache_resource(show_spinner="Loading data...")
def load_pickle(name: str):
    with open(DATA / name, "rb") as f:
        return pickle.load(f)


def as_html(obj) -> str:
    """Turn whatever was pickled (IPython HTML object or plain string) into an HTML string."""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "data") and isinstance(obj.data, str):  # IPython.display.HTML
        return obj.data
    if hasattr(obj, "_repr_html_"):
        return obj._repr_html_()
    raise TypeError(f"Don't know how to render {type(obj)}")


st.title("Dry Kidney")

surface_tab, x_tab, y_tab = st.tabs(["Surface", "Animation X", "Animation Y"])

with surface_tab:
    fig = load_pickle("DryKidneySurface.pkl")
    st.plotly_chart(fig, use_container_width=True)

with x_tab:
    # components.html renders the page in an iframe, so the animation's
    # JavaScript (play/pause, slider) works as it does in a notebook.
    components.html(as_html(load_pickle("DryKidneyX.pkl")), height=800, scrolling=True)

with y_tab:
    components.html(as_html(load_pickle("DryKidneyY.pkl")), height=800, scrolling=True)
