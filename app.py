import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import math
import base64

st.set_page_config(
    page_title="OPR ArmyBuilder FR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# FONCTIONS UTILITAIRES
# ======================================================
def calculate_max_count(unit, count_rule):
    """Calcule le nombre maximum d'améliorations possibles"""
    if not count_rule or not isinstance(count_rule, dict):
        return 1

    rule_type = count_rule.get("type", "fixed")
    value = count_rule.get("value", 1)

    if rule_type == "fixed":
        return value
    elif rule_type == "size_based":
        return unit.get("size", 1) * value
    elif rule_type == "quality_based":
        return unit.get("quality", 3) * value
    elif rule_type == "defense_based":
        return unit.get("defense", 3) * value
    elif rule_type == "percentage":
        return math.ceil(unit.get("size", 1) * (value / 100))
    else:
        return value

def format_count_options(option, unit, current_count=0):
    """Formate les options de compteur pour une amélioration"""
    max_count = calculate_max_count(unit, option.get("max_count", {"type": "fixed", "value": 1}))
    min_count = option.get("min_count", 0)
    cost_per_unit = option.get("cost_per_unit", option.get("cost", 0))

    if option.get("weapon") or option.get("special_rules"):
        max_count = min(max_count, unit.get("size", 1))

    choices = []
    for count in range(min_count, max_count + 1):
        total_cost = count * cost_per_unit
        weapon = option.get("weapon", {})
        weapon_label = option.get("name", "Amélioration")

        if weapon:
            weapon_label = format_weapon_option(weapon)

        label = f"{count} × {weapon_label} (+{total_cost} pts)"
        choices.append({
            "label": label,
            "count": count,
            "cost": total_cost,
            "option": option
        })

    return choices, max_count

def check_dependencies(unit_key, requirements):
    """Vérifie les dépendances basées sur les noms d'options sélectionnées"""
    if not requirements or unit_key not in st.session_state.unit_selections:
        return True

    if isinstance(requirements, list):
        for required_option in requirements:
            found = False
            for selection in st.session_state.unit_selections[unit_key].values():
                if isinstance(selection, str) and required_option.lower() in selection.lower():
                    found = True
                    break
            if not found:
                return False
        return True

    return False

def format_weapon_option(weapon, cost=0):
    """Formate l'option d'arme pour la sélection"""
    if not weapon or not isinstance(weapon, dict):
        return "Aucune arme"

    name = weapon.get('name', 'Arme')
    attacks = weapon.get('attacks', '?')
    ap = weapon.get('armor_piercing', '?')
    range_text = weapon.get('range', 'Mêlée')
    special_rules = weapon.get('special_rules', [])

    try:
        attacks = int(attacks) if str(attacks).isdigit() else attacks
        ap = int(ap) if str(ap).isdigit() else ap
    except:
        pass

    profile = f"{name} ({range_text}, A{attacks}"
    if ap not in ("-", 0, "0", None):
        profile += f"/PA{ap}"
    profile += ")"

    if special_rules:
        profile += f" | {', '.join([str(r) for r in special_rules])}"

    if cost > 0:
        profile += f" (+{cost} pts)"

    return profile

# ======================================================
# CSS
# ======================================================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background: transparent;}

.stApp {
    background: #e9ecef;
    color: #212529;
}

section[data-testid="stSidebar"] {
    background: #dee2e6;
    border-right: 1px solid #adb5bd;
    box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}

h1, h2, h3 {
    color: #202c45;
    letter-spacing: 0.04em;
    font-weight: 600;
}

.stSelectbox, .stNumberInput, .stTextInput {
    background-color: white;
    border-radius: 6px;
    border: 1px solid #ced4da;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}

.filter-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 20px 0;
}

.filter-button {
    padding: 8px 15px;
    border-radius: 6px;
    border: 1px solid #ddd;
    background-color: #f8f9fa;
    color: #495057;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
}

.filter-button:hover {
    background-color: #e9ecef;
}

.filter-button.active {
    background-color: #3498db;
    color: white;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# INITIALISATION
# ======================================================
if "page" not in st.session_state:
    st.session_state.page = "setup"
if "army_list" not in st.session_state:
    st.session_state.army_list = []
if "army_cost" not in st.session_state:
    st.session_state.army_cost = 0
if "unit_selections" not in st.session_state:
    st.session_state.unit_selections = {}
if "game" not in st.session_state:
    st.session_state.game = None
if "faction" not in st.session_state:
    st.session_state.faction = None
if "points" not in st.session_state:
    st.session_state.points = 0
if "list_name" not in st.session_state:
    st.session_state.list_name = ""
if "units" not in st.session_state:
    st.session_state.units = []
if "faction_special_rules" not in st.session_state:
    st.session_state.faction_special_rules = []
if "faction_spells" not in st.session_state:
    st.session_state.faction_spells = {}

# ======================================================
# CONFIGURATION DES JEUX OPR
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "min_points": 250, "max_points": 10000, "default_points": 1000,
        "hero_limit": 375, "unit_copy_rule": 750, "unit_max_cost_ratio": 0.35, "unit_per_points": 150
    },
    "Age of Fantasy: Regiments": {
        "min_points": 500, "max_points": 20000, "default_points": 2000,
        "hero_limit": 500, "unit_copy_rule": 1000, "unit_max_cost_ratio": 0.4, "unit_per_points": 200
    },
    "Grimdark Future": {
        "min_points": 250, "max_points": 10000, "default_points": 1000,
        "hero_limit": 375, "unit_copy_rule": 750, "unit_max_cost_ratio": 0.35, "unit_per_points": 150
    }
}

# ======================================================
# PAGE 1 – CONFIGURATION
# ======================================================
if st.session_state.page == "setup":
    st.title("🛡️ OPR ArmyBuilder FR")

    factions_by_game, games = load_factions()
    if not games:
        st.error("Aucun jeu trouvé")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        game = st.selectbox(
            "Jeu",
            games,
            index=games.index(st.session_state.get("game")) if st.session_state.get("game") in games else 0
        )

    with col2:
        faction_options = list(factions_by_game.get(game, {}).keys())
        if not faction_options:
            st.error("Aucune faction disponible")
            st.stop()
        faction = st.selectbox("Faction", faction_options)

    with col3:
        game_cfg = GAME_CONFIG.get(game, {})
        points = st.number_input(
            "Points",
            min_value=game_cfg.get("min_points", 250),
            max_value=game_cfg.get("max_points", 10000),
            value=game_cfg.get("default_points", 1000)
        )

    list_name = st.text_input(
        "Nom de la liste",
        value=st.session_state.get("list_name", f"Liste_{datetime.now().strftime('%Y%m%d')}")
    )

    if st.button("Créer l'armée"):
        st.session_state.game = game
        st.session_state.faction = faction
        st.session_state.points = points
        st.session_state.list_name = list_name

        faction_data = factions_by_game[game][faction]
        st.session_state.units = faction_data.get("units", [])
        st.session_state.faction_special_rules = faction_data.get("faction_special_rules", [])
        st.session_state.faction_spells = faction_data.get("spells", {})

        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.session_state.unit_selections = {}

        st.session_state.page = "army"
        st.rerun()

# ======================================================
# CHARGEMENT DES FACTIONS
# ======================================================
@st.cache_data
def load_factions():
    factions = {}
    games = set()
    try:
        FACTIONS_DIR = Path(__file__).resolve().parent / "frontend" / "public" / "factions"
        if not FACTIONS_DIR.exists():
            FACTIONS_DIR = Path(__file__).resolve().parent / "lists" / "data" / "factions"

        for fp in FACTIONS_DIR.glob("*.json"):
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                    game = data.get("game")
                    faction = data.get("faction")
                    if game and faction:
                        if game not in factions:
                            factions[game] = {}
                        factions[game][faction] = data
                        games.add(game)
            except Exception as e:
                st.warning(f"Erreur chargement {fp.name}: {e}")
    except Exception as e:
        st.error(f"Erreur chargement factions: {e}")
        return {}, []

    return factions, sorted(games) if games else []

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE
# ======================================================
if st.session_state.page == "army":
    # Vérifications initiales
    required_keys = ["game", "faction", "points", "list_name", "units"]
    if not all(key in st.session_state for key in required_keys):
        st.error("Configuration incomplète")
        if st.button("Retour à la configuration"):
            st.session_state.page = "setup"
            st.rerun()
        st.stop()

    st.title(f"{st.session_state.list_name} - {st.session_state.army_cost}/{st.session_state.points} pts")

    # Section Export/Import
    colE1, colE2, colE3 = st.columns(3)
    with colE1:
        if st.button("Export JSON"):
            pass  # Implémentation à compléter
    with colE2:
        if st.button("Export HTML"):
            pass  # Implémentation à compléter
    with colE3:
        uploaded_file = st.file_uploader("Importer une liste")

    # Filtres et sélection d'unité
    filter_categories = {
        "Tous": None,
        "Héros": ["hero"],
        "Unités": ["unit"]
    }

    st.subheader("Filtres")
    for category in filter_categories:
        if st.button(category):
            st.session_state.unit_filter = category
            st.rerun()

    filtered_units = st.session_state.units
    if hasattr(st.session_state, 'unit_filter') and st.session_state.unit_filter != "Tous":
        filtered_units = [u for u in st.session_state.units if u.get('unit_detail') in filter_categories[st.session_state.unit_filter]]

    if not filtered_units:
        st.warning("Aucune unité disponible")
        st.stop()

    unit = st.selectbox("Unité", filtered_units, format_func=lambda u: u.get("name", "Unité"))

    # Configuration de l'unité sélectionnée
    unit_key = f"unit_{unit['name']}"
    if unit_key not in st.session_state.unit_selections:
        st.session_state.unit_selections[unit_key] = {}

    weapons = unit.get("weapon", [])
    if not isinstance(weapons, list):
        weapons = [weapons]

    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0
    weapon_upgrades = []

    # Gestion des groupes d'améliorations
    for g_idx, group in enumerate(unit.get("upgrade_groups", [])):
        g_key = f"group_{g_idx}"
        st.subheader(group.get("group", "Améliorations"))

        # AMÉLIORATIONS PAR FIGURINE (variable_weapon_count)
        if group.get("type") == "variable_weapon_count":
            st.write(group.get("description", ""))

            # Récupérer les armes de base remplaçables
            base_weapons = [w for w in weapons if w.get("name") in group.get("options", [{}])[0].get("replaces", [])]
            replaceable_count = len(base_weapons)

            # Préparer les options
            opt = group.get("options", [{}])[0]
            max_count = min(
                calculate_max_count(unit, opt.get("max_count", {"type": "fixed", "value": 1})),
                replaceable_count
            )

            count = st.slider(
                f"Nombre de {opt.get('name', 'améliorations')} (0-{max_count})",
                min_value=0,
                max_value=max_count,
                value=0,
                key=f"{unit_key}_{g_key}_count"
            )

            if count > 0:
                total_cost = count * opt.get("cost", opt.get("cost_per_unit", 0))
                upgrades_cost += total_cost

                # Stocker la sélection
                st.session_state.unit_selections[unit_key][g_key] = {
                    "count": count,
                    "total_cost": total_cost,
                    "weapon": opt.get("weapon")
                }

                # Remplacer les armes
                for i in range(count):
                    if base_weapons:
                        weapons.remove(base_weapons[0])
                        weapons.append(opt["weapon"])

        # AUTRES TYPES D'AMÉLIORATIONS
        elif group.get("type") == "upgrades":
            for opt in group.get("options", []):
                opt_key = f"{g_key}_{opt['name']}"
                if st.checkbox(f"{opt['name']} (+{opt['cost']} pts)", key=opt_key):
                    upgrades_cost += opt["cost"]
                    if "special_rules" in opt:
                        selected_options[opt["name"]] = opt

        # AUTRES TYPES (montures, etc.)
        else:
            pass  # Implémentation pour autres types

    # Calcul du coût final
    multiplier = 1
    if unit.get("type") != "hero" and st.checkbox("Unité combinée"):
        multiplier = 2

    final_cost = (unit.get("base_cost", 0) + weapon_cost + upgrades_cost) * multiplier

    if st.button(f"Ajouter à l'armée ({final_cost} pts)"):
        unit_data = {
            "name": unit["name"],
            "type": unit.get("type", "unit"),
            "cost": final_cost,
            "size": unit.get("size", 10) * multiplier if unit.get("type") != "hero" else 1,
            "quality": unit.get("quality", 3),
            "defense": unit.get("defense", 3),
            "weapon": weapons,
            "options": selected_options
        }

        st.session_state.army_list.append(unit_data)
        st.session_state.army_cost += final_cost
        st.rerun()

# ======================================================
# EXPORT HTML (simplifié)
# ======================================================
def export_html(army_list, army_name, army_limit):
    html = f"""
    <html>
    <head><title>{army_name}</title></head>
    <body>
    <h1>{army_name} - {sum(u['cost'] for u in army_list)}/{army_limit} pts</h1>
    """

    for unit in army_list:
        html += f"""
        <div>
            <h2>{unit['name']} ({unit['cost']} pts)</h2>
            <p>Qualité: {unit.get('quality', 3)}+, Défense: {unit.get('defense', 3)}+</p>
            <h3>Armes:</h3>
            <ul>
        """

        for weapon in unit.get("weapon", []):
            if isinstance(weapon, dict):
                html += f"""
                <li>{weapon.get('name', 'Arme')} (A{weapon.get('attacks', '?')}/PA{weapon.get('armor_piercing', '?')})</li>
                """

        html += """
            </ul>
        </div>
        """

    html += """
    </body>
    </html>
    """
    return html
