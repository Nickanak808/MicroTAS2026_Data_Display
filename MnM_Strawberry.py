import json
import pickle
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
page_title = "MnM: Strawberry in Air"
st.set_page_config(page_title=page_title, layout="wide")

DATA = Path(__file__).parent / "Data"

# Single source of truth for colors: .streamlit/config.toml
BG = st.get_option("theme.backgroundColor") or "#151312"
TEXT = st.get_option("theme.textColor") or "#FFFFFF"

# ── EDIT THESE ───────────────────────────────────────────────────────────────
# Tab label -> filename prefix. Files are expected as:
#   Data/<prefix>Surface.pkl, Data/<prefix>X.pkl, Data/<prefix>Y.pkl
SETS = {
    #"Mouse Kidney in Air": "DryKidney",
    #"Mouse Kidney in Media": "WetKidney",
    #"Tissue Phantom in Air": "DryTurtle",
    #"Tissue Phantom in Water": "WetTurtle",
    #"Clear Phantom in Air": "ClearTurtle",
    "Strawberry in Air": "Strawberry",
}
# Per-animation settings. These are the defaults for the sidebar controls.
#   suffix:   filename suffix (Data/<prefix><suffix>.pkl)
#   height:   frame height in px
#   max_zoom: upper limit on scaling, in % (100 = never enlarge past natural size)
#   optional: if True, a missing file is skipped silently instead of warning
ANIMATIONS = {
    "X": {"suffix": "X", "height": 400, "max_zoom": 100, "optional": False},
    "Y": {"suffix": "Y", "height": 400, "max_zoom": 100, "optional": False},
    "Z": {"suffix": "Z", "height": 750, "max_zoom": 100, "optional": True},
}
# Optional per-tab overrides of the defaults above, keyed by (tab label, animation).
# Example: {("Set 2", "Z"): {"height": 900, "max_zoom": 150}}
OVERRIDES = {
    ("Mouse Kidney in Media","X"): {"height": 500, "max_zoom": 150},
    ("Mouse Kidney in Media","Y"): {"height": 500, "max_zoom": 150},
    ("Tissue Phantom in Water","X"): {"height": 500, "max_zoom": 150},
    ("Tissue Phantom in Water","Y"): {"height": 500, "max_zoom": 150},
    ("Strawberry in Air","Y"): {"height": 550, "max_zoom": 150},
}

# Text shown above each display, written as Markdown. Keys are (tab label, item),
# where item is "Surface", "X", "Y" or "Z". Use None as the tab label for text
# that should appear in every tab; a tab-specific entry takes priority.
NOTES = {
    # "Top" goes at the very top of a tab, above everything else.
    ("Mouse Kidney in Air", "Top"): "### About this sample\nA lightly formalin fixed mouse kidney imaged dry on a glass slide, dropped with PBS to avoid excessive drying.",
    ("Mouse Kidney in Media", "Top"): "### About this sample\nA freshly sectioned mouse kidney imaged in an 8-well chamber slide filled with RPMI 1640 + 10% FBS media.",
    ("Tissue Phantom in Air", "Top"): "### About this sample\nA PDMS tissue phantom made with coconut milk for optical scattering. Imaged dry in a 2-well chamber slide. The same phantom was used for both imaging conditions.",
    ("Tissue Phantom in Water", "Top"): "### About this sample\nA PDMS tissue phantom made with coconut milk for optical scattering. Imaged in DI water in a 2-well chamber slide. The same phantom was used for both imaging conditions.",
    ("Clear Phantom in Air", "Top"): "### About this sample\nA PDMS tissue phantom made WITHOUT coconut milk for ease of imaging stains via confocal microscopy. Imaged dry in a 2-well chamber slide, which was filled with DI water to allow for staining.",
    ("Strawberry in Air", "Top"): "### About this sample\nA slice of strawberry, imaged early in the project to give perspective to the capabilities of the platform. Imaged at a lower resolution (100 um), dry, on top of a glass slide.",
    (None, "Surface"): "3D surface resolved from OCT data.\nLeft click + drag to rotate, right click + drag to pan, scroll to zoom.",
    (None, "X"): "Use the controls below the frame to play or step through.",
}
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Display")
    plot_height = st.slider("Surface plot height (px)", 500, 1800, 600, 50)
    st.checkbox("Raw animation mode (debug)", key="raw_mode",
                help="Skip auto-fit scaling and show each animation's HTML as-is.")
    st.caption("Per-animation height, zoom and on/off live in each tab, "
               "inside every animation's own settings panel.")


@st.cache_resource(show_spinner="Loading data...")
def load_pickle(name: str):
    with open(DATA / name, "rb") as f:
        return pickle.load(f)


def as_html(obj) -> str:
    """IPython HTML object or plain string -> HTML string."""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "data") and isinstance(obj.data, str):
        return obj.data
    if hasattr(obj, "_repr_html_"):
        return obj._repr_html_()
    raise TypeError(f"Don't know how to render {type(obj)}")


# Wrapper page: loads the animation in an inner iframe, measures its natural
# size, then scales it (CSS transform) to fit the available width AND height,
# centered. Never scales above 100%. Re-fits when the window is resized.
FIT_TEMPLATE = """
<style>
  html, body { margin:0; height:100%; overflow:hidden; background:transparent; }
  #box { position:relative; width:100%; height:100vh; overflow:hidden; }
  #f { position:absolute; left:0; top:0; border:0; transform-origin:0 0;
       width:3000px; height:3000px; visibility:hidden; background:__BG__; }
</style>
<div id="box"><iframe id="f"></iframe></div>
<script>
  const f = document.getElementById('f'), box = document.getElementById('box');
  let w = 0, h = 0, tries = 0;
  const BIG = 3000, FALLBACK_W = 1200, MIN_SIZE = 100;

  function extent(d) {
    let mw = 0, mh = 0;
    for (const el of d.body.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      mw = Math.max(mw, r.right); mh = Math.max(mh, r.bottom);
    }
    return [mw, mh];
  }

  function measure() {
    const d = f.contentDocument;
    if (!d || !d.body) return false;
    // Always measure in a large viewport, so a previous tiny size can't
    // collapse the layout and lock the measurement at ~0.
    f.style.width = BIG + 'px'; f.style.height = BIG + 'px';
    let [mw, mh] = extent(d);
    // Content that stretches to the full viewport is responsive: pick a sane
    // width and re-measure the height at that width.
    if (mw >= BIG - 10) {
      f.style.width = FALLBACK_W + 'px';
      [mw, mh] = extent(d);
      mw = Math.max(mw, FALLBACK_W);
    }
    // Nothing meaningful rendered yet (scripts/images still loading): retry.
    if (mw < MIN_SIZE || mh < MIN_SIZE) {
      f.style.visibility = 'hidden';
      return false;
    }
    w = Math.ceil(mw) + 8; h = Math.ceil(mh) + 8;
    f.style.width = w + 'px'; f.style.height = h + 'px';
    fit();
    return true;
  }

  // Poll until real content appears, then keep re-checking for a few seconds
  // (later frames/images can change the size).
  function poll() {
    const ok = measure();
    tries++;
    if (tries < 40) setTimeout(poll, ok && tries > 8 ? 1000 : 250);
  }

  function fit() {
    if (!w || !h) return;
    if (box.clientWidth < 2 || box.clientHeight < 2) return;  // tab is hidden
    const s = Math.min(box.clientWidth / w, box.clientHeight / h, __MAXS__);
    f.style.transform = 'scale(' + s + ')';
    f.style.left = Math.max(0, (box.clientWidth - w * s) / 2) + 'px';
    f.style.visibility = 'visible';
  }

  f.onload = () => { tries = 0; poll(); };
  // Tabs that aren't showing have zero size. When this frame becomes visible
  // (or is resized) re-measure and re-fit, so the animation never stays blank.
  let lastW = 0, lastH = 0;
  new ResizeObserver(() => {
    const cw = box.clientWidth, ch = box.clientHeight;
    if (cw < 2 || ch < 2) { lastW = 0; lastH = 0; return; }
    if (cw === lastW && ch === lastH) return;
    lastW = cw; lastH = ch;
    tries = 0; poll();
  }).observe(box);
  f.srcdoc = __DOC__;
</script>
"""


def show_animation(html_str: str, height: int, max_zoom: int = 100):
    if st.session_state.get("raw_mode"):
        # Debug: bypass the auto-fit wrapper and render the HTML as-is.
        components.html(html_str, height=height, scrolling=True)
        return
    # Theme the animation page itself (buttons, labels, page background).
    themed = f"<style>html,body{{background:{BG};color:{TEXT};}}</style>" + html_str
    doc = json.dumps(themed).replace("</", "<\\/")
    page = FIT_TEMPLATE.replace("__DOC__", doc).replace("__BG__", BG).replace("__MAXS__", str(max_zoom / 100))
    components.html(page, height=height, scrolling=False)


def show_plotly(fig, height: int):
    fig.update_layout(
        height=height,
        autosize=True,
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        scene_bgcolor=BG,  # 3D surface background; ignored if the figure has no scene
        font_color=TEXT,
    )
    config = {"scrollZoom": True, "displaylogo": False}
    try:
        st.plotly_chart(fig, width="stretch", config=config)
    except TypeError:  # older Streamlit
        st.plotly_chart(fig, use_container_width=True, config=config)


def note(tab_label: str, item: str):
    text = NOTES.get((tab_label, item)) or NOTES.get((None, item))
    if text:
        st.markdown(text)

st.title(page_title)
note("Strawberry in Air", "Top")

st.markdown("[Click Here](https://mnmutas26-start-page.streamlit.app) to return to the start page & poster information.")

st.subheader("Other Samples")
st.markdown("[Mouse Kidney in Air](https://mnmutas26-drykidney.streamlit.app)")
st.markdown("[Mouse Kidney in Media](https://mnmutas26-wetkidney.streamlit.app)")
st.markdown("[Tissue Phantom in Air](https://mnmutas26-dryphantom.streamlit.app)")
st.markdown("[Tissue Phantom in Water](https://mnmutas26-wetphantom.streamlit.app)")
st.markdown("[Clear Phantom in Air](https://mnmutas26-clearphantom.streamlit.app)")
#st.markdown("[Strawberry in Air](https://mnmutas26-strawberry.streamlit.app)")

tabs = st.tabs(list(SETS.keys()))
for tab, (label, prefix) in zip(tabs, SETS.items()):
    with tab:
        # Surface
        st.subheader("Surface")
        note(label, "Surface")
        surface_path = DATA / f"{prefix}Surface.pkl"
        if surface_path.exists():
            show_plotly(load_pickle(surface_path.name), plot_height)
        else:
            st.warning(f"Missing file: Data/{surface_path.name}")

        # Animations, stacked on the same page
        for anim_label, cfg in ANIMATIONS.items():
            path = DATA / f"{prefix}{cfg['suffix']}.pkl"
            if not path.exists():
                if not cfg["optional"]:
                    st.subheader(f"Animation {anim_label}")
                    st.warning(f"Missing file: Data/{path.name}")
                continue
            st.subheader(f"Slices along the {anim_label} axis")
            note(label, anim_label)
            base = {**cfg, **OVERRIDES.get((label, anim_label), {})}
            key = f"{label}_{anim_label}"
            # Each animation in each tab has its own window settings.
            with st.expander("Window settings", expanded=False):
                c1, c2, c3 = st.columns(3)
                loaded = c1.toggle("Load animation", value=True, key=f"show_{key}",
                                   help="Turn off to free browser memory.")
                height = c2.slider("Height (px)", 300, 1800, base["height"], 50,
                                   key=f"h_{key}")
                zoom = c3.slider("Max zoom (%)", 25, 300, base["max_zoom"], 5,
                                 key=f"z_{key}")
            if loaded:
                show_animation(as_html(load_pickle(path.name)), height, zoom)
            else:
                st.caption("Animation not loaded. Switch 'Load animation' back on to show it.")