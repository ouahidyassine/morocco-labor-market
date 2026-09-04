import requests
import json
import time
import os

# URL de base de l'API CKAN du portail Open Data marocain
API_BASE = "https://data.gov.ma/data/api/3/action"

# Dossiers de sortie
RAW_DIR = "data/raw"
BRONZE_DIR = "data/bronze"


def fetch_catalog():
    """
    Appelle l'API CKAN pour récupérer la liste des datasets
    emploi du HCP.
    Retourne une liste de dictionnaires, un par dataset.
    """
    url = f"{API_BASE}/package_search"

    # fq = filter query
    # groups:emploi          → uniquement le groupe Emploi
    # organization:haut-...  → uniquement les données du HCP
    params = {
        "fq": "groups:emploi AND organization:haut-commissariat-au-plan",
        "rows": 100
    }

    print("Connexion à l'API HCP...")
    response = requests.get(url, params=params, timeout=15)

    # Lève une exception si le serveur répond avec une erreur HTTP
    response.raise_for_status()

    data = response.json()

    if not data["success"]:
        raise Exception("L'API a retourné success=false")

    datasets = data["result"]["results"]
    print(f"{len(datasets)} datasets trouvés")
    return datasets


def save_catalog(datasets):
    """
    Sauvegarde le catalogue complet en JSON dans data/bronze/.
    Utile pour déboguer et pour Airflow plus tard.
    """
    os.makedirs(BRONZE_DIR, exist_ok=True)
    path = os.path.join(BRONZE_DIR, "catalog.json")

    # On garde uniquement les infos utiles : name, title, resources
    catalog = []
    for ds in datasets:
        catalog.append({
            "name": ds["name"],
            "title": ds["title"],
            "resources": [
                {
                    "url": r["url"],
                    "format": r["format"],
                    "name": r["name"]
                }
                for r in ds.get("resources", [])
            ]
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Catalogue sauvegardé : {path}")
    return catalog


def download_files(catalog):
    """
    Télécharge chaque fichier XLSX du catalogue dans data/raw/.
    Attend 1 seconde entre chaque téléchargement.
    """
    os.makedirs(RAW_DIR, exist_ok=True)

    success = 0
    failed = 0

    for ds in catalog:
        name = ds["name"]

        for resource in ds["resources"]:

            # On ne télécharge que les fichiers Excel
            if resource["format"].upper() != "XLSX":
                continue

            filepath = os.path.join(RAW_DIR, f"{name}.xlsx")

            try:
                print(f"Téléchargement : {name}.xlsx")
                r = requests.get(resource["url"], timeout=20)
                r.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(r.content)

                success += 1

            except Exception as e:
                print(f"  ERREUR sur {name} : {e}")
                failed += 1

            # 1 seconde de délai entre chaque requête — bonne pratique
            time.sleep(1)

    print(f"\nTerminé — OK: {success} | Echecs: {failed}")


if __name__ == "__main__":
    datasets = fetch_catalog()
    catalog = save_catalog(datasets)
    download_files(catalog)