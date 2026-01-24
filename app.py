import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib
import re
import copy
import math

# Configuration initiale
st.set_page_config(
    page_title="OPR Army Forge FR - Simon Joinville Fouquet",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chemins des fichiers
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
FACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration des jeux
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
    }
}

# Fonctions utilitaires (identiques à votre version)
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
    mount_data = mount['mount'] if 'mount' in mount else mount
    details = mount_name
    if 'quality' in mount_data or 'defense' in mount_data:
        details += " ("
        if 'quality' in mount_data:
            details += f"Qua{mount_data['quality']}+"
        if 'defense' in mount_data:
            details += f" Déf{mount_data['defense']}+"
        details += ")"
    if 'special_rules' in mount_data and mount_data['special_rules']:
        details += " | " + ", ".join(mount_data['special_rules'])
    if 'weapons' in mount_data and mount_data['weapons']:
        for weapon in mount_data['weapons']:
            weapon_details = format_weapon_details(weapon)
            details += f" | {weapon.get('name', 'Arme')} (A{weapon_details['attacks']}, PA({weapon_details['ap']})"
            if weapon_details['special']:
                details += ", " + ", ".join(weapon_details['special'])
            details += ")"
    return details

def format_unit_option(u):
    name_part = f"{u['name']}"
    if u.get('type') == "hero":
        name_part += " [1]"
    else:
        name_part += f" [{u.get('size', 10)}]"
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
    rules_part = ", ".join(u['special_rules']) if 'special_rules' in u and u['special_rules'] else ""
    return f"{name_part} - {qua_def} - {weapons_part} - {rules_part} {u['base_cost']}pts"

# Local Storage
def ls_get(key):
    try:
        unique_key = f"{key}_{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}"
        st.markdown(f"""
        <script>
        const value = localStorage.getItem("{key}");
        const input = document.createElement("input");
        input.type = "hidden";
        input.id = "{unique_key}";
        input.value = value || "";
        document.body.appendChild(input);
        </script>
        """, unsafe_allow_html=True)
        return st.text_input("", key=unique_key, label_visibility="collapsed")
    except Exception as e:
        st.error(f"Erreur LocalStorage: {e}")
        return None

def ls_set(key, value):
    try:
        if not isinstance(value, str):
            value = json.dumps(value)
        escaped_value = value.replace("'", "\\'").replace('"', '\\"')
        st.markdown(f"""
        <script>
        localStorage.setItem("{key}", `{escaped_value}`);
        </script>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erreur LocalStorage: {e}")

# Chargement des factions
@st.cache_data
def load_factions():
    factions = {}
    games = set()

    if FACTIONS_DIR.exists():
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

    if not games:
        st.warning("Aucun fichier de faction trouvé. Veuillez ajouter vos fichiers JSON dans le dossier 'lists/data/factions/'")
        return {}, []

    return factions, sorted(games)

# Initialisation
factions_by_game, games = load_factions()

if "page" not in st.session_state:
    st.session_state.page = "faction_select"
    st.session_state.army_list = []
    st.session_state.army_cost = 0
    st.session_state.history = []
    st.session_state.current_unit = None
    st.session_state.current_unit_options = {}

# PAGE 1 - Sélection de la faction et création de liste
if st.session_state.page == "faction_select":
    st.title("OPR Army Forge FR")

    if not games:
        st.error("Aucun jeu trouvé. Veuillez ajouter des fichiers de faction dans le dossier approprié.")
        st.stop()

    game = st.selectbox("Jeu", games)
    game_config = GAME_CONFIG.get(game, GAME_CONFIG["Age of Fantasy"])

    points = st.number_input(
        "Points",
        min_value=game_config["min_points"],
        max_value=game_config["max_points"],
        value=game_config["default_points"],
        step=game_config["point_step"]
    )

    list_name = st.text_input("Nom de la liste", f"Liste_{datetime.now().strftime('%Y%m%d')}")

    # Chargement des listes sauvegardées
    st.subheader("Mes listes sauvegardées")
    saved_lists = ls_get("opr_saved_lists")
    if saved_lists:
        try:
            saved_lists = json.loads(saved_lists)
            if isinstance(saved_lists, list):
                for i, saved_list in enumerate(saved_lists):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{saved_list.get('name', 'Liste sans nom')}**")
                        st.caption(f"{saved_list.get('game', 'Inconnu')} • {saved_list.get('faction', 'Inconnue')} • {saved_list.get('total_cost', 0)}/{saved_list.get('points', 0)} pts")
                    with col2:
                        if st.button(f"Charger", key=f"load_{i}"):
                            st.session_state.game = saved_list["game"]
                            st.session_state.faction = saved_list["faction"]
                            st.session_state.points = saved_list["points"]
                            st.session_state.list_name = saved_list["name"]
                            st.session_state.army_list = saved_list["army_list"]
                            st.session_state.army_cost = saved_list["total_cost"]
                            st.session_state.history = []
                            st.session_state.page = "army_builder"
                            st.rerun()
        except Exception as e:
            st.error(f"Erreur chargement listes: {e}")

    if st.button("Créer une nouvelle liste"):
        if not factions_by_game.get(game, {}):
            st.error("Aucune faction disponible pour ce jeu")
            st.stop()

        st.session_state.game = game
        st.session_state.faction = st.selectbox("Faction", list(factions_by_game[game].keys()))
        st.session_state.points = points
        st.session_state.list_name = list_name
        st.session_state.units = factions_by_game[game][st.session_state.faction]["units"]
        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.session_state.history = []
        st.session_state.page = "army_builder"
        st.rerun()

# PAGE 2 - Sélection des unités (interface inspirée de votre capture)
elif st.session_state.page == "army_builder":
    st.title(st.session_state.list_name)
    st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_cost}/{st.session_state.points} pts")

    # Boutons de contrôle
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        undo_disabled = len(st.session_state.history) == 0
        if st.button("↩ Annuler la dernière action", disabled=undo_disabled):
            if st.session_state.history:
                previous_state = st.session_state.history.pop()
                st.session_state.army_list = copy.deepcopy(previous_state["army_list"])
                st.session_state.army_cost = previous_state["army_cost"]
                st.rerun()

    with col2:
        if st.button("🗑 Réinitialiser la liste"):
            st.session_state.history.append({
                "army_list": copy.deepcopy(st.session_state.army_list),
                "army_cost": st.session_state.army_cost
            })
            st.session_state.army_list = []
            st.session_state.army_cost = 0
            st.rerun()

    with col3:
        if st.button("⬅ Retour"):
            st.session_state.page = "faction_select"
            st.rerun()

    # Affichage des règles spéciales de la faction
    if 'special_rules_descriptions' in factions_by_game[st.session_state.game][st.session_state.faction]:
        st.markdown("""
        <style>
        .faction-rules {
            background-color: #2a2a2a;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .rule-title {
            color: #ffd700;
            font-weight: bold;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="faction-rules">', unsafe_allow_html=True)
        st.markdown('<div class="rule-title">📜 Règles Spéciales de la Faction</div>', unsafe_allow_html=True)

        for rule_name, description in factions_by_game[st.session_state.game][st.session_state.faction]['special_rules_descriptions'].items():
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="font-weight: bold; color: #ccc;">{rule_name}:</div>
                <div style="color: #aaa; font-size: 0.9em; margin-left: 10px;">{description}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Séparation par type (Héros/Unités)
    heroes = [u for u in st.session_state.units if u.get('type') == 'hero']
    units = [u for u in st.session_state.units if u.get('type') != 'hero']

    if heroes:
        st.markdown("### 🌟 HÉROS")
        for unit in heroes:
            with st.container():
                # Utilisation de colonnes pour le bouton
                col1, col2 = st.columns([0.8, 0.2])

                with col1:
                    st.markdown(f"""
                    <div style="background-color: #2a2a2a; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <h4 style="margin: 0; color: #ffd700;">{unit['name']} [{unit.get('size', 1)}]</h4>
                                <p style="margin: 5px 0; color: #aaa;">Qua {unit['quality']}+ / Déf {unit.get('defense', '?')}+</p>
                            </div>
                        </div>
                        <div style="margin-top: 10px; color: #ccc;">
                            <p style="margin: 5px 0; font-style: italic;">
                            {', '.join(unit.get('special_rules', []))}
                            </p>
                            <p style="margin: 5px 0;">
                            {format_weapon_details(unit['weapons'][0])['name']} (A{format_weapon_details(unit['weapons'][0])['attacks']}, PA({format_weapon_details(unit['weapons'][0])['ap']}){', ' + ', '.join(format_weapon_details(unit['weapons'][0])['special']) if format_weapon_details(unit['weapons'][0])['special'] else ''})
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)  # Espacement
                    if st.button(f"Ajouter", key=f"add-{unit['name']}"):
                        st.session_state.current_unit = unit
                        st.session_state.current_unit_options = {
                            'combined': False,
                            'weapon': unit['weapons'][0],
                            'mount': None,
                            'selected_options': {}
                        }
                        st.session_state.page = "unit_options"
                        st.rerun()

    if units:
        st.markdown("### 🏳️ UNITÉS")
        for unit in units:
            with st.container():
                # Utilisation de colonnes pour le bouton
                col1, col2 = st.columns([0.8, 0.2])

                with col1:
                    st.markdown(f"""
                    <div style="background-color: #1e1e1e; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <h4 style="margin: 0; color: #fff;">{unit['name']} [{unit.get('size', 10)}]</h4>
                                <p style="margin: 5px 0; color: #aaa;">Qua {unit['quality']}+ / Déf {unit.get('defense', '?')}+</p>
                            </div>
                        </div>
                        <div style="margin-top: 10px; color: #ccc;">
                            <p style="margin: 5px 0; font-style: italic;">
                            {', '.join(unit.get('special_rules', []))}
                            </p>
                            <p style="margin: 5px 0;">
                            {format_weapon_details(unit['weapons'][0])['name']} (A{format_weapon_details(unit['weapons'][0])['attacks']}, PA({format_weapon_details(unit['weapons'][0])['ap']}){', ' + ', '.join(format_weapon_details(unit['weapons'][0])['special']) if format_weapon_details(unit['weapons'][0])['special'] else ''})
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)  # Espacement
                    if st.button(f"Ajouter", key=f"add-{unit['name']}"):
                        st.session_state.current_unit = unit
                        st.session_state.current_unit_options = {
                            'combined': False,
                            'weapon': unit['weapons'][0],
                            'mount': None,
                            'selected_options': {}
                        }
                        st.session_state.page = "unit_options"
                        st.rerun()

    # Affichage de la liste d'armée actuelle
    st.divider()
    st.subheader(f"Liste d'armée actuelle ({st.session_state.army_cost}/{st.session_state.points} pts)")

    if not st.session_state.army_list:
        st.info("Ajoutez des unités pour commencer à construire votre armée")

    for i, u in enumerate(st.session_state.army_list):
        with st.container():
            col1, col2 = st.columns([0.8, 0.2])

            with col1:
                st.markdown(f"""
                <div style="background-color: {'#2a2a2a' if u.get('type') == 'hero' else '#1e1e1e'}; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h4 style="margin: 0; color: {'#ffd700' if u.get('type') == 'hero' else '#fff'};">
                                {u['name']} [{u.get('size', 1)}] {'🌟' if u.get('type') == 'hero' else ''}
                            </h4>
                            <p style="margin: 5px 0; color: #aaa;">
                                Qua {u['quality']}+ / Déf {u.get('defense', '?')}+{f" / Coriace {u.get('coriace')}" if u.get('coriace') else ""}
                            </p>
                        </div>
                    </div>
                    <div style="margin-top: 10px; color: #ccc;">
                        <p style="margin: 5px 0; font-style: italic;">
                            {u['weapon']['name']} (A{u['weapon']['attacks']}, PA({u['weapon']['ap']}){', ' + ', '.join(u['weapon']['special']) if u['weapon']['special'] else ''})
                        </p>
                        {f"<p style='margin: 5px 0;'>Monture: {format_mount_details(u['mount'])}</p>" if u.get('mount') else ""}
                        {f"<p style='margin: 5px 0;'>Options: {', '.join([opt['name'] for group in u.get('options', {}).values() for opt in group])}</p>" if u.get('options') else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)  # Espacement
                if st.button(f"Supprimer", key=f"del-{i}"):
                    st.session_state.history.append({
                        "army_list": copy.deepcopy(st.session_state.army_list),
                        "army_cost": st.session_state.army_cost
                    })
                    st.session_state.army_cost -= u["cost"]
                    st.session_state.army_list.pop(i)
                    st.rerun()

    # Export
    st.divider()
    col1, col2, col3 = st.columns(3)

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
        if st.button("Sauvegarder"):
            saved_lists = ls_get("opr_saved_lists")
            current_lists = json.loads(saved_lists) if saved_lists else []
            current_lists.append(army_data)
            ls_set("opr_saved_lists", current_lists)
            st.success("Liste sauvegardée!")

    with col2:
        st.download_button(
            "Exporter en JSON",
            json.dumps(army_data, indent=2, ensure_ascii=False),
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json"
        )

    with col3:
        # Export HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Liste OPR - {army_data['name']}</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 20px;
                    color: #333;
                    background-color: #f5f5f5;
                }}
                .army-title {{
                    text-align: center;
                    margin-bottom: 20px;
                    color: #2c3e50;
                }}
                .army-info {{
                    text-align: center;
                    margin-bottom: 30px;
                    color: #666;
                }}
                .faction-rules {{
                    background-color: #2a2a2a;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .rule-title {{
                    color: #ffd700;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .unit-container {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    padding: 20px;
                    page-break-inside: avoid;
                }}
                .hero-container {{
                    background-color: #2a2a2a;
                    color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    padding: 20px;
                    page-break-inside: avoid;
                }}
                .unit-header {{
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #2c3e50;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                .hero-header {{
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #ffd700;
                    border-bottom: 1px solid #444;
                    padding-bottom: 10px;
                }}
                .hero-badge {{
                    background-color: gold;
                    color: black;
                    padding: 2px 8px;
                    border-radius: 10px;
                    margin-left: 10px;
                    font-weight: bold;
              