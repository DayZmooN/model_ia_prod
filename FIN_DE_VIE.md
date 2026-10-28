# FIN DE VIE — Inventaire des composants

**Règle :** toutes les ressources Azure sont supprimées en J5. Les éléments
"gardés" le sont uniquement dans le dépôt GitHub (gratuit, sans coût récurrent).

## A. Composants à retirer en fin de projet

| Composant                                                     | Quand | Comment                                      | Ordre | Ce qu'on garde                                  | Coût de le laisser en place   |
| ------------------------------------------------------------- | ----- | -------------------------------------------- | ----- | ----------------------------------------------- | ----------------------------- |
| Container App `classifieur-films`                             | J5    | `az containerapp delete`                     | 1     | Le `Dockerfile` et le tag d'image dans le dépôt | ~5–10 €/mois (CPU + mémoire)  |
| Environnement Container App                                   | J5    | `az containerapp env delete`                 | 2     | —                                               | facturé tant que l'env existe |
| ACR `acrfilmkarim2026`                                        | J5    | `az acr delete`                              | 3     | La recette de build (Dockerfile) dans le dépôt  | ~5 €/mois (Basic) même vide   |
| Secrets GitHub (ACR_USERNAME, ACR_PASSWORD, ACR_LOGIN_SERVER) | J5    | Suppression dans _Settings → Secrets_        | 4     | —                                               | 0 €                           |
| Groupe de ressources (si dédié)                               | J5    | `az group delete` (jamais un groupe partagé) | 5     | —                                               | 0 € après suppression         |

## B. Composants conservés (dépôt, sans coût)

| Composant                                  | Ce qu'on garde | Pourquoi                                         |
| ------------------------------------------ | -------------- | ------------------------------------------------ |
| Modèle (`model/model.keras`)               | Oui            | Reproductibilité, réentraînement futur           |
| TF-IDF (`model/vectoriseur.joblib`)        | Oui            | Idem                                             |
| `metrics.json`, `reference.csv`            | Oui            | Traçabilité du score et des données de référence |
| Code API, Dockerfile, workflow             | Oui            | Le produit, c'est le code                        |
| Données `textes_films_horreur_comedie.csv` | Oui            | Source                                           |
| Dépôt GitHub                               | Oui            | Archive du projet                                |

## C. Fin de vie partielle vs totale

- **Fin de vie partielle** : on retire l'application et le registre Azure, mais on
  garde le modèle et le code. Cas visé si le projet devait être repris plus tard.
- **Fin de vie totale** : on retire **tout**, y compris le dépôt et les données.
  **Non appliquée ici** : le dépôt est le livrable.

## D. Preuve d'application (rempli à la fin)

- [x] **Verification de suppression des ressources** : exécuté via la commande `az resource list --resource-group kryahiRG --output table` confirmant l'absence de l'application `film-api`, de l'environnement `karim-film-env` et du registre `karimregistry`[cite: 10].
- [x] **Relève du coût cumulé** : validé sur Azure Cost Management pour un montant total de **0,06 €** (Registre de conteneurs : 0,06 € ; autres lignes < 0,01 €)[cite: 9].
- [x] **Isolation du groupe de ressources** : suppression ciblée des 3 composants individuels réalisée afin de préserver les ressources partagées du groupe `kryahiRG`[cite: 10].

_(Rempli le : **28/10/2026**)_
