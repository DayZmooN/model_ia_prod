# Classifieur de résumés de films — Horreur vs Comédie

![CI](https://github.com/DayZmooN/model_ia_prod/actions/workflows/ci.yml/badge.svg)

Une API FastAPI qui prend le résumé d'un film en anglais et prédit s'il s'agit d'une **horreur** ou d'une **comédie**, avec un score de confiance.

Projet réalisé dans le cadre de ma formation **Simplon — Introduction au deep learning**.
Le modèle a été entraîné sur 2 346 résumés (1 200 horreur / 1 200 comédie, avant dédoublonnage), puis mis en production dans une image Docker avec une barrière qualité qui refuse de déployer un modèle trop faible.

> 🌐 **Déploiement :** L'API a été déployée avec succès sur Azure Container Apps. Les ressources ont ensuite été supprimées (voir la section _Fin de vie_) pour éviter des coûts inutiles. L'URL publique n'est donc plus active.

---

## ⚠️ À lire avant de tester

**Le modèle est entraîné sur des résumés en anglais.** Si vous lui envoyez du français, l'API va le détecter (grâce à la librairie `langdetect`) et renvoyer une erreur **HTTP 400**. C'est une sécurité pour éviter des prédictions aberrantes.

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
- [CI/CD et Déploiement](#cicd-et-déploiement)
- [Performances du modèle](#performances-du-modèle)
- [Ce que j'ai appris en le construisant](#ce-que-jai-appris-en-le-construisant)
- [Limites et pistes](#limites-et-pistes)

---

## Ce que fait l'API

Quatre routes principales :

| Route      | Méthode | Rôle                                                        |
| ---------- | ------- | ----------------------------------------------------------- |
| `/health`  | GET     | Vérifier que l'API tourne et récupérer la version du modèle |
| `/predict` | POST    | Envoyer un résumé (JSON) et recevoir une prédiction         |
| `/`        | GET     | Route racine de test                                        |
| `/docs`    | GET     | Interface Swagger générée automatiquement par FastAPI       |

Le modèle est un petit réseau de neurones (2 couches denses) entraîné sur des vecteurs TF-IDF. Rien de spectaculaire, mais le F1 tient la route (voir plus bas).

---

## Structure du projet

```text
model_ia_prod/
├── .github/
│   └── workflows/
│       └── ci.yml               # Pipeline CI/CD (Tests -> Image -> ACR)
├── api/
│   ├── __init__.py
│   └── main.py                  # API FastAPI (routes, chargement du modèle, langdetect)
├── model/
│   ├── model.keras              # Réseau entraîné
│   ├── vectoriseur.joblib       # TF-IDF fitté sur les résumés d'entraînement
│   ├── metrics.json             # Métriques + versions utilisées
│   └── reference.csv            # Échantillon de référence (20 lignes)
├── tests/
│   ├── test_api.py              # Tests fonctionnels (health, predict, erreurs)
│   └── test_quality.py          # Test de la barrière qualité
├── config.yaml                  # Seuils de la barrière qualité
├── check_quality.py             # Script qui vérifie metrics.json contre config.yaml
├── pytest.ini                   # Configuration pytest
├── Dockerfile                   # Image multi-stage avec quality-gate
├── .dockerignore
├── .gitignore
├── 01_modele_classification_films.ipynb   # Notebook d'entraînement
├── requirements.txt             # Dépendances pour le Notebook (entraînement)
├── requirements-api.txt         # Dépendances pour l'API (production)
└── README.md
```

````

---

## Installation locale

Le projet utilise **deux fichiers de dépendances** distincts pour séparer l'entraînement de la production :

1. **`requirements.txt`** : pour le notebook (Jupyter, pandas, optuna, keras_tuner...).
2. **`requirements-api.txt`** : pour l'API et Docker (FastAPI, uvicorn, langdetect...).

### Pour lancer l'API :

```bash
# Cloner / se placer dans le dossier
cd model_ia_prod

# Créer un environnement virtuel
python -m venv venv

# Activer (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# ou (macOS / Linux)
source venv/bin/activate

# Installer les dépendances de l'API
pip install --pre -r requirements-api.txt
```

⚠️ `tensorflow-cpu==2.22.0rc0` est une **pré-version**. `pip` l'ignore silencieusement sans l'option `--pre`.

### Pour lancer le Notebook :

```bash
pip install -r requirements.txt
jupyter notebook
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

Ensuite : ouvrez **http://127.0.0.1:8000/docs** dans un navigateur.

---

## Utiliser l'API

### Avec Swagger (le plus simple)

`http://127.0.0.1:8000/docs` → `POST /predict` → **Try it out** → coller un résumé → **Execute**.

### Avec PowerShell (Windows)

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict `
  -ContentType "application/json" `
  -Body '{"text":"A serial killer stalks and murders families in a haunted house at night."}'
```

> 💡 En PowerShell, utilisez des **quotes simples** autour du JSON. Les `\"` façon bash produisent une erreur `JSON decode error`.

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

- L'API répond (`/health`, `/`).
- Une prédiction valide fonctionne (horreur + comédie).
- Les cas invalides sont refusés (texte trop court, champ manquant, texte en français).
- Le modèle respecte les seuils de `config.yaml`.

---

## Barrière qualité

Le projet refuse de déployer un modèle trop faible. C'est implémenté à deux niveaux :

1. **`check_quality.py`** : lit `config.yaml` et `model/metrics.json`, échoue si un seuil n'est pas respecté.
2. **`tests/test_quality.py`** : même vérification dans `pytest`.

### Les seuils (`config.yaml`)

```yaml
f1_min: 0.82
test_size_min: 400
```

> **Justification :** Le seuil F1 de 0.82 correspond au F1 du modèle final (0.857) diminué de la marge de bruit statistique (±0.031 pour 469 exemples de test). Cela absorbe les variations aléatoires normales tout en détectant une vraie dégradation.

---

## Docker

L'image est construite en **deux stages** :

- **`quality-gate`** : lance `check_quality.py`. Si le modèle est mauvais, le build échoue.
- **`runtime`** : image finale minimale, non-root, avec un `HEALTHCHECK` sur `/health`.

### Construire et lancer l'image

```bash
docker build -t movie-classifier-api .
docker run -d --name movie-api -p 8000:8000 movie-classifier-api
docker logs movie-api
```

---

## CI/CD et Déploiement

Le pipeline GitHub Actions (`.github/workflows/ci.yml`) s'exécute à chaque `git push` sur `main` et comporte 3 jobs :

1. **`test`** : installe les dépendances, lance `check_quality.py` et `pytest -v`.
2. **`image`** (dépend du job `test`) : construit l'image Docker, lance un conteneur et vérifie que l'API répond.
3. **`publier`** (dépend du job `image`) : pousse l'image sur **Azure Container Registry (ACR)**, étiquetée avec le SHA du commit.

**Déploiement Azure :**
L'application a été déployée sur **Azure Container Apps** (1 CPU, 2 Go de RAM). Le déploiement final était manuel via `az containerapp update` pour vérifier le tag de l'image avant la mise en production.

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

---

## Ce que j'ai appris en le construisant

Quelques points qui m'ont vraiment marqué :

- **La génération OpenAPI de FastAPI est sensible à la moindre erreur de typage.** Une classe Pydantic manquante (`MovieInput`) et `/openapi.json` renvoie une 500.
- **Un modèle peut être excellent en local et… prédire n'importe quoi en prod** si on oublie la langue du jeu d'entraînement. D'où l'ajout de `langdetect`.
- **`tensorflow-cpu==X.Y.ZrcN` ne s'installe pas tout seul.** Il faut `--pre`.
- **Docker saute les stages qu'on ne lui demande pas explicitement.** Il faut un `COPY --from=quality-gate` pour forcer l'exécution de la barrière qualité.
- **Le rollback** : J'ai pu tester le retour à une version précédente sur Azure simplement en changeant le tag de l'image.

---

## Limites et pistes

- **Support multilingue** : Le modèle est restreint à l'anglais (bloqué par `langdetect`). Réentraîner sur un corpus français serait la suite logique.
- **Démarrage à froid** : L'application Azure a été configurée avec `min-replicas: 0` pour économiser de l'argent, ce qui entraîne 30 à 60 secondes d'attente lors du premier appel.
- **Version de dépendance** : J'ai utilisé `tensorflow-cpu==2.22.0rc0` pour être compatible avec Python 3.14.
- **Registre de modèles** : Les artefacts sont versionnés dans Git. À grande échelle, il faudrait un registre (MLflow, Azure ML, S3).

---

## Fin de vie (Nettoyage)

Après validation du projet, les ressources Azure ont été supprimées pour éviter la facturation :

- L'application Container App (`film-api`).
- L'environnement Container Apps (`karim-film-env`).
- Le registre Azure Container Registry (`karimregistry`).

Le groupe de ressources partagé `kryahiRG` a été conservé.

---

## Auteur

**Karim** — Formation Simplon, _Introduction au deep learning_ — Octobre 2026.
Projet réalisé en autonomie, du notebook d'entraînement jusqu'à l'image Docker et au déploiement Cloud.

```

```
````
