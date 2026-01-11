import json
import re
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
# UTILITAIRES
# -------------------------------------------------
def extract_coriace(rules):
    """
    Additionne toutes les valeurs de Coriace trouvées dans une liste de règles,
    y compris dans une phrase (ex: Griffes lourdes (..., Coriace (+6), ...))
    """
    total = 0
    for rule in rules:
        matches = re.findall(r"Coriace\s*\(\+?(\d+)\)", rule)
        for m in matches:
            total += int(m)
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
faction_map = {}

for fp in faction_files:
    try:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            game = data.get("game", "Inconnu")
            name = data.get("faction", fp.stem)
            games.add(game)
            faction_map.setdefault(game, {})[name] = fp
    except Exception as e:
        st.warning(f"Erreur lecture {fp.name} : {e}")

selected_game = st.selectbox("Sélectionner le jeu", sorted(games))
selected_faction = st.selectbox(
    "Sélectionner la faction",
    sorted(faction_map[selected_game].keys())
)

# -------------------------------------------------
# CHARGEMENT DE LA FACTION
# -------------------------------------------------
with open(faction_map[selected_game][selected_faction], encoding="utf-8") as f:
    faction = json.load(f)

st.subheader(f"Faction : {faction.get('faction')}")
st.caption(f"Jeu : {faction.get('game')}")

units = faction.get("units", [])
if not units:
    st.warning("Aucune unité disponible.")
    st.stop()

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "army_list" not in st.session_state:
    st.session_state.army_list = []
if "army_total_cost" not in st.session_state:
    st.session_state.army_total_cost = 0

# -------------------------------------------------
# SÉLECTEUR D’UNITÉ
# -------------------------------------------------
st.divider()
st.subheader("Configurer une unité")

def unit_label(u):
    return f"{u['name']} ({u['base_cost']} pts | Q{u['quality']}+ / D{u['defense']}+)"

unit_names = [u["name"] for u in units]
selected_unit_name = st.selectbox(
    "Choisir une unité",
    unit_names,
    format_func=lambda n: unit_label(next(u for u in units if u["name"] == n))
)

unit = next(u for u in units if u["name"] == selected_unit_name)

# -------------------------------------------------
# BASE PROFIL
# -------------------------------------------------
total_cost = unit["base_cost"]
base_rules = list(unit.get("special_rules", []))
weapon = unit.get("weapons", [{}])[0]
selected_options = {}
selected_mount = None

# -------------------------------------------------
# OPTIONS
# -------------------------------------------------
st.subheader("Options")

for group in unit.get("upgrade_groups", []):
    key = f"{unit['name']}_{group['group']}"
    choices = ["— Aucun —"] + [o["name"] for o in group["options"]]
    choice = st.selectbox(group["group"], choices, key=key)

    if choice != "— Aucun —":
        opt = next(o for o in group["options"] if o["name"] == choice)
        total_cost += opt.get("cost", 0)

        if group["type"] == "weapon":
            weapon = opt["weapon"] | {"name": opt["name"]}
        elif group["type"] == "mount":
            selected_mount = {
                "name": opt["name"],
                "special_rules": opt.get("special_rules", [])
            }
        else:
            selected_options[group["group"]] = {"name": opt["name"]}

# -------------------------------------------------
# AJOUT À L’ARMÉE
# -------------------------------------------------
st.markdown(f"### 💰 Coût total de l’unité : **{total_cost} pts**")

if st.button("➕ Ajouter à l’armée"):
    st.session_state.army_list.append({
        "name": unit["name"],
        "cost": total_cost,
        "quality": unit["quality"],
        "defense": unit["defense"],
        "base_rules": base_rules,
        "weapon": weapon,
        "options": selected_options,
        "mount": selected_mount
    })
    st.session_state.army_total_cost += total_cost
    st.success("Unité ajoutée à l’armée")

# -------------------------------------------------
# LISTE DE L’ARMÉE
# -------------------------------------------------
st.divider()
st.subheader("Liste de l’armée")

if not st.session_state.army_list:
    st.write("Aucune unité ajoutée.")
else:
    for i, u in enumerate(st.session_state.army_list, 1):
        col_card, col_btn = st.columns([5, 1])

        base_coriace = extract_coriace(u.get("base_rules", []))
        mount_coriace = extract_coriace(u["mount"]["special_rules"]) if u.get("mount") else 0
        total_coriace = base_coriace + mount_coriace

        with col_card:
            st.markdown(f"""
<div style="border:1px solid #ccc;border-radius:8px;padding:15px;background:#f9f9f9">

<strong>{u['name']} [{i}]</strong> — {u['cost']} pts<br><br>

<div style="display:flex;gap:10px;margin-bottom:10px">
<span style="background:#4a89dc;color:white;padding:4px 12px;border-radius:14px">Qualité {u['quality']}+</span>
<span style="background:#5cb85c;color:white;padding:4px 12px;border-radius:14px">Défense {u['defense']}+</span>
{f"<span style='background:#d9534f;color:white;padding:4px 12px;border-radius:14px'>Coriace {total_coriace}</span>" if total_coriace > 0 else ""}
</div>

<strong>Règles spéciales :</strong><br>
{', '.join(u.get('base_rules', [])) or 'Aucune'}<br><br>

<strong>Arme :</strong><br>
{u['weapon']['name']} | A{u['weapon']['attacks']} | PA({u['weapon']['armor_piercing']})
{f" | {', '.join(u['weapon'].get('special_rules', []))}" if u['weapon'].get('special_rules') else ''}<br><br>

<strong>Options sélectionnées :</strong><br>
{', '.join(o['name'] for o in u['options'].values()) or 'Aucune'}<br><br>

{f"<strong>Monture :</strong><br>{u['mount']['name']} — {', '.join(u['mount']['special_rules'])}" if u.get("mount") else ""}

</div>
""", unsafe_allow_html=True)

        with col_btn:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.army_total_cost -= u["cost"]
                st.session_state.army_list.pop(i - 1)
                st.rerun()

    st.markdown(f"### 💰 Total armée : **{st.session_state.army_total_cost} pts**")
