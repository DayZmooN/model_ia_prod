# 🎬 Classifieur de résumés de films — Horreur vs Comédie

Une API FastAPI qui prend le résumé d'un film en anglais et prédit s'il s'agit
d'une **horreur** ou d'une **comédie**, avec un score de confiance.

Projet réalisé dans le cadre de ma formation **Simplon — Introduction au deep learning**.
Le modèle a été entraîné sur 2 346 résumés (1 200 horreur / 1 200 comédie, avant
dédoublonnage), puis mis en production dans une image Docker avec une barrière
qualité qui refuse de déployer un modèle trop faible.

---

## ⚠️ À lire avant de tester

**Le modèle est entraîné sur des résumés en anglais.** Si vous lui envoyez du
français, il va renvoyer une prédiction quand même — mais elle ne veut rien dire,
parce que tous les mots français sont absents de son vocabulaire (un TF-IDF de
5 000 mots anglais). Ce n'est pas un bug, c'est une limite du jeu de données
d'entraînement.

👉 Pour tester correctement, utilisez des phrases comme :

- _"A serial killer stalks and murders families in a haunted house at night."_ → Horreur
- _"A clumsy man keeps making hilarious mistakes at a disastrous wedding."_ → Comédie

---

## Sommaire

- [Ce que fait l'API](#ce-que-fait-lapi)
- [Structure du projet](#structure-du-projet)
- [Installation locale](#installation-locale)
- [Lancer l'API](#lancer-lapi)
- [Utiliser l'API](#utiliser-lapi)
- [Tests](#tests)
- [Barrière qualité](#barrière-qualité)
- [Docker](#docker)
- [Performances du modèle](#performances-du-modèle)
- [Ce que j'ai appris en le construisant](#ce-que-jai-appris-en-le-construisant)
- [Limites et pistes](#limites-et-pistes)

---

## Ce que fait l'API

Trois routes, c'est tout :

| Route      | Méthode | Rôle                                                        |
| ---------- | ------- | ----------------------------------------------------------- |
| `/health`  | GET     | Vérifier que l'API tourne et récupérer la version du modèle |
| `/predict` | POST    | Envoyer un résumé (JSON) et recevoir une prédiction         |
| `/docs`    | GET     | Interface Swagger générée automatiquement par FastAPI       |

Le modèle est un petit réseau de neurones (2 couches denses, ~10k paramètres)
entraîné sur des vecteurs TF-IDF. Rien de spectaculaire, mais le F1 tient la
route (voir plus bas).

---

## Structure du projet

```text
model_ia_prod/
├── api/
│   ├── __init__.py
│   └── main.py                  # l'API FastAPI (routes + chargement du modèle)
├── model/
│   ├── model.keras              # réseau entraîné
│   ├── vectoriseur.joblib       # TF-IDF fitté sur les résumés d'entraînement
│   ├── metrics.json             # métriques + versions utilisées
│   └── reference.csv            # échantillon de référence (20 lignes)
├── tests/
│   ├── test_api.py              # tests fonctionnels (health, predict, erreurs)
│   └── test_quality.py          # test de la barrière qualité
├── scripts/
│   └── check_quality.py         # ou à la racine, au choix
├── config.yaml                  # seuils de la barrière qualité
├── check_quality.py             # vérifie metrics.json contre config.yaml
├── pytest.ini                   # configuration pytest
├── requirements-api.txt         # dépendances runtime
├── Dockerfile                   # image multi-stage avec quality-gate
├── .dockerignore
├── .gitignore
├── 01_modele_classification_films.ipynb   # notebook d'entraînement
└── README.md
```

````

---

## Installation locale

Python 3.14 (celle qui a servi à entraîner le modèle). Sur une autre version,
TensorFlow risque de ne pas être dispo en stable — voir la section Docker pour
un contournement.

```bash
# Cloner / se placer dans le dossier
cd model_ia_prod

# Créer un environnement virtuel
python -m venv venv

# Activer (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# ou (macOS / Linux)
source venv/bin/activate

# Installer les dépendances
pip install -r requirements-api.txt
```

⚠️ `tensorflow-cpu==2.22.0rc0` est une **pré-version**. `pip install` tout seul
l'ignore silencieusement. Il faut `--pre` :

```bash
pip install --pre -r requirements-api.txt
```

---

## Lancer l'API

```bash
uvicorn api.main:app --reload
```

Vous devriez voir :

```
⏳ Chargement du modèle...
✅ Modèle chargé : model/model.keras
✅ Vectoriseur chargé : model/vectoriseur.joblib
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Ensuite : ouvrez **http://127.0.0.1:8000/docs** dans un navigateur. C'est
l'interface Swagger, générée par FastAPI, qui permet de tester toutes les routes
sans écrire une ligne de code. C'est le moyen le plus simple pour vérifier que
tout marche.

---

## Utiliser l'API

### Avec Swagger (le plus simple)

`http://127.0.0.1:8000/docs` → `POST /predict` → **Try it out** → coller un
résumé → **Execute**.

### Avec curl (bash / macOS / Linux)

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"A serial killer stalks and murders families in a haunted house at night."}'
```

### Avec PowerShell (Windows)

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict `
  -ContentType "application/json" `
  -Body '{"text":"A serial killer stalks and murders families in a haunted house at night."}'
```

> 💡 En PowerShell, utilisez des **quotes simples** autour du JSON. Les `\"`
> façon bash ne marchent pas et produisent une erreur `JSON decode error`.

**Réponse attendue :**

```json
{
  "classe": "Horreur",
  "probabilite": 0.99,
  "version": "1.0.0"
}
```

---

## Tests

10 tests, lancés avec `pytest` :

```bash
pytest -v
```

Ils couvrent :

- l'API répond (`/health`, `/`)
- une prédiction valide fonctionne (horreur + comédie)
- les cas invalides sont refusés (texte trop court, champ manquant, mauvais type)
- le modèle respecte les seuils de `config.yaml`

Résultat attendu :

```
tests/test_api.py::test_health PASSED
tests/test_api.py::test_root PASSED
tests/test_api.py::test_predict_horror PASSED
tests/test_api.py::test_predict_comedy PASSED
tests/test_api.py::test_text_too_short PASSED
tests/test_api.py::test_missing_field PASSED
tests/test_api.py::test_wrong_type PASSED
tests/test_quality.py::test_metrics_file_exists PASSED
tests/test_quality.py::test_config_file_exists PASSED
tests/test_quality.py::test_model_meets_quality_bar PASSED

10 passed in ~7s
```

---

## Barrière qualité

Le projet refuse de déployer un modèle trop faible. C'est implémenté à deux
niveaux, qui se doublonnent volontairement :

1. **`check_quality.py`** — lit `config.yaml` et `model/metrics.json`, échoue si
   un seuil n'est pas respecté.
2. **`tests/test_quality.py`** — même vérification, mais dans `pytest`, pour
   qu'un simple `pytest` détecte un mauvais modèle sans dépendre du script.

### Les seuils (`config.yaml`)

```yaml
f1_min: 0.82
test_size_min: 400
```

### Justification (pour le rapport)

> Le seuil F1 de 0.82 correspond au F1 du modèle final (0.857) diminué de la
> marge de bruit statistique (±0.031 pour 469 exemples de test), ce qui absorbe
> les variations aléatoires normales tout en détectant une vraie dégradation.
> La taille minimale de 400 garantit que cette marge reste sous ±0.035.

### Tester manuellement

```bash
python check_quality.py
# ✅ F1 OK : 0.8571 ≥ 0.8200
# ✅ Taille de test OK : 469 ≥ 400
# ✅ BARRIÈRE QUALITÉ : SUCCÈS — modèle accepté
```

Si vous remplacez temporairement `f1_test` par `0.50` dans `metrics.json`, le
script affiche `❌ F1 insuffisant` et renvoie un code de sortie `1` — ce qui
stoppe un pipeline CI.

---

## Docker

L'image est construite en **deux stages** :

- **`quality-gate`** : lance `check_quality.py`. Si le modèle est mauvais, le
  build échoue — impossible de créer une image avec un modèle dégradé.
- **runtime** : image finale minimale, non-root, avec un `HEALTHCHECK` sur
  `/health`.

### Construire l'image

```bash
docker build -t movie-classifier-api .
```

### Lancer

```bash
docker run -d --name movie-api -p 8000:8000 movie-classifier-api
```

### Vérifier

```bash
docker logs movie-api
# ⏳ Chargement du modèle...
# ✅ Modèle chargé : model/model.keras
# ✅ Vectoriseur chargé : model/vectoriseur.joblib
# INFO: Uvicorn running on http://0.0.0.0:8000

docker inspect --format='{{.State.Health.Status}}' movie-api
# healthy
```

Puis ouvrez **http://localhost:8000/docs**.

### Arrêter

```bash
docker stop movie-api
docker rm movie-api
```

---

## Performances du modèle

Tiré de `model/metrics.json` :

| Métrique                 | Valeur                                         |
| ------------------------ | ---------------------------------------------- |
| F1 sur le test           | **0.857**                                      |
| Taille du test           | 469 exemples                                   |
| Taille de l'entraînement | 1 407 exemples                                 |
| Features TF-IDF          | 5 000                                          |
| Type de modèle           | Keras (2 couches denses, dropout 0.2, lr 1e-4) |
| TensorFlow               | 2.22.0rc0                                      |
| scikit-learn             | 1.9.1                                          |

À titre de comparaison, dans le notebook, Naive Bayes atteint un F1 de 0.875
sur le test — mais l'écart avec le réseau optimisé (0.862) reste **dans la
marge de bruit** (±0.031). J'ai choisi de garder le réseau parce que le brief
demandait un fichier `.keras`, et le score reste solide.

---

## Ce que j'ai appris en le construisant

Quelques points qui m'ont vraiment marqué, et qui valent la peine d'être notés
si vous refaites un projet similaire :

- **La génération OpenAPI de FastAPI est sensible à la moindre erreur de typage.**
  Une classe Pydantic manquante (`MovieInput` oubliée) et `/openapi.json` renvoie
  une 500. Le symptôme est trompeur (l'app a l'air de tourner), la cause est en
  fait une `NameError` au chargement du module.

- **Un modèle peut être excellent en local et… prédire n'importe quoi en prod
  si vous oubliez la langue du jeu d'entraînement.** Mon premier test avec du
  français renvoyait "Comédie" à 70 % pour une histoire de tueur en série. Ce
  n'était pas un bug — c'était un texte vide du point de vue du vectorizer.

- **`tensorflow-cpu==X.Y.ZrcN` ne s'installe pas tout seul.** Il faut `--pre`,
  sinon `pip` saute la ligne sans rien dire. J'ai perdu une heure là-dessus.

- **Docker saute les stages qu'on ne lui demande pas explicitement.** Si le stage
  final ne fait pas `COPY --from=quality-gate ...`, le quality-gate est purement
  ignoré. Un `touch` + `COPY` de fichier témoin corrige ça proprement.

- **`\"` dans PowerShell, ce n'est pas un échappement.** Il faut utiliser des
  quotes simples ou `Invoke-RestMethod`. Piège classique.

---

## Limites et pistes

Ce que je ferais si j'avais plus de temps :

- **Support multilingue.** Soit en détectant la langue et en renvoyant une erreur
  claire (déjà faisable avec `langdetect`), soit en réentraînant sur un corpus
  français, soit en traduisant automatiquement les requêtes.
- **Plus de classes.** Le binaire horreur/comédie est volontairement simple.
  Passer à 5-6 genres (thriller, SF, drame, action…) serait plus utile en vrai.
- **Un vrai registre de modèles.** Aujourd'hui, `model.keras` est commité dans
  Git. En production, il faudrait un registre (MLflow, Azure ML, S3) pour
  versionner les modèles séparément du code.
- **Pipeline CI/CD complet.** GitHub Actions qui lance `pytest` + `check_quality`
  à chaque push, construit l'image, la pousse sur un registry, la déploie.
- **Un modèle plus fin.** Un petit transformer (DistilBERT) aurait probablement
  un meilleur F1 — mais c'est aussi plus lourd à dockeriser, et le brief demandait
  un `.keras`.

---


````

## Auteur

**Karim** — Formation Simplon, _Introduction au deep learning_ — Octobre 2026.

Projet réalisé en autonomie, du notebook d'entraînement jusqu'à l'image Docker
en passant par les tests et la barrière qualité.
