"""A simple, tabbed prototype built on the FireWatch MVP."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from firewatch.events import build_events  # noqa: E402
from firewatch.harmonize import harmonize  # noqa: E402
from firewatch.loaders import load_observations  # noqa: E402
from firewatch.peat import load_peat_layer, points_on_peat  # noqa: E402
from firewatch.scoring import score_events  # noqa: E402


DATA_DIR = ROOT / "data"
LEVEL_COLORS = {"High": "#ff6b5f", "Medium": "#ffb454", "Low": "#8fa3b8"}

st.set_page_config(
    page_title="Borneo FireWatch · Prototype",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #071411; color: #eef5ef; }
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stMainMenu"] { display: none !important; }
    [data-testid="stSidebar"] { background: #0c201a; border-right: 1px solid #1d3a30; }
    .block-container { max-width: 1440px; padding-top: 2rem; }
    .hero {
        background: linear-gradient(115deg, #12382c 0%, #145347 58%, #b34d32 140%);
        border: 1px solid #2b6655; border-radius: 22px; padding: 28px 32px;
        margin-bottom: 20px;
    }
    .eyebrow { color: #9de0c9; font-size: .78rem; font-weight: 800;
        letter-spacing: .14em; text-transform: uppercase; }
    .hero h1 { color: #f5fbf7; font-size: clamp(2rem, 4vw, 3.2rem);
        margin: 4px 0 2px; }
    .hero p { color: #d3e8dd; font-size: 1.05rem; margin: 0; }
    .stMetric { background: #0d211b; border: 1px solid #204338;
        border-radius: 15px; padding: 14px 17px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_scenario() -> tuple[pd.DataFrame, pd.DataFrame]:
    observations = load_observations(DATA_DIR / "sample_hotspots.csv")
    peat_layer = load_peat_layer(
        DATA_DIR / "demo_peat_illustrative.geojson",
        illustrative=True,
    )
    observations["on_peat"] = points_on_peat(
        observations["latitude"], observations["longitude"], peat_layer
    )
    matched = harmonize(observations)
    events, _ = build_events(matched)
    return matched, score_events(events, peat_layer.available)


def event_map(events: pd.DataFrame):
    figure = px.scatter_mapbox(
        events,
        lat="latitude",
        lon="longitude",
        color="attention_level",
        color_discrete_map=LEVEL_COLORS,
        size="detections",
        size_max=28,
        hover_name="event_id",
        hover_data={
            "attention_score": True,
            "nearest_town": True,
            "detections": True,
        },
        zoom=4.2,
        center={"lat": 2.8, "lon": 113.1},
        height=600,
    )
    figure.update_layout(
        mapbox_style="open-street-map",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#eaf3ed",
        legend={"orientation": "h", "y": 1.02, "x": 0},
    )
    return figure


def render_overview(events: pd.DataFrame) -> None:
    high_count = int((events["attention_level"] == "High").sum())
    matched_events = int(events["both_satellites"].sum())

    first, second, third = st.columns(3)
    first.metric("Fire areas", len(events))
    second.metric("High priority", high_count)
    third.metric("Seen by both satellites", matched_events)

    top = events.iloc[0]
    st.subheader("Top priority area")
    st.write(
        f'{top["event_id"]} near {top["nearest_town"]} · '
        f'{top["attention_level"]} · {top["attention_score"]}/100'
    )
    st.plotly_chart(event_map(events), use_container_width=True)


def render_investigation(observations: pd.DataFrame) -> None:
    matched_pairs = int((observations["match_status"] == "matched").sum() / 2)
    first, second = st.columns(2)
    first.metric("Satellite signals", len(observations))
    second.metric("Matched pairs", matched_pairs)
    st.dataframe(
        observations.sort_values("observed_at", ascending=False).head(10)[
            ["source", "observed_at", "region", "match_status"]
        ],
        hide_index=True,
        use_container_width=True,
    )


def render_report(events: pd.DataFrame) -> None:
    area_labels = {
        f"{row.event_id} near {row.nearest_town}": row.event_id
        for row in events.itertuples()
    }
    with st.form("ground_report"):
        area = st.selectbox("Area", list(area_labels))
        report = st.radio(
            "What are you seeing?",
            ["Possible fire", "No fire", "Not sure"],
            horizontal=True,
        )
        submitted = st.form_submit_button("Add report")

    if submitted:
        st.session_state.setdefault("prototype_reports", []).append(
            {"Area": area_labels[area], "Report": report}
        )
        st.success("Report added for this session.")

    st.caption("Demo reports are not saved or sent to responders.")


try:
    observations, events = load_scenario()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Could not load the bundled prototype scenario: {error}")
    st.stop()

if events.empty:
    st.error("The bundled scenario did not produce any fire areas.")
    st.stop()

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow" style="margin-top:14px">Borneo FireWatch</div>
      <h1>Fire signals across Borneo.</h1>
      <p>Satellite hotspots and the areas that need a closer look.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

situation_tab, investigate_tab, report_tab = st.tabs(
    ["Situation", "Investigate", "Ground report"]
)
with situation_tab:
    render_overview(events)

with investigate_tab:
    render_investigation(observations)

with report_tab:
    render_report(events)
