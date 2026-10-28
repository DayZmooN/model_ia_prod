````markdown:PROCEDURE_MISE_EN_PRODUCTION.md
# PROCÉDURE DE MISE EN PRODUCTION

## 1. Déclencheur

Déploiement manuel d'une nouvelle image validée par la chaîne CI
(3 jobs verts : `test`, `image`, `publier`). Aucun déploiement automatique :
la décision est humaine.

## 2. Qui décide, qui exécute

- **Décide** : Karim (rôle : responsable de la mise en production).
- **Exécute** : Karim, sur le portail Azure / `az containerapp update`.
- **Traçabilité** : chaque déploiement = une ligne du journal ci-dessous.

## 3. Vérifications avant déploiement

1. La CI est verte sur le commit à déployer (onglet Actions GitHub).
2. L'image correspondant au `github.sha` existe dans ACR
   (`az acr repository list --name acrfilmkarim2026`).
3. La barrière qualité passe : `metrics.json` contient **F1 ≥ 0,82**.
4. Les tests locaux (pytest) passent : API, validation des entrées, F1 min.

## 4. Déploiement

```bash
az containerapp update \
  --name classifieur-films \
  --resource-group <rg> \
  --image acrfilmkarim2026.azurecr.io/classifieur-films:<SHA>

````

## 5. Contrôle post-déploiement

1. `GET /health` renvoie `ok` **et** le bon identifiant de commit.
2. `GET /predict` répond correctement sur les 3 cas (valide, invalide, limite).
3. Route `/hello` (si ajoutée) répond sur l'adresse publique.

## 6. Retour arrière

- **Condition** : `/health` ne renvoie pas le bon SHA, ou `/predict` échoue,
  ou régression visible sur les 3 cas de contrôle.
- **Mode** : redéploiement de l'image **précédente** (tag = SHA précédent).
- **Qui décide** : Karim, responsable de la mise en production.
- **Qui exécute** : Karim.
- **Délai cible** : < 5 min (une commande `az containerapp update`).

## 7. JOURNAL DES VERSIONS

| Date       | Commit (SHA) | Changement                                                                      | Déployé par | Résultat       | Retour arrière ? |
| ---------- | ------------ | ------------------------------------------------------------------------------- | ----------- | -------------- | ---------------- |
| 22/10/2026 | `03b293d`    | Initialisation v1.0.0 (API FastAPI, modèle Keras et barrière qualité F1 ≥ 0.82) | Karim       | ✅ OK (Succès) | Non              |
| 28/10/2026 | `470f421`    | Version v1.1.0 - Ajout de la route /hello pour test de déploiement Azure        | Karim       | ✅ OK (Succès) | Non              |
| 28/10/2026 | `03b293d`    | Rollback v1.0.0 - Retour à la version stable suite au test de la route /hello   | Karim       | ✅ OK (Succès) | Oui              |

### Mode d'emploi du journal

- **Une ligne par déploiement** (ou par rollback), dans l'ordre chronologique.
- **Date** : au format `JJ/MM/AAAA` (ex. `22/10/2026`).
- **Commit (SHA)** : le SHA court du commit déployé, obtenu avec :

```bash
git rev-parse --short HEAD

```

- **Changement** : description courte (ex. `v1 : première mise en ligne`,
  `v2 : ajout route /hello`, `v3 : rollback vers v1`).
- **Déployé par** : la personne qui a exécuté `az containerapp update` (ici `Karim`).
- **Résultat** : `✅ OK` ou `❌ Échec` + précision.
- **Retour arrière ?** : `Non` si validé, `Oui` si rollback. Dans ce cas,
  ajouter une **ligne supplémentaire** pour documenter le rollback.

```

```
