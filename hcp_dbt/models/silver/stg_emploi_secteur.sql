{{ config(materialized='view', schema='silver') }}

WITH source AS (
    SELECT * FROM {{ source('bronze', 'bronze_data_1_22') }}
),

cleaned AS (
    SELECT
        "Milieu"                    AS milieu,
        "Secteur"                   AS secteur,
        periode,
        CAST(valeur AS NUMERIC)     AS taux_emploi,
        dataset_name,
        titre
    FROM source
    WHERE "Milieu" IS NOT NULL
      AND valeur IS NOT NULL
)

SELECT * FROM cleaned