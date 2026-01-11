import json
import textwrap
from pathlib import Path
import streamlit as st

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="OPR Army Builder FR", layout="centered")
st.title("OPR Army Builder 🇫🇷")

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# -------------------------------------------------
# OUTILS
# -------------------------------------------------
def extract_coriace(rules):
    total = 0
    for r in rules:
        if "Coriace" in r:
            val = r.split("(")[-1].replace(")", "").replace("+", "")
            try:
                total += int(val)
            except:
                pass
    return total

# -------------------------------------------------
# CHARGEMENT DES FACTIONS
# -------------------------------------------------
if not FACTIONS_DIR.exists():
    st.error(f"Dossier factions introuvable : {FACTIONS_DIR}")
    st.stop()

faction_files = sorted(FACTIONS_DIR.glob("*.json"))
if not faction_files:
    st.error("Aucun fichier faction trouvé")
    st.stop()

games = set()
factions = {}

for fp in faction_files:
    with open(fp, encoding="utf-8") as f:
        data = json.load(f)
        game = data.get("game", "Inconnu")
        name = data.get("faction", fp.stem)
        games.add(game)
        factions[name] = {"file": fp, "game": game}

# -------------------------------------------------
# SÉLECTEURS
# -------------------------------------------------
selected_game = st.selectbox("Sélectionner le jeu", sorted(games))

available_factions = {
    name: info for name, info in factions.items()
    if info["game"] == selected_game
}

selected_faction = st.selectbox(
    "Sélectionner la faction",
    sorted(available_factions.keys())
)

with open(available_factions[selected_faction]["file"], encoding="utf-8") as f:
    faction = json.load(f)

st.subheader(f"Faction : {faction['faction']}")

units = faction.get("units", [])
if not units:
    st.warning("Aucune unité définie.")
    st.stop()

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "army_list" not in st.session_state:
    st.session_state.army_list = []

# -------------------------------------------------
# CONFIGURATION D’UNE UNITÉ
# -------------------------------------------------
st.divider()
st.subheader("Configurer une unité")

unit_names = [u["name"] for u in units]
selected_unit_name = st.selectbox("Choisir une unité", unit_names)
unit = next(u for u in units if u["name"] == selected_unit_name)

total_cost = unit["base_cost"]
base_rules = unit.get("special_rules", []).copy()
options = {}
mount = None
weapon = unit["weapons"][0]

# Options
for group in unit.get("upgrade_groups", []):
    choices = ["— Aucun —"] + [o["name"] for o in group["options"]]
    choice = st.selectbox(group["group"], choices)

    if choice != "— Aucun —":
        opt = next(o for o in group["options"] if o["name"] == choice)
        total_cost += opt.get("cost", 0)

        if group["type"] == "mount":
            mount = opt
        elif group["type"] == "weapon":
            weapon = opt["weapon"] | {"name": opt["name"]}
        else:
            options[group["group"]] = opt

# -------------------------------------------------
# AJOUT À L’ARMÉE
# -------------------------------------------------
if st.button("➕ Ajouter à l’armée"):
    st.session_state.army_list.append({
        "name": unit["name"],
        "cost": total_cost,
        "quality": unit["quality"],
        "defense": unit["defense"],
        "base_rules": base_rules,
        "weapon": weapon,
        "options": options,
        "mount": mount
    })
    st.success("Unité ajoutée")

# -------------------------------------------------
# AFFICHAGE LISTE DE L’ARMÉE
# -------------------------------------------------
st.divider()
st.subheader("Liste de l’armée")

for i, u in enumerate(st.session_state.army_list):
    base_coriace = extract_coriace(u["base_rules"])
    mount_coriace = extract_coriace(u["mount"]["special_rules"]) if u["mount"] else 0
    total_coriace = base_coriace + mount_coriace

    st.markdown(
        textwrap.dedent(f"""
        <style>
        .army-card {{
            border:1px solid #ccc;
            border-radius:10px;
            padding:15px;
            margin-bottom:15px;
            background:#f9f9f9;
        }}
        .badge {{
            display:inline-block;
            background:#4a89dc;
            color:white;
            padding:6px 12px;
            border-radius:15px;
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
            <div>{", ".join(u["base_rules"])}</div>

            {(
                f'''
                <div class="section-title">Options sélectionnées</div>
                <div>{", ".join(opt["name"] for opt in u["options"].values())}</div>
                '''
            ) if u["options"] else ""}

            {(
                f'''
                <div class="section-title">Monture</div>
                <div>
                    <strong>{u["mount"]["name"]}</strong><br>
                    {", ".join(u["mount"]["special_rules"])}
                </div>
                '''
            ) if u["mount"] else ""}
        </div>
        """),
        unsafe_allow_html=True
    )

    if st.button("❌ Supprimer", key=f"del_{i}"):
        st.session_state.army_list.pop(i)
        st.rerun()
