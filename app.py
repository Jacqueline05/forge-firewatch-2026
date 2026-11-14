"""A guided, presentation-friendly prototype built on the FireWatch MVP."""
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
SOURCE_COLORS = {"MODIS": "#ff985e", "VIIRS": "#55d6c2"}

st.set_page_config(
    page_title="Borneo FireWatch · Prototype",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #071411; color: #eef5ef; }
    [data-testid="stHeader"] { background: rgba(7, 20, 17, .92); }
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
    .demo-pill {
        display: inline-block; color: #ffe5b6; background: #46341e;
        border: 1px solid #81633a; border-radius: 999px;
        padding: 5px 11px; font-size: .75rem; font-weight: 700;
    }
    .panel {
        background: #0d211b; border: 1px solid #204338; border-radius: 18px;
        padding: 20px 22px; height: 100%;
    }
    .panel h3 { margin-top: 0; }
    .muted { color: #a7bdb2; }
    .priority {
        border-left: 4px solid #ff6b5f; background: #17241f;
        padding: 14px 16px; border-radius: 5px 12px 12px 5px; margin: 10px 0;
    }
    .stMetric { background: #0d211b; border: 1px solid #204338;
        border-radius: 15px; padding: 14px 17px; }
    div[data-testid="stTabs"] button { font-weight: 700; }
    div[data-testid="stForm"] { background: #0d211b; border: 1px solid #204338;
        border-radius: 16px; padding: 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_scenario() -> tuple[pd.DataFrame, pd.DataFrame, bool]:
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
    return matched, score_events(events, peat_layer.available), peat_layer.available


def event_map(events: pd.DataFrame, signals: bool = False):
    if signals:
        figure = px.scatter_mapbox(
            events,
            lat="latitude",
            lon="longitude",
            color="source",
            color_discrete_map=SOURCE_COLORS,
            size="confidence",
            size_max=15,
            hover_name="id",
            hover_data={"source": True, "confidence": True, "region": True},
            zoom=4.2,
            center={"lat": 2.8, "lon": 113.1},
            height=500,
        )
    else:
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
                "days_active": True,
                "on_peat": True,
            },
            zoom=4.2,
            center={"lat": 2.8, "lon": 113.1},
            height=500,
        )
    figure.update_layout(
        mapbox_style="open-street-map",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#eaf3ed",
        legend={"orientation": "h", "y": 1.02, "x": 0},
    )
    return figure


def render_overview(events: pd.DataFrame, peat_available: bool) -> None:
    high_count = int((events["attention_level"] == "High").sum())
    matched_events = int(events["both_satellites"].sum())
    peat_count = int(events["on_peat"].sum()) if peat_available else "n/a"

    st.subheader("The situation at a glance")
    first, second, third, fourth = st.columns(4)
    first.metric(
        "Fire areas",
        len(events),
        help="Nearby satellite detections grouped into one area.",
    )
    second.metric("High attention", high_count, help="Areas scoring 70 or higher.")
    third.metric("Seen by both satellites", matched_events)
    fourth.metric("On illustrative peat", peat_count)

    left, right = st.columns([0.88, 1.45], gap="large")
    with left:
        top = events.iloc[0]
        st.markdown(
            f"""
            <div class="panel">
              <div class="eyebrow">Priority area · {top["attention_level"]} attention</div>
              <h2>{top["event_id"]} near {top["nearest_town"]}</h2>
              <p class="muted">{top["reasons"]}</p>
              <div class="priority">
                <strong>Attention score: {top["attention_score"]}/100</strong><br>
                <span class="muted">{top["detections"]} signals · {top["days_active"]}
                observation day(s) · confidence {top["mean_confidence"]:.0f}</span>
              </div>
              <p><strong>Why it matters:</strong> Agreement across satellites,
              repeat observations and peatland context help teams decide what
              to review first.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Peat polygons and satellite records in this prototype are illustrative "
            "scenario data, not current fire reports."
        )
    with right:
        st.plotly_chart(event_map(events), use_container_width=True)
        st.caption(
            "Each marker is a grouped fire area. Marker size represents the number "
            "of detections; the score is a review-priority aid, not fire confirmation."
        )

    st.info(
        "FireWatch turns separate satellite heat detections into a reviewable "
        "picture: where signals agree, which areas persist, and what may deserve "
        "human follow-up."
    )


def render_investigation(
    observations: pd.DataFrame, events: pd.DataFrame
) -> None:
    st.subheader("Investigate the satellite signals")
    st.write(
        "Compare MODIS and VIIRS detections. A match means the sensors saw nearby "
        "heat within the time and distance thresholds—it does not prove a fire."
    )

    regions = ["All regions"] + sorted(observations["region"].astype(str).unique())
    selected_region = st.selectbox("Focus area", regions, key="prototype_region")
    signals = observations.copy()
    fire_areas = events.copy()
    if selected_region != "All regions":
        signals = signals[signals["region"] == selected_region]
        fire_areas = fire_areas[fire_areas["region"] == selected_region]

    matched_count = int((signals["match_status"] == "matched").sum() / 2)
    c1, c2, c3 = st.columns(3)
    c1.metric("Signals in view", len(signals))
    c2.metric("Cross-satellite pairs", matched_count)
    c3.metric("Grouped fire areas", len(fire_areas))

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.plotly_chart(event_map(signals, signals=True), use_container_width=True)
    with right:
        daily = (
            signals.assign(day=signals["observed_at"].dt.strftime("%b %d"))
            .groupby(["day", "source"], as_index=False)
            .size()
        )
        chart = px.bar(
            daily,
            x="day",
            y="size",
            color="source",
            barmode="group",
            color_discrete_map=SOURCE_COLORS,
            labels={"day": "Observation day (UTC)", "size": "Signals"},
        )
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#eaf3ed",
            margin={"l": 0, "r": 0, "t": 20, "b": 0},
            legend={"orientation": "h", "y": 1.12, "x": 0},
        )
        st.plotly_chart(chart, use_container_width=True)

    with st.expander("Inspect records and match status"):
        st.dataframe(
            signals[
                [
                    "id",
                    "source",
                    "observed_at",
                    "region",
                    "confidence",
                    "match_status",
                    "match_distance_km",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )


def render_response(events: pd.DataFrame) -> None:
    st.subheader("Add a ground report")
    st.write(
        "The map helps direct attention; local knowledge adds context. Record a "
        "prototype report to show how a response loop could work."
    )
    options = {
        f'{row.event_id} · near {row.nearest_town} · {row.attention_level} '
        f'({row.attention_score}/100)': row.event_id
        for row in events.itertuples()
    }
    with st.form("prototype_ground_report", clear_on_submit=True):
        area_label = st.selectbox("Fire area", list(options))
        verdict = st.radio(
            "What are you seeing?",
            ["Confirmed fire", "Possible false alarm", "Not sure"],
            horizontal=True,
        )
        note = st.text_input("Short note (optional)", max_chars=180)
        submitted = st.form_submit_button("Add report", type="primary")
    if submitted:
        st.session_state.setdefault("prototype_reports", []).append(
            {
                "Fire area": options[area_label],
                "Report": verdict,
                "Note": note.strip() or "No additional note",
            }
        )
        st.success(
            "Report added to this browser session. It has not been sent to an "
            "official response team."
        )

    reports = st.session_state.get("prototype_reports", [])
    if reports:
        st.markdown("#### Reports added during this demo")
        st.dataframe(pd.DataFrame(reports), hide_index=True, use_container_width=True)
    else:
        st.caption("No reports yet. Add one above to demonstrate the feedback loop.")

    st.warning(
        "Prototype only: reports are kept in Streamlit session memory and are not "
        "saved to the production feedback file or shared with responders."
    )


try:
    observations, events, peat_available = load_scenario()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Could not load the bundled prototype scenario: {error}")
    st.stop()

if events.empty:
    st.error("The bundled scenario did not produce any fire areas.")
    st.stop()

first_day = observations["observed_at"].min().strftime("%d %b %Y")
last_day = observations["observed_at"].max().strftime("%d %b %Y")

with st.sidebar:
    st.markdown("### Demo flow")
    view = st.radio(
        "Choose a step",
        ["1 · Situation", "2 · Investigate", "3 · Ground report"],
        label_visibility="collapsed",
    )
    st.divider()
    with st.expander("90-second presentation guide", expanded=True):
        st.markdown(
            """
            1. **Start with the map:** detections become grouped fire areas.
            2. **Open Investigate:** show how two sensors can agree or differ.
            3. **Close with a report:** local context can improve the picture.

            **One-line pitch:** “Borneo FireWatch helps teams prioritize
            satellite heat signals with explainable evidence and ground feedback.”
            """
        )
    st.caption(f"Scenario period: {first_day} – {last_day}")
    st.caption("No sign-in, API key, or network data feed is required for this demo.")

st.markdown(
    """
    <div class="hero">
      <span class="demo-pill">HACKATHON PROTOTYPE · FICTIONAL SCENARIO</span>
      <div class="eyebrow" style="margin-top:14px">Borneo FireWatch</div>
      <h1>From heat signals to clearer decisions.</h1>
      <p>Explore satellite agreement, fire-area persistence and human reports
      in one guided view.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if view == "1 · Situation":
    render_overview(events, peat_available)
elif view == "2 · Investigate":
    render_investigation(observations, events)
else:
    render_response(events)

st.divider()
st.caption(
    "A thermal anomaly is not a confirmed fire. Attention scores and the "
    "illustrative peat layer support exploration only—not emergency response."
)
