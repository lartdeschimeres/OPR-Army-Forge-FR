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
if "widget_counter" not in st.session_state:
    st.session_state.widget_counter = 0  # Compteur pour les clés uniques

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
# FONCTIONS UTILITAIRES (inchangées)
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

# ======================================================
# EXPORT HTML (avec règles spéciales en une ligne)
# ======================================================
def export_html(army_list, army_name, army_limit):
    def esc(txt):
        return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    sorted_army_list = sorted(army_list, key=lambda x: 0 if x.get("type") == "hero" else 1)
    html = f"""<!DOCTYPE html>
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
  --text-main: #e6e6e6;
  --border: #555;
}}
body {{
  background: var(--bg-main);
  color: var(--text-main);
  font-family: "Segoe UI", Roboto, Arial, sans-serif;
  margin: 0;
  padding: 20px;
}}
.unit-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  margin-bottom: 20px;
  padding: 16px;
}}
.rules {{
  font-size: 12px;
  margin-top: 10px;
}}
</style>
</head>
<body>
<div class="army">
  <h1 style="text-align: center; color: var(--accent);">{esc(army_name)}</h1>
"""

    for unit in sorted_army_list:
        name = esc(unit.get("name", "Unité"))
        cost = unit.get("cost", 0)
        quality = esc(unit.get("quality", "-"))
        defense = esc(unit.get("defense", "-"))
        coriace = unit.get("coriace")
        unit_size = unit.get("size", 10)
        if unit.get("type", "").lower() == "hero":
            unit_size = 1

        html += f"""
<div class="unit-card">
  <h2>{name} [{unit_size}] - {cost} pts</h2>
  <div class="stats">
    Qualité {quality}+ | Défense {defense}+"""
        if coriace and coriace > 0:
            html += f" | Coriace {coriace}"
        html += "</div>"

        # Armes
        weapons = unit.get("weapon", [])
        if weapons:
            if not isinstance(weapons, list):
                weapons = [weapons]
            html += "<h3>Armes équipées :</h3><ul>"
            for w in weapons:
                html += f"<li>{esc(w.get('name', '-'))} (A{w.get('attacks', '-')}, PA{w.get('ap', '-')})</li>"
            html += "</ul>"

        # Règles spéciales (en une ligne)
        rules = unit.get("rules", [])
        if rules:
            html += f"<div class='rules'><strong>Règles spéciales :</strong> {', '.join(esc(r) for r in rules)}</div>"

        # Options et montures (inchangé)
        options = unit.get("options", {})
        if options:
            html += "<h3>Options :</h3><ul>"
            for group_name, opts in options.items():
                if isinstance(opts, list) and opts:
                    html += f"<li><strong>{esc(group_name)}:</strong> {', '.join(esc(opt.get('name', '')) for opt in opts)}</li>"
            html += "</ul>"

        mount = unit.get("mount")
        if mount:
            html += f"<h3>Monture :</h3><p>{esc(mount.get('name', 'Aucune'))}</p>"
        html += "</div>"
    html += "</div></body></html>"
    return html

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE (avec gestion des boutons radio/checkboxes)
# ======================================================
elif st.session_state.page == "army":
    st.markdown(f"### {st.session_state.list_name}")
    st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_cost}/{st.session_state.points} pts")
    game_config = GAME_CONFIG.get(st.session_state.game, GAME_CONFIG["Age of Fantasy"])
    faction_data = factions_by_game[st.session_state.game][st.session_state.faction]

    # Sélection de l'unité
    unit = st.selectbox("Unité disponible", st.session_state.units, format_func=format_unit_option, key="unit_select")
    weapon = unit.get("weapons", [])
    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0

    # Boucle des groupes d'améliorations (avec clés uniques)
    for group in unit.get("upgrade_groups", []):
        st.session_state.widget_counter += 1
        unique_key = f"{unit['name']}_{st.session_state.widget_counter}"

        if group["type"] == "weapon":
            # Boutons radio pour les armes (choix unique)
            weapon_options = ["Arme de base"]
            for o in group["options"]:
                weapon_details = format_weapon_details(o["weapon"])
                weapon_options.append(f"{o['name']} (+{o['cost']} pts)")
            if f"{unique_key}_weapon" not in st.session_state:
                st.session_state[f"{unique_key}_weapon"] = weapon_options[0]
            selected_weapon = st.radio(
                "Arme",
                weapon_options,
                key=f"{unique_key}_weapon",
                index=weapon_options.index(st.session_state[f"{unique_key}_weapon"])
            )
            st.session_state[f"{unique_key}_weapon"] = selected_weapon
            if selected_weapon != weapon_options[0]:
                opt_name = selected_weapon.split(" (+")[0]
                opt = next((o for o in group["options"] if o["name"] == opt_name), None)
                if opt:
                    weapon = [opt["weapon"]] if unit.get("type") == "hero" else unit.get("weapons", []) + [opt["weapon"]]
                    weapon_cost += opt["cost"]

        elif group["type"] == "mount":
            # Boutons radio pour les montures (choix unique)
            mount_labels = ["Aucune monture"]
            mount_map = {}
            for o in group["options"]:
                mount_labels.append(f"{o['name']} (+{o['cost']} pts)")
                mount_map[o['name']] = o
            if f"{unique_key}_mount" not in st.session_state:
                st.session_state[f"{unique_key}_mount"] = mount_labels[0]
            selected_mount = st.radio(
                "Monture",
                mount_labels,
                key=f"{unique_key}_mount",
                index=mount_labels.index(st.session_state[f"{unique_key}_mount"])
            )
            st.session_state[f"{unique_key}_mount"] = selected_mount
            if selected_mount != mount_labels[0]:
                mount = mount_map[selected_mount.split(" (+")[0]]
                mount_cost += mount["cost"]

        else:
            # Checkboxes pour les améliorations (choix multiples)
            if unit.get("type", "").lower() == "hero":
                option_labels = ["Aucune amélioration"]
                option_map = {}
                for o in group["options"]:
                    option_labels.append(f"{o['name']} (+{o['cost']} pts)")
                    option_map[f"{o['name']} (+{o['cost']} pts)"] = o
                if f"{unique_key}_hero" not in st.session_state:
                    st.session_state[f"{unique_key}_hero"] = option_labels[0]
                selected = st.radio(
                    f"Amélioration – {group['group']}",
                    option_labels,
                    key=f"{unique_key}_hero",
                    index=option_labels.index(st.session_state[f"{unique_key}_hero"])
                )
                st.session_state[f"{unique_key}_hero"] = selected
                if selected != option_labels[0]:
                    opt = option_map[selected]
                    selected_options[group['group']] = [opt]
                    upgrades_cost += opt["cost"]
            else:
                st.write("Améliorations (choix multiples):")
                for o in group["options"]:
                    option_key = f"{unique_key}_{o['name']}"
                    if option_key not in st.session_state:
                        st.session_state[option_key] = False
                    if st.checkbox(
                        f"{o['name']} (+{o['cost']} pts)",
                        value=st.session_state[option_key],
                        key=option_key
                    ):
                        st.session_state[option_key] = True
                        selected_options.setdefault(group["group"], []).append(o)
                        upgrades_cost += o["cost"]
                    else:
                        st.session_state[option_key] = False

    # ... (reste du code inchangé : calcul des coûts, ajout à l'armée, export, etc.)
