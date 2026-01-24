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

# Fonction pour afficher les règles spéciales avec accordéons
def display_faction_rules(faction_data):
    """Affiche les règles spéciales de la faction avec accordéons compacts"""
    if not faction_data or 'special_rules_descriptions' not in faction_data:
        st.warning("Aucune règle spéciale définie pour cette faction.")
        return

    st.markdown("""
    <style>
    .faction-rules-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        border-left: 4px solid #3498db;
    }
    .rule-accordion {
        margin-bottom: 5px;
        border-bottom: 1px solid #eee;
    }
    .rule-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        cursor: pointer;
        font-weight: bold;
        color: #2c3e50;
    }
    .rule-header:hover {
        color: #3498db;
    }
    .rule-content {
        padding: 0 0 10px 0;
        display: none;
        color: #555;
        font-size: 0.9em;
        margin-top: 5px;
    }
    .expand-icon {
        transition: transform 0.2s;
        display: inline-block;
        font-size: 0.8em;
    }
    </style>

    <script>
    function toggleRule(id) {
        const content = document.getElementById('rule-content-' + id);
        const icon = document.getElementById('rule-icon-' + id);

        if (content.style.display === 'block') {
            content.style.display = 'none';
            icon.style.transform = 'rotate(0deg)';
            icon.textContent = '▼';
        } else {
            content.style.display = 'block';
            icon.style.transform = 'rotate(180deg)';
            icon.textContent = '▲';
        }
    }
    </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="faction-rules-container">', unsafe_allow_html=True)
    st.subheader("📜 Règles Spéciales de la Faction")

    rule_id = 0
    for rule_name, description in faction_data['special_rules_descriptions'].items():
        rule_id += 1
        safe_rule_name = str(rule_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        safe_description = str(description).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        st.markdown(f"""
        <div class="rule-accordion">
            <div class="rule-header" onclick="toggleRule({rule_id})">
                <span>{safe_rule_name}</span>
                <span id="rule-icon-{rule_id}" class="expand-icon">▼</span>
            </div>
            <div id="rule-content-{rule_id}" class="rule-content">
                {safe_description}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Fonctions utilitaires (identiques à votre version originale)
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

# Chargement des factions (utilise strictement le JSON fourni)
@st.cache_data
def load_factions():
    factions = {}
    games = set()

    # Chargement des fichiers JSON existants
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

    # Si aucun fichier n'est trouvé, on utilise une structure vide
    if not games:
        st.warning("Aucun fichier de faction trouvé. Veuillez ajouter vos fichiers JSON dans le dossier 'lists/data/factions/'")
        return {}, []

    return factions, sorted(games)

# Initialisation
factions_by_game, games = load_factions()

if "page" not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.army_list = []
    st.session_state.army_cost = 0
    st.session_state.history = []

# PAGE 1 – CONFIGURATION
if st.session_state.page == "setup":
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
                            st.session_state.units = factions_by_game[saved_list["game"]][saved_list["faction"]]["units"]
                            st.session_state.history = []
                            st.session_state.page = "army"
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
        st.session_state.page = "army"
        st.rerun()

# PAGE 2 – CONSTRUCTEUR D'ARMÉE
elif st.session_state.page == "army":
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
            st.session_state.page = "setup"
            st.rerun()

    # AFFICHAGE DES RÈGLES SPÉCIALES EN TÊTE DE LISTE
    if 'special_rules_descriptions' in factions_by_game[st.session_state.game][st.session_state.faction]:
        display_faction_rules(factions_by_game[st.session_state.game][st.session_state.faction])

    # Vérification des règles
    game_config = GAME_CONFIG.get(st.session_state.game, GAME_CONFIG["Age of Fantasy"])
    if not validate_army_rules(st.session_state.army_list, st.session_state.points, st.session_state.game):
        st.warning("⚠️ Certaines règles ne sont pas respectées.")

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

    base_size = unit.get('size', 10)
    base_cost = unit["base_cost"]

    # Vérification du coût maximum
    max_cost = st.session_state.points * game_config["unit_max_cost_ratio"]
    if unit["base_cost"] > max_cost:
        st.error(f"Cette unité ({unit['base_cost']} pts) dépasse la limite de {int(max_cost)} pts")
        st.stop()

    weapon = unit.get("weapons", [{}])[0]
    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0

    # Gestion des unités combinées (désactivé pour les héros)
    if unit.get("type") == "hero":
        combined = False
    else:
        combined = st.checkbox("Unité combinée", value=False)

    # Options de l'unité (utilise strictement les données du JSON)
    for group in unit.get("upgrade_groups", []):
        st.markdown(f"**{group['group']}**")

        if group["type"] == "weapon":
            weapon_options = ["Arme de base"]
            for o in group["options"]:
                weapon_details = format_weapon_details(o["weapon"])
                cost_diff = o["cost"]
                weapon_options.append(f"{o['name']} (A{weapon_details['attacks']}, PA({weapon_details['ap']}){', ' + ', '.join(weapon_details['special']) if weapon_details['special'] else ''}) (+{cost_diff} pts)")

            selected_weapon = st.radio("Arme", weapon_options, key=f"{unit['name']}_weapon")
            if selected_weapon != "Arme de base":
                opt_name = selected_weapon.split(" (")[0]
                opt = next((o for o in group["options"] if o["name"] == opt_name), None)
                if opt:
                    weapon = opt["weapon"]
                    weapon_cost = opt["cost"]

        elif group["type"] == "mount":
            mount_labels = ["Aucune monture"]
            mount_map = {}
            for o in group["options"]:
                mount_details = format_mount_details(o)
                label = f"{mount_details} (+{o['cost']} pts)"
                mount_labels.append(label)
                mount_map[label] = o

            selected_mount = st.radio("Monture", mount_labels, key=f"{unit['name']}_mount")
            if selected_mount != "Aucune monture":
                opt = mount_map[selected_mount]
                mount = opt
                mount_cost = opt["cost"]

        else:  # Améliorations d'unité
            if group.get("type") == "upgrades":
                if len(group["options"]) == 1:  # Un seul choix possible
                    option_names = ["Aucune"] + [f"{o['name']} (+{o['cost']} pts)" for o in group["options"]]
                    selected = st.radio(group["group"], option_names, key=f"{unit['name']}_{group['group']}")
                    if selected != "Aucune":
                        opt_name = selected.split(" (+")[0]
                        opt = next((o for o in group["options"] if o["name"] == opt_name), None)
                        if opt:
                            if group["group"] not in selected_options:
                                selected_options[group["group"]] = []
                            selected_options[group["group"]].append(opt)
                            upgrades_cost += opt["cost"]
                else:  # Plusieurs choix possibles
                    st.write("Sélectionnez les améliorations (plusieurs choix possibles):")
                    for o in group["options"]:
                        if st.checkbox(f"{o['name']} (+{o['cost']} pts)", key=f"{unit['name']}_{group['group']}_{o['name']}"):
                            if group["group"] not in selected_options:
                                selected_options[group["group"]] = []
                            if not any(opt.get("name") == o["name"] for opt in selected_options.get(group["group"], [])):
                                selected_options[group["group"]].append(o)
                                upgrades_cost += o["cost"]

    # Calcul du coût final
    if combined and unit.get("type") != "hero":
        final_cost = (base_cost + weapon_cost) * 2 + mount_cost + upgrades_cost
        unit_size = base_size * 2
    else:
        final_cost = base_cost + weapon_cost + mount_cost + upgrades_cost
        unit_size = base_size

    st.markdown(f"**Taille finale: {unit_size}** {'(x2 combinée)' if combined and unit.get('type') != 'hero' else ''}")
    st.markdown(f"**Coût total: {final_cost} pts**")

    if st.button("Ajouter à l'armée"):
        st.session_state.history.append({
            "army_list": copy.deepcopy(st.session_state.army_list),
            "army_cost": st.session_state.army_cost
        })

        total_coriace = get_coriace_from_rules(unit.get("special_rules", []))
        if mount:
            _, mount_coriace = get_mount_details(mount)
            total_coriace += mount_coriace
        if selected_options:
            for opts in selected_options.values():
                if isinstance(opts, list):
                    for opt in opts:
                        total_coriace += get_coriace_from_rules(opt.get("special_rules", []))
        if 'special_rules' in weapon:
            total_coriace += get_coriace_from_rules(weapon["special_rules"])
        if combined and unit.get('type') != "hero":
            total_coriace += get_coriace_from_rules(unit.get('special_rules', []))

        unit_data = {
            "name": unit["name"],
            "type": unit.get("type", "unit"),
            "cost": final_cost,
            "size": unit_size,
            "quality": unit["quality"],
            "defense": unit["defense"],
            "rules": [format_special_rule(r) for r in unit.get("special_rules", [])],
            "weapon": format_weapon_details(weapon),
            "options": selected_options,
            "mount": mount,
            "coriace": total_coriace if total_coriace > 0 else None
        }

        test_army = copy.deepcopy(st.session_state.army_list)
        test_army.append(unit_data)
        if not validate_army_rules(test_army, st.session_state.points, st.session_state.game, final_cost):
            st.error("Cette unité ne peut pas être ajoutée (règles violées)")
        else:
            st.session_state.army_list.append(unit_data)
            st.session_state.army_cost += final_cost
            st.rerun()

    # Liste de l'armée
    st.divider()
    st.subheader("Liste de l'armée")

    if not st.session_state.army_list:
        st.info("Ajoutez des unités pour commencer")

    for i, u in enumerate(st.session_state.army_list):
        with st.container():
            qua_def = f"Qua {u['quality']}+ / Déf {u['defense']}+"
            if u.get("coriace"):
                qua_def += f" / Coriace {u['coriace']}"

            unit_header = f"### {u['name']} [{u['size']}] ({u['cost']} pts) | {qua_def}"
            if u.get("type") == "hero":
                unit_header += " | 🌟 Héros"
            st.markdown(unit_header)

            if u.get("rules"):
                st.markdown(f"**Règles spéciales:** {', '.join(u['rules'])}")

            if 'weapon' in u:
                w = u['weapon']
                st.markdown(f"**Arme:** {w['name']} (A{w['attacks']}, PA({w['ap']}){', ' + ', '.join(w['special']) if w['special'] else ''})")

            if u.get("options"):
                for group, opts in u["options"].items():
                    st.markdown(f"**{group}:**")
                    for opt in opts:
                        st.markdown(f"• {opt['name']}")

            if u.get("mount"):
                st.markdown(f"**Monture:** {format_mount_details(u['mount'])}")

            if st.button(f"Supprimer {u['name']}", key=f"del_{i}"):
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
        # Export HTML avec règles spéciales en accordéon
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
                }}
                .faction-rules {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                    border-left: 4px solid #3498db;
                }}
                .rule-accordion {{
                    margin-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }}
                .rule-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
                    cursor: pointer;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .rule-header:hover {{
                    color: #3498db;
                }}
                .rule-content {{
                    padding: 0 0 10px 0;
                    display: none;
                    color: #555;
                    font-size: 0.9em;
                    margin-top: 5px;
                }}
                .expand-icon {{
                    transition: transform 0.2s;
                    display: inline-block;
                    font-size: 0.8em;
                }}
                .unit-container {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                    padding: 20px;
                    page-break-inside: avoid;
                }}
                /* [Le reste du CSS...] */
            </style>
        </head>
        <body>
            <h1>Liste d'armée OPR - {army_data['name']}</h1>
            <div>
                <strong>Jeu:</strong> {army_data['game']} |
                <strong>Faction:</strong> {army_data['faction']} |
                <strong>Points:</strong> {army_data['total_cost']}/{army_data['points']}
            </div>
        """

        # Ajout des règles spéciales dans l'export HTML
        if 'special_rules_descriptions' in factions_by_game[army_data['game']][army_data['faction']]:
            html_content += """
            <div class="faction-rules">
                <h2>Règles Spéciales de la Faction</h2>
            """

            rule_id = 0
            for rule_name, description in factions_by_game[army_data['game']][army_data['faction']]['special_rules_descriptions'].items():
                rule_id += 1
                safe_rule_name = str(rule_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                safe_description = str(description).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                html_content += f"""
                <div class="rule-accordion">
                    <div class="rule-header" onclick="toggleRule({rule_id})">
                        <span>{safe_rule_name}</span>
                        <span id="rule-icon-{rule_id}" class="expand-icon">▼</span>
                    </div>
                    <div id="rule-content-{rule_id}" class="rule-content">
                        {safe_description}
                    </div>
                </div>
                """

            html_content += """
                <script>
                function toggleRule(id) {
                    const content = document.getElementById('rule-content-' + id);
                    const icon = document.getElementById('rule-icon-' + id);

                    if (content.style.display === 'block') {
                        content.style.display = 'none';
                        icon.style.transform = 'rotate(0deg)';
                        icon.textContent = '▼';
                    } else {
                        content.style.display = 'block';
                        icon.style.transform = 'rotate(180deg)';
                        icon.textContent = '▲';
                    }
                }
                </script>
            </div>
            """

        # Ajout des unités
        for unit in army_data['army_list']:
            rules = unit.get('rules', [])
            special_rules = ", ".join(rules) if rules else "Aucune"

            weapon_info = unit.get('weapon', {})
            if not isinstance(weapon_info, dict):
                weapon_info = {
                    "name": "Arme non spécifiée",
                    "attacks": "?",
                    "ap": "?",
                    "special": []
                }

            unit_name = f"{unit['name']} [{unit.get('size', 1)}]"
            unit_name = str(unit_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            weapon_name = str(weapon_info['name']).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            weapon_attacks = str(weapon_info['attacks']).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            weapon_ap = str(weapon_info['ap']).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            weapon_special = ', '.join(weapon_info['special']) if weapon_info['special'] else '-'
            weapon_special = str(weapon_special).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            hero_badge = ""
            if unit.get('type') == "hero":
                hero_badge = '<span style="background-color: gold; color: black; padding: 2px 8px; border-radius: 10px; margin-left: 10px; font-weight: bold; font-size: 0.9em;">HÉROS</span>'

            html_content += f"""
            <div class="unit-container">
                <div style="font-size: 1.5em; font-weight: bold; margin-bottom: 10px; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                    {unit_name}
                    {hero_badge}
                    <span style="float: right; background-color: #3498db; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{unit['cost']} pts</span>
                </div>

                <div style="display: flex; margin-bottom: 15px;">
                    <div style="background-color: #3498db; color: white; padding: 8px 12px; border-radius: 4px; margin-right: 10px; font-weight: bold; text-align: center; min-width: 80px;">
                        <div style="font-size: 0.8em; display: block; margin-bottom: 3px;">Qualité</div>
                        <div style="font-size: 1.2em;">{unit['quality']}+</div>
                    </div>
                    <div style="background-color: #3498db; color: white; padding: 8px 12px; border-radius: 4px; margin-right: 10px; font-weight: bold; text-align: center; min-width: 80px;">
                        <div style="font-size: 0.8em; display: block; margin-bottom: 3px;">Défense</div>
                        <div style="font-size: 1.2em;">{unit.get('defense', '?')}+</div>
                    </div>
            """

            if unit.get('coriace'):
                html_content += f"""
                    <div style="background-color: #3498db; color: white; padding: 8px 12px; border-radius: 4px; margin-right: 10px; font-weight: bold; text-align: center; min-width: 80px;">
                        <div style="font-size: 0.8em; display: block; margin-bottom: 3px;">Coriace</div>
                        <div style="font-size: 1.2em;">{unit['coriace']}</div>
                    </div>
                """

            html_content += """
                </div>
            """

            if rules:
                html_content += f'<div style="font-style: italic; color: #555; margin-bottom: 15px;"><strong>Règles spéciales:</strong> {special_rules}</div>'

            html_content += f"""
                <div style="font-weight: bold; margin: 15px 0 10px 0; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;">Arme</div>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th style="background-color: #f8f9fa; text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Nom</th>
                            <th style="background-color: #f8f9fa; text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">PORT</th>
                            <th style="background-color: #f8f9fa; text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">ATK</th>
                            <th style="background-color: #f8f9fa; text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">PA</th>
                            <th style="background-color: #f8f9fa; text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">SPE</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{weapon_name}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">-</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{weapon_attacks}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{weapon_ap}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{weapon_special}</td>
                        </tr>
                    </tbody>
                </table>
            """

            if 'options' in unit and unit['options']:
                for group_name, opts in unit['options'].items():
                    if isinstance(opts, list) and opts:
                        group_name_clean = str(group_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        html_content += f'<div style="font-weight: bold; margin: 15px 0 10px 0; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;">{group_name_clean}:</div>'
                        for opt in opts:
                            opt_name = str(opt.get("name", "")).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_content += f'<div>• {opt_name}</div>'

            if 'mount' in unit and unit['mount']:
                mount_details = format_mount_details(unit["mount"])
                mount_details_clean = str(mount_details).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_content += f'<div style="font-weight: bold; margin: 15px 0 10px 0; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;">Monture</div><p>{mount_details_clean}</p>'

            html_content += "</div>"

        html_content += """
        </body>
        </html>
        """

        st.download_button(
            "Exporter en HTML",
            html_content,
            file_name=f"{st.session_state.list_name}.html",
            mime="text/html"
        )