import json
from pathlib import Path
import streamlit as st

# -------------------------------------------------
# CONFIG GÉNÉRALE
# -------------------------------------------------
st.set_page_config(page_title="OPR Army Builder FR", layout="centered")
st.title("OPR Army Builder 🇫🇷")

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# -------------------------------------------------
# CHARGEMENT DES FACTIONS ET EXTRACTION DES JEUX
# -------------------------------------------------
if not FACTIONS_DIR.exists():
    st.error(f"Dossier factions introuvable : {FACTIONS_DIR}")
    st.stop()

faction_files = sorted(FACTIONS_DIR.glob("*.json"))

if not faction_files:
    st.error("Aucun fichier faction trouvé")
    st.stop()

# Extraire les jeux uniques depuis les fichiers
games = set()
faction_map = {}

for fp in faction_files:
    try:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            game = data.get("game", "Inconnu")
            games.add(game)
            name = data.get("faction", fp.stem)
            faction_map[name] = {"file": fp, "game": game}
    except Exception as e:
        st.warning(f"Impossible de lire {fp.name} : {e}")

if not games:
    st.error("Aucun jeu trouvé dans les fichiers")
    st.stop()

# Sélecteur de jeu
selected_game = st.selectbox(
    "Sélectionner le jeu",
    sorted(games)
)

# Filtrer les factions pour le jeu sélectionné
game_factions = {
    name: info for name, info in faction_map.items()
    if info["game"] == selected_game
}

if not game_factions:
    st.error(f"Aucune faction trouvée pour le jeu {selected_game}")
    st.stop()

# Sélecteur de faction
selected_faction = st.selectbox(
    "Sélectionner la faction",
    sorted(game_factions.keys())
)

# -------------------------------------------------
# CHARGEMENT DE LA FACTION
# -------------------------------------------------
FACTION_PATH = game_factions[selected_faction]["file"]

with open(FACTION_PATH, encoding="utf-8") as f:
    faction = json.load(f)

# -------------------------------------------------
# AFFICHAGE FACTION
# -------------------------------------------------
st.subheader(f"Faction : {faction.get('faction','Inconnue')}")
st.caption(f"Jeu : {faction.get('game', selected_game)}")

units = faction.get("units", [])
if not units:
    st.warning("Aucune unité disponible pour cette faction.")
    st.stop()

# -------------------------------------------------
# SESSION STATE POUR LA LISTE D'ARMÉE
# -------------------------------------------------
if "army_list" not in st.session_state:
    st.session_state.army_list = []
if "army_total_cost" not in st.session_state:
    st.session_state.army_total_cost = 0

# -------------------------------------------------
# SÉLECTEUR D’UNITÉ
# -------------------------------------------------
st.divider()
st.subheader("Ajouter une unité à l'armée")

if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = units[0]["name"]

def unit_label(u):
    return f"{u['name']} ({u['base_cost']} pts | Q{u['quality']}+ / D{u['defense']}+)"

unit_names = [u["name"] for u in units]

selected_name = st.selectbox(
    "Choisir une unité",
    unit_names,
    index=unit_names.index(st.session_state.selected_unit),
    format_func=lambda n: unit_label(next(u for u in units if u["name"] == n))
)

st.session_state.selected_unit = selected_name
unit = next(u for u in units if u["name"] == selected_name)

# -------------------------------------------------
# OPTIONS & CALCUL
# -------------------------------------------------
total_cost = unit.get("base_cost", 0)
final_rules = list(unit.get("special_rules", []))
final_weapons = list(unit.get("weapons", []))

for group in unit.get("upgrade_groups", []):
    key = f"{unit['name']}_{group['group']}"
    options = ["— Aucun —"] + [opt["name"] for opt in group["options"]]
    choice = st.selectbox(group["group"], options, key=key)

    if choice != "— Aucun —":
        opt = next(o for o in group["options"] if o["name"] == choice)
        total_cost += opt.get("cost", 0)
        if "special_rules" in opt:
            final_rules.extend(opt["special_rules"])
        if "weapon" in opt:
            final_weapons = [opt["weapon"]]

# -------------------------------------------------
# PROFIL FINAL DE L'UNITÉ
# -------------------------------------------------
st.divider()
st.subheader("Profil final de l'unité")

st.markdown(f"## 💰 Coût total : **{total_cost} pts**")

st.markdown("### 🛡️ Règles spéciales")
if final_rules:
    for r in sorted(set(final_rules)):
        st.write(f"- {r}")
else:
    st.write("—")

st.markdown("### ⚔️ Armes")
if final_weapons:
    for w in final_weapons:
        st.write(
            f"- **{w.get('name','Arme')}** | "
            f"A{w.get('attacks','?')} | "
            f"PA({w.get('armor_piercing','?')}) "
            f"{' '.join(w.get('special_rules', []))}"
        )
else:
    st.write("—")

# -------------------------------------------------
# BOUTON POUR AJOUTER L'UNITÉ À L'ARMÉE
# -------------------------------------------------
if st.button("➕ Ajouter à l'armée"):
    st.session_state.army_list.append({
        "name": unit["name"],
        "cost": total_cost,
        "rules": final_rules,
        "weapons": final_weapons
    })
    st.session_state.army_total_cost += total_cost
    st.success(f"Unité {unit['name']} ajoutée à l'armée !")

# -------------------------------------------------
# AFFICHAGE DE LA LISTE D'ARMÉE
# -------------------------------------------------
st.divider()
st.subheader("Liste de l'armée")

if not st.session_state.army_list:
    st.write("Aucune unité ajoutée pour le moment.")
else:
    for i, army_unit in enumerate(st.session_state.army_list, 1):
        st.write(f"{i}. **{army_unit['name']}** ({army_unit['cost']} pts)")
        if army_unit["rules"]:
            st.write(f"   - Règles spéciales : {', '.join(army_unit['rules'])}")
        if army_unit["weapons"]:
            for w in army_unit["weapons"]:
                st.write(f"   - Arme : {w.get('name', 'Arme')} (A{w.get('attacks', '?')}, PA{w.get('armor_piercing', '?')})")

    st.markdown(f"### 💰 **Coût total de l'armée : {st.session_state.army_total_cost} pts**")

# -------------------------------------------------
# CHAMP POUR LE COÛT TOTAL SOUHAITÉ DE L'ARMÉE
# -------------------------------------------------
st.divider()
army_target_cost = st.number_input(
    "Coût total souhaité pour l'armée (en points) :",
    min_value=0,
    value=1000,
    step=50
)

# -------------------------------------------------
# INDICATEUR DE PROGRÈS
# -------------------------------------------------
progress = st.session_state.army_total_cost / army_target_cost
st.progress(progress)
st.write(f"Progression : {st.session_state.army_total_cost}/{army_target_cost} pts")
