import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import math

st.set_page_config(
    page_title="OPR Army Forge",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# CSS
# ======================================================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent;}

    .stApp {
        background: #f5f5f5;
        color: #333333;
    }

    section[data-testid="stSidebar"] {
        background: #e9ecef;
        border-right: 1px solid #dee2e6;
    }

    h1, h2, h3 {
        color: #2c3e50;
        letter-spacing: 0.04em;
    }

    .card {
        background: #ffffff;
        border: 2px solid #3498db;
        border-radius: 8px;
        padding: 1.2rem;
        transition: all 0.2s ease;
        cursor: pointer;
        box-shadow: 0 0 10px rgba(52, 152, 219, 0.2);
    }

    .card:hover {
        border-color: #2980b9;
        box-shadow: 0 0 20px rgba(52, 152, 219, 0.4);
        transform: translateY(-2px);
    }

    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        background: #3498db;
        color: white;
        font-size: 0.75rem;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #3498db, #2980b9) !important;
        color: white !important;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        border: none;
    }

    .rule-item, .spell-item {
        font-size: 14px;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }
    .rule-name, .spell-name {
        font-weight: bold;
        color: #bb86fc;
        margin-right: 10px;
    }
    .rule-description, .spell-description {
        color: #ccc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
# SIDEBAR – CONTEXTE & NAVIGATION
# ======================================================
with st.sidebar:
    st.markdown("<div style='height:1px;'></div>", unsafe_allow_html=True)

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
        if all(key in st.session_state for key in ["game", "faction", "points", "list_name"]):
            st.session_state.page = "army"
            st.rerun()
        else:
            st.error("Veuillez compléter la configuration avant de passer à la construction.")

# ======================================================
# CONFIGURATION DES JEUX OPR (EXTENSIBLE)
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "min_points": 250,
        "max_points": 10000,
        "default_points": 1000,
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    },
    "Age of Fantasy: Regiments": {
        "min_points": 500,
        "max_points": 20000,
        "default_points": 2000,
        "hero_limit": 500,
        "unit_copy_rule": 1000,
        "unit_max_cost_ratio": 0.4,
        "unit_per_points": 200
    },
    "Grimdark Future": {
        "min_points": 250,
        "max_points": 10000,
        "default_points": 1000,
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    },
    "Grimdark Future: Firefight": {
        "min_points": 150,
        "max_points": 1000,
        "default_points": 300,
        "hero_limit": 300,
        "unit_copy_rule": 300,
        "unit_max_cost_ratio": 0.6,
        "unit_per_points": 100
    },
    "Age of Fantasy: Skirmish": {
        "min_points": 150,
        "max_points": 1000,
        "default_points": 300,
        "hero_limit": 300,
        "unit_copy_rule": 300,
        "unit_max_cost_ratio": 0.6,
        "unit_per_points": 100
    }
}

# ======================================================
# FONCTIONS DE VALIDATION
# ======================================================
def check_hero_limit(army_list, army_points, game_config):
    max_heroes = math.floor(army_points / game_config["hero_limit"])
    hero_count = sum(1 for unit in army_list if unit.get("type") == "hero")
    if hero_count > max_heroes:
        st.error(f"Limite de héros dépassée! Max: {max_heroes} (1 héros/{game_config['hero_limit']} pts)")
        return False
    return True

def check_unit_max_cost(army_list, army_points, game_config, new_unit_cost=None):
    max_cost = army_points * game_config["unit_max_cost_ratio"]
    for unit in army_list:
        if unit["cost"] > max_cost:
            st.error(f"Unité {unit['name']} dépasse {int(max_cost)} pts (35% du total)")
            return False
    if new_unit_cost and new_unit_cost > max_cost:
        st.error(f"Cette unité dépasse {int(max_cost)} pts (35% du total)")
        return False
    return True

def check_unit_copy_rule(army_list, army_points, game_config):
    x_value = math.floor(army_points / game_config["unit_copy_rule"])
    max_copies = 1 + x_value
    unit_counts = {}
    for unit in army_list:
        name = unit["name"]
        unit_counts[name] = unit_counts.get(name, 0) + 1
    for unit_name, count in unit_counts.items():
        if count > max_copies:
            st.error(f"Trop de copies de {unit_name}! Max: {max_copies}")
            return False
    return True

def validate_army_rules(army_list, army_points, game):
    game_config = GAME_CONFIG.get(game, {})
    return (check_hero_limit(army_list, army_points, game_config) and
            check_unit_max_cost(army_list, army_points, game_config) and
            check_unit_copy_rule(army_list, army_points, game_config))

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
        name_part += f" [{u.get('size', 10)}]"
    qua_def = f"Qua {u['quality']}+ / Déf {u.get('defense', '?')}"
    result = f"{name_part} - {qua_def} {u['base_cost']}pts"
    return result

def export_army_json():
    return {
        "game": st.session_state.game,
        "faction": st.session_state.faction,
        "points": st.session_state.points,
        "list_name": st.session_state.list_name,
        "army_cost": st.session_state.army_cost,
        "units": st.session_state.army_list,
        "exported_at": datetime.now().isoformat()
    }

# ======================================================
# EXPORT HTML
# ======================================================
def export_html(army_list, army_name, army_limit):
    def esc(txt):
        return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Héros en premier
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
}}

th, td {{
  border: 1px solid var(--border);
  padding: 6px;
}}

th {{
  background: var(--bg-header);
}}

.section-title {{
  font-weight: bold;
  margin-top: 12px;
  margin-bottom: 6px;
}}

.rules span {{
  display: inline-block;
  margin-right: 10px;
  color: var(--accent);
  font-size: 12px;
}}

.special-block {{
  margin-top: 40px;
}}

.special-block h3 {{
  text-align: center;
  color: var(--accent);
  border-top: 1px solid var(--border);
  padding-top: 10px;
}}

.columns {{
  display: flex;
  gap: 20px;
}}

.column {{
  flex: 1;
  font-size: 12px;
}}
</style>
</head>
<body>

<div class="army">
<div class="army-title">
{esc(army_name)} — {sum(u["cost"] for u in sorted_army_list)} / {army_limit} pts
</div>
"""

    for unit in sorted_army_list:
        size = 1 if unit.get("type") == "hero" else unit.get("size", 10)

        html += f"""
<section class="unit-card">
<div class="unit-header">
<h2>{esc(unit["name"])} [{size}]</h2>
<span class="cost">{unit["cost"]} pts</span>
</div>

<div class="stats">
<span>Qualité {unit.get("quality")}+</span>
<span>Défense {unit.get("defense")}+</span>
"""

        if "coriace" in unit:
            html += f"<span>Coriace {unit['coriace']}+</span>"

        html += "</div>"

        weapons = unit.get("weapon", [])
        if not isinstance(weapons, list):
            weapons = [weapons]

        if weapons:
            html += """
<div class="section-title">Armes</div>
<table>
<tr><th>Nom</th><th>Portée</th><th>Att</th><th>PA</th><th>Règles</th></tr>
"""
            for w in weapons:
                html += f"""
<tr>
<td>{esc(w.get("name","-"))}</td>
<td>{esc(w.get("range","-"))}</td>
<td>{esc(w.get("attacks","-"))}</td>
<td>{esc(w.get("armor_piercing","-"))}</td>
<td>{esc(", ".join(w.get("special_rules",[])))}</td>
</tr>
"""
            html += "</table>"

        upgrades = unit.get("weapon_upgrades", [])
        if upgrades:
            html += "<div class='section-title'>Améliorations d'arme</div><ul>"
            for u in upgrades:
                html += f"<li>{esc(u.get('name'))}</li>"
            html += "</ul>"

        options = unit.get("options", {})
        if options:
            html += "<div class='section-title'>Options</div>"
            for g, opts in options.items():
                html += f"<strong>{esc(g)}</strong>: "
                html += ", ".join(esc(o.get("name")) for o in opts)
                html += "<br>"

        mount = unit.get("mount")
        if mount:
            html += f"<div class='section-title'>Monture</div><div>{esc(mount.get('name'))}</div>"

        html += "</section>"

    if st.session_state.get("faction_special_rules"):
        rules = st.session_state.faction_special_rules
        mid = (len(rules) + 1) // 2
        html += "<div class='special-block'><h3>Règles de Faction</h3><div class='columns'>"
        for col in (rules[:mid], rules[mid:]):
            html += "<div class='column'>"
            for r in col:
                html += f"<strong>{esc(r['name'])}</strong>: {esc(r['description'])}<br><br>"
            html += "</div>"
        html += "</div></div>"

    if st.session_state.get("faction_spells"):
        html += "<div class='special-block'><h3>Sorts de Faction</h3>"
        for n, s in st.session_state.faction_spells.items():
            html += f"<strong>{esc(n)}</strong> ({s.get('cost')}): {esc(s.get('description'))}<br><br>"
        html += "</div>"

    html += "</div></body></html>"
    return html

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
                    if "faction_special_rules" not in data:
                        data["faction_special_rules"] = []
                    if "spells" not in data:
                        data["spells"] = {}
                    factions[game][faction] = data
                    games.add(game)
        except Exception as e:
            st.warning(f"Erreur chargement {fp.name}: {e}")
    return factions, sorted(games) if games else list(GAME_CONFIG.keys())

# ======================================================
# PAGE 1 – CONFIGURATION
# ======================================================
if st.session_state.page == "setup":
    st.markdown("## 🛡️ OPR Army Forge")
    st.markdown(
        "<p class='muted'>Construisez, équilibrez et façonnez vos armées pour "
        "Age of Fantasy et Grimdark Future.</p>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    factions_by_game, games = load_factions()
    if not games:
        st.error("Aucun jeu trouvé")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<span class='badge'>Jeu</span>", unsafe_allow_html=True)
        game = st.selectbox(
            "Choisissez un système",
            games,
            index=games.index(st.session_state.get("game")) if st.session_state.get("game") in games else 0,
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("<span class='badge'>Faction</span>", unsafe_allow_html=True)
        faction = st.selectbox(
            "Faction",
            list(factions_by_game[game].keys()),
            index=0,
            label_visibility="collapsed"
        )

    with col3:
        st.markdown("<span class='badge'>Format</span>", unsafe_allow_html=True)
        game_cfg = GAME_CONFIG.get(game, {})
        points = st.number_input(
            "Points",
            min_value=game_cfg.get("min_points", 250),
            max_value=game_cfg.get("max_points", 10000),
            value=game_cfg.get("default_points", 1000),
            step=250,
            label_visibility="collapsed"
        )

    st.markdown("")

    colA, colB = st.columns([2, 1])

    with colA:
        st.markdown("<span class='badge'>Nom de la liste</span>", unsafe_allow_html=True)
        list_name = st.text_input(
            "Nom de la liste",
            value=st.session_state.get(
                "list_name",
                f"Liste_{datetime.now().strftime('%Y%m%d')}"
            ),
            label_visibility="collapsed"
        )

    with colB:
        st.markdown("<span class='badge'>Action</span>", unsafe_allow_html=True)
        st.markdown(
            "<p class='muted'>Prêt à forger votre armée ?</p>",
            unsafe_allow_html=True
        )

        can_build = all([game, faction, points > 0, list_name.strip() != ""])

        if st.button(
            "🔥 Construire l'armée",
            use_container_width=True,
            type="primary",
            disabled=not can_build
        ):
            st.session_state.game = game
            st.session_state.faction = faction
            st.session_state.points = points
            st.session_state.list_name = list_name

            faction_data = factions_by_game[game][faction]
            st.session_state.units = faction_data["units"]
            st.session_state.faction_special_rules = faction_data.get("faction_special_rules", [])
            st.session_state.faction_spells = faction_data.get("spells", {})

            st.session_state.army_list = []
            st.session_state.army_cost = 0
            st.session_state.unit_selections = {}

            st.session_state.page = "army"
            st.rerun()

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE
# ======================================================
elif st.session_state.page == "army":
    if not all(key in st.session_state for key in ["game", "faction", "points", "list_name", "units", "faction_special_rules", "faction_spells"]):
        st.error("Erreur de configuration. Veuillez retourner à la page de configuration.")
        st.stop()

    st.session_state.setdefault("list_name", "Nouvelle Armée")
    st.session_state.setdefault("army_cost", 0)
    st.session_state.setdefault("army_list", [])
    st.session_state.setdefault("unit_selections", {})

    st.title(f"{st.session_state.list_name} - {st.session_state.army_cost}/{st.session_state.points} pts")

    if st.button("⬅️ Retour à la configuration"):
        st.session_state.page = "setup"
        st.rerun()

    st.divider()
    st.subheader("📤 Export de la liste")

    colE1, colE2 = st.columns(2)

    with colE1:
        json_data = json.dumps(export_army_json(), indent=2, ensure_ascii=False)
        st.download_button(
            "📄 Export JSON",
            data=json_data,
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json",
            use_container_width=True
        )

    with colE2:
        html_data = export_html(st.session_state.army_list, st.session_state.list_name, st.session_state.points)
        st.download_button(
            "🌐 Export HTML",
            data=html_data,
            file_name=f"{st.session_state.list_name}.html",
            mime="text/html",
            use_container_width=True
        )

    st.subheader("📊 Points de l'Armée")
    points_used = st.session_state.army_cost
    points_total = st.session_state.points
    progress_ratio = min(points_used / points_total, 1.0) if points_total > 0 else 0

    st.progress(progress_ratio)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Points utilisés :** {points_used} pts")
    with col2:
        st.markdown(f"**Points totaux :** {points_total} pts")

    if points_used > points_total:
        st.error("⚠️ Dépassement du total de points autorisé")

    st.divider()

    points = st.session_state.points
    game_cfg = GAME_CONFIG.get(st.session_state.game, {})

    st.subheader("📊 Progression de l'armée")
    col1, col2, col3 = st.columns(3)

    with col1:
        units_cap = math.floor(points / game_cfg.get("unit_per_points", 150))
        units_now = len([u for u in st.session_state.army_list if u.get("type") != "hero"])
        st.progress(min(units_now / max(units_cap, 1), 1.0))
        st.caption(f"Unités : {units_now} / {units_cap}")

    with col2:
        heroes_cap = math.floor(points / game_cfg.get("hero_limit", 375))
        heroes_now = len([u for u in st.session_state.army_list if u.get("type") == "hero"])
        st.progress(min(heroes_now / max(heroes_cap, 1), 1.0))
        st.caption(f"Héros : {heroes_now} / {heroes_cap}")

    with col3:
        copy_cap = 1 + math.floor(points / game_cfg.get("unit_copy_rule", 750))
        st.progress(min(copy_cap / 5, 1.0))
        st.caption(f"Copies max : {copy_cap} / unité")

    st.divider()

    # ======================================================
    # RÈGLES SPÉCIALES DE FACTION
    # ======================================================
    if hasattr(st.session_state, 'faction_special_rules') and st.session_state.faction_special_rules:
        with st.expander("📜 Règles spéciales de la faction", expanded=True):
            for rule in st.session_state.faction_special_rules:
                if isinstance(rule, dict):
                    st.markdown(f"**{rule.get('name', 'Règle sans nom')}**: {rule.get('description', '')}", unsafe_allow_html=True)
                else:
                    st.markdown(f"- {rule}", unsafe_allow_html=True)

    # ======================================================
    # SORTS DE LA FACTION
    # ======================================================
    if hasattr(st.session_state, 'faction_spells') and st.session_state.faction_spells:
        with st.expander("✨ Sorts de la faction", expanded=True):
            for spell_name, spell_details in st.session_state.faction_spells.items():
                if isinstance(spell_details, dict):
                    st.markdown(
                        f"**{spell_name}** ({spell_details.get('cost', '?')} pts): {spell_details.get('description', '')}",
                        unsafe_allow_html=True
                    )

    st.subheader("Liste de l'Armée")

    if not st.session_state.army_list:
        st.markdown("Aucune unité ajoutée pour le moment.")
    else:
        for i, unit_data in enumerate(st.session_state.army_list):
            with st.expander(f"{unit_data['name']} - {unit_data['cost']} pts", expanded=False):
                st.markdown(f"**Type :** {unit_data['type']}")
                st.markdown(f"**Taille :** {unit_data.get('size', '?')}")
                st.markdown(f"**Qualité :** {unit_data.get('quality', '?')}+")
                st.markdown(f"**Défense :** {unit_data.get('defense', '?')}+")

                if st.button(f"Supprimer {unit_data['name']}", key=f"delete_{i}"):
                    st.session_state.army_cost -= unit_data['cost']
                    st.session_state.army_list.pop(i)
                    st.rerun()

    st.divider()

    unit = st.selectbox(
        "Unité disponible",
        st.session_state.units,
        format_func=format_unit_option,
        key="unit_select",
    )

    unit_key = f"unit_{unit['name']}"
    st.session_state.unit_selections.setdefault(unit_key, {})

    weapons = list(unit.get("weapons", []))
    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0
    weapon_upgrades = []

    for g_idx, group in enumerate(unit.get("upgrade_groups", [])):
        g_key = f"group_{g_idx}"
        st.subheader(group.get("group", "Améliorations"))

        # ---------- ARMES ----------
        if group.get("type") == "weapon":
            choices = ["Arme de base"]
            opt_map = {}

            for o in group.get("options", []):
                label = f"{o['name']} (+{o['cost']} pts)"
                choices.append(label)
                opt_map[label] = o

            current = st.session_state.unit_selections[unit_key].get(g_key, choices[0])
            choice = st.radio(
                "Sélection de l'arme",
                choices,
                index=choices.index(current) if current in choices else 0,
                key=f"{unit_key}_{g_key}_weapon",
            )

            st.session_state.unit_selections[unit_key][g_key] = choice

            if choice != "Arme de base":
                opt = opt_map[choice]
                weapon_cost += opt["cost"]
                weapons = [opt["weapon"]] if unit.get("type") == "hero" else [opt["weapon"]]

        # ---------- AMÉLIORATIONS D'ARME ----------
        elif group.get("type") == "weapon_upgrades":
            choices = ["Aucune amélioration d'arme"]
            opt_map = {}

            for o in group.get("options", []):
                label = f"{o['name']} (+{o['cost']} pts)"
                choices.append(label)
                opt_map[label] = o

            current = st.session_state.unit_selections[unit_key].get(g_key, choices[0])
            choice = st.radio(
                "Amélioration d'arme",
                choices,
                index=choices.index(current) if current in choices else 0,
                key=f"{unit_key}_{g_key}_weapon_upgrade",
            )

            st.session_state.unit_selections[unit_key][g_key] = choice

            if choice != "Aucune amélioration d'arme":
                opt = opt_map[choice]
                upgrades_cost += opt["cost"]
                weapon_upgrades.append(opt["weapon"])

        # ---------- MONTURE ----------
        elif group.get("type") == "mount":
            choices = ["Aucune monture"]
            opt_map = {}

            for o in group.get("options", []):
                label = f"{o['name']} (+{o['cost']} pts)"
                choices.append(label)
                opt_map[label] = o

            current = st.session_state.unit_selections[unit_key].get(g_key, choices[0])
            choice = st.radio(
                "Monture",
                choices,
                index=choices.index(current) if current in choices else 0,
                key=f"{unit_key}_{g_key}_mount",
            )

            st.session_state.unit_selections[unit_key][g_key] = choice

            if choice != "Aucune monture":
                mount = opt_map[choice]
                mount_cost = mount["cost"]

        # ---------- OPTIONS / RÔLES ----------
        elif group.get("type") == "role" and unit.get("type") == "hero":
            choices = ["Aucun rôle"]
            opt_map = {}

            for o in group.get("options", []):
                label = f"{o['name']} (+{o['cost']} pts)"
                choices.append(label)
                opt_map[label] = o

            current = st.session_state.unit_selections[unit_key].get(g_key, choices[0])
            choice = st.radio(
                "Rôle du héros",
                choices,
                index=choices.index(current) if current in choices else 0,
                key=f"{unit_key}_{g_key}_role",
            )

            st.session_state.unit_selections[unit_key][g_key] = choice

            if choice != "Aucun rôle":
                opt = opt_map[choice]
                upgrades_cost += opt["cost"]
                selected_options[group.get("group", "Rôle")] = [opt]

        # ---------- OPTIONS NORMALES (checkbox) ----------
        else:
            for o in group.get("options", []):
                opt_key = f"{unit_key}_{g_key}_{o['name']}"
                checked = st.checkbox(
                    f"{o['name']} (+{o['cost']} pts)",
                    value=st.session_state.unit_selections[unit_key].get(opt_key, False),
                    key=opt_key,
                )
                st.session_state.unit_selections[unit_key][opt_key] = checked
                if checked:
                    upgrades_cost += o["cost"]
                    selected_options.setdefault(group.get("group", "Options"), []).append(o)

    multiplier = 2 if unit.get("type") != "hero" and st.checkbox("Unité combinée") else 1

    base_cost = unit.get("base_cost", 0)
    final_cost = (base_cost + weapon_cost + upgrades_cost) * multiplier + mount_cost

    st.subheader("Coût de l'unité sélectionnée")
    st.markdown(f"**Coût total :** {final_cost} pts")
    st.divider()

    if st.button("➕ Ajouter à l'armée"):
        if st.session_state.army_cost + final_cost > st.session_state.points:
            st.error(f"⛔ Dépassement du format : {st.session_state.army_cost + final_cost} / {st.session_state.points} pts")
            st.stop()

        # Coriace uniquement si l’unité possède la règle
        coriace = None
        base_coriace = unit.get("coriace")

        if base_coriace is not None:
            coriace = base_coriace
            if mount:
                coriace += mount.get("defense_bonus", 0)

        unit_data = {
            "name": unit["name"],
            "type": unit.get("type", "unit"),
            "cost": final_cost,
            "size": unit.get("size", 10) * multiplier if unit.get("type") != "hero" else 1,
            "quality": unit.get("quality"),
            "defense": unit.get("defense"),
            "weapon": weapons,
            "weapon_upgrades": weapon_upgrades,
            "options": selected_options,
            "mount": mount,
        }

        # On n’ajoute coriace que s’il existe
        if coriace is not None:
            unit_data["coriace"] = coriace

        test_army = st.session_state.army_list + [unit_data]

        if validate_army_rules(test_army, st.session_state.points, st.session_state.game):
            st.session_state.army_list.append(unit_data)
            st.session_state.army_cost += final_cost
            st.rerun()
