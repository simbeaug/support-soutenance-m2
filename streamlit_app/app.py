"""
Outil interactif de soutenance — mémoire M2 UPEC
Immigration et criminalité en France : démêler réalité socio-économique et perception médiatique
Auteur : Simon ([co-auteur])
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
    page_title="Immigration & cadrage médiatique",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# ============================================================
# COEFFICIENTS M2 (régression sur le panel fusionné, N=60)
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

# WCB p-values pour annoter
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
# HELPERS — projection source → départements
# ============================================================
def project_source_to_depts(source_panel: pd.DataFrame, year: int, var: str, mapping: dict) -> pd.DataFrame:
    """Projette une variable source-level sur les départements couverts par chaque titre."""
    sub = source_panel[source_panel["year"] == year]
    rows = []
    for _, row in sub.iterrows():
        depts = mapping.get(row["source"], [])
        for d in depts:
            rows.append({"code_dept": d, "value": row[var], "source": row["source"]})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Dédupliquer : un département peut être couvert par plusieurs titres (ex : Brest = Ouest-France + Le Télégramme)
    # → moyenne
    return df.groupby("code_dept", as_index=False).agg({"value": "mean", "source": lambda s: ", ".join(sorted(set(s)))})


def predict_share_crime_frame(immig, crime, chom, pauv, dens):
    """Applique le modèle M2 à un vecteur de caractéristiques."""
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
    st.markdown("### 🇫🇷 Immigration et cadrage médiatique")
    st.caption("Outil interactif de soutenance — mémoire M2, UPEC")
    st.markdown("---")
    page = st.radio("Navigation", ["🗺️  Cartographie", "🎚️  Simulateur", "ℹ️  À propos"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Données : INSEE (réel), Europresse + DistilCamemBERT (média), 2016-2021.")

source_panel = load_panel_source()
dept_panel   = load_panel_dept()
mapping      = load_source_to_depts()
geojson      = load_geojson()

# ============================================================
# PAGE 1 — CARTOGRAPHIE
# ============================================================
if page.endswith("Cartographie"):
    st.title("Cartographie du découplage")
    st.markdown(
        "Comparez côte à côte deux cartes pour observer si la géographie de la **réalité socio-économique** "
        "et celle du **cadrage médiatique** se correspondent. Le résultat central du mémoire devient visible : "
        "**la couleur de la pauvreté ressemble à celle du cadrage criminel ; la couleur de l'immigration "
        "réelle ressemble à celle du crime réel, mais ni l'une ni l'autre n'explique le cadrage une fois les contrôles posés.**"
    )

    VAR_OPTIONS = {
        "Cadrage criminel (presse)":      ("share_crime_frame", "OrRd",  "Part d'articles immigration cadrés crime"),
        "Taux d'immigration (réel)":      ("TAUX_IMMI",         "Blues", "% d'immigrés (INSEE)"),
        "Taux de pauvreté":               ("TAUX_PAUVRETE",     "Purples","% de personnes sous le seuil de pauvreté"),
        "Crime réel pour 1000 hab.":      ("TAUX_CRIM_GLOBAL_1000", "Reds", "Indice de criminalité globale"),
        "Taux de chômage":                ("TAUX_CHOMAGE",      "Greens","% de chômeurs"),
    }

    c_top1, c_top2, c_top3 = st.columns([1, 1, 2])
    with c_top1:
        var_left = st.selectbox("Carte de gauche", list(VAR_OPTIONS.keys()), index=2)
    with c_top2:
        var_right = st.selectbox("Carte de droite", list(VAR_OPTIONS.keys()), index=0)
    with c_top3:
        year = st.slider("Année", 2016, 2021, 2019)

    if geojson is None:
        st.error("⚠️  data/departements.geojson manquant. Voir le README.")
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
            labels={"value": label, "source": "Titre(s)"},
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

    st.caption(
        "Note : les valeurs sont projetées au niveau du **territoire de couverture de chaque titre** (les départements "
        "couverts par un même journal partagent la même valeur). Les territoires non couverts par les 10 titres retenus "
        "(Alsace, Alpes, Centre-Val-de-Loire en partie) apparaissent en blanc."
    )


# ============================================================
# PAGE 2 — SIMULATEUR
# ============================================================
elif page.endswith("Simulateur"):
    st.title("Simulateur de cadrage criminel")
    st.markdown(
        "Faites varier les caractéristiques d'un territoire fictif et observez la prédiction du modèle M2 "
        "sur la part d'articles immigration cadrés en termes de criminalité (**share_crime_frame**). "
        "Le but : voir **quelle variable bouge réellement le résultat**."
    )

    c1, c2 = st.columns([1, 1.2])

    with c1:
        st.subheader("Caractéristiques du territoire")

        preset = st.radio("Scénario rapide", ["Personnalisé", "Territoire riche", "Territoire pauvre", "Moyenne du corpus"], horizontal=True)
        if preset == "Territoire riche":
            d = {"immig": 7.0, "crime": 45.0, "chom": 6.0, "pauv": 10.0, "dens": 250}
        elif preset == "Territoire pauvre":
            d = {"immig": 9.0, "crime": 60.0, "chom": 12.0, "pauv": 18.0, "dens": 250}
        elif preset == "Moyenne du corpus":
            d = {"immig": 8.5, "crime": 52.0, "chom":  8.5, "pauv": 14.5, "dens": 280}
        else:
            d = {"immig": 8.5, "crime": 52.0, "chom":  8.5, "pauv": 14.5, "dens": 280}

        immig = st.slider("Taux d'immigration (%)",   3.0, 20.0, d["immig"], 0.1)
        pauv  = st.slider("Taux de pauvreté (%)",     8.0, 25.0, d["pauv"],  0.1)
        chom  = st.slider("Taux de chômage (%)",      4.0, 16.0, d["chom"],  0.1)
        crime = st.slider("Crime réel (pour 1000)", 20.0, 90.0, d["crime"], 1.0)
        dens  = st.slider("Densité (hab/km², échelle log)", 30, 5000, int(d["dens"]), 10)

    with c2:
        st.subheader("Prédiction")
        pred = predict_share_crime_frame(immig, crime, chom, pauv, dens)
        pred_pct = pred * 100
        baseline = predict_share_crime_frame(8.5, 52, 8.5, 14.5, 280) * 100

        st.metric(
            label="Part d'articles immigration cadrés crime",
            value=f"{pred_pct:.1f} %",
            delta=f"{pred_pct - baseline:+.1f} pts vs. moyenne du corpus",
        )

        # Décomposition : contribution de chaque variable par rapport à la moyenne
        contribs = {
            "Pauvreté":            COEFS["pauvrete"]    * (pauv  - 14.5) * 100,
            "Chômage":             COEFS["chomage"]     * (chom  -  8.5) * 100,
            "log(Densité)":        COEFS["logdens"]     * (np.log(dens) - np.log(280)) * 100,
            "Immigration":         COEFS["immigration"] * (immig -  8.5) * 100,
            "Crime réel":          COEFS["crime_real"]  * (crime - 52)   * 100,
        }
        order = sorted(contribs.keys(), key=lambda k: abs(contribs[k]), reverse=True)

        st.markdown("**Contribution de chaque variable** (en points par rapport à la moyenne du corpus)")
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
            "Lecture : une barre rouge = la variable tire le cadrage criminel vers le haut, "
            "bleue = vers le bas, par rapport à un territoire « moyen » du corpus. "
            "**Faites monter l'immigration de 5 à 20% : la prédiction ne bouge presque pas. "
            "Faites monter la pauvreté de 10 à 20% : la prédiction change visiblement.**"
        )

    # Significativité
    st.markdown("---")
    st.markdown("##### Significativité statistique (M2, N=60, 10 clusters)")
    rows = []
    for k, lbl in [("immigration", "Immigration"), ("pauvrete", "Pauvreté"),
                   ("chomage", "Chômage"), ("logdens", "log(Densité)"), ("crime_real", "Crime réel")]:
        p = WCB_P.get(k)
        sig = "—" if p is None else (
            "✅ Significatif (p < 0,001)" if p < 0.001 else
            "✅ Significatif (5%)" if p < 0.05 else
            "❌ Non significatif"
        )
        rows.append({"Variable": lbl, "Coefficient β": f"{COEFS[k]:+.4f}", "WCB p-value": "—" if p is None else f"{p:.3f}", "Statut": sig})
    st.table(pd.DataFrame(rows))


# ============================================================
# PAGE 3 — À PROPOS
# ============================================================
else:
    st.title("À propos")
    st.markdown("""
**Mémoire de M2** — Université Paris-Est Créteil (UPEC), 2025-2026
Auteurs : Simon Beaugrand et Mélissa Kurnaz

### Question
Les médias français maintiennent-ils une **surreprésentation** du lien entre immigration et criminalité par rapport à la
réalité statistique, ou ce lien **se dissout-il** des deux côtés une fois le contexte socio-économique pris en compte ?

### Méthodologie
- **Volet économétrique** : panel département × année, 2016-2021 (96 départements, 576 observations), OLS + effets fixes
+ stratégie IV (shift-share).
- **Volet NLP** : corpus original de **25 783 articles** sur l'immigration extraits de **10 quotidiens régionaux** via Europresse,
analyse par dictionnaires lexicaux pour le cadrage et **DistilCamemBERT** pour le sentiment.

### Réponse
**Double découplage**. Sous contrôles, l'immigration n'explique ni le crime réel, ni la façon dont la presse cadre ce crime.
Des deux côtés, la variable corrélée au résultat est la **pauvreté** du territoire.

### Cet outil
- **Onglet Cartographie** : compare deux cartes côte à côte. En données brutes, les trois 
variables socio-économiques (pauvreté, immigration, crime réel) montrent toutes une corrélation 
géographique visible avec le cadrage médiatique. C'est précisément ce constat de confusion 
non-contrôlée qui motive la régression rigoureuse.
- **Onglet Simulateur** : applique le modèle M2 estimé avec tous les contrôles simultanés. 
Faire varier l'immigration ne change presque pas la prédiction de cadrage criminel, faire 
varier la pauvreté la change beaucoup.
""")
