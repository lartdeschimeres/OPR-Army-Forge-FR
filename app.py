import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib
import re
import base64
import math

# ======================================================
# CONFIGURATION POUR SIMON
# ======================================================
st.set_page_config(
    page_title="OPR Army Forge FR - Simon Joinville Fouquet",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
        "description": "Jeu de bataille rangée dans un univers fantasy médiéval",
        "hero_limit": 375,  # 1 Héros par tranche de 375 pts
        "unit_copy_rule": 750,  # 1+X copies où X=1 pour 750 pts
        "unit_max_cost_ratio": 0.35,  # 35% du total des points
        "unit_per_points": 150  # 1 unité maximum par tranche de 150 pts
    },
    "Grimdark Future": {
        "display_name": "Grimdark Future",
        "max_points": 10000,
        "min_points": 200,
        "default_points": 800,
        "point_step": 200,
        "description": "Jeu de bataille futuriste avec unités mécanisées",
        "hero_limit": 400,
        "unit_copy_rule": 800,
        "unit_max_cost_ratio": 0.40,
        "unit_per_points": 160
    }
}

# ======================================================
# FONCTIONS POUR LES RÈGLES SPÉCIFIQUES
# ======================================================
def check_hero_limit(army_list, total_points, game_config):
    """Vérifie la limite de héros"""
    if game_config.get("hero_limit"):
        max_heroes = math.floor(total_points / game_config["hero_limit"])
        hero_count = sum(1 for unit in army_list if unit.get("type") == "hero")

        if hero_count > max_heroes:
            st.error(f"Limite de héros dépassée! Maximum autorisé: {max_heroes} (1 héros par {game_config['hero_limit']} pts)")
            return False
    return True

def check_unit_copy_rule(army_list, total_points, game_config):
    """Vérifie la règle des copies d'unités"""
    if game_config.get("unit_copy_rule"):
        x_value = math.floor(total_points / game_config["unit_copy_rule"])
        max_copies = 1 + x_value

        # Compter les copies de chaque unité
        unit_counts = {}
        for unit in army_list:
            unit_name = unit["name"]
            count_key = unit_name  # On ne distingue plus les unités combinées pour le comptage

            if count_key in unit_counts:
                unit_counts[count_key] += 1
            else:
                unit_counts[count_key] = 1

        # Vérifier les limites
        for unit_name, count in unit_counts.items():
            if count > max_copies:
                st.error(f"Trop de copies de l'unité! Maximum autorisé: {max_copies} (1+{x_value} pour {game_config['unit_copy_rule']} pts)")
                return False
    return True

def check_unit_max_cost(army_list, total_points, game_config, new_unit_cost=None):
    """Vérifie qu'aucune unité ne dépasse le ratio maximum de coût"""
    if not game_config.get("unit_max_cost_ratio"):
        return True

    max_cost = total_points * game_config["unit_max_cost_ratio"]

    # Vérifier les unités existantes
    for unit in army_list:
        if unit["cost"] > max_cost:
            st.error(f"L'unité {unit['name']} ({unit['cost']} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
            return False

    # Vérifier la nouvelle unité si fournie
    if new_unit_cost and new_unit_cost > max_cost:
        st.error(f"Cette unité ({new_unit_cost} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
        return False

    return True

def check_unit_per_points(army_list, total_points, game_config):
    """Vérifie le nombre maximum d'unités par tranche de points"""
    if game_config.get("unit_per_points"):
        max_units = math.floor(total_points / game_config["unit_per_points"])

        if len(army_list) > max_units:
            st.error(f"Trop d'unités! Maximum autorisé: {max_units} (1 unité par {game_config['unit_per_points']} pts)")
            return False
    return True

def validate_army_rules(army_list, total_points, game, new_unit_cost=None):
    """Valide toutes les règles spécifiques au jeu"""
    game_config = GAME_CONFIG.get(game, {})

    if game in GAME_CONFIG:
        return (check_hero_limit(army_list, total_points, game_config) and
                check_unit_copy_rule(army_list, total_points, game_config) and
                check_unit_max_cost(army_list, total_points, game_config, new_unit_cost) and
                check_unit_per_points(army_list, total_points, game_config))

    return True

# ======================================================
# FONCTIONS UTILITAIRES (inchangées)
# ======================================================
def format_special_rule(rule):
    """Formate les règles spéciales avec parenthèses"""
    if not isinstance(rule, str):
        return str(rule)
    if "(" in rule and ")" in rule:
        return rule
    match = re.search(r"(\D+)(\d+)", rule)
    if match:
        return f"{match.group(1)}({match.group(2)})"
    return rule

# ... (les autres fonctions utilitaires restent inchangées)

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE (partie corrigée)
# ======================================================
elif st.session_state.page == "army":
    st.title(st.session_state.list_name)
    st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_cost}/{st.session_state.points} pts")

    # Vérification des règles spécifiques au jeu
    game_config = GAME_CONFIG.get(st.session_state.game, GAME_CONFIG["Age of Fantasy"])

    if not validate_army_rules(st.session_state.army_list, st.session_state.points, st.session_state.game):
        st.warning("⚠️ Certaines règles spécifiques ne sont pas respectées. Voir les messages d'erreur ci-dessus.")

    if st.button("⬅ Retour"):
        st.session_state.page = "setup"
        st.rerun()

    # Ajout d'une unité
    st.divider()
    st.subheader("Ajouter une unité")

    # Sélection de l'unité
    unit = st.selectbox(
        "Unité disponible",
        st.session_state.units,
        format_func=format_unit_option,
        index=0,
        key="unit_select"
    )

    # Vérification du coût maximum AVANT les améliorations
    max_cost = st.session_state.points * game_config["unit_max_cost_ratio"]
    if unit["base_cost"] > max_cost:
        st.error(f"Cette unité ({unit['base_cost']} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
        st.stop()

    # Initialisation
    base_cost = unit["base_cost"]
    weapon = unit.get("weapons", [{}])[0]
    selected_options = {}
    mount = None
    combined = False
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0

    # Unité combinée (pas pour les héros)
    if unit.get("type") != "hero":
        combined = st.checkbox("Unité combinée", value=False)

    # Options de l'unité
    for group in unit.get("upgrade_groups", []):
        # ... (le code des options reste inchangé)

    # Calcul du coût final
    cost = base_cost + weapon_cost + mount_cost + upgrades_cost

    # Vérification finale du coût maximum
    if not check_unit_max_cost(st.session_state.army_list, st.session_state.points, game_config, cost):
        st.stop()

    st.markdown(f"**Coût total: {cost} pts**")

    if st.button("Ajouter à l'armée"):
        try:
            weapon_data = format_weapon_details(weapon)

            # Calcul de la coriace
            total_coriace = 0
            if 'special_rules' in unit and isinstance(unit.get('special_rules'), list):
                total_coriace += get_coriace_from_rules(unit['special_rules'])
            if mount:
                _, mount_coriace = get_mount_details(mount)
                total_coriace += mount_coriace
            if selected_options:
                for opts in selected_options.values():
                    if isinstance(opts, list):
                        for opt in opts:
                            if 'special_rules' in opt and isinstance(opt.get('special_rules'), list):
                                total_coriace += get_coriace_from_rules(opt['special_rules'])
            if 'special_rules' in weapon and isinstance(weapon.get('special_rules'), list):
                total_coriace += get_coriace_from_rules(weapon['special_rules'])
            if combined and unit.get('type') != "hero":
                base_coriace = get_coriace_from_rules(unit.get('special_rules', []))
                total_coriace += base_coriace

            total_coriace = total_coriace if total_coriace > 0 else None

            unit_data = {
                "name": unit["name"],
                "type": unit.get("type", "unit"),
                "cost": cost,
                "quality": unit["quality"],
                "defense": unit["defense"],
                "rules": [format_special_rule(r) for r in unit.get("special_rules", [])],
                "weapon": weapon_data,
                "options": selected_options,
                "mount": mount,
                "coriace": total_coriace,
                "combined": combined,
            }

            # Vérification finale complète
            test_army = st.session_state.army_list.copy()
            test_army.append(unit_data)
            test_total = st.session_state.army_cost + cost

            if not validate_army_rules(test_army, test_total, st.session_state.game, cost):
                st.error("Cette unité ne peut pas être ajoutée car elle violerait les règles du jeu.")
            else:
                st.session_state.army_list.append(unit_data)
                st.session_state.army_cost += cost
                st.rerun()

        except Exception as e:
            st.error(f"Erreur lors de la création de l'unité: {str(e)}")
