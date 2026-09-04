import pandas as pd
import os
import json
import re
import psycopg2
from dotenv import load_dotenv

# Charger les variables depuis .env
load_dotenv()

# ─── Configuration PostgreSQL ──────────────────────────────────────────────

DB_CONFIG = {
    "host": "localhost",
    "database": os.getenv("DB_NAME", "morocco_labor_market"),
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "port": 5432
}

# ─── Chemins ──────────────────────────────────────────────────────────────
RAW_DIR = "data/raw"
CATALOG_FILE = "data/bronze/catalog.json"


# ─── Fonction 1 : charger le mapping name → title ─────────────────────────
def load_catalog():
    """
    Lit le catalogue JSON sauvegardé par extract.py.
    Retourne un dictionnaire : {"data_1_3": "Taux de chômage...", ...}
    """
    with open(CATALOG_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    # On crée un dictionnaire pour retrouver facilement le titre
    # d'un dataset à partir de son nom technique
    return {ds["name"]: ds["title"] for ds in catalog}


# ─── Fonction 2 : détecter les colonnes catégorielles ─────────────────────
def detect_dim_cols(df):
    """
    Identifie les colonnes "dimension" (Milieu, Sexe, Région...)
    par opposition aux colonnes temporelles (1997, 1998, 2006T1...).

    On parcourt les colonnes de gauche à droite.
    Dès qu'on trouve une colonne qui ressemble à une année
    ou un trimestre, on s'arrête.
    Tout ce qui précède = colonnes dimension.
    """
    dim_cols = []

    for col in df.columns:
        col_str = str(col).strip()

        # Pattern année : exactement 4 chiffres ex "1997", "2023"
        if re.match(r"^\d{4}$", col_str):
            break

        # Pattern trimestre : ex "2006T1", "2023T4"
        if re.match(r"^\d{4}T\d$", col_str):
            break

        dim_cols.append(col)

    return dim_cols


# ─── Fonction 3 : détecter si les données sont trimestrielles ─────────────
def is_trimestrial(df, dim_cols):
    """
    Retourne True si les colonnes temporelles sont des trimestres
    (ex: 2006T1) plutôt que des années (ex: 1997).
    """
    # Les colonnes temporelles = toutes les colonnes sauf les dimensions
    time_cols = [c for c in df.columns if c not in dim_cols]

    if not time_cols:
        return False

    # On regarde juste la première colonne temporelle
    first = str(time_cols[0]).strip()
    return bool(re.match(r"^\d{4}T\d$", first))


# ─── Fonction 4 : lire et transformer un fichier Excel ────────────────────
def process_file(filepath, dataset_name, name_to_title):
    """
    Lit un fichier Excel HCP et le transforme en format long (unpivot).
    Retourne un DataFrame prêt à être inséré dans PostgreSQL.
    Retourne None si le fichier ne peut pas être traité.
    """
    title = name_to_title.get(dataset_name, dataset_name)

    # header=3 : les lignes 0, 1, 2 sont titre + lignes vides
    # La vraie ligne d'en-tête est à l'index 3
    df = pd.read_excel(filepath, header=3)

    # Supprimer les lignes entièrement vides
    df = df.dropna(how="all").reset_index(drop=True)

    # Nettoyer les noms de colonnes (supprimer les espaces)
    df.columns = [str(c).strip() for c in df.columns]

    # Supprimer les colonnes "Unnamed: X" — artefacts Excel
    # qui apparaissent quand une cellule est vide dans le header
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Supprimer les lignes entièrement vides (après nettoyage)
    df = df.dropna(how="all")

    # Détecter les colonnes dimension et temporelles
    dim_cols = detect_dim_cols(df)
    time_cols = [c for c in df.columns if c not in dim_cols]

    # Si on n'a pas trouvé de colonnes dimension ou temporelles
    # le fichier a une structure inattendue → on l'ignore
    if not dim_cols or not time_cols:
        print(f"  SKIP : structure non reconnue")
        return None

    trimestrial = is_trimestrial(df, dim_cols)

    # ── UNPIVOT (Wide → Long) ──────────────────────────────────────────
    # id_vars   : colonnes qui restent fixes (Milieu, Sexe, Région...)
    # value_vars : colonnes à transformer en lignes (les années/trimestres)
    # var_name  : nom de la nouvelle colonne pour les périodes
    # value_name : nom de la nouvelle colonne pour les valeurs
    melted = df.melt(
        id_vars=dim_cols,
        value_vars=time_cols,
        var_name="periode" if trimestrial else "annee",
        value_name="valeur"
    )

    # ── Nettoyage des valeurs numériques ──────────────────────────────
    # Convertir en string d'abord pour pouvoir utiliser str.replace()
    melted["valeur"] = melted["valeur"].astype(str).str.strip()

    # Remplacer la virgule décimale française par le point anglais
    # ex: "13,8" → "13.8"
    melted["valeur"] = melted["valeur"].str.replace(",", ".", regex=False)

    # Mettre à None les valeurs manquantes représentées comme "-"
    # ou comme chaînes vides
    valeurs_manquantes = ["-", "nan", "NaN", "", "None", " "]
    melted.loc[melted["valeur"].isin(valeurs_manquantes), "valeur"] = None

    # Convertir en numérique — errors="coerce" transforme
    # les valeurs non convertibles en NaN au lieu de lever une erreur
    melted["valeur"] = pd.to_numeric(melted["valeur"], errors="coerce")

    # Supprimer les lignes sans valeur numérique valide
    melted = melted.dropna(subset=["valeur"])

    # Ajouter des colonnes de traçabilité
    # Elles permettent de savoir d'où vient chaque ligne
    melted["dataset_name"] = dataset_name
    melted["titre"] = title

    return melted


# ─── Fonction 5 : insérer un DataFrame dans PostgreSQL ────────────────────
def insert_to_postgres(df, table_name, schema="bronze"):
    """
    Crée une table dans PostgreSQL et insère les données.
    Toutes les colonnes sont créées en TEXT — dbt se chargera
    de caster les types en Silver.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cols = list(df.columns)

    # Construire la liste des colonnes pour le CREATE TABLE
    # Toutes en TEXT pour éviter les erreurs de type à ce stade
    col_defs = ", ".join([f'"{c}" TEXT' for c in cols])

    # Construire la liste des colonnes pour l'INSERT
    col_names = ", ".join([f'"{c}"' for c in cols])

    # Construire les placeholders pour les valeurs (%s par colonne)
    placeholders = ", ".join(["%s"] * len(cols))

    # Supprimer la table si elle existe déjà (pour pouvoir relancer)
    cur.execute(f'DROP TABLE IF EXISTS {schema}."{table_name}"')

    # Créer la table
    cur.execute(f'CREATE TABLE {schema}."{table_name}" ({col_defs})')

    # Insérer les données ligne par ligne
    for _, row in df.iterrows():
        values = [str(v) if v is not None else None for v in row]
        cur.execute(
            f'INSERT INTO {schema}."{table_name}" ({col_names}) '
            f'VALUES ({placeholders})',
            values
        )

    # Valider la transaction
    conn.commit()
    cur.close()
    conn.close()


# ─── Fonction principale ───────────────────────────────────────────────────
def load_all():
    """
    Orchestre le traitement de tous les fichiers Excel :
    lire → transformer → insérer dans PostgreSQL.
    """
    name_to_title = load_catalog()
    success = 0
    failed = 0

    for filename in sorted(os.listdir(RAW_DIR)):
        if not filename.endswith(".xlsx"):
            continue

        # "data_1_3.xlsx" → "data_1_3"
        dataset_name = filename.replace(".xlsx", "")

        filepath = os.path.join(RAW_DIR, filename)

        # Nom de la table dans PostgreSQL
        # ex: "data_1_3" → "bronze_data_1_3"
        table_name = f"bronze_{dataset_name}"

        print(f"Traitement : {dataset_name} → {table_name}")

        try:
            df = process_file(filepath, dataset_name, name_to_title)

            if df is None:
                failed += 1
                continue

            insert_to_postgres(df, table_name)
            print(f"  OK : {len(df)} lignes chargées")
            success += 1

        except Exception as e:
            print(f"  ERREUR : {e}")
            failed += 1

    print(f"\nTotal — OK: {success} | Echecs: {failed}")


if __name__ == "__main__":
    load_all()