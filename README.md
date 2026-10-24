# Cours pratique d'Analytics Engineering avec PostgreSQL, dbt-core et Streamlit

## 1. Introduction

L'Analytics Engineering se situe à l'intersection de la data engineering, de l'analytics et du
BI. Son rôle consiste à transformer des données brutes en tables fiables, lisibles et prêtes à
être utilisées par les analystes, les métiers et les outils de visualisation.

Dans ce projet, nous jouons le rôle d'un Analytics Engineer dans une petite entreprise de
retail, **Stroopwafelshop**. Les données arrivent sous forme de fichiers CSV fournis par les
équipes opérationnelles. Notre mission est de :

- centraliser ces données dans PostgreSQL
- les transformer avec dbt-core
- produire un schéma en étoile simple
- exposer des indicateurs dans un dashboard Streamlit

Ce workflow reflète un cas réel d'entreprise, mais dans une version légère, locale et
reproductible.

## 2. Architecture globale

L'architecture du projet repose sur trois briques open source :

- **PostgreSQL** : base locale utilisée comme data warehouse pédagogique
- **dbt-core** : outil de transformation SQL, modélisation et tests
- **Streamlit** : interface analytique locale pour les KPIs et visualisations

### Flux global

1. Les fichiers CSV sont déposés dans `data/`.
2. Un script Python charge les données dans le schéma `raw` de PostgreSQL.
3. dbt lit les tables `raw`, standardise les colonnes dans la couche `staging`, puis construit
   les dimensions, la table de faits et des vues orientées dashboard dans la couche `analytics`.
4. Streamlit interroge les marts dbt pour alimenter le dashboard.

### Pourquoi cette architecture ?

- Elle sépare clairement l'ingestion, la transformation et la consommation.
- Elle reprend les bonnes pratiques d'un entrepôt de données moderne.
- Elle reste entièrement locale, donc simple à reproduire par un apprenant.

## 3. Ingestion des données

### Objectif

La première étape consiste à charger les fichiers CSV dans PostgreSQL sans faire de calcul
complexe. Le schéma `raw` sert de zone d'atterrissage.

### Fichiers source

Le projet contient six datasets :

- `Employees.csv`
- `Products.csv`
- `Promotions.csv`
- `Sales.csv`
- `Sales_lines.csv`
- `Shifts.csv`

### Principe d'ingestion

Le script `scripts/load_data.py` réalise les actions suivantes :

1. lecture du fichier `.env`
2. création de la base `stroopwafelshop` si besoin
3. création des schémas `raw` et `analytics`
4. lecture de chaque CSV avec `pandas`
5. chargement des données dans PostgreSQL avec `SQLAlchemy`

### Pourquoi conserver une couche raw ?

En entreprise, la couche brute permet :

- de rejouer facilement les traitements
- d'isoler les problèmes de qualité à la source
- de conserver une trace fidèle des données reçues
- de découpler ingestion et modélisation

## 4. Modélisation avec dbt

dbt permet d'organiser les transformations SQL par couches logiques.

### La couche staging

La couche `staging` prépare les données brutes pour l'analyse :

- renommage des colonnes
- cast des types
- standardisation des noms
- création de colonnes utiles comme `full_name`, `sold_at` ou `shift_duration_hours`

Exemples :

- `stg_employees` convertit les dates et crée le nom complet
- `stg_sales` reconstruit un timestamp `sold_at`
- `stg_shifts` transforme une plage horaire comme `10:00-14:00` en début, fin et durée

### La couche marts

Les marts représentent la couche métier consommable.

#### Dimensions

- `dim_employees`
- `dim_products`
- `dim_promotions`
- `dim_shifts`

#### Table de faits

- `fct_sales`

Le grain de `fct_sales` est **la ligne de ticket**. C'est un choix important, car il permet de
répondre à des questions analytiques détaillées :

- quels produits sont les plus vendus ?
- quelles promotions génèrent du chiffre d'affaires ?
- quels employés réalisent le plus de ventes ?

### La sous-couche marts/dashboard

Dans ce projet, nous avons ajouté une sous-couche `models/marts/dashboard/` pour
répondre à un besoin spécifique : **Streamlit n'offre pas le modèle sémantique d'un outil BI
comme Power BI**.

Les modèles ajoutés sont :

- `mart_sales_detail` : vue détaillée dénormalisée au grain ligne de vente
- `mart_sales_transactions` : vue au grain ticket pour le KPI transactions
- `mart_sales_performance` : vue agrégée pour les graphiques de pilotage

Cette sous-couche permet de préparer dans dbt des datasets déjà proches des besoins de
consommation du dashboard.

### Le schéma en étoile

Le modèle final suit une logique de star schema :

- la table de faits porte les mesures (`quantity_sold`, `total_price`, `total_discount`)
- les dimensions apportent le contexte métier (produit, employé, promotion, shift)

Cette structure facilite :

- la compréhension métier
- les jointures BI
- la performance des requêtes analytiques

### Choix de matérialisation

Le type de matérialisation dépend du rôle de chaque couche :

- `staging` en **view** : logique légère, réutilisable, sans duplication physique
- `dim_*` et `fct_sales` en **table** : coeur du modèle analytique, stable et performant
- `marts/dashboard` en **view** : couche de présentation calculée à partir des tables métier

Cette stratégie est cohérente avec un usage hybride :

- `dim_*` et `fct_sales` pour un vrai modèle étoile BI
- `marts/dashboard` pour une application Streamlit qui consomme des datasets déjà prêts

## 5. Tests et qualité des données

dbt ne sert pas seulement à transformer les données. Il sert aussi à vérifier leur qualité.

### Tests ajoutés dans ce projet

- `not_null` sur les clés principales
- `unique` sur les identifiants de dimensions et la clé de grain de `fct_sales`
- `relationships` entre la table de faits et les dimensions
- `accepted_values` sur `payment_type`

### Pourquoi ces tests sont-ils essentiels ?

- Ils détectent rapidement les ruptures d'intégrité.
- Ils sécurisent les dashboards et les analyses métier.
- Ils rapprochent le projet d'un vrai standard de production.

### Commandes dbt à connaître

```bash
cd analytics_engineering_project/dbt_project
DBT_PROFILES_DIR=. ../../.venv/bin/dbt debug
DBT_PROFILES_DIR=. ../../.venv/bin/dbt run
DBT_PROFILES_DIR=. ../../.venv/bin/dbt test
```

## 6. Dashboard

Le dashboard Streamlit remplace Tableau dans une logique 100 % locale.

### KPI exposés

- ventes totales en unités
- chiffre d'affaires
- nombre de transactions

### Visualisations

- évolution du chiffre d'affaires dans le temps
- top produits
- performance des employés
- impact des promotions

### Filtres métier

- période
- produit
- employé

Le dashboard lit directement les vues `mart_sales_detail`, `mart_sales_transactions` et
`mart_sales_performance` construites par dbt dans le schéma `analytics`.

### Pourquoi ne pas tout faire avec mart_sales_detail ?

`mart_sales_detail` contient déjà presque toutes les données nécessaires au dashboard.
Techniquement, on pourrait recalculer dans Streamlit :

- les transactions
- les agrégats par date
- les top produits
- la performance employés
- l'impact des promotions

Mais cela déplacerait une partie de la logique métier dans le code applicatif.

Les vues `mart_sales_transactions` et `mart_sales_performance` ont donc été ajoutées pour :

- séparer clairement les grains d'analyse
- centraliser la logique métier dans dbt
- simplifier le code Streamlit
- rendre les KPI plus explicites et plus maintenables

### Et pour Power BI ?

`analytics.mart_sales_detail` peut être utilisée comme table plate unique dans un prototype
ou un dashboard très simple.

En revanche, pour un vrai dashboard Power BI, il est préférable d'utiliser directement le
modèle en étoile :

- `dim_employees`
- `dim_products`
- `dim_promotions`
- `dim_shifts`
- `fct_sales`

Pourquoi ?

- Power BI sait gérer les relations et le modèle sémantique
- reconstruire des dimensions depuis `mart_sales_detail` dans Power Query reviendrait à
  refaire le travail de modélisation déjà fait dans dbt
- cela augmente le risque d'incohérence sur le grain et la logique métier

## 7. Cas réel en entreprise

Ce projet reproduit un scénario très proche d'une situation réelle :

- des données arrivent depuis des fichiers métiers
- les sources ne sont pas toujours prêtes pour l'analyse
- il faut créer une couche fiable pour les équipes BI
- les indicateurs doivent être centralisés dans un outil de restitution

Dans une vraie entreprise, on remplacerait éventuellement les CSV par :

- un export ERP
- une API de caisse
- un connecteur ELT
- un outil d'ordonnancement

Mais la logique reste la même :

1. ingestion
2. standardisation
3. modélisation
4. tests
5. consommation BI

## 8. Conclusion

Avec ce projet, vous mettez en pratique l'essentiel du métier d'Analytics Engineer :

- concevoir une pipeline locale de bout en bout
- structurer un data warehouse simple dans PostgreSQL
- modéliser des données avec dbt-core
- sécuriser la qualité avec des tests
- servir les besoins métier via un dashboard Streamlit

### Bonnes pratiques à retenir

- séparer `raw` et `analytics`
- nommer clairement les modèles et les colonnes
- tester systématiquement les clés et relations
- choisir explicitement le grain des tables de faits
- construire les dashboards sur les marts, jamais sur les sources brutes

Ce projet constitue une excellente base de portfolio, mais aussi un très bon exercice
pratique pour comprendre comment une équipe data livre de la valeur métier à partir de
données brutes.
