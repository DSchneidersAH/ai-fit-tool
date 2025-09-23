import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="AI Fit Tool", layout="wide")

# -------- Load external CSS --------
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("style.css niet gevonden – draai je in prod zonder mounts?")

# -------- Dimensions / Profiles --------
DIMENSIONS = [
    "Repeatability",
    "Variation",
    "Complexity",
    "Pace",
    "Scalability",
    "Data Structure",
    "Adaptability",
    "Impact",
    "Explainability",
    "Cost",
]

SLIDER_COPY = {
    "Repeatability": {
        "question": "How repeatable is this task?",
        "low": "Similar routine",
        "high": "Unique every time",
    },
    "Variation": {
        "question": "How much variation does the execution involve?",
        "low": "Hardly any variation",
        "high": "Lots of variation",
    },
    "Complexity": {
        "question": "How complex is the task in terms of dependencies and variables?",
        "low": "Simple and independent",
        "high": "Highly complex",
    },
    "Pace": {
        "question": "What should be the pace of task completion?",
        "low": "Delay is acceptable",
        "high": "Real-time",
    },
    "Scalability": {
        "question": "How important is the ability to scale the task up or down?",
        "low": "Stable, fixed workload",
        "high": "Needs to scale dynamically",
    },
    "Data Structure": {
        "question": "How structured is the input and output data or information?",
        "low": "Standardised & structured",
        "high": "Highly unstructured",
    },
    "Adaptability": {
        "question": "How much adaptability is required over time?",
        "low": "Stable and predictable",
        "high": "Needs frequent adjustment",
    },
    "Impact": {
        "question": "What is the impact of an error in this task?",
        "low": "Low impact, easy to fix",
        "high": "High impact, costly/critical",
    },
    "Explainability": {
        "question": "How explainable should the decision-making be?",
        "low": "Low need for explainability",
        "high": "High need for explainability",
    },
    "Cost": {
        "question": "How important is the cost per execution?",
        "low": "Not important",
        "high": "Highly important",
    },
}

SCALE_MIN = 1
SCALE_MAX = 10
SCALE_STEP = 1

def map_to_scale(value: int, src_min: int = 1, src_max: int = 10) -> int:
    """Convert a 1-5 score to the widened 1-10 scale (rounded)."""
    if value < src_min or value > src_max:
        raise ValueError("Profile values must be between 1 and 5 before scaling")
    src_span = src_max - src_min
    dst_span = SCALE_MAX - SCALE_MIN
    scaled = SCALE_MIN + ((value - src_min) / src_span) * dst_span
    return int(round(scaled))

PROFILES = {
    "Human":  [map_to_scale(v) for v in [9, 4, 3, 2, 1, 5, 8, 7, 7, 1]],
    "System": [map_to_scale(v) for v in [1, 1, 3, 8, 9, 1, 1, 4, 9, 9]],
    "AI":     [map_to_scale(v) for v in [6, 8, 4, 4, 5, 6, 5, 3, 2, 6]],
}

MAX_TOTAL_DIFF = (SCALE_MAX - SCALE_MIN) * len(DIMENSIONS)

# -------- Layout: 50% | 50% --------
col_config, col_body = st.columns([5, 5], gap="large")

# ========== CONFIG (left) ==========
with col_config:
    config_card = st.container()
    with config_card:
        st.markdown('<div class="card-marker card-marker--config"></div>', unsafe_allow_html=True)

        st.header("Score your task")
        #st.caption(
        #    "To understand which approach fits your solution best, keep a task in mind and score it on the following dimensions. Do this for each task in your solution."
        #)

        defaults = [5] * len(DIMENSIONS)
        slider_values = []
        for dim, default in zip(DIMENSIONS, defaults):
            meta = SLIDER_COPY.get(
                dim,
                {"question": dim, "low": "Low", "high": "High"},
            )

            st.markdown(
                f'<p class="slider-question">{meta["question"]}</p>',
                unsafe_allow_html=True,
            )

            col_low, col_slider, col_high = st.columns([1.2, 3.6, 1.2])
            with col_low:
                st.markdown(
                    f'<span class="slider-edge slider-edge--left">{meta["low"]}</span>',
                    unsafe_allow_html=True,
                )
            with col_slider:
                slider_values.append(
                    st.slider(
                        dim,
                        min_value=SCALE_MIN,
                        max_value=SCALE_MAX,
                        value=default,
                        step=SCALE_STEP,
                        key=f"sl_{dim}",
                        label_visibility="collapsed",
                    )
                )
            with col_high:
                st.markdown(
                    f'<span class="slider-edge slider-edge--right">{meta["high"]}</span>',
                    unsafe_allow_html=True,
                )

current_task = slider_values

# -------- Helpers --------
def radar_factory(num_vars: int):
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    theta += theta[:1]
    return theta

def plot_radar(ax, categories, values, label=None, style="-", fill_alpha=0.10, lw=2):
    theta = radar_factory(len(categories))
    vals = values + values[:1]
    ax.plot(theta, vals, style, linewidth=lw, label=label)
    if fill_alpha and fill_alpha > 0:
        ax.fill(theta, vals, alpha=fill_alpha)

def fit_score(task, profile):
    total_diff = sum(abs(t - p) for t, p in zip(task, profile))
    if MAX_TOTAL_DIFF == 0:
        return 100.0
    score = 100.0 - (total_diff / MAX_TOTAL_DIFF) * 100.0
    return max(0.0, score)

# ========== BODY (right: Chart over Fit, equal height) ==========
with col_body:
    chart_card = st.container()
    with chart_card:
        st.markdown('<div class="card-marker card-marker--chart"></div>', unsafe_allow_html=True)

        fig = plt.figure(figsize=(6, 4), dpi=500)
        ax = plt.subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ticks_deg = np.degrees(np.linspace(0, 2*np.pi, len(DIMENSIONS), endpoint=False))
        ax.set_thetagrids(ticks_deg, DIMENSIONS, fontsize=8)
        ax.set_rlabel_position(0)
        ax.set_ylim(0, SCALE_MAX)
        ax.set_yticks(range(SCALE_MIN, SCALE_MAX + 1))
        ax.set_yticklabels([str(v) for v in range(SCALE_MIN, SCALE_MAX + 1)])
        ax.tick_params(axis="x", pad=16, labelsize=8, colors="#444444")
        ax.tick_params(axis="y", labelsize=7, colors="#666666")
        ax.yaxis.grid(color="#d5d5d5", linewidth=0.6)

        # widen canvas so the figure stays landscape and leaves breathing room for the legend
        plt.subplots_adjust(left=0.08, right=0.54, top=0.90, bottom=0.10)

        for name, vals in PROFILES.items():
            plot_radar(ax, DIMENSIONS, vals, label=name, style="--", fill_alpha=0.06, lw=1.2)
        plot_radar(ax, DIMENSIONS, current_task, label="Your Task", style="-", fill_alpha=0.12, lw=1.8)

        ax.legend(
            loc="center left",
            bbox_to_anchor=(1.5, 0.5),
            frameon=True,
            borderaxespad=0.0,
        )
        st.pyplot(fig, clear_figure=True)

    fit_card = st.container()
    with fit_card:
        st.markdown('<div class="card-marker card-marker--fit"></div>', unsafe_allow_html=True)

        scores = {n: fit_score(current_task, v) for n, v in PROFILES.items()}
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        st.subheader("📊 Fit scores")
        st.table({"Profile": [r[0] for r in ranked], "Score": [f"{round(r[1])}%" for r in ranked]})
        st.success(f"**Best fit:** {ranked[0][0]} ({ranked[0][1]:.0f}%)")
