from pathlib import Path

import plotly.graph_objects as go
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
def fit_score(task, profile):
    total_diff = sum(abs(t - p) for t, p in zip(task, profile))
    if MAX_TOTAL_DIFF == 0:
        return 100.0
    score = 100.0 - (total_diff / MAX_TOTAL_DIFF) * 100.0
    return max(0.0, score)


def build_radar_figure(task_values):
    # close the polygon by repeating the first point at the end
    categories = DIMENSIONS + [DIMENSIONS[0]]
    palette = {
        "Human": {
            "color": "#1f77b4",
            "fill": "rgba(31, 119, 180, 0.08)",
            "dash": "dash",
        },
        "System": {
            "color": "#ff7f0e",
            "fill": "rgba(255, 127, 14, 0.08)",
            "dash": "dash",
        },
        "AI": {
            "color": "#2ca02c",
            "fill": "rgba(44, 160, 44, 0.08)",
            "dash": "dash",
        },
    }

    fig = go.Figure()

    for name, values in PROFILES.items():
        style = palette.get(name, {"color": "#6c757d", "fill": "rgba(0,0,0,0.05)", "dash": "dash"})
        vals = values + values[:1]
        fig.add_trace(
            go.Scatterpolar(
                r=vals,
                theta=categories,
                name=name,
                mode="lines",
                line=dict(color=style["color"], width=1.4, dash=style["dash"]),
                fill="toself",
                fillcolor=style["fill"],
                hovertemplate=f"<b>%{{theta}}</b><br>%{{r:.0f}}<extra>{name}</extra>",
            )
        )

    task_vals = task_values + task_values[:1]
    fig.add_trace(
        go.Scatterpolar(
            r=task_vals,
            theta=categories,
            name="Your Task",
            mode="lines",
            line=dict(color="#111111", width=2.2),
            fill="toself",
            fillcolor="rgba(17, 17, 17, 0.12)",
            hovertemplate="<b>%{theta}</b><br>%{r:.0f}<extra>Your Task</extra>",
        )
    )

    fig.update_layout(
        height=440,
        margin=dict(t=36, b=36, l=40, r=160),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                range=[SCALE_MIN, SCALE_MAX],
                tickvals=list(range(SCALE_MIN, SCALE_MAX + 1)),
                tickfont=dict(size=11, color="#666666"),
                gridcolor="#d5d5d5",
                gridwidth=1,
            ),
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickfont=dict(size=11, color="#444444"),
            ),
        ),
        legend=dict(
            title=None,
            orientation="v",
            yanchor="middle",
            xanchor="left",
            x=1.18,
            y=0.5,
            font=dict(size=11, color="#333333"),
            bgcolor="rgba(255,255,255,0.85)",
        ),
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig

# ========== BODY (right: Chart over Fit, equal height) ==========
with col_body:
    chart_card = st.container()
    with chart_card:
        st.markdown('<div class="card-marker card-marker--chart"></div>', unsafe_allow_html=True)

        fig = build_radar_figure(current_task)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    fit_card = st.container()
    with fit_card:
        st.markdown('<div class="card-marker card-marker--fit"></div>', unsafe_allow_html=True)

        scores = {n: fit_score(current_task, v) for n, v in PROFILES.items()}
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        st.subheader("📊 Fit scores")
        st.table({"Profile": [r[0] for r in ranked], "Score": [f"{round(r[1])}%" for r in ranked]})
        st.success(f"**Best fit:** {ranked[0][0]} ({ranked[0][1]:.0f}%)")
