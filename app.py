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
    "Throughput",
    "Variatie",
    "Creativiteit",
    "Data",
    "Uitlegbaarheid",
    "Efficiëntie",
]

PROFILES = {
    "Human":  [2, 5, 5, 3, 5, 2],
    "System": [5, 1, 1, 2, 5, 5],
    "AI":     [4, 4, 3, 5, 2, 4],
}

# -------- Layout: 40% | 60% --------
col_config, col_body = st.columns([4, 6], gap="large")

# ========== CONFIG (left) ==========
with col_config:
    config_card = st.container()
    with config_card:
        st.markdown('<div class="card-marker card-marker--config"></div>', unsafe_allow_html=True)

        st.header("⚙️ Configureer taak")
        st.caption(
            "Schaal 1–5 per as • Throughput: 1=constant · 5=schaalbaar • "
            "Variatie: 1=geen · 5=veel uitzonderingen • Creativiteit: 1=niet nodig · 5=essentieel • "
            "Data: 1=gestructureerd · 5=ongestructureerd • Uitlegbaarheid: 1=heel belangrijk · 5=minder belangrijk • "
            "Efficiëntie: 1=simpele taken · 5=complex op schaal"
        )

        defaults = [3, 3, 3, 3, 3, 3]
        slider_values = []
        for dim, default in zip(DIMENSIONS, defaults):
            slider_values.append(
                st.slider(dim, min_value=1, max_value=5, value=default, step=1, key=f"sl_{dim}")
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
    return 30 - sum(abs(t - p) for t, p in zip(task, profile))

# ========== BODY (right: Chart over Fit, equal height) ==========
with col_body:
    chart_card = st.container()
    with chart_card:
        st.markdown('<div class="card-marker card-marker--chart"></div>', unsafe_allow_html=True)

        fig = plt.figure(figsize=(14, 6))
        ax = plt.subplot(111, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ticks_deg = np.degrees(np.linspace(0, 2*np.pi, len(DIMENSIONS), endpoint=False))
        ax.set_thetagrids(ticks_deg, DIMENSIONS)
        ax.set_rlabel_position(0)
        ax.set_ylim(0, 5)

        # more space on the right for legend
        plt.subplots_adjust(left=0.06, right=0.62, top=0.92, bottom=0.12)

        for name, vals in PROFILES.items():
            plot_radar(ax, DIMENSIONS, vals, label=name, style="--", fill_alpha=0.06, lw=1.8)
        plot_radar(ax, DIMENSIONS, current_task, label="Current Task", style="-", fill_alpha=0.12, lw=2.4)

        ax.legend(loc="upper left", bbox_to_anchor=(1.10, 1.0), frameon=False, borderaxespad=0.0)
        plt.title("Human vs System vs AI vs Current Task")
        st.pyplot(fig, clear_figure=True, use_container_width=True)

    fit_card = st.container()
    with fit_card:
        st.markdown('<div class="card-marker card-marker--fit"></div>', unsafe_allow_html=True)

        scores = {n: fit_score(current_task, v) for n, v in PROFILES.items()}
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        st.subheader("📊 Fit scores")
        st.table({"Profile": [r[0] for r in ranked], "Score": [round(r[1], 1) for r in ranked]})
        st.success(f"**Best fit:** {ranked[0][0]}")
