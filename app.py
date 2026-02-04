import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import math

# ======================================================
# INITIALISATION DE BASE
# ======================================================
if "page" not in st.session_state:
    st.session_state.page = "setup"
if "army_list" not in st.session_state:
    st.session_state.army_list = []
if "army_cost" not in st.session_state:
    st.session_state.army_cost = 0
if "unit_selections" not in st.session_state:
    st.session_state.unit_selections = {}

# ======================================================
# CONFIGURATION DES JEUX
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    },
    "Grimdark Future": {
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    }
}

# ======================================================
# FONCTIONS UTILITAIRES
# ======================================================
def format_weapon_details(weapon):
    if not weapon:
        return {"name": "Arme non spécifiée", "attacks": "?", "ap": "?", "special": []}
    return {
        "name": weapon.get('name', 'Arme non nommée'),
        "attacks": weapon.get('attacks', '?'),
        "ap": weapon.get('armor_piercing', '?'),
        "special": weapon.get('special_rules', [])
    }

def format_unit_option(u):
    name_part = f"{u['name']}"
    if u.get('type') == "hero":
        name_part += " [1]"
    else:
        base_size = u.get('size', 10)
        name_part += f" [{base_size}]"
    qua_def = f"Qua {u['quality']}+ / Déf {u.get('defense', '?')}"
    result = f"{name_part} - {qua_def}"
    result += f" {u['base_cost']}pts"
    return result

# ======================================================
# CHARGEMENT DES FACTIONS
# ======================================================
@st.cache_data
def load_factions():
    factions = {}
    games = set()
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
    return factions, sorted(games) if games else list(GAME_CONFIG.keys())

# ======================================================
# PAGE 1 – CONFIGURATION
# ======================================================
if st.session_state.page == "setup":
    st.title("OPR Army Forge - Configuration")

    # Sélection du jeu
    factions_by_game, games = load_factions()
    if not games:
        st.error("Aucun jeu trouvé")
        st.stop()

    game = st.selectbox("Sélectionnez un jeu", games)
    faction = st.selectbox("Sélectionnez une faction", factions_by_game[game].keys())
    points = st.number_input("Points", min_value=250, max_value=10000, value=1000)
    list_name = st.text_input("Nom de la liste", f"Liste_{datetime.now().strftime('%Y%m%d')}")

    if st.button("Construire l'armée"):
        st.session_state.game = game
        st.session_state.faction = faction
        st.session_state.points = points
        st.session_state.list_name = list_name
        st.session_state.units = factions_by_game[game][faction]["units"]
        st.session_state.page = "army"
        st.rerun()

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE (version corrigée)
# ======================================================
elif st.session_state.page == "army":
    st.title(f"{st.session_state.list_name} - {st.session_state.army_cost}/{st.session_state.points} pts")

    if st.button("Retour à la configuration"):
        st.session_state.page = "setup"
        st.rerun()

    # Sélection de l'unité
    unit = st.selectbox(
        "Unité disponible",
        st.session_state.units,
        format_func=format_unit_option,
        key="unit_select"
    )

    # Initialisation des variables
    weapon = unit.get("weapons", [])
    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0

    # Initialisation de la structure de sélection pour cette unité
    unit_key = f"unit_{unit['name']}"
    if unit_key not in st.session_state.unit_selections:
        st.session_state.unit_selections[unit_key] = {}

    # Traitement des améliorations
    for group_idx, group in enumerate(unit.get("upgrade_groups", [])):
        group_key = f"group_{group_idx}"
        st.subheader(group['group'])

        if group["type"] == "weapon":
            # Boutons radio pour les armes (choix unique)
            weapon_options = ["Arme de base"]
            for o in group["options"]:
                weapon_details = format_weapon_details(o["weapon"])
                weapon_options.append(f"{o['name']} (+{o['cost']} pts)")

            # Récupération de la sélection précédente
            current_selection = st.session_state.unit_selections[unit_key].get(group_key, weapon_options[0])

            selected_weapon = st.radio(
                "Sélectionnez une arme",
                weapon_options,
                index=weapon_options.index(current_selection) if current_selection in weapon_options else 0,
                key=f"{unit_key}_{group_key}_weapon"
            )

            # Mise à jour de la sélection
            st.session_state.unit_selections[unit_key][group_key] = selected_weapon

            if selected_weapon != "Arme de base":
                opt_name = selected_weapon.split(" (+")[0]
                opt = next((o for o in group["options"] if o["name"] == opt_name), None)
                if opt:
                    if unit.get("type") == "hero":
                        weapon = [opt["weapon"]]
                    else:
                        weapon = unit.get("weapons", []) + [opt["weapon"]]
                    weapon_cost += opt["cost"]

        elif group["type"] == "mount":
            # Boutons radio pour les montures
            mount_options = ["Aucune monture"]
            mount_map = {}
            for o in group["options"]:
                mount_options.append(f"{o['name']} (+{o['cost']} pts)")
                mount_map[f"{o['name']} (+{o['cost']} pts)"] = o

            current_selection = st.session_state.unit_selections[unit_key].get(group_key, mount_options[0])

            selected_mount = st.radio(
                "Sélectionnez une monture",
                mount_options,
                index=mount_options.index(current_selection) if current_selection in mount_options else 0,
                key=f"{unit_key}_{group_key}_mount"
            )

            st.session_state.unit_selections[unit_key][group_key] = selected_mount

            if selected_mount != "Aucune monture":
                opt = mount_map.get(selected_mount)
                if opt:
                    mount = opt
                    mount_cost = opt["cost"]

        else:
            # Checkboxes pour les améliorations (choix multiples)
            if unit.get("type") == "hero":
                option_labels = ["Aucune amélioration"]
                option_map = {}
                for o in group["options"]:
                    label = f"{o['name']} (+{o['cost']} pts)"
                    option_labels.append(label)
                    option_map[label] = o

                current_selection = st.session_state.unit_selections[unit_key].get(group_key, option_labels[0])

                selected = st.radio(
                    f"Amélioration – {group['group']}",
                    option_labels,
                    index=option_labels.index(current_selection) if current_selection in option_labels else 0,
                    key=f"{unit_key}_{group_key}_hero"
                )

                st.session_state.unit_selections[unit_key][group_key] = selected

                if selected != "Aucune amélioration":
                    opt = option_map.get(selected)
                    if opt:
                        selected_options[group['group']] = [opt]
                        upgrades_cost += opt["cost"]
            else:
                for o in group["options"]:
                    option_key = f"{o['name']}"
                    if option_key not in st.session_state.unit_selections[unit_key]:
                        st.session_state.unit_selections[unit_key][option_key] = False

                    if st.checkbox(
                        f"{o['name']} (+{o['cost']} pts)",
                        value=st.session_state.unit_selections[unit_key][option_key],
                        key=f"{unit_key}_{group_key}_{option_key}"
                    ):
                        st.session_state.unit_selections[unit_key][option_key] = True
                        selected_options.setdefault(group["group"], []).append(o)
                        upgrades_cost += o["cost"]
                    else:
                        st.session_state.unit_selections[unit_key][option_key] = False

    # Doublage des effectifs (uniquement pour les unités non-héros)
    if unit.get("type") != "hero":
        double_size = st.checkbox("Unité combinée (doubler les effectifs)")
        multiplier = 2 if double_size else 1
    else:
        multiplier = 1

    # Calcul du coût final
    base_cost = unit.get("base_cost", 0)
    core_cost = (base_cost + weapon_cost) * multiplier
    final_cost = core_cost + upgrades_cost + mount_cost

    if st.button("Ajouter à l'armée"):
        try:
            unit_data = {
                "name": unit["name"],
                "type": unit.get("type", "unit"),
                "cost": final_cost,
                "base_cost": base_cost,
                "size": unit.get("size", 10) * multiplier,
                "quality": unit.get("quality", 3),
                "defense": unit.get("defense", 3),
                "rules": unit.get("special_rules", []),
                "weapon": weapon,
                "options": selected_options,
                "mount": mount,
                "game": st.session_state.game
            }

            st.session_state.army_list.append(unit_data)
            st.session_state.army_cost += final_cost
            st.rerun()

        except Exception as e:
            st.error(f"Erreur: {str(e)}")

    # Affichage de la liste de l'armée
    st.divider()
    st.subheader("Liste de l'armée")
    if not st.session_state.army_list:
        st.info("Ajoutez des unités pour commencer")

    for i, u in enumerate(st.session_state.army_list):
        with st.expander(f"{u['name']} ({u['cost']} pts)"):
            st.markdown(f"**Qualité/Défense**: {u['quality']}+/{u['defense']}+")
            if 'weapon' in u and u['weapon']:
                st.markdown("**Armes:**")
                for w in u['weapon']:
                    st.markdown(f"- {w.get('name', 'Arme')} (A{w.get('attacks', '?')}, PA{w.get('ap', '?')})")

            if u.get("options"):
                for group_name, opts in u["options"].items():
                    st.markdown(f"**{group_name}:** {', '.join(o.get('name', '') for o in opts)}")

            if st.button(f"Supprimer {u['name']}", key=f"del_{i}"):
                st.session_state.army_cost -= u["cost"]
                st.session_state.army_list.pop(i)
                st.rerun()

    # Export
    st.divider()
    st.subheader("Exporter l'armée")
    army_data = {
        "name": st.session_state.list_name,
        "game": st.session_state.game,
        "faction": st.session_state.faction,
        "army_list": st.session_state.army_list
    }

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Exporter en JSON",
            json.dumps(army_data, indent=2),
            f"{st.session_state.list_name}.json"
        )
    with col2:
        st.download_button(
            "Exporter en HTML",
            json.dumps(army_data, indent=2),
            f"{st.session_state.list_name}.html"
        )
