import os
import csv
import json
import streamlit as st

# ======================
# Helpers
# ======================

def try_load(paths):
    for p in paths:
        try:
            with open(p, encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            st.error(f"JSON invalide dans {p}: {e}")
            st.stop()
    st.error(f"Aucun fichier trouvé parmi: {', '.join(paths)}")
    st.stop()

def load_faction_mapping(csv_path="data/factions_by_game.csv"):
    mapping = {}
    if not os.path.exists(csv_path):
        return mapping, f"Mapping non trouvé: {csv_path}"
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                game = (row.get('Game') or '').strip()
                filep = (row.get('faction_file') or '').strip()
                name = (row.get('faction_name') or '').strip()
                if not game:
                    continue
                mapping.setdefault(game, []).append({
                    'file': filep if filep else None,
                    'name': name if name else None
                })
        return mapping, f"Mapping chargé depuis {csv_path}"
    except Exception as e:
        return {}, f"Erreur lecture mapping CSV: {e}"

def scan_faction_jsons(dirs=None):
    if dirs is None:
        dirs = ['data/lists/data/factions', 'data/factions']
    found = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith('.json'):
                p = os.path.join(d, fn)
                try:
                    with open(p, encoding='utf-8') as f:
                        j = json.load(f)
                        name = j.get('faction') or j.get('name')
                except Exception:
                    name = os.path.splitext(fn)[0]
                found.append({'file': p, 'name': name})
    return found

# ======================
# Initialisation
# ======================

st.title("OPR Army Builder 🇫🇷")

# Jeux OPR
GAMES = [
    "Age of Fantasy",
    "Age of Fantasy Skirmish",
    "Age of Fantasy Regiment",
    "Grimdark Future",
    "Grimdark Future Firefight",
    "Warfleet",
]

# Paths fallback
faction_paths = ['data/lists/data/factions/sisters_blessed.json']
rules_paths = ['data/lists/data/rules/opr_limits.json']

rules = try_load(rules_paths)

# Session state
if 'selected_game' not in st.session_state:
    st.session_state.selected_game = GAMES[0]

if 'selected_faction_name' not in st.session_state:
    st.session_state.selected_faction_name = None

if 'selected_faction_path' not in st.session_state:
    st.session_state.selected_faction_path = None

if 'faction' not in st.session_state:
    st.session_state.faction = try_load(faction_paths)

if 'army' not in st.session_state:
    st.session_state.army = []

# ======================
# Sélection du jeu
# ======================

selected_game = st.selectbox(
    "Variante OPR (jeu)",
    GAMES,
    key="selected_game"
)

# unit_per_points
DEFAULT_UNIT_PER_POINTS = {
    "Age of Fantasy": 200,
    "Age of Fantasy Skirmish": 100,
    "Age of Fantasy Regiment": 300,
    "Grimdark Future": 200,
    "Grimdark Future Firefight": 150,
    "Warfleet": 400,
}

unit_per_points = rules.get("unit_per_points_by_game", {}).get(
    selected_game,
    rules.get("unit_per_points", DEFAULT_UNIT_PER_POINTS[selected_game])
)

# ======================
# Chargement factions
# ======================

mapping, _ = load_faction_mapping("data/factions_by_game.csv")

faction_options = []
seen = set()

for entry in mapping.get(selected_game, []):
    name = entry.get("name")
    filep = entry.get("file")
    if name and name not in seen:
        faction_options.append({'name': name, 'file': filep})
        seen.add(name)

for found in scan_faction_jsons():
    if found['name'] not in seen:
        faction_options.append(found)
        seen.add(found['name'])

if not faction_options:
    st.error("Aucune faction disponible.")
    st.stop()

# ======================
# Sélection faction
# ======================

faction_names = [f['name'] for f in faction_options]

sel_name = st.selectbox(
    "Sélectionner la faction",
    faction_names,
    key="selected_faction_name"
)

selected_entry = next(f for f in faction_options if f['name'] == sel_name)
selected_path = selected_entry.get('file')

# Charger la faction SEULEMENT si elle change
if selected_path != st.session_state.selected_faction_path:
    st.session_state.selected_faction_path = selected_path
    st.session_state.army = []  # reset armée

    if selected_path and os.path.exists(selected_path):
        with open(selected_path, encoding='utf-8') as f:
            st.session_state.faction = json.load(f)
    else:
        st.session_state.faction = {
            "faction": sel_name,
            "units": []
        }

    st.session_state.faction["faction"] = sel_name

# ======================
# Affichage
# ======================

st.subheader(f"Faction : {st.session_state.faction.get('faction')}")
st.caption(f"Jeu : {selected_game} — unit_per_points : {unit_per_points}")

# ======================
# Ajout unités
# ======================

units = st.session_state.faction.get("units", [])

if not units:
    st.warning("Aucune unité disponible pour cette faction.")
else:
    unit_names = [u.get("name", "Sans nom") for u in units]
    col1, col2 = st.columns([3, 1])

    with col1:
        sel_unit = st.selectbox("Ajouter une unité", unit_names)

    with col2:
        if st.button("➕ Ajouter"):
            unit = next(u for u in units if u.get("name") == sel_unit)
            st.session_state.army.append({
                **unit,
                "base_cost": int(unit.get("base_cost", 0))
            })

# ======================
# Liste actuelle
# ======================

st.subheader("🧾 Liste actuelle")

if not st.session_state.army:
    st.info("Aucune unité ajoutée.")
else:
    for i, u in enumerate(st.session_state.army):
        cols = st.columns([6, 1])
        cols[0].write(f"- {u['name']} ({u['base_cost']} pts)")
        if cols[1].button("🗑️", key=f"del_{i}"):
            st.session_state.army.pop(i)
            st.experimental_rerun()

# ======================
# Budget & validation
# ======================

budget = st.number_input("Budget total", min_value=0, value=1000, step=50)
total = sum(u["base_cost"] for u in st.session_state.army)

st.markdown(f"### Total : **{total} pts**")

max_units = budget // unit_per_points

if total > budget:
    st.error("❌ Dépasse le budget")
elif len(st.session_state.army) > max_units:
    st.error("❌ Trop d’unités")
else:
    st.success("✅ Liste valide")
