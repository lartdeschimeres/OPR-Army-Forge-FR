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
    match = re.search(r"Coriace\s*\(?(\d+)\)?", rule)
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
    st.session_state.page = "faction_select"  # Page initiale pour sélectionner la faction
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

# PAGE 2 - Sélection des unités (comme dans votre capture d'écran)
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
        .faction-rules-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        .rule-header {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="faction-rules-container">', unsafe_allow_html=True)
        st.subheader("📜 Règles Spéciales de la Faction")

        for rule_name, description in factions_by_game[st.session_state.game][st.session_state.faction]['special_rules_descriptions'].items():
            st.markdown(f"""
            <div class="rule-header">{rule_name}:</div>
            <p style="margin-bottom: 10px; color: #555; font-size: 0.9em;">{description}</p>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Affichage des unités disponibles (comme dans votre capture d'écran)
    st.subheader("Unités disponibles")

    # Séparation par type (Héros/Unités)
    heroes = [u for u in st.session_state.units if u.get('type') == 'hero']
    units = [u for u in st.session_state.units if u.get('type') != 'hero']

    if heroes:
        st.markdown("### 🌟 HÉROS")
        for unit in heroes:
            with st.container():
                st.markdown(f"""
                <div style="background-color: #2a2a2a; color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #ffd700;">{unit['name']} [{unit.get('size', 1)}]</h4>
                            <p style="margin: 5px 0; color: #aaa;">Qua {unit['quality']}+ / Déf {unit.get('defense', '?')}+</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="margin: 0; color: #4CAF50; font-weight: bold;">{unit['base_cost']} pts</p>
                            <button style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;"
                                    onclick="document.getElementById('select-unit-{unit['name'].replace(' ', '-')}').click()">+</button>
                        </div>
                    </div>
                    <div style="margin-top: 10px; color: #ccc;">
                        <p style="margin: 5px 0;">{', '.join(unit.get('special_rules', []))}</p>
                        <p style="margin: 5px 0; font-style: italic;">
                        {format_weapon_details(unit['weapons'][0])['name']} (A{format_weapon_details(unit['weapons'][0])['attacks']}, PA({format_weapon_details(unit['weapons'][0])['ap']}){', ' + ', '.join(format_weapon_details(unit['weapons'][0])['special']) if format_weapon_details(unit['weapons'][0])['special'] else ''})
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Bouton caché pour sélectionner l'unité
                if st.button(f"Sélectionner {unit['name']}", key=f"select-unit-{unit['name'].replace(' ', '-')}"):
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
                st.markdown(f"""
                <div style="background-color: #1e1e1e; color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #fff;">{unit['name']} [{unit.get('size', 10)}]</h4>
                            <p style="margin: 5px 0; color: #aaa;">Qua {unit['quality']}+ / Déf {unit.get('defense', '?')}+</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="margin: 0; color: #4CAF50; font-weight: bold;">{unit['base_cost']} pts</p>
                            <button style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;"
                                    onclick="document.getElementById('select-unit-{unit['name'].replace(' ', '-')}').click()">+</button>
                        </div>
                    </div>
                    <div style="margin-top: 10px; color: #ccc;">
                        <p style="margin: 5px 0;">{', '.join(unit.get('special_rules', []))}</p>
                        <p style="margin: 5px 0; font-style: italic;">
                        {format_weapon_details(unit['weapons'][0])['name']} (A{format_weapon_details(unit['weapons'][0])['attacks']}, PA({format_weapon_details(unit['weapons'][0])['ap']}){', ' + ', '.join(format_weapon_details(unit['weapons'][0])['special']) if format_weapon_details(unit['weapons'][0])['special'] else ''})
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Bouton caché pour sélectionner l'unité
                if st.button(f"Sélectionner {unit['name']}", key=f"select-unit-{unit['name'].replace(' ', '-')}"):
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
            st.markdown(f"""
            <div style="background-color: #2a2a2a; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: {'#ffd700' if u.get('type') == 'hero' else '#fff'};">
                            {u['name']} [{u.get('size', 1)}] {'🌟' if u.get('type') == 'hero' else ''}
                        </h4>
                        <p style="margin: 5px 0; color: #aaa;">
                            Qua {u['quality']}+ / Déf {u.get('defense', '?')}+{f" / Coriace {u.get('coriace')}" if u.get('coriace') else ""}
                        </p>
                    </div>
                    <div style="text-align: right; color: #4CAF50; font-weight: bold;">
                        {u['cost']} pts
                    </div>
                </div>
                <div style="margin-top: 10px; color: #ccc;">
                    <p style="margin: 5px 0; font-style: italic;">
                        {u['weapon']['name']} (A{u['weapon']['attacks']}, PA({u['weapon']['ap']}){', ' + ', '.join(u['weapon']['special']) if u['weapon']['special'] else ''})
                    </p>
                    {f"<p style='margin: 5px 0;'>Monture: {format_mount_details(u['mount'])}</p>" if u.get('mount') else ""}
                    {f"<p style='margin: 5px 0;'>Options: {', '.join([opt['name'] for group in u.get('options', {}).values() for opt in group])}</p>" if u.get('options') else ""}
                </div>
                <div style="margin-top: 10px;">
                    <button style="background-color: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;"
                            onclick="document.getElementById('delete-unit-{i}').click()">Supprimer</button>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Bouton caché pour supprimer l'unité
            if st.button(f"Supprimer {u['name']}", key=f"delete-unit-{i}"):
                st.session_state.history.append({
                    "army_list": copy.deepcopy(st.session_state.army_list),
                    "army_cost": st.session_state.army_cost
                })
                st.session_state.army_cost -= u["cost"]
                st.session_state.army_list.pop(i)
                st.rerun()

# PAGE 3 - Sélection des options pour une unité
elif st.session_state.page == "unit_options":
    unit = st.session_state.current_unit
    options = st.session_state.current_unit_options

    st.title(f"Personnaliser: {unit['name']}")
    st.caption(f"Type: {'Héros' if unit.get('type') == 'hero' else 'Unité'} • Base: {unit['base_cost']} pts")

    # Bouton retour
    if st.button("⬅ Retour à la liste"):
        st.session_state.page = "army_builder"
        st.rerun()

    # Affichage des caractéristiques de base
    st.markdown(f"""
    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">Caractéristiques de base</h4>
        <p><strong>Taille:</strong> {unit.get('size', 10)} | <strong>Qualité:</strong> {unit['quality']}+ | <strong>Défense:</strong> {unit.get('defense', '?')}+</p>
        <p><strong>Règles spéciales:</strong> {', '.join(unit.get('special_rules', []))}</p>
        <p><strong>Arme de base:</strong> {format_weapon_details(unit['weapons'][0])['name']} (A{format_weapon_details(unit['weapons'][0])['attacks']}, PA({format_weapon_details(unit['weapons'][0])['ap']}){', ' + ', '.join(format_weapon_details(unit['weapons'][0])['special']) if format_weapon_details(unit['weapons'][0])['special'] else ''})</p>
    </div>
    """, unsafe_allow_html=True)

    # Option "Unité combinée" (désactivée pour les héros)
    if unit.get('type') != 'hero':
        options['combined'] = st.checkbox("Unité combinée", value=options['combined'])

    # Sélection des options
    total_cost = unit['base_cost']
    current_size = unit.get('size', 10)

    # Gestion des armes
    if 'weapons' in unit and len(unit['weapons']) > 1:
        st.subheader("Armes")
        weapon_options = []
        for weapon in unit['weapons']:
            weapon_details = format_weapon_details(weapon)
            weapon_options.append(f"{weapon_details['name']} (A{weapon_details['attacks']}, PA({weapon_details['ap']}){', ' + ', '.join(weapon_details['special']) if weapon_details['special'] else ''})")

        selected_weapon = st.selectbox(
            "Sélectionnez une arme",
            weapon_options,
            index=0,
            key="weapon_select"
        )

        # Mise à jour du coût et des détails de l'arme
        selected_index = weapon_options.index(selected_weapon)
        options['weapon'] = unit['weapons'][selected_index]

    # Gestion des montures
    if 'upgrade_groups' in unit:
        for group in unit['upgrade_groups']:
            if group['type'] == 'mount':
                st.subheader(group['group'])
                mount_options = ["Aucune monture"]
                mount_details = {}

                for option in group['options']:
                    mount_options.append(f"{option['name']} (+{option['cost']} pts)")
                    mount_details[option['name']] = option

                selected_mount = st.selectbox(
                    "Sélectionnez une monture",
                    mount_options,
                    index=0,
                    key=f"mount_{group['group']}"
                )

                if selected_mount != "Aucune monture":
                    mount_name = selected_mount.split(" (+")[0]
                    options['mount'] = mount_details[mount_name]
                    total_cost += mount_details[mount_name]['cost']
                else:
                    options['mount'] = None

    # Gestion des améliorations
    if 'upgrade_groups' in unit:
        for group in unit['upgrade_groups']:
            if group['type'] == 'upgrades':
                st.subheader(group['group'])

                if len(group['options']) == 1:  # Sélection unique
                    selected_option = st.selectbox(
                        f"Sélectionnez une {group['group'].lower()}",
                        ["Aucune"] + [f"{opt['name']} (+{opt['cost']} pts)" for opt in group['options']],
                        index=0,
                        key=f"upgrade_{group['group']}"
                    )

                    if selected_option != "Aucune":
                        option_name = selected_option.split(" (+")[0]
                        selected_opt = next(opt for opt in group['options'] if opt['name'] == option_name)
                        if group['group'] not in options['selected_options']:
                            options['selected_options'][group['group']] = []
                        options['selected_options'][group['group']] = [selected_opt]
                        total_cost += selected_opt['cost']
                    else:
                        options['selected_options'][group['group']] = []
                else:  # Sélection multiple
                    for option in group['options']:
                        if st.checkbox(
                            f"{option['name']} (+{option['cost']} pts)",
                            key=f"upgrade_{group['group']}_{option['name']}"
                        ):
                            if group['group'] not in options['selected_options']:
                                options['selected_options'][group['group']] = []
                            if not any(opt['name'] == option['name'] for opt in options['selected_options'].get(group['group'], [])):
                                options['selected_options'][group['group']].append(option)
                                total_cost += option['cost']

    # Calcul du coût final
    if options['combined'] and unit.get('type') != 'hero':
        total_cost = (unit['base_cost'] + (options['mount']['cost'] if options['mount'] else 0) +
                     sum(opt['cost'] for group in options['selected_options'].values() for opt in group)) * 2
        current_size = unit.get('size', 10) * 2
    else:
        total_cost = unit['base_cost'] + (options['mount']['cost'] if options['mount'] else 0) + \
                     sum(opt['cost'] for group in options['selected_options'].values() for opt in group)
        current_size = unit.get('size', 10)

    st.divider()
    st.markdown(f"""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px;">
        <h4 style="margin-top: 0;">Récapitulatif</h4>
        <p><strong>Taille finale:</strong> {current_size} {'(x2 combinée)' if options['combined'] and unit.get('type') != 'hero' else ''}</p>
        <p><strong>Coût total:</strong> {total_cost} pts</p>
    </div>
    """, unsafe_allow_html=True)

    # Bouton pour ajouter à l'armée
    if st.button("Ajouter à l'armée"):
        # Calcul de la coriace totale
        total_coriace = get_coriace_from_rules(unit.get('special_rules', []))
        if options['mount']:
            mount_data = options['mount']['mount'] if 'mount' in options['mount'] else options['mount']
            total_coriace += get_coriace_from_rules(mount_data.get('special_rules', []))
        if options['selected_options']:
            for group_opts in options['selected_options'].values():
                for opt in group_opts:
                    total_coriace += get_coriace_from_rules(opt.get('special_rules', []))
        if 'special_rules' in options['weapon']:
            total_coriace += get_coriace_from_rules(options['weapon'].get('special_rules', []))

        # Création de l'unité finale
        unit_data = {
            "name": unit["name"],
            "type": unit.get("type", "unit"),
            "cost": total_cost,
            "size": current_size,
            "quality": unit["quality"],
            "defense": unit["defense"],
            "rules": [format_special_rule(r) for r in unit.get("special_rules", [])],
            "weapon": format_weapon_details(options['weapon']),
            "options": options['selected_options'],
            "mount": options['mount'],
            "coriace": total_coriace if total_coriace > 0 else None,
            "combined": options['combined'] and unit.get('type') != 'hero'
        }

        # Vérification des règles
        test_army = copy.deepcopy(st.session_state.army_list)
        test_army.append(unit_data)
        game_config = GAME_CONFIG.get(st.session_state.game, GAME_CONFIG["Age of Fantasy"])

        if not validate_army_rules(test_army, st.session_state.points, st.session_state.game, total_cost):
            st.error("Cette unité ne peut pas être ajoutée car elle violerait les règles du jeu.")
        else:
            st.session_state.history.append({
                "army_list": copy.deepcopy(st.session_state.army_list),
                "army_cost": st.session_state.army_cost
            })
            st.session_state.army_list.append(unit_data)
            st.session_state.army_cost += total_cost
            st.session_state.page = "army_builder"
            st.rerun()