SELECT 'stg_chomage_regional' AS modele, taux_chomage AS valeur
FROM {{ ref('stg_chomage_regional') }}
WHERE taux_chomage < 0 OR taux_chomage > 100

UNION ALL

SELECT 'stg_chomage_age_sexe', taux_chomage
FROM {{ ref('stg_chomage_age_sexe') }}
WHERE taux_chomage < 0 OR taux_chomage > 100

UNION ALL

SELECT 'stg_activite', taux_activite
FROM {{ ref('stg_activite') }}
WHERE taux_activite < 0 OR taux_activite > 100

UNION ALL

SELECT 'stg_emploi_global', taux_emploi
FROM {{ ref('stg_emploi_global') }}
WHERE taux_emploi < 0 OR taux_emploi > 100

UNION ALL

SELECT 'stg_emploi_secteur', taux_emploi
FROM {{ ref('stg_emploi_secteur') }}
WHERE taux_emploi < 0 OR taux_emploi > 100