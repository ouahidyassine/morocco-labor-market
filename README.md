# Marché du travail au Maroc — Pipeline ELT

Pipeline de données automatisé sur les statistiques officielles de l'emploi
au Maroc, de l'API du Haut-Commissariat au Plan jusqu'au dashboard Power BI.

![Dashboard](dashboard/dashboard.png)

## Architecture

API CKAN (data.gov.ma) → Python → PostgreSQL → dbt → Power BI

| Couche | Contenu | Outil |
|---|---|---|
| Bronze | 29 datasets bruts, format long | Python (pandas, psycopg2) |
| Silver | 5 indicateurs nettoyés et typés | dbt (vues) |
| Gold | Table consolidée pour l'analyse | dbt (table) |

## Source des données

Portail Open Data national du Maroc (data.gov.ma), API CKAN publique.
29 jeux de données du Haut-Commissariat au Plan sur l'emploi, licence ODbL.

Deux sites d'offres d'emploi ont été évalués au départ. Rekrute.ma interdit
le scraping de ses pages d'offres dans son `robots.txt`. Emploi.ma déploie
une protection anti-bot active (Cloudflare Turnstile). Le projet a donc été
redirigé vers l'API officielle du HCP — données plus riches, aucune
ambiguïté légale.

## Qualité des données

Plusieurs fichiers HCP (`data_1_2`, `data_1_5`, `data_1_18`) présentent une
erreur systématique : les cellules dont les modalités sont des permutations
l'une de l'autre portent la même valeur. En 2023, le taux de chômage
Urbain × Total × 15 ans et plus est identique au taux
National × Total × 15-24 ans (35,8 %).

Le défaut a été détecté par deux invariants métier implémentés en tests dbt :
un taux agrégé étant une moyenne pondérée de ses composantes, il doit être
compris entre elles.

| Test | Résultat |
|---|---|
| `assert_taux_dans_bornes` | PASS |
| `assert_total_entre_sexes` | 68 violations |
| `assert_national_entre_milieux` | 19 violations |

Le dashboard n'affiche que les séries National × Total, conformes aux taux
publiés par le HCP (13,0 % de chômage national en 2023).

## Résultats

- Le chômage des 15-24 ans atteint 28,6 % contre 3,7 % chez les 45 ans et plus
- Le taux de chômage national progresse de 9,9 % à 13,0 % entre 2014 et 2023

## Exécution

```bash
pip install -r requirements.txt
python scraper/extract.py
python scraper/load.py
cd hcp_dbt && dbt run && dbt test
```

## Stack

Python · PostgreSQL · dbt · Power BI · Git