import json
import re
from pathlib import Path
import streamlit as st

# Configuration de base
st.set_page_config(page_title="OPR Army Builder FR", layout="centered")
st.title("OPR Army Builder 🇫🇷")

# Chargement des données
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

if not FACTIONS_DIR.exists():
    st.error(f"Dossier factions introuvable : {FACTIONS_DIR}")
    st.stop()

faction_files = sorted(FACTIONS_DIR.glob("*.json"))
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

selected_game = st.selectbox("Sélectionner le jeu", sorted(games))
game_factions = {name: info for name, info in faction_map.items() if info["game"] == selected_game}
selected_faction = st.selectbox("Sélectionner la faction", sorted(game_factions.keys()))

FACTION_PATH = game_factions[selected_faction]["file"]
with open(FACTION_PATH, encoding="utf-8") as f:
    faction = json.load(f)

units = faction.get("units", [])
if not units:
    st.warning("Aucune unité disponible pour cette faction.")
    st.stop()

# Sélection de l'unité
selected_unit_name = st.selectbox("Choisir une unité", [u["name"] for u in units])
unit = next(u for u in units if u["name"] == selected_unit_name)

# Configuration de l'unité
total_cost = unit.get("base_cost", 0)
final_rules = list(unit.get("special_rules", []))
current_weapon = unit.get("weapons", [{"name": "Arme non définie", "attacks": "?", "armor_piercing": "?"}])[0]
selected_options = {}
selected_mount = None

# Sélecteurs d'options
for group in unit.get("upgrade_groups", []):
    key = f"{unit['name']}_{group['group']}"
    options = ["— Aucun —"] + [opt["name"] for opt in group["options"]]
    choice = st.selectbox(f"{group['group']}", options, key=key)

    if choice != "— Aucun —":
        opt = next(o for o in group["options"] if o["name"] == choice)
        total_cost += opt.get("cost", 0)
        selected_options[group["group"]] = opt
        if "special_rules" in opt:
            final_rules.extend(opt["special_rules"])
        if "weapon" in opt:
            current_weapon = opt["weapon"]
            current_weapon["name"] = opt["name"]
        if group["group"] == "Monture":
            selected_mount = opt

# Ajout à l'armée
if st.button("Ajouter à l'armée"):
    if "army_list" not in st.session_state:
        st.session_state.army_list = []
    if "army_total_cost" not in st.session_state:
        st.session_state.army_total_cost = 0

    # Calcul de Coriace
    coriace_value = 0
    base_coriace = next((rule for rule in final_rules if "Coriace" in rule), None)
    if base_coriace:
        match = re.search(r'Coriace \((\d+)\)', base_coriace)
        if match:
            coriace_value = int(match.group(1))

    if selected_mount:
        mount_rules = selected_mount.get("special_rules", [])
        for rule in mount_rules:
            if "Coriace" in rule:
                match = re.search(r'Coriace \(\+(\d+)\)', rule)
                if match:
                    coriace_value += int(match.group(1))

    final_coriace = f"Coriace ({coriace_value})" if coriace_value > 0 else None
    base_rules = [rule for rule in final_rules if not rule.startswith("Coriace")]
    if final_coriace:
        base_rules.append(final_coriace)

    st.session_state.army_list.append({
        "name": unit["name"],
        "cost": total_cost,
        "base_rules": base_rules,
        "current_weapon": current_weapon,
        "quality": unit.get("quality", "?"),
        "defense": unit.get("defense", "?"),
        "mount": selected_mount,
        "options": {k: v for k, v in selected_options.items() if k != "Monture"}
    })
    st.session_state.army_total_cost += total_cost
    st.success(f"Unité {unit['name']} ajoutée à l'armée !")

# Affichage de la liste d'armée
st.subheader("Liste de l'armée")
if "army_list" in st.session_state and st.session_state.army_list:
    for i, army_unit in enumerate(st.session_state.army_list, 1):
        with st.expander(f"{army_unit['name']} [{i}] - {army_unit['cost']}pts"):
            st.markdown(f"**Qualité {army_unit['quality']}+** | **Défense {army_unit['defense']}+**")

            st.markdown("**Règles spéciales**")
            for rule in army_unit["base_rules"]:
                st.write(f"- {rule}")

            st.markdown("**Arme équipée**")
            weapon = army_unit["current_weapon"]
            st.write(f"- **{weapon.get('name', 'Arme non définie')}** | A{weapon.get('attacks', '?')} | PA({weapon.get('armor_piercing', '?')})")

            if army_unit.get("mount"):
                st.markdown("**Monture**")
                mount = army_unit["mount"]
                st.write(f"- {mount['name']} (+{mount.get('cost', 0)} pts)")
                st.write(f"  Règles spéciales: {', '.join(mount.get('special_rules', []))}")

            if army_unit.get("options"):
                st.markdown("**Options sélectionnées**")
                for opt in army_unit["options"].values():
                    st.write(f"- {opt['name']}")

st.markdown(f"**Coût total de l'armée : {st.session_state.army_total_cost} pts**")
