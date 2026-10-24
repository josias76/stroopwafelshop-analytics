# Projet Analytics Engineering Local

## 1. Présentation

Ce projet transforme le cas d'étude **Stroopwafelshop** en pipeline Analytics Engineering
100 % local et open source. L'objectif est de simuler un environnement d'entreprise avec :

- PostgreSQL pour le stockage des données brutes et des tables analytiques
- dbt-core pour la modélisation et les tests de qualité
- Streamlit pour remplacer Tableau par un dashboard local

Le résultat est un mini data warehouse prêt pour l'apprentissage, la démonstration et le portfolio.

## 2. Architecture

Le pipeline suit quatre couches simples :

1. `data/` contient les CSV sources.
2. `scripts/load_data.py` crée la base PostgreSQL, les schémas `raw` et `analytics`, puis charge les CSV dans `raw`.
3. `dbt_project/` transforme les tables brutes en modèles `staging`, `marts` puis `marts/dashboard`.
4. `analytics_dashboard/streamlit_app.py` lit les tables analytiques et expose les KPIs métier.

### Stratégie de matérialisation

Le projet applique une matérialisation différente selon le rôle de chaque couche :

- `staging` en `view` : couche légère de nettoyage, standardisation et renommage
- `marts` coeur (`dim_*`, `fct_sales`) en `table` : couche métier robuste, stable et réutilisable dans un outil BI comme Power BI
- `marts/dashboard` en `view` : couche de présentation dérivée des tables métier, pensée pour Streamlit

## 3. Configuration PostgreSQL

Une connexion PostgreSQL locale est attendue. Les paramètres sont lus depuis le `.env` présent à la racine du dépôt :

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
```

Le script d'ingestion crée automatiquement la base `stroopwafelshop` si elle n'existe pas.

## 4. Chargement des données

Depuis la racine du dépôt :

```bash
cd analytics_engineering_project
../.venv/bin/python scripts/load_data.py
```

Le script :

- crée la base `stroopwafelshop`
- crée les schémas `raw` et `analytics`
- charge les six fichiers CSV dans `raw.employees`, `raw.products`, `raw.promotions`, `raw.sales`, `raw.sales_lines` et `raw.shifts`

## 5. Lancement dbt

Le profil dbt est stocké localement dans `dbt_project/profiles.yml`.

```bash
cd analytics_engineering_project/dbt_project
DBT_PROFILES_DIR=. ../../.venv/bin/dbt debug
DBT_PROFILES_DIR=. ../../.venv/bin/dbt run
DBT_PROFILES_DIR=. ../../.venv/bin/dbt test
```

Le projet construit :

- `stg_employees`
- `stg_products`
- `stg_promotions`
- `stg_sales`
- `stg_sales_lines`
- `stg_shifts`
- `dim_employees`
- `dim_products`
- `dim_promotions`
- `dim_shifts`
- `fct_sales`
- `mart_sales_detail`
- `mart_sales_transactions`
- `mart_sales_performance`

### Rôle des modèles dashboard

Le dossier `dbt_project/models/marts/dashboard/` contient des modèles prêts à consommer
par Streamlit, qui ne dispose pas d'un modèle sémantique équivalent à Power BI.

- `mart_sales_detail` : vue détaillée dénormalisée au grain ligne de vente
- `mart_sales_transactions` : vue au grain ticket pour les KPI de transactions
- `mart_sales_performance` : vue agrégée pour les graphiques de pilotage

## 6. Lancement du dashboard

Depuis la racine du projet :

```bash
cd analytics_engineering_project
../.venv/bin/streamlit run analytics_dashboard/streamlit_app.py
```

Le dashboard propose :

- des KPIs de ventes, chiffre d'affaires et transactions
- une évolution des ventes dans le temps
- un classement des meilleurs produits
- une analyse de la performance des employés
- une vue sur l'impact des promotions
- des filtres par date, produit et employé

Le dashboard ne joint plus directement les dimensions et la table de faits. Il s'appuie
sur des marts métier prêtes à l'emploi :

- `mart_sales_detail` pour le détail dénormalisé
- `mart_sales_transactions` pour les tickets de caisse
- `mart_sales_performance` pour les agrégats de pilotage

## 7. Utilisation avec Power BI

`analytics.mart_sales_detail` contient presque toutes les informations utiles pour un
dashboard simple. Elle peut servir de table plate unique dans Streamlit ou dans un
prototype Power BI.

En revanche, pour un vrai dashboard Power BI, il est préférable d'utiliser directement :

- `analytics.dim_employees`
- `analytics.dim_products`
- `analytics.dim_promotions`
- `analytics.dim_shifts`
- `analytics.fct_sales`

Pourquoi ne pas utiliser `mart_sales_detail` comme base principale dans Power BI :

- la vue est dénormalisée et pensée pour la consommation rapide, pas pour reconstruire un modèle étoile
- recréer des dimensions et une table de faits dans Power Query à partir d'une vue plate reviendrait à refaire dans Power BI un travail déjà réalisé dans dbt
- cela augmente le risque d'erreurs de grain, de duplication et de logique métier dispersée

Les vues `mart_sales_transactions` et `mart_sales_performance` existent donc pour
sortir la logique de calcul de l'application Streamlit et la déplacer dans dbt, avec des
grains adaptés aux besoins du dashboard.
## 8. Résultats

Une fois la pipeline exécutée, vous disposez :

- d'une couche `raw` qui reproduit une ingestion de fichiers métiers
- d'une couche `analytics` propre, testée et documentée
- d'un schéma en étoile simple orienté BI
- d'un dashboard local immédiatement exploitable

## 9. Aller plus loin

Pour rapprocher encore ce projet d'un environnement réel :

- ajoutez des snapshots dbt pour historiser les promotions ou les employés
- créez une dimension calendrier
- orchestrez le chargement et dbt avec cron, Airflow ou Dagster
- ajoutez des tests personnalisés sur les règles métier
- publiez le projet sur GitHub avec captures d'écran du dashboard
