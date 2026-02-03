import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib
import re
import base64
import math

# ======================================================
# SESSION STATE – valeurs par défaut
# ======================================================
if "page" not in st.session_state:
    st.session_state.page = "setup"

if "army_list" not in st.session_state:
    st.session_state.army_list = []

if "army_cost" not in st.session_state:
    st.session_state.army_cost = 0

# ======================================================
# SIDEBAR – CONTEXTE & NAVIGATION
# ======================================================
with st.sidebar:
    st.title("🛡️ Army Forge")

    st.subheader("📋 Armée")

    game = st.session_state.get("game", "—")
    faction = st.session_state.get("faction", "—")
    points = st.session_state.get("points", 0)
    army_cost = st.session_state.get("army_cost", 0)

    st.markdown(f"**Jeu :** {game}")
    st.markdown(f"**Faction :** {faction}")
    st.markdown(f"**Format :** {points} pts")

    if points > 0:
        st.progress(min(army_cost / points, 1.0))
        st.markdown(f"**Coût :** {army_cost} / {points} pts")

        if army_cost > points:
            st.error("⚠️ Dépassement de points")

    st.divider()

    st.subheader("🧭 Navigation")

    if st.button("⚙️ Configuration", use_container_width=True):
        st.session_state.page = "setup"
        st.rerun()

    if st.button("🧩 Construction", use_container_width=True):
        st.session_state.page = "army"
        st.rerun()

# ======================================================
# CONFIGURATION
# ======================================================
GAME_COVERS = {
    "Age of Fantasy": "assets/games/aof_cover.jpg",
    "Age of Fantasy Quest": "assets/games/aofq_cover.jpg",
    "Age of Fantasy Regiments": "assets/games/aofr_cover.jpg",
    "Grimdark Future": "assets/games/gf_cover.jpg",
    "Grimdark Future Firefight": "assets/games/gff_cover.jpg",
    "Grimdark Future Squad": "assets/games/gfsq_cover.jpg",
}

from pathlib import Path

BASE_DIR = Path(__file__).parent

GAME_CARDS = {
    "Grimdark Future": {
        "image": BASE_DIR / "assets/games/gf_cover.jpg",
        "description": "Escarmouches sci-fi à grande échelle"
    },
    "GF Firefight": {
        "image": BASE_DIR / "assets/games/gff_cover.jpg",
        "description": "Combat tactique en petites escouades"
    },
    "Age of Fantasy": {
        "image": BASE_DIR / "assets/games/aof_cover.jpg",
        "description": "Batailles fantasy"
    },
    "Age of Fantasy Skirmish": {
        "image": BASE_DIR / "assets/games/aofs_cover.jpg",
        "description": "Fantasy en escarmouche"
    },
}

st.set_page_config(
    page_title="OPR Army Forge FR",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================================================
# HEADER – Identité & Contexte (UX ArmyForge ++)
# ======================================================
with st.container():
    st.markdown("""
    <style>
        .af-header {
            background: linear-gradient(90deg, #1e1e1e, #2b2b2b);
            padding: 16px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: #f0f0f0;
        }
        .af-title {
            font-size: 22px;
            font-weight: 700;
        }
        .af-sub {
            font-size: 14px;
            opacity: 0.9;
        }
        .af-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .af-actions button {
            margin-right: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    game = st.session_state.get("game", "—")
    faction = st.session_state.get("faction", "—")
    list_name = st.session_state.get("list_name", "Liste sans nom")
    total = st.session_state.get("army_cost", 0)
    limit = st.session_state.get("points", 0)

    st.markdown(f"""
    <div class="af-header">
        <div class="af-row">
            <div>
                <div class="af-title">🛡 OPR Army Forge</div>
                <div class="af-sub">🎲 {game} &nbsp;&nbsp;|&nbsp;&nbsp; 🏴‍☠️ {faction}</div>
            </div>
            <div class="af-sub">
                📋 <b>{list_name}</b><br>
                📊 <b>{total}</b> / {limit} pts
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# CSS personnalisé pour les expanders et l'interface
st.markdown("""
<style>
    .stExpander > details > summary {
        background-color: #e9ecef;
        padding: 8px 12px;
        border-radius: 4px;
        font-weight: bold;
        color: #2c3e50;
    }
    .stExpander > details > div {
        padding: 10px 12px;
        background-color: #f8f9fa;
        border-radius: 0 0 4px 4px;
    }
    .army-header {
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #444;
    }
    .army-title {
        font-size: 22px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .army-meta {
        font-size: 12px;
        color: #bbb;
    }
    .unit-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
    .hero-badge {
        color: gold;
        font-weight: bold;
    }
    .rule-badge {
        background-color: #e9ecef;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 5px;
        font-size: 12px;
    }
    .weapon-info {
        font-style: normal;
        color: #333;
    }
    .mount-info {
        font-style: normal;
        color: #333;
    }
    .role-improvement {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Chemins des fichiers
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
FACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# ======================================================
# CONFIGURATION DES JEUX ET LEURS LIMITATIONS
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "display_name": "Age of Fantasy",
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "point_step": 250,
        "description": "Jeu de bataille dans un univers fantasy médiéval",
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    },
    "Grimdark Future": {
        "display_name": "Grimdark Future",
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "point_step": 250,
        "description": "Jeu de bataille futuriste",
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    }
}

# ======================================================
# FONCTIONS POUR LES RÈGLES SPÉCIFIQUES
# ======================================================
def check_hero_limit(army_list, army_points, game_config):
    if game_config.get("hero_limit"):
        max_heroes = math.floor(army_points / game_config["hero_limit"])
        hero_count = sum(1 for unit in army_list if unit.get("type", "").lower() == "hero")
        if hero_count > max_heroes:
            st.error(f"Limite de héros dépassée! Maximum autorisé: {max_heroes} (1 héros par {game_config['hero_limit']} pts)")
            return False
    return True

def check_unit_copy_rule(army_list, army_points, game_config):
    if not game_config.get("unit_copy_rule"):
        return True

    x_value = math.floor(army_points / game_config["unit_copy_rule"])
    max_copies = 1 + x_value

    unit_counts = {}

    for unit in army_list:
        name = unit["name"]
        unit_counts[name] = unit_counts.get(name, 0) + 1

    for unit_name, count in unit_counts.items():
        if count > max_copies:
            st.error(
                f"Trop de copies de l'unité {unit_name}! "
                f"Maximum autorisé: {max_copies} "
                f"(1+{x_value} pour {game_config['unit_copy_rule']} pts)"
            )
            return False

    return True

def check_unit_max_cost(army_list, army_points, game_config, new_unit_cost=None):
    if not game_config.get("unit_max_cost_ratio"):
        return True
    max_cost = army_points * game_config["unit_max_cost_ratio"]
    for unit in army_list:
        if unit["cost"] > max_cost:
            st.error(f"L'unité {unit['name']} ({unit['cost']} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
            return False
    if new_unit_cost and new_unit_cost > max_cost:
        st.error(f"Cette unité ({new_unit_cost} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
        return False
    return True

def check_unit_per_points(army_list, army_points, game_config):
    if game_config.get("unit_per_points"):
        max_units = math.floor(army_points / game_config["unit_per_points"])
        if len(army_list) > max_units:
            st.error(f"Trop d'unités! Maximum autorisé: {max_units} (1 unité par {game_config['unit_per_points']} pts)")
            return False
    return True

def validate_army_rules(army_list, army_points, game, new_unit_cost=None):
    game_config = GAME_CONFIG.get(game, {})
    if game in GAME_CONFIG:
        return (check_hero_limit(army_list, army_points, game_config) and
                check_unit_copy_rule(army_list, army_points, game_config) and
                check_unit_max_cost(army_list, army_points, game_config, new_unit_cost) and
                check_unit_per_points(army_list, army_points, game_config))
    return True

# ======================================================
# FONCTIONS UTILITAIRES
# ======================================================
def format_special_rule(rule):
    if not isinstance(rule, str):
        return str(rule)
    if "(" in rule and ")" in rule:
        return rule
    match = re.search(r"(\D+)(\d+)", rule)
    if match:
        return f"{match.group(1)}({match.group(2)})"
    return rule

def extract_coriace_value(rule):
    if not isinstance(rule, str):
        return 0
    match = re.search(r"Coriace\s*$?(\d+)$?", rule)
    if match:
        return int(match.group(1))
    return 0

def get_coriace_from_rules(rules):
    if not rules or not isinstance(rules, list):
        return 0
    total = 0
    for rule in rules:
        total += extract_coriace_value(rule)
    return total

def get_mount_details(mount):
    if not mount:
        return None, 0
    mount_data = mount
    if 'mount' in mount:
        mount_data = mount['mount']
    special_rules = []
    if 'special_rules' in mount_data and isinstance(mount_data['special_rules'], list):
        special_rules = mount_data['special_rules']
    coriace = get_coriace_from_rules(special_rules)
    return special_rules, coriace

def format_weapon_details(weapon):
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

def format_mount_details(mount):
    if not mount:
        return "Aucune monture"
    mount_name = mount.get('name', 'Monture non nommée')
    mount_data = mount
    if 'mount' in mount:
        mount_data = mount['mount']
    details = mount_name
    if 'quality' in mount_data or 'defense' in mount_data:
        details += " ("
        if 'quality' in mount_data:
            details += f"Qua{mount_data['quality']}+"
        if 'defense' in mount_data:
            details += f" Défense {mount_data['defense']}+"
        details += ")"
    if 'special_rules' in mount_data and mount_data['special_rules']:
        details += " | " + ", ".join(mount_data['special_rules'])
    if 'weapons' in mount_data and mount_data['weapons']:
        for weapon in mount_data['weapons']:
            weapon_details = format_weapon_details(weapon)
            details += " | " + f"{weapon.get('name', 'Arme')} (A{weapon_details['attacks']}, PA({weapon_details['ap']})"
            if weapon_details['special']:
                details += ", " + ", ".join(weapon_details['special'])
            details += ")"
    return details

def format_unit_option(u):
    name_part = f"{u['name']}"
    if u.get('type') == "hero":
        name_part += " [1]"  # Les héros ont toujours un effectif de 1
    else:
        base_size = u.get('size', 10)
        name_part += f" [{base_size}]"  # Les unités ont leur effectif de base
    qua_def = f"Qua {u['quality']}+ / Déf {u.get('defense', '?')}"
    coriace = get_coriace_from_rules(u.get('special_rules', []))
    if 'mount' in u and u['mount']:
        _, mount_coriace = get_mount_details(u['mount'])
        coriace += mount_coriace
    if coriace > 0:
        qua_def += f" / Coriace {coriace}"
    weapons_part = ""
    if 'weapons' in u and u['weapons']:
        weapons = []
        for weapon in u['weapons']:
            weapon_details = format_weapon_details(weapon)
            weapons.append(f"{weapon.get('name', 'Arme')} (A{weapon_details['attacks']}, PA({weapon_details['ap']}){', ' + ', '.join(weapon_details['special']) if weapon_details['special'] else ''})")
        weapons_part = " | ".join(weapons)
    rules_part = ""
    if 'special_rules' in u and u['special_rules']:
        rules_part = ", ".join(u['special_rules'])
    result = f"{name_part} - {qua_def}"
    if weapons_part:
        result += f" - {weapons_part}"
    if rules_part:
        result += f" - {rules_part}"
    result += f" {u['base_cost']}pts"
    return result

def find_option_by_name(options, name):
    try:
        return next((o for o in options if o.get("name") == name), None)
    except Exception:
        return None

def display_faction_rules(faction_data):
    if not faction_data or 'special_rules_descriptions' not in faction_data:
        return
    st.subheader("📜 Règles Spéciales de la Faction")
    rules_descriptions = faction_data['special_rules_descriptions']
    if not rules_descriptions:
        st.info("Cette faction n'a pas de règles spéciales spécifiques.")
        return
    for rule_name, description in rules_descriptions.items():
        with st.expander(f"**{rule_name}**", expanded=False):
            st.markdown(f"{description}")

# ======================================================
# EXPORT HTML
# ======================================================
def export_html(army_list, army_name, army_limit):
    def esc(txt):
        return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Trier la liste pour afficher les héros en premier
    sorted_army_list = sorted(army_list, key=lambda x: 0 if x.get("type") == "hero" else 1)

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Liste d'Armée OPR - {esc(army_name)}</title>
<style>
:root {{
  --bg-main: #2e2f2b;
  --bg-card: #3a3c36;
  --bg-header: #1f201d;
  --accent: #9fb39a;
  --accent-soft: #6e7f6a;
  --text-main: #e6e6e6;
  --text-muted: #b0b0b0;
  --border: #555;
}}
body {{
  background: var(--bg-main);
  color: var(--text-main);
  font-family: "Segoe UI", Roboto, Arial, sans-serif;
  margin: 0;
  padding: 20px;
}}

.army {{
  max-width: 1100px;
  margin: auto;
}}

.army-title {{
  text-align: center;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}}

.unit-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  margin-bottom: 40px;
  padding: 16px;
  page-break-inside: avoid;
}}

.unit-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-header);
  padding: 10px 14px;
  margin: -16px -16px 12px -16px;
}}

.unit-header h2 {{
  margin: 0;
  font-size: 18px;
  color: var(--accent);
}}

.cost {{
  font-weight: bold;
}}

.stats {{
  margin-bottom: 10px;
