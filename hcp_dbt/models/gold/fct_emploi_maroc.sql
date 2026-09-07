{{ config(materialized='table', schema='gold') }}

WITH chomage_regional AS (
    SELECT
        'chomage_regional'      AS indicateur,
        milieu,
        region,
        sexe,
        CAST(NULL AS TEXT)      AS secteur,
        CAST(NULL AS TEXT)      AS tranche_age,
        CAST(annee AS TEXT)     AS periode,
        taux_chomage            AS valeur
    FROM {{ ref('stg_chomage_regional') }}
),

chomage_age_sexe AS (
    SELECT
        'chomage_age_sexe'      AS indicateur,
        milieu,
        CAST(NULL AS TEXT)      AS region,
        sexe,
        CAST(NULL AS TEXT)      AS secteur,
        tranche_age,
        CAST(annee AS TEXT)     AS periode,
        taux_chomage            AS valeur
    FROM {{ ref('stg_chomage_age_sexe') }}
),

activite AS (
    SELECT
        'taux_activite'         AS indicateur,
        milieu,
        CAST(NULL AS TEXT)      AS region,
        sexe,
        CAST(NULL AS TEXT)      AS secteur,
        CAST(NULL AS TEXT)      AS tranche_age,
        CAST(annee AS TEXT)     AS periode,
        taux_activite           AS valeur
    FROM {{ ref('stg_activite') }}
),

emploi_global AS (
    SELECT
        'taux_emploi'           AS indicateur,
        milieu,
        CAST(NULL AS TEXT)      AS region,
        CAST(NULL AS TEXT)      AS sexe,
        CAST(NULL AS TEXT)      AS secteur,
        CAST(NULL AS TEXT)      AS tranche_age,
        CAST(annee AS TEXT)     AS periode,
        taux_emploi             AS valeur
    FROM {{ ref('stg_emploi_global') }}
),

emploi_secteur AS (
    SELECT
        'emploi_secteur'        AS indicateur,
        milieu,
        CAST(NULL AS TEXT)      AS region,
        CAST(NULL AS TEXT)      AS sexe,
        secteur,
        CAST(NULL AS TEXT)      AS tranche_age,
        periode,
        taux_emploi             AS valeur
    FROM {{ ref('stg_emploi_secteur') }}
)

SELECT * FROM chomage_regional
UNION ALL
SELECT * FROM chomage_age_sexe
UNION ALL
SELECT * FROM activite
UNION ALL
SELECT * FROM emploi_global
UNION ALL
SELECT * FROM emploi_secteur