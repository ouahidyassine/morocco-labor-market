{{ config(materialized='view', schema='silver') }}

WITH source AS (
    SELECT * FROM {{ source('bronze', 'bronze_data_1_3') }}
),

cleaned AS (
    SELECT
        "Milieu de résidence"       AS milieu,
        "Régions"                   AS region,
        "Sexe"                      AS sexe,
        CAST(annee AS INTEGER)      AS annee,
        CAST(valeur AS NUMERIC)     AS taux_chomage,
        dataset_name,
        titre
    FROM source
    WHERE "Milieu de résidence" IS NOT NULL
      AND valeur IS NOT NULL
)

SELECT * FROM cleaned