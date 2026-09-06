{{ config(materialized='view', schema='silver') }}

WITH source AS (
    SELECT * FROM {{ source('bronze', 'bronze_data_1_2') }}
),

cleaned AS (
    SELECT
        "Mileu"                     AS milieu,
        "Sexe"                      AS sexe,
        "Age"                       AS tranche_age,
        CAST(annee AS INTEGER)      AS annee,
        CAST(valeur AS NUMERIC)     AS taux_chomage,
        dataset_name,
        titre
    FROM source
    WHERE "Mileu" IS NOT NULL
      AND valeur IS NOT NULL
)

SELECT * FROM cleaned