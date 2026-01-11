import json
from pathlib import Path
import streamlit as st
import re

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="OPR Army Builder FR", layout="centered")
st.title("OPR Army Builder 🇫🇷")

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# -------------------------------------------------
# UTILS
# -------------------------------------------------
def extract_coriace(rules):
    """Extrait la valeur Coriace (x) depuis une liste de règles"""
    total = 0
    for r in rules:
        m = re.search(r"Coriace\s*\((\d+)\)", r)
        if m:
            total += int(m.group(1))
    return total

# -------------------------------------------------
# LOAD FACTIONS
# -------------------------------------------------
if not FACTIONS_DIR.exists():
    st.error(f"Dossier factions introuvable : {FACTIONS_DIR}")
    st.stop()

faction_files = sorted(FACTIONS_DIR.glob("*.json"))
if not faction_files:
    st.error("Aucun fichier faction trouvé")
    st.stop()

games = set()
faction_map = {}

for fp in faction_files:
    with open(fp, encoding="utf-8") as f:
        data = json.load(f)
        game = data.get("game", "Inconnu")
        name = data.get("faction", fp.stem)
        games.add(game)
        faction_map[name] = {"file": fp, "game": game}

selected_game = st.selectbox("Sélectionner le jeu", sorted(games))

game_factions = {
    name: info for name, info in faction_map.items()
    if info["game"] == selected_game
}

selected_faction = st.selectbox("Sélectionner la faction", sorted(game_factions))

with open(game_factions[selected_faction]["file"], encoding="utf-8") as f:
    faction = json.load(f)

units = faction.get("units", [])

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "army_list" not in st.session_state:
    st.session_state.army_list = []
if "army_total_cost" not in st.session_state:
    st.session_state.army_total_cost = 0

# -------------------------------------------------
# UNIT SELECTOR
# -------------------------------------------------
st.divider()
st.subheader("Configurer une unité")

unit_names = [u["name"] for u in units]
selected_unit_name = st.selectbox("Choisir une unité", unit_names)

unit = next(u for u in units if u["name"] == selected_unit_name)

# -------------------------------------------------
# BASE PROFILE
# -------------------------------------------------
base_cost = unit["base_cost"]
base_rules = unit.get("special_rules", [])
base_coriace = extract_coriace(base_rules)

total_cost = base_cost
selected_options = {}
selected_mount = None
mount_coriace = 0

# -------------------------------------------------
# OPTIONS
# -------------------------------------------------
for group in unit.get("upgrade_groups", []):
    choices = ["— Aucun —"] + [o["name"] for o in group["options"]]
    choice = st.selectbox(group["group"], choices)

    if choice != "— Aucun —":
        opt = next(o for o in group["options"] if o["name"] == choice)
        total_cost += opt.get("cost", 0)

        if opt.get("type") == "mount":
            selected_mount = opt
            mount_coriace += extract_coriace(opt.get("special_rules", []))
        else:
            selected_options[group["group"]] = opt

# -------------------------------------------------
# ADD UNIT
# -------------------------------------------------
if st.button("➕ Ajouter à l'armée"):
    st.session_state.army_list.append({
        "name": unit["name"],
        "cost": total_cost,
        "quality": unit.get("quality"),
        "defense": unit.get("defense"),
        "base_rules": base_rules,
        "base_coriace": base_coriace,
        "mount": selected_mount,
        "mount_coriace": mount_coriace,
        "options": selected_options
    })
    st.session_state.army_total_cost += total_cost
    st.success("Unité ajoutée")

# -------------------------------------------------
# ARMY LIST
# -------------------------------------------------
st.divider()
st.subheader("Liste de l'armée")

for i, u in enumerate(st.session_state.army_list):
    total_coriace = u["base_coriace"] + u["mount_coriace"]

    st.markdown(f"""
    <style>
    .army-card {{
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }}
    .badge {{
        display:inline-block;
        padding:6px 12px;
        border-radius:15px;
        background:#4a89dc;
        color:white;
        margin-right:8px;
    }}
    .section-title {{
        font-weight:bold;
        color:#4a89dc;
        margin-top:10px;
    }}
    </style>

    <div class="army-card">
        <h4>{u['name']} — {u['cost']} pts</h4>

        <div>
            <span class="badge">Qualité {u['quality']}+</span>
            <span class="badge">Défense {u['defense']}+</span>
            <span class="badge">Coriace {total_coriace}</span>
        </div>

        <div class="section-title">Règles spéciales</div>
        <div>{", ".join(u["base_rules"]) if u["base_rules"] else "Aucune"}</div>

        {(
            f'''
            <div class="section-title">Options sélectionnées</div>
            <div>{", ".join(opt["name"] for opt in u["options"].values())}</div>
            '''
        ) if u["options"] else ""}

        {(
            f'''
            <div class="section-title">Monture</div>
            <div><strong>{u["mount"]["name"]}</strong><br>
            {", ".join(u["mount"].get("special_rules", []))}</div>
            '''
        ) if u["mount"] else ""}
    </div>
    """, unsafe_allow_html=True)

    if st.button("❌ Supprimer", key=f"del_{i}"):
        st.session_state.army_total_cost -= u["cost"]
        st.session_state.army_list.pop(i)
        st.rerun()

st.markdown(f"### 💰 Total armée : {st.session_state.army_total_cost} pts")
