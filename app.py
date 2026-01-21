import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib

# Configuration de base
st.set_page_config(
    page_title="OPR Army Forge FR",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chemins des fichiers
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
FACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Fonctions utilitaires de base
def format_special_rule(rule):
    """Formate les règles spéciales"""
    if not isinstance(rule, str):
        return str(rule)
    return rule

def extract_coriace_value(rule):
    """Extrait la valeur de Coriace"""
    if not isinstance(rule, str):
        return 0
    return 0

def get_coriace_from_rules(rules):
    """Calcule la Coriace"""
    if not rules or not isinstance(rules, list):
        return 0
    return 0

def format_weapon_details(weapon):
    """Formate les détails d'une arme"""
    if not weapon:
        return {
            "name": "Arme non spécifiée",
            "attacks": "?",
            "ap": "?",
            "special": []
        }
    return {
        "name": weapon.get('name', 'Arme non nommée'),
        "attacks": weapon.get('attacks', '?'),
        "ap": weapon.get('armor_piercing', '?'),
        "special": weapon.get('special_rules', [])
    }

def format_unit_option(u):
    """Formate l'affichage des unités"""
    name_part = f"{u['name']} [1]"
    qua_def = f"Qua {u['quality']}+ / Déf {u.get('defense', '?')}+"
    result = f"{name_part} - {qua_def} - {u['base_cost']}pts"
    return result

@st.cache_data
def load_factions():
    """Charge les factions"""
    factions = {}
    games = set()

    # Création d'un fichier de faction par défaut si le dossier est vide
    if not list(FACTIONS_DIR.glob("*.json")):
        default_faction = {
            "game": "Age of Fantasy",
            "faction": "Disciples de la Guerre",
            "units": [
                {
                    "name": "Guerrier",
                    "base_cost": 60,
                    "quality": 3,
                    "defense": 3,
                    "type": "infantry",
                    "special_rules": [],
                    "weapons": [{
                        "name": "Épée",
                        "attacks": 1,
                        "armor_piercing": 0,
                        "special_rules": []
                    }]
                }
            ]
        }
        with open(FACTIONS_DIR / "default.json", "w", encoding="utf-8") as f:
            json.dump(default_faction, f, indent=2)

    for fp in FACTIONS_DIR.glob("*.json"):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
                game = data.get("game")
                faction = data.get("faction")
                if game and faction:
                    factions.setdefault(game, {})[faction] = data
                    games.add(game)
        except Exception as e:
            st.warning(f"Erreur chargement {fp.name}: {e}")

    return factions, sorted(games) if games else ["Age of Fantasy"]

# Initialisation
factions_by_game, games = load_factions()

if "page" not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.army_list = []
    st.session_state.army_cost = 0

# Page 1 - Configuration
if st.session_state.page == "setup":
    st.title("OPR Army Forge FR")

    if not games:
        st.error("Aucune faction trouvée")
        st.stop()

    game = st.selectbox("Jeu", games)
    faction = st.selectbox("Faction", factions_by_game[game].keys())
    points = st.number_input("Points", 250, 5000, 1000, 250)
    list_name = st.text_input("Nom de la liste", f"Liste_{datetime.now().strftime('%Y%m%d')}")

    if st.button("Créer une nouvelle liste"):
        st.session_state.game = game
        st.session_state.faction = faction
        st.session_state.points = points
        st.session_state.list_name = list_name
        st.session_state.units = factions_by_game[game][faction]["units"]
        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.session_state.page = "army"
        st.rerun()

# Page 2 - Constructeur d'armée
elif st.session_state.page == "army":
    st.title(st.session_state.list_name)
    st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_cost}/{st.session_state.points} pts")

    if st.button("⬅ Retour"):
        st.session_state.page = "setup"
        st.rerun()

    # Ajout d'une unité
    st.divider()
    st.subheader("Ajouter une unité")

    unit = st.selectbox(
        "Unité disponible",
        st.session_state.units,
        format_func=format_unit_option,
        index=0,
        key="unit_select"
    )

    base_cost = unit["base_cost"]
    weapon = unit.get("weapons", [{}])[0]
    weapon_data = format_weapon_details(weapon)

    st.markdown(f"**Coût total: {base_cost} pts**")

    if st.button("Ajouter à l'armée"):
        unit_data = {
            "name": unit["name"],
            "cost": base_cost,
            "quality": unit["quality"],
            "defense": unit["defense"],
            "rules": unit.get("special_rules", []),
            "weapon": weapon_data,
            "coriace": 0,
            "type": unit.get("type", "")
        }
        st.session_state.army_list.append(unit_data)
        st.session_state.army_cost += base_cost
        st.rerun()

    # Liste de l'armée
    st.divider()
    st.subheader("Liste de l'armée")

    if not st.session_state.army_list:
        st.info("Ajoutez des unités pour commencer")

    for i, u in enumerate(st.session_state.army_list):
        with st.container():
            unit_header = f"### {u['name']} ({u['cost']} pts) | Qua {u['quality']}+ / Déf {u['defense']}+"
            st.markdown(unit_header)

            if u.get("rules"):
                rules_text = ", ".join(u["rules"])
                st.markdown(f"**Règles spéciales:** {rules_text}")

            if 'weapon' in u:
                st.markdown(f"**Arme:** {u['weapon']['name']} (A{u['weapon']['attacks']}, PA({u['weapon']['ap']}){', ' + ', '.join(u['weapon']['special']) if u['weapon']['special'] else ''})")

            if st.button(f"Supprimer {u['name']}", key=f"del_{i}"):
                st.session_state.army_cost -= u["cost"]
                st.session_state.army_list.pop(i)
                st.rerun()

    # Export
    st.divider()
    col1, col2 = st.columns(2)

    army_data = {
        "name": st.session_state.list_name,
        "game": st.session_state.game,
        "faction": st.session_state.faction,
        "points": st.session_state.points,
        "total_cost": st.session_state.army_cost,
        "army_list": st.session_state.army_list,
        "date": datetime.now().isoformat()
    }

    with col1:
        st.download_button(
            "Exporter en JSON",
            json.dumps(army_data, indent=2, ensure_ascii=False),
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json"
        )
