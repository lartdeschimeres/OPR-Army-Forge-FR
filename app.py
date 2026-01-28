import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib
import re
import base64
import math

# ======================================================
# CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="OPR Army Forge FR",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé
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
    .weapon-specs {
        font-style: italic;
        color: #666;
    }
    .mount-specs {
        font-style: italic;
        color: #666;
    }
    .unit-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# Chemins des fichiers
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
FACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# ======================================================
# CONFIGURATION DES JEUX
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "display_name": "Age of Fantasy",
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "point_step": 250,
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    }
}

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
    mount_data = mount
    if 'mount' in mount:
        mount_data = mount['mount']
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
            details += f" | {weapon.get('name', 'Arme')} (A{weapon_details['attacks']}, PA{weapon_details['ap']}"
            if weapon_details['special']:
                details += ", " + ", ".join(weapon_details['special'])
            details += ")"
    return details

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
            weapons.append(f"{weapon.get('name', 'Arme')} (A{weapon_details['attacks']}, PA{weapon_details['ap']}{', ' + ', '.join(weapon_details['special']) if weapon_details['special'] else ''})")
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
# EXPORT HTML
# ======================================================
def export_html(army_list, army_name, army_limit):
    def esc(txt):
        return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

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
  margin-bottom: 20px;
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
}}
.stats span {{
  display: inline-block;
  background: var(--accent-soft);
  color: #000;
  padding: 4px 8px;
  margin-right: 6px;
  font-size: 12px;
  font-weight: bold;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-size: 12px;
  border: 1px solid var(--border);
}}
th, td {{
  border: 1px solid var(--border);
  padding: 6px;
  text-align: left;
}}
th {{
  background: var(--bg-header);
  color: var(--text-main);
}}
.rules {{
  margin-top: 10px;
  font-size: 12px;
}}
.rules span {{
  display: inline-block;
  margin-right: 8px;
  color: var(--accent);
}}
.section-title {{
  font-weight: bold;
  margin-top: 10px;
  margin-bottom: 5px;
  color: var(--text-main);
}}
.special-rules-title {{
  font-size: 18px;
  font-weight: bold;
  margin-top: 40px;
  margin-bottom: 15px;
  color: var(--accent);
  text-align: center;
  border-top: 1px solid var(--border);
  padding-top: 10px;
}}
.special-rules-container {{
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  margin-bottom: 20px;
}}
.special-rules-column {{
  flex: 1;
  padding: 0 10px;
}}
.special-rules-column div {{
  margin-bottom: 8px;
}}
.weapon-specs {{
  font-style: italic;
  color: var(--text-muted);
}}
</style>
</head>
<body>
<div class="army">
  <div class="army-title">
    {esc(army_name)} - {sum(unit['cost'] for unit in army_list)}/{army_limit} pts - {st.session_state.game}
  </div>
"""

    for unit in army_list:
        name = esc(unit.get("name", "Unité"))
        cost = unit.get("cost", 0)
        quality = esc(unit.get("quality", "-"))
        defense = esc(unit.get("defense", "-"))
        coriace = unit.get("coriace")

        unit_size = unit.get("size", 10)
        if unit.get("type") == "hero":
            unit_size = 1

        html += f"""
<section class="unit-card">
  <div class="unit-header">
    <h2>{name} [{unit_size}]</h2>
    <span class="cost">{cost} pts</span>
  </div>

  <div class="stats">
    <span>Qualité {quality}+</span>
    <span>Défense {defense}+</span>
"""

        if coriace and coriace > 0:
            html += f"<span>Coriace {coriace}</span>"

        html += "</div>"

        # ---- ARMES ----
        weapons = unit.get("weapon")
        if weapons:
            if not isinstance(weapons, list):
                weapons = [weapons]

            html += '<div class="section-title">Armes équipées :</div>'
            html += """
<table>
<thead>
<tr>
  <th>Arme</th>
  <th>Att</th>
  <th>PA</th>
  <th>Règles spéciales</th>
</tr>
</thead>
<tbody>
"""
            for w in weapons:
                html += f"""
<tr>
  <td>{esc(w.get('name', '-'))}</td>
  <td>{esc(w.get('attacks', '-'))}</td>
  <td>{esc(w.get('ap', '-'))}</td>
  <td>{esc(", ".join(w.get('special', [])) if w.get('special') else '-')}</td>
</tr>
"""
            html += "</tbody></table>"

        # ---- RÈGLES SPÉCIALES ----
        rules = unit.get("rules", [])
        if rules:
            html += '<div class="section-title">Règles spéciales :</div>'
            html += "<div class='rules'>"
            for r in rules:
                html += f"<span>{esc(r)}</span>"
            html += "</div>"

        # ---- OPTIONS ----
        options = unit.get("options", {})
        if options:
            html += '<div class="section-title">Options :</div>'
            for group_name, opts in options.items():
                if isinstance(opts, list) and opts:
                    html += f"<div><strong>{esc(group_name)} :</strong> "
                    for opt in opts:
                        html += f"{esc(opt.get('name', ''))}, "
                    html += "</div>"

        # ---- MONTURE (pour les héros) ----
        mount = unit.get("mount")
        if mount:
            mount_name = esc(mount.get("name", "Monture non nommée"))
            mount_data = mount
            if 'mount' in mount:
                mount_data = mount['mount']

            html += '<div class="section-title">Monture :</div>'
            html += f"<div><strong>{mount_name}</strong>"

            if 'quality' in mount_data or 'defense' in mount_data:
                html += " ("
                if 'quality' in mount_data:
                    html += f"Qualité {mount_data['quality']}+"
                if 'defense' in mount_data:
                    html += f" Défense {mount_data['defense']}+"
                html += ")"

            if 'special_rules' in mount_data and mount_data['special_rules']:
                html += " | " + ", ".join(mount_data['special_rules'])

            if 'weapons' in mount_data and mount_data['weapons']:
                for weapon in mount_data['weapons']:
                    weapon_details = format_weapon_details(weapon)
                    html += f" | {weapon.get('name', 'Arme')} (A{weapon_details['attacks']}, PA{weapon_details['ap']}"
                    if weapon_details['special']:
                        html += ", " + ", ".join(weapon_details['special'])
                    html += ")"

            html += "</div>"

        html += "</section>"

    html += """
</div>
</body>
</html>
"""
    return html

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE (modifiée)
# ======================================================
elif st.session_state.page == "army":
    st.markdown(
        f"""
        <div class="army-header">
            <div class="army-title">{st.session_state.list_name}</div>
            <div class="army-meta">
              {st.session_state.army_cost} / {st.session_state.points} pts
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("⬅ Retour à la page 1"):
        st.session_state.page = "setup"
        st.rerun()

    st.title(st.session_state.list_name)
    st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_cost}/{st.session_state.points} pts")

    game_config = GAME_CONFIG.get(st.session_state.game, GAME_CONFIG["Age of Fantasy"])
    faction_data = factions_by_game[st.session_state.game][st.session_state.faction]

    st.divider()
    st.subheader("Points d'armée")
    show_points_progress(st.session_state.army_cost, st.session_state.points)
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
    max_cost = st.session_state.points * game_config["unit_max_cost_ratio"]
    if unit["base_cost"] > max_cost:
        st.error(f"Cette unité ({unit['base_cost']} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
        st.stop()

    weapon = unit.get("weapons", [{}])[0]
    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0

    for group in unit.get("upgrade_groups", []):
        st.markdown(f"**{group['group']}**")
        if group["type"] == "weapon":
            weapon_options = ["Arme de base"]
            for o in group["options"]:
                weapon_details = format_weapon_details(o["weapon"])
                cost_diff = o["cost"]
                weapon_options.append(f"{o['name']} (A{weapon_details['attacks']}, PA{weapon_details['ap']}{', ' + ', '.join(weapon_details['special']) if weapon_details['special'] else ''}) (+{cost_diff} pts)")
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
        else:
            # Gestion différente pour les héros et les unités
            if unit.get("type") == "hero":
                # Pour les héros: boutons radio (choix unique)
                option_names = ["Aucune amélioration"]
                option_map = {}
                for o in group["options"]:
                    option_names.append(f"{o['name']} (+{o['cost']} pts)")
                    option_map[f"{o['name']} (+{o['cost']} pts)"] = o

                selected_option = st.radio(
                    f"Amélioration {group['group']}",
                    option_names,
                    key=f"{unit['name']}_{group['group']}_hero"
                )

                if selected_option != "Aucune amélioration":
                    opt = option_map[selected_option]
                    if group["group"] not in selected_options:
                        selected_options[group["group"]] = []
                    selected_options[group["group"]].append(opt)
                    upgrades_cost += opt["cost"]
            else:
                # Pour les unités: checkbox (choix multiples)
                st.write("Sélectionnez les améliorations (plusieurs choix possibles):")
                for o in group["options"]:
                    if st.checkbox(f"{o['name']} (+{o['cost']} pts)", key=f"{unit['name']}_{group['group']}_{o['name']}"):
                        if group["group"] not in selected_options:
                            selected_options[group["group"]] = []
                        if not any(opt.get("name") == o["name"] for opt in selected_options.get(group["group"], [])):
                            selected_options[group["group"]].append(o)
                            upgrades_cost += o["cost"]

    # Calcul du coût final et de la taille
    final_cost = base_cost + weapon_cost + mount_cost + upgrades_cost
    unit_size = base_size

    # Affichage de l'effectif final
    if unit.get("type") == "hero":
        st.markdown("**Effectif final : [1]** (héros)")
    else:
        st.markdown(f"**Effectif final : [{unit_size}]**")

    st.markdown(f"**Coût total: {final_cost} pts**")

    if st.button("Ajouter à l'armée"):
        try:
            weapon_data = format_weapon_details(weapon)
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
            total_coriace = total_coriace if total_coriace > 0 else None

            unit_data = {
                "name": unit["name"],
                "type": unit.get("type", "unit"),
                "cost": final_cost,
                "base_cost": base_cost,
                "size": unit_size,
                "quality": unit["quality"],
                "defense": unit["defense"],
                "rules": [format_special_rule(r) for r in unit.get("special_rules", []) if "Coriace(0)" not in r],
                "weapon": weapon_data,
                "options": selected_options,
                "mount": mount,
                "coriace": total_coriace,
                "game": st.session_state.game
            }

            test_army = st.session_state.army_list.copy()
            test_army.append(unit_data)
            test_total = st.session_state.army_cost + final_cost
            if test_total > st.session_state.points:
                st.error(f"⚠️ La limite de points ({st.session_state.points}) est dépassée! Ajout annulé.")
            elif not validate_army_rules(test_army, st.session_state.points, st.session_state.game, final_cost):
                st.error("Cette unité ne peut pas être ajoutée car elle violerait les règles du jeu.")
            else:
                st.session_state.army_list.append(unit_data)
                st.session_state.army_cost += final_cost
                st.rerun()
        except Exception as e:
            st.error(f"Erreur lors de la création de l'unité: {str(e)}")

    st.divider()
    st.subheader("Liste de l'armée")
    if not st.session_state.army_list:
        st.info("Ajoutez des unités pour commencer")
    for i, u in enumerate(st.session_state.army_list):
        with st.container():
            qua_def_coriace = f"Qua {u['quality']}+ / Déf {u['defense']}+"
            if u.get("coriace"):
                qua_def_coriace += f" / Coriace {u['coriace']}"

            unit_header = f"### {u['name']} [{u.get('size', 1) if u.get('type') != 'hero' else 1}] ({u['cost']} pts) | {qua_def_coriace}"
            if u.get("type") == "hero":
                unit_header += " | 🌟 Héros"
            st.markdown(unit_header)

            if u.get("rules"):
                rules_text = ", ".join(u["rules"])
                st.markdown(f"**Règles spéciales:** {rules_text}")

            if 'weapon' in u and u['weapon']:
                weapon_details = format_weapon_details(u['weapon'])
                st.markdown(f"**Arme:** {weapon_details['name']} (A{weapon_details['attacks']}, PA{weapon_details['ap']}{', ' + ', '.join(weapon_details['special']) if weapon_details['special'] else ''})")

            if u.get("options"):
                for group_name, opts in u["options"].items():
                    if isinstance(opts, list) and opts:
                        st.markdown(f"**{group_name}:**")
                        for opt in opts:
                            st.markdown(f"• {opt.get('name', '')}")

            if u.get("mount"):
                mount_details = format_mount_details(u["mount"])
                st.markdown(f"**Monture:** {mount_details}")

            if st.button(f"Supprimer {u['name']}", key=f"del_{i}"):
                st.session_state.army_cost -= u["cost"]
                st.session_state.army_list.pop(i)
                st.rerun()
