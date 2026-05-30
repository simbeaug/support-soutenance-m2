# Déploiement sur Streamlit Community Cloud

Guide pas-à-pas pour mettre l'app en ligne et partager l'URL avec Mélissa.
Temps total : 15 à 20 minutes. Aucune ligne de commande, tout passe par le navigateur.

## Étape 1. Compte GitHub

Si tu n'as pas de compte GitHub :
1. Aller sur https://github.com/signup
2. Renseigner email, mot de passe, username. Username court et professionnel
   (il apparaîtra dans l'URL de l'app, par exemple `simondupont`).
3. Valider l'email.

Si tu as déjà un compte, tu te connectes simplement.

## Étape 2. Créer le repository

1. En haut à droite, clique sur le « + » → **New repository**.
2. Repository name : `memoire-m2-soutenance` (ou un nom de ton choix, sans accents ni espaces).
3. Description : « Outil interactif pour la soutenance du mémoire M2 UPEC ».
4. **Public** (recommandé pour ce cas, plus simple à déployer).
5. **Coche « Add a README file »**.
6. Clique sur **Create repository**.

Tu arrives sur la page du repo, qui ne contient qu'un fichier README.md vide.

## Étape 3. Uploader les fichiers du dossier `streamlit_app/`

1. Sur la page du repo, clique sur **Add file → Upload files**.
2. Ouvre le dossier `streamlit_app/` sur ton ordi, et **drag-and-drop tous les fichiers et sous-dossiers** dans la zone d'upload :
   - `app.py`
   - `requirements.txt`
   - `README.md` (il écrasera le README vide créé par GitHub — c'est voulu)
   - `.gitignore`
   - `DEPLOY.md` (ce fichier, pour mémoire)
   - le dossier `data/` complet, avec `panel_source.csv`, `source_to_depts.json` et `departements.geojson` à l'intérieur

   **Astuce** : si le drag-and-drop refuse les dossiers, tu peux sélectionner tous les fichiers du dossier `data/` et les glisser ; GitHub recréera la hiérarchie pourvu que tu nommes correctement (ou plus simplement, tu zippes `streamlit_app/`, tu décompresses sur ton bureau, et tu drag-and-drop le contenu).

3. En bas de la page, **commit message** : « Initial deployment ».
4. Clique **Commit changes**.

Vérification : sur la page d'accueil du repo tu dois voir `app.py`, `requirements.txt`, `README.md`, et un dossier `data/` qui contient les trois fichiers.

## Étape 4. Déployer sur Streamlit Cloud

1. Va sur https://share.streamlit.io
2. Clique **Sign up** (ou Sign in si tu as déjà un compte).
3. Choisis **Continue with GitHub**. Streamlit te demande l'autorisation d'accéder à tes repos publics : accepte.
4. Une fois connecté, clique **Create app** ou **New app**.
5. Trois champs à remplir :
   - **Repository** : tape le nom de ton repo (`memoire-m2-soutenance`) ou choisis-le dans la liste qui apparaît.
   - **Branch** : `main` (laisser par défaut).
   - **Main file path** : `app.py`
6. Sous **App URL (optional)**, tu peux personnaliser. Par exemple `memoire-immigration-cadrage`.
   Ton URL finale sera `https://memoire-immigration-cadrage.streamlit.app`.
7. Clique **Deploy**.

Streamlit clone ton repo, installe les dépendances de `requirements.txt`, et lance l'app.
Compte 2 à 4 minutes la première fois (tu verras le log de l'installation défiler).

## Étape 5. Vérifier que tout marche

Une fois le déploiement terminé, tu arrives sur l'app en direct. Vérifie en cinq minutes :

1. **Onglet Cartographie** : les deux cartes s'affichent. Si elles sont vides, c'est probablement que `data/departements.geojson` n'a pas été uploadé. Retourne sur GitHub, vérifie qu'il est bien dans `data/`, taille proche de 3,4 Mo.
2. **Curseur d'année** : changer l'année met à jour les cartes.
3. **Onglet Simulateur** : les sliders bougent, la prédiction se met à jour, le graphique de contribution s'affiche.
4. **Onglet À propos** : le texte s'affiche correctement.

Si tu vois une erreur dans l'app, l'onglet **Manage app → Logs** en bas à droite te donne la trace Python. Les erreurs classiques :
- `FileNotFoundError: data/departements.geojson` → fichier non uploadé. Retourner sur GitHub, ajouter.
- `ModuleNotFoundError` → dépendance manquante. Ajouter la lib dans `requirements.txt` et re-commit.

## Étape 6. Partager avec Mélissa

Copie l'URL (`https://memoire-immigration-cadrage.streamlit.app`) et envoie-la-lui. Elle n'a strictement
rien à installer. L'app reste accessible 24/7.

## Modifications après déploiement

Pour mettre à jour l'app (par exemple ajouter `panel_dept.csv` plus tard) :
1. Sur GitHub, navigue dans le repo jusqu'au fichier à modifier.
2. Clique sur l'icône crayon en haut à droite.
3. Édite, puis en bas : **Commit changes**.
4. Streamlit Cloud détecte le changement et redéploie en 1-2 minutes automatiquement.

Pour uploader un nouveau fichier :
1. Sur GitHub, naviguer dans le dossier de destination.
2. **Add file → Upload files**, drag-and-drop, commit.

## Backup recommandé pour la soutenance

M�me avec l'app déployée, garde sur clé USB :
- Une copie du dossier `streamlit_app/` complet (pour pouvoir lancer en local si Internet est lent).
- La capture vidéo (90 secondes) que tu auras faite de la démo.
- Cette URL imprimée sur ta dernière slide (ou en bas de tes notes), au cas où le PC d'examen
  n'autorise pas tes clés USB.

Triple ceinture, mais une soutenance qui se prépare bien, c'est trois copies de tout.

## Problèmes courants et solutions rapides

| Erreur | Cause | Solution |
|---|---|---|
| « Repository not found » dans Streamlit Cloud | Le repo est privé et Streamlit n'a pas accès | Passer le repo en public, ou autoriser l'accès privé dans les paramètres Streamlit |
| App reste sur « Your app is in the oven » | Première compilation lente | Patienter 5 min. Si ça ne décolle pas, vérifier les Logs |
| Cartes vides, message dans Streamlit | `departements.geojson` manquant ou mal nommé | Vérifier sur GitHub le chemin exact `data/departements.geojson` |
| « ModuleNotFoundError: streamlit_folium » | Lib manquante dans requirements | Pas applicable ici (l'app n'utilise pas folium), mais en général : ajouter au `requirements.txt` |
| L'app reboote toute seule | Inactivité prolongée (tier gratuit) | Normal. Ouvrir l'URL réveille l'app en 30 sec |
