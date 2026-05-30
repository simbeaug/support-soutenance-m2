# Outil interactif de soutenance

Démonstration interactive du résultat principal du mémoire :
**la géographie du cadrage médiatique de l'immigration suit celle de la pauvreté, pas celle de l'immigration réelle.**

## Lancement rapide

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre dans le navigateur (`http://localhost:8501`).

## Structure du dossier

```
streamlit_app/
├── app.py                    # application Streamlit (3 onglets)
├── requirements.txt
├── README.md
└── data/
    ├── panel_source.csv       # ✅ inclus : panel fusionné 10 titres × 6 ans (60 obs)
    ├── source_to_depts.json   # ✅ inclus : mapping titre → départements couverts
    ├── departements.geojson   # ✅ inclus : 96 départements métropolitains (data.gouv via gregoiredavid)
    └── panel_dept.csv         # ❌ OPTIONNEL : panel département × année (Mélissa)
```

### `panel_dept.csv` (optionnel)

Si tu veux afficher les cartes en **résolution département** plutôt qu'en territoire de presse, dépose le panel département
de Mélissa sous le nom `data/panel_dept.csv` avec **au minimum** les colonnes :
- `code_dept` (string, ex. "01", "75", "2A")
- `year` (int)
- `TAUX_CRIM_GLOBAL_1000`, `TAUX_IMMI`, `TAUX_PAUVRETE`, `TAUX_CHOMAGE`, `DENSITE`

Sans ce fichier, les valeurs sont projetées au niveau **territoire de couverture du titre** (tous les départements
d'un même journal partagent la même couleur). C'est moins fin mais ça raconte aussi l'histoire.

## Les trois onglets

1. **🗺️ Cartographie** — Deux cartes de France côte à côte, choix libre des variables, curseur temporel.
   Voir le bloc "Suggestion de lecture pour la soutenance" en bas de page pour les trois comparaisons à montrer au jury.

2. **🎚️ Simulateur** — Sliders pour les caractéristiques d'un territoire fictif ; la prédiction du modèle M2
   s'actualise en direct, avec décomposition de la contribution de chaque variable.

3. **ℹ️ À propos** — Contexte et message-clé du mémoire (utile si tu veux laisser l'outil en libre accès au jury).

## Backup avant la soutenance

Une démo Streamlit qui crashe devant le jury, c'est la pire chose qui puisse arriver. Prépare une **vidéo de capture
d'écran** de l'application (OBS Studio, QuickTime ou Loom) en deux temps :
1. Trois comparaisons de cartes (pauvreté/cadrage, immigration/cadrage, crime réel/cadrage),
2. Trois sliders du simulateur (immigration de 5 à 20, pauvreté de 10 à 20, observation de la prédiction).

Garde la vidéo sur ta machine **et** sur clé USB.

## Personnalisation rapide

- **Couleurs des cartes** : modifie le `color_continuous_scale` dans `VAR_OPTIONS` (échelles plotly disponibles ici :
  https://plotly.com/python/builtin-colorscales/).
- **Coefficients M2** : modifie le dictionnaire `COEFS` en haut de `app.py` si tu réestimes le modèle avec d'autres données.
- **Plage des sliders du simulateur** : modifie les `min`/`max` des `st.slider` dans la fonction Simulateur.
