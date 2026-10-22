# PLAN — Mise en production d'un modèle de classification de films

## Contexte

Modèle binaire (1 = horreur, 0 = comédie) entraîné sur 2400 résumés de films
(`textes_films_horreur_comedie.csv`). Objectif : le sortir du notebook et le mettre
en ligne sur Azure Container Apps, avec contrôles automatiques (tests, barrière
qualité, GitHub Actions), traçabilité des versions et plan de fin de vie.

- **Seuil qualité retenu : F1 ≥ 0,85 sur le test** (utilisé par la barrière qualité).
- **Compte Azure** : fourni par le centre de formation.
- **Règle budgétaire** : aucune ressource durable, tout est supprimé en J5
  (voir `FIN_DE_VIE.md`).
- **Nom ACR visé** : `acrfilmkarim2026` (unique au monde, minuscules, alphanumérique).
- **Durée** : J1 = aujourd'hui → J5 = +4 jours ouvrés.

## Tâches

| #   | Tâche                                                         | Dépend de | Charge estimée | Charge réelle | Ressources humaines | Ressources matérielles | Ressources techniques  | Financier                 | Date prévue |
| --- | ------------------------------------------------------------- | --------- | -------------- | ------------- | ------------------- | ---------------------- | ---------------------- | ------------------------- | ----------- |
| T1  | Audit + nettoyage CSV                                         | —         | 2 h            |               | 1 apprenant         | PC                     | Python, pandas         | 0 €                       | J1          |
| T2  | Découpage train/test/prod (60/20/20, stratifié)               | T1        | 1 h            |               | 1 apprenant         | PC                     | scikit-learn           | 0 €                       | J1          |
| T3  | TF-IDF appris sur train seul                                  | T2        | 1 h            |               | 1 apprenant         | PC                     | scikit-learn           | 0 €                       | J1          |
| T4  | 3 modèles de référence (logreg, NB, réseau simple)            | T3        | 2 h            |               | 1 apprenant         | PC                     | sklearn, Keras         | 0 €                       | J1          |
| T5  | KerasTuner — recherche aléatoire 20 essais                    | T4        | 2 h            |               | 1 apprenant         | PC                     | keras-tuner            | 0 €                       | J2          |
| T6  | Optuna — mêmes conditions que KerasTuner                      | T5        | 2 h            |               | 1 apprenant         | PC                     | optuna                 | 0 €                       | J2          |
| T7  | Verdict test (5 graines, comparaison baseline)                | T6        | 1 h            |               | 1 apprenant         | PC                     | Keras                  | 0 €                       | J2          |
| T8  | Sauvegarde `model/` (.keras, joblib, metrics.json, référence) | T7        | 1 h            |               | 1 apprenant         | PC                     | joblib, json           | 0 €                       | J2          |
| A1  | API FastAPI (`/health`, `/predict`)                           | T8        | 2 h            |               | 1 apprenant         | PC                     | FastAPI, uvicorn       | 0 €                       | J3          |
| A2  | Tests locaux pytest                                           | A1        | 1 h            |               | 1 apprenant         | PC                     | pytest                 | 0 €                       | J3          |
| A3  | Barrière qualité (`config.yaml` F1 ≥ 0,85 + script)           | A1        | 1 h            |               | 1 apprenant         | PC                     | PyYAML                 | 0 €                       | J3          |
| B1  | `Dockerfile` + `.dockerignore` (image slim)                   | A2, A3    | 2 h            |               | 1 apprenant         | PC + Docker            | Docker                 | 0 €                       | J3          |
| B2  | Container local + rejeu tests                                 | B1        | 1 h            |               | 1 apprenant         | PC                     | docker run             | 0 €                       | J3          |
| C1  | Workflow GitHub Actions — job `test`                          | A2        | 1 h            |               | 1 apprenant         | GitHub                 | YAML                   | 0 €                       | J4          |
| C2  | Job `image` (build + `/health`)                               | C1, B1    | 1 h            |               | 1 apprenant         | GitHub                 | Docker-in-CI           | 0 €                       | J4          |
| C3  | ACR `acrfilmkarim2026` (Basic) + admin activé                 | —         | 1 h            |               | 1 apprenant         | Portail Azure          | az acr                 | ~5 €/mois, supprimé J5    | J4          |
| C4  | Job `publier` (image taguée `github.sha`)                     | C2, C3    | 1 h            |               | 1 apprenant         | GitHub + Azure         | secrets GitHub         | 0 €                       | J4          |
| D1  | Container App Azure (1 CPU, 2 Go, ingress)                    | C4        | 2 h            |               | 1 apprenant         | Portail Azure          | az containerapp        | ~5–10 €/mois, supprimé J5 | J4          |
| D2  | Tests publics `/health` + `/predict` (3 cas)                  | D1        | 0,5 h          |               | 1 apprenant         | Navigateur             | —                      | 0 €                       | J4          |
| E1  | Route `/hello` + push + redéploiement manuel (nouveau SHA)    | D2        | 1 h            |               | 1 apprenant         | PC + Azure             | az containerapp update | 0 €                       | J5          |
| E2  | Rollback (redéploiement ancien SHA)                           | E1        | 0,5 h          |               | 1 apprenant         | Azure                  | az containerapp update | 0 €                       | J5          |
| F1  | Relevé du coût réel + suppression complète des ressources     | E2        | 1 h            |               | 1 apprenant         | Portail Azure          | az resource delete     | 0 € après suppression     | J5          |
| G1  | Rédaction finale `PROCEDURE_MISE_EN_PRODUCTION.md`            | E2        | 1 h            |               | 1 apprenant         | PC                     | Markdown               | 0 €                       | J5          |
| G2  | Rédaction finale `FIN_DE_VIE.md` + preuves                    | F1        | 1 h            |               | 1 apprenant         | PC                     | Markdown               | 0 €                       | J5          |
| G3  | Fiche d'une page (plan vs réel, trajet, seuil, limites)       | G1, G2    | 1 h            |               | 1 apprenant         | PC                     | —                      | 0 €                       | J5          |

## Chemin critique

T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → A1 → A2 → B1 → C2 → C4 → D1 → D2 → E1 → E2 → F1 → G2 → G3

## Tâches hors chemin critique (avec marge)

A3, B2, C1, C3, G1 (peuvent être décalées ou faites en parallèle sans retarder la mise en production)

## Hypothèses

- Le test set est utilisé **une seule fois** en T7 (avant l'API), jamais après.
- Les 20 % "production" de la partie 1 du notebook ne servent **jamais** à l'évaluation :
  uniquement de référence pour `reference.csv`.
- Toutes les ressources Azure sont supprimées en J5 → coût final attendu : **0 € après suppression**,
  coût cumulé relevé en F1.
- Commit de départ du dépôt créé en début de J1.

## Risques identifiés

- **Dépassement de temps sur KerasTuner/Optuna** → limiter à 20 essais, lancer si possible en parallèle.
- **Oubli d'une ressource Azure** → checklist dans `FIN_DE_VIE.md`.
- **Fuite de données TF-IDF** → règle stricte : `fit_transform` sur train, `transform` sur test.
- **Nom ACR déjà pris** → vérifié à C3 avec `az acr check-name --name acrfilmkarim2026`
  (au pire, suffixer l'année ou les initiales).
