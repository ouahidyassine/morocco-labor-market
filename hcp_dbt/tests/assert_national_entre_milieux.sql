-- Le taux national est une moyenne pondérée des taux urbain et rural :
-- il est forcément compris entre les deux. Le line chart repose
-- sur cet invariant, une violation doit donc bloquer le pipeline.

WITH par_milieu AS (
    SELECT
        tranche_age,
        annee,
        MAX(CASE WHEN milieu = 'National' THEN taux_chomage END) AS national,
        MAX(CASE WHEN milieu = 'Urbain'   THEN taux_chomage END) AS urbain,
        MAX(CASE WHEN milieu = 'Rural'    THEN taux_chomage END) AS rural
    FROM {{ ref('stg_chomage_age_sexe') }}
    WHERE sexe = 'Total'
    GROUP BY tranche_age, annee
)

SELECT *
FROM par_milieu
WHERE national IS NOT NULL
  AND urbain IS NOT NULL
  AND rural IS NOT NULL
  AND (national < LEAST(urbain, rural)
       OR national > GREATEST(urbain, rural))