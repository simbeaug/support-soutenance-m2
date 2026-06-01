"""
Interactive defense tool — M2 Thesis, UPEC
Medias, Immigration and Crime Rates in France: separating socio-economic factors from media perception
Authors: Simon Beaugrand and Mélissa Kurnaz
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Immigration & media framing",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# ============================================================
# M2 COEFFICIENTS (regression on the merged panel, N=60)
# share_crime_frame ~ const + b1*TAUX_IMMI + b2*TAUX_CRIM + b3*TAUX_CHOMAGE
#                   + b4*TAUX_PAUVRETE + b5*log(DENSITE)
# ============================================================
COEFS = {
    "const":      -0.0306,
    "immigration": 0.00056,
    "crime_real": -0.00069,
    "chomage":    -0.0336,
    "pauvrete":    0.0328,
    "logdens":     0.0153,
}

# WCB p-values for annotation
WCB_P = {
    "immigration": 0.921,
    "crime_real":  None,
    "chomage":     0.039,
    "pauvrete":    0.0002,  # randomization inference
    "logdens":     0.355,
}

# ============================================================
# DATA LOADERS (cache)
# ============================================================
@st.cache_data
def load_panel_source():
    return pd.read_csv(DATA / "panel_source.csv")

@st.cache_data
def load_panel_dept():
    p = DATA / "panel_dept.csv"
    return pd.read_csv(p, dtype={"CODGEO": str, "DEP": str, "code_dept": str}, low_memory=False) if p.exists() else None

@st.cache_data
def load_source_to_depts():
    with open(DATA / "source_to_depts.json", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_geojson():
    p = DATA / "departements.geojson"
    if not p.exists(): return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# HELPERS — project source-level data onto departments
# ============================================================
def project_source_to_depts(source_panel: pd.DataFrame, year: int, var: str, mapping: dict) -> pd.DataFrame:
    """Project a source-level variable onto the departments covered by each title."""
    sub = source_panel[source_panel["year"] == year]
    rows = []
    for _, row in sub.iterrows():
        depts = mapping.get(row["source"], [])
        for d in depts:
            rows.append({"code_dept": d, "value": row[var], "source": row["source"]})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Deduplicate: a department may be covered by several titles (e.g., Brest = Ouest-France + Le Télégramme)
    # → average across titles
    return df.groupby("code_dept", as_index=False).agg({"value": "mean", "source": lambda s: ", ".join(sorted(set(s)))})


def predict_share_crime_frame(immig, crime, chom, pauv, dens):
    """Apply the M2 model to a feature vector."""
    return (COEFS["const"]
            + COEFS["immigration"] * immig
            + COEFS["crime_real"] * crime
            + COEFS["chomage"] * chom
            + COEFS["pauvrete"] * pauv
            + COEFS["logdens"] * np.log(max(dens, 1.0)))


# ============================================================
# UI — SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🇫🇷 Immigration & media framing")
    st.caption("Interactive defense tool — M2 Thesis, UPEC")
    st.markdown("---")
    page = st.radio("Navigation", ["🗺️  Cartography", "🎚️  Simulator", "ℹ️  About"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Data: INSEE (real-world), Europresse + DistilCamemBERT (media), 2016-2021.")

source_panel = load_panel_source()
dept_panel   = load_panel_dept()
mapping      = load_source_to_depts()
geojson      = load_geojson()

# ============================================================
# PAGE 1 — CARTOGRAPHY
# ============================================================
if page.endswith("Cartography"):
    st.title("Mapping the raw correlations")
    st.markdown(
        "Compare two maps of France side by side. In **raw geographic distributions**, all socio-economic "
        "variables — poverty, immigration, unemployment, recorded crime — display some correlation with "
        "crime framing. The patterns are similar across variables. This is precisely the **confounded picture** "
        "that motivates a rigorous regression with simultaneous controls. The **Simulator** tab applies the M2 "
        "model and shows which variable actually survives."
    )

    VAR_OPTIONS = {
        "Crime framing (press)":            ("share_crime_frame", "OrRd",  "Share of immigration articles framed as crime"),
        "Immigration rate (real)":          ("TAUX_IMMI",         "Blues", "% immigrants (INSEE)"),
        "Poverty rate":                     ("TAUX_PAUVRETE",     "Purples","% below the poverty line"),
        "Recorded crime per 1,000":         ("TAUX_CRIM_GLOBAL_1000", "Reds", "Overall crime index"),
        "Unemployment rate":                ("TAUX_CHOMAGE",      "Greens","% unemployed"),
    }

    c_top1, c_top2, c_top3 = st.columns([1, 1, 2])
    with c_top1:
        var_left = st.selectbox("Left map", list(VAR_OPTIONS.keys()), index=2)
    with c_top2:
        var_right = st.selectbox("Right map", list(VAR_OPTIONS.keys()), index=0)
    with c_top3:
        year = st.slider("Year", 2016, 2021, 2019)

    if geojson is None:
        st.error("⚠️  data/departements.geojson missing. See the README.")
        st.stop()

    def make_map(var_label):
        col, scale, label = VAR_OPTIONS[var_label]
        df_proj = project_source_to_depts(source_panel, year, col, mapping)
        fig = px.choropleth(
            df_proj,
            geojson=geojson,
            locations="code_dept",
            featureidkey="properties.code",
            color="value",
            color_continuous_scale=scale,
            hover_data={"code_dept": True, "value": ":.2f", "source": True},
            labels={"value": label, "source": "Title(s)"},
        )
        fig.update_geos(
            visible=False, fitbounds="locations",
            projection_type="mercator",
            bgcolor="rgba(0,0,0,0)",
        )
        fig.update_layout(
            title=dict(text=f"<b>{var_label}</b> — {year}", x=0.5, xanchor="center"),
            margin=dict(l=0, r=0, t=40, b=0),
            height=520,
            coloraxis_colorbar=dict(title=""),
        )
        return fig

    c_left, c_right = st.columns(2)
    with c_left:
        st.plotly_chart(make_map(var_left), use_container_width=True)
    with c_right:
        st.plotly_chart(make_map(var_right), use_container_width=True)

    st.markdown("---")
    with st.expander("💡 Suggested reading for the defense"):
        st.markdown(
            "1. **Compare any socio-economic variable with crime framing** → you will see that the colour "
            "patterns broadly follow each other. This is the raw confounding that the regression has to disentangle.\n"
            "2. **Compare immigration with recorded crime** → strong visual correlation in the cross-section. "
            "This is the journalist's reading — and it is precisely what controls dissolve.\n"
            "3. **Switch to the Simulator tab** to see which variable actually drives the prediction once all "
            "controls are applied simultaneously. Spoiler: poverty does; immigration does not."
        )

    st.caption(
        "Note: values are projected at the **press coverage zone** level (departments covered by the same title "
        "share the same value). Territories not covered by the 10 selected titles (parts of Alsace, the Alps, "
        "Centre-Val-de-Loire) appear in white."
    )


# ============================================================
# PAGE 2 — SIMULATOR
# ============================================================
elif page.endswith("Simulator"):
    st.title("Crime-framing simulator")
    st.markdown(
        "Vary the characteristics of a hypothetical territory and observe the M2 model's prediction for the "
        "share of immigration articles framed as crime (**share_crime_frame**). The goal: see "
        "**which variable actually moves the result** once all controls are applied simultaneously."
    )

    c1, c2 = st.columns([1, 1.2])

    with c1:
        st.subheader("Territory characteristics")

        preset = st.radio("Quick scenario", ["Custom", "Affluent territory", "Deprived territory", "Corpus average"], horizontal=True)
        if preset == "Affluent territory":
            d = {"immig": 7.0, "crime": 45.0, "chom": 6.0, "pauv": 10.0, "dens": 250}
        elif preset == "Deprived territory":
            d = {"immig": 9.0, "crime": 60.0, "chom": 12.0, "pauv": 18.0, "dens": 250}
        elif preset == "Corpus average":
            d = {"immig": 8.5, "crime": 52.0, "chom":  8.5, "pauv": 14.5, "dens": 280}
        else:
            d = {"immig": 8.5, "crime": 52.0, "chom":  8.5, "pauv": 14.5, "dens": 280}

        immig = st.slider("Immigration rate (%)",          3.0, 20.0, d["immig"], 0.1)
        pauv  = st.slider("Poverty rate (%)",              8.0, 25.0, d["pauv"],  0.1)
        chom  = st.slider("Unemployment rate (%)",         4.0, 16.0, d["chom"],  0.1)
        crime = st.slider("Recorded crime (per 1,000)",   20.0, 90.0, d["crime"], 1.0)
        dens  = st.slider("Density (inhab/km², log scale)", 30, 5000, int(d["dens"]), 10)

    with c2:
        st.subheader("Prediction")
        pred = predict_share_crime_frame(immig, crime, chom, pauv, dens)
        pred_pct = pred * 100
        baseline = predict_share_crime_frame(8.5, 52, 8.5, 14.5, 280) * 100

        st.metric(
            label="Share of immigration articles framed as crime",
            value=f"{pred_pct:.1f} %",
            delta=f"{pred_pct - baseline:+.1f} pts vs. corpus average",
        )

        # Decomposition: contribution of each variable relative to the corpus average
        contribs = {
            "Poverty":            COEFS["pauvrete"]    * (pauv  - 14.5) * 100,
            "Unemployment":       COEFS["chomage"]     * (chom  -  8.5) * 100,
            "log(Density)":       COEFS["logdens"]     * (np.log(dens) - np.log(280)) * 100,
            "Immigration":        COEFS["immigration"] * (immig -  8.5) * 100,
            "Recorded crime":     COEFS["crime_real"]  * (crime - 52)   * 100,
        }
        order = sorted(contribs.keys(), key=lambda k: abs(contribs[k]), reverse=True)

        st.markdown("**Contribution of each variable** (in points relative to the corpus average)")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[contribs[k] for k in order],
            y=order,
            orientation="h",
            marker_color=["#E74C3C" if contribs[k] > 0 else "#3498DB" for k in order],
            text=[f"{contribs[k]:+.2f} pts" for k in order],
            textposition="outside",
            hovertemplate="%{y}: %{x:+.2f} points<extra></extra>",
        ))
        fig.add_vline(x=0, line_color="gray", line_width=1)
        fig.update_layout(
            height=260,
            margin=dict(l=10, r=80, t=20, b=20),
            xaxis_title="Contribution (points)",
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Reading: a red bar means the variable pulls crime framing UP relative to a corpus-average territory; "
            "a blue bar pulls it DOWN. "
            "**Move immigration from 5 to 20%: the prediction barely changes. "
            "Move poverty from 10 to 20%: the prediction shifts visibly.**"
        )

    # Statistical significance
    st.markdown("---")
    st.markdown("##### Statistical significance (M2, N=60, 10 clusters)")
    rows = []
    for k, lbl in [("immigration", "Immigration"), ("pauvrete", "Poverty"),
                   ("chomage", "Unemployment"), ("logdens", "log(Density)"), ("crime_real", "Recorded crime")]:
        p = WCB_P.get(k)
        sig = "—" if p is None else (
            "✅ Significant (p < 0.001)" if p < 0.001 else
            "✅ Significant (5%)" if p < 0.05 else
            "❌ Not significant"
        )
        rows.append({"Variable": lbl, "Coefficient β": f"{COEFS[k]:+.4f}", "WCB p-value": "—" if p is None else f"{p:.3f}", "Status": sig})
    st.table(pd.DataFrame(rows))


# ============================================================
# PAGE 3 — ABOUT
# ============================================================
else:
    st.title("About")
    st.markdown("""
**M2 Thesis** — Université Paris-Est Créteil (UPEC), 2025-2026
Authors: Simon Beaugrand and Mélissa Kurnaz

### Research question
Do French media maintain an **overrepresentation** of the link between immigration and crime relative to
statistical reality, or does this link **dissolve on both sides** once the socio-economic context is
controlled for?

### Methodology
- **Econometric chapter**: department × year panel, 2016-2021 (96 departments, 576 observations), OLS +
two-way fixed effects + IV strategy (shift-share).
- **NLP chapter**: original corpus of **25,783 articles** on immigration extracted from **10 regional
dailies** via Europresse, lexical-dictionary analysis for framing and **DistilCamemBERT** for sentiment.

### Finding
**Double decoupling**. Once the socio-economic context is controlled for, immigration explains neither
recorded crime nor the way the regional press frames immigration in criminal terms. On both sides, the
variable correlated with the outcome is the **poverty rate** of the territory.

### This tool
- **Cartography tab**: compares two side-by-side maps. In raw terms, all socio-economic variables
(poverty, immigration, recorded crime) display some geographic correlation with crime framing. This is
the confounded picture that motivates the regression.
- **Simulator tab**: applies the M2 regression with all controls held constant. Moving the immigration
slider barely changes the prediction; moving the poverty slider changes it significantly. This is the
double decoupling, made tangible.
""")
