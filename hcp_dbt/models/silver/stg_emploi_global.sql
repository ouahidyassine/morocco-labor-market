{{ config(materialized='view', schema='silver') }}

WITH source AS (
    SELECT * FROM {{ source('bronze', 'bronze_data_1_7') }}
),

cleaned AS (
    SELECT
        "Milieu de résidence"       AS milieu,
        CAST(annee AS INTEGER)      AS annee,
        CAST(valeur AS NUMERIC)     AS taux_emploi,
        dataset_name,
        titre
    FROM source
    WHERE "Milieu de résidence" IS NOT NULL
      AND valeur IS NOT NULL
)

SELECT * FROM cleaned