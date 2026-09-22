{{ config(severity = 'warn') }}

-- Le taux de chômage total est une moyenne pondérée des taux
-- masculin et féminin : il est forcément compris entre les deux.
-- Chaque ligne retournée signale une valeur erronée dans la source.

WITH par_sexe AS (
    SELECT
        milieu,
        tranche_age,
        annee,
        MAX(CASE WHEN sexe = 'Total'    THEN taux_chomage END) AS total,
        MAX(CASE WHEN sexe = 'Masculin' THEN taux_chomage END) AS masculin,
        MAX(CASE WHEN sexe = 'Feminin'  THEN taux_chomage END) AS feminin
    FROM {{ ref('stg_chomage_age_sexe') }}
    GROUP BY milieu, tranche_age, annee
)

SELECT *
FROM par_sexe
WHERE total IS NOT NULL
  AND masculin IS NOT NULL
  AND feminin IS NOT NULL
  AND (total < LEAST(masculin, feminin)
       OR total > GREATEST(masculin, feminin))