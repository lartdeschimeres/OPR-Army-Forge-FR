import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import streamlit.components.v1 as components
import hashlib
import re

# ======================================================
# CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="OPR Army Builder FR",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# ======================================================
# UTILITAIRES
# ======================================================
def format_special_rule(rule):
    return rule if isinstance(rule, str) else str(rule)

def extract_coriace_value(rule):
    if not isinstance(rule, str):
        return 0
    m = re.search(r"Coriace\s*\(?(\d+)\)?", rule)
    return int(m.group(1)) if m else 0

def get_coriace_from_rules(rules):
    return sum(extract_coriace_value(r) for r in rules or [])

def get_mount_details(mount):
    if not mount:
        return [], 0
    mount_data = mount.get("mount", mount)
    rules = mount_data.get("special_rules", [])
    return rules, get_coriace_from_rules(rules)

def calculate_total_coriace(data):
    total = get_coriace_from_rules(data.get("special_rules", []))

    if data.get("mount"):
        _, c = get_mount_details(data["mount"])
        total += c

    for opts in data.get("options", {}).values():
        for o in opts:
            total += get_coriace_from_rules(o.get("special_rules", []))

    return total if total > 0 else None

def format_weapon_details(w):
    if not w:
        return ""
    txt = f"A{w.get('attacks')} AP({w.get('armor_piercing')})"
    if w.get("special_rules"):
        txt += ", " + ", ".join(w["special_rules"])
    return txt

def format_unit_option(u):
    return f"{u['name']} | Q{u['quality']}+ D{u['defense']}+ | {u['base_cost']} pts"

# ======================================================
# FACTIONS
# ======================================================
@st.cache_data
def load_factions():
    factions = {}
    games = set()

    for fp in FACTIONS_DIR.glob("*.json"):
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            factions.setdefault(data["game"], {})[data["faction"]] = data
            games.add(data["game"])

    return factions, sorted(games)

factions_by_game, games = load_factions()

# ======================================================
# SESSION
# ======================================================
if "page" not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.army_list = []
    st.session_state.army_cost = 0

# ======================================================
# PAGE SETUP
# ======================================================
if st.session_state.page == "setup":
    st.title("OPR Army Builder FR")

    game = st.selectbox("Jeu", games)
    faction = st.selectbox("Faction", factions_by_game[game].keys())
    points = st.number_input("Points", 250, 5000, 1000, 250)
    list_name = st.text_input("Nom de la liste", "Nouvelle Liste")

    if st.button("Créer la liste"):
        st.session_state.game = game
        st.session_state.faction = faction
        st.session_state.points = points
        st.session_state.list_name = list_name
        st.session_state.units = factions_by_game[game][faction]["units"]
        st.session_state.page = "army"
        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.rerun()

# ======================================================
# PAGE ARMÉE
# ======================================================
elif st.session_state.page == "army":
    st.title(st.session_state.list_name)
    st.caption(
        f"{st.session_state.game} • {st.session_state.faction} • "
        f"{st.session_state.army_cost}/{st.session_state.points} pts"
    )

    if st.button("⬅ Retour"):
        st.session_state.page = "setup"
        st.rerun()

    st.divider()
    st.subheader("Ajouter une unité")

    unit = st.selectbox(
        "Unité",
        st.session_state.units,
        format_func=format_unit_option
    )

    base_cost = unit["base_cost"]
    weapon = unit.get("weapons", [{}])[0]
    selected_options = {}
    mount = None
    weapon_cost = 0
    mount_cost = 0
    upgrades_cost = 0

    for group in unit.get("upgrade_groups", []):
        st.markdown(f"**{group['group']}**")

        # ARMES
        if group["type"] == "weapon":
            labels = ["Arme de base"]
            weapon_map = {}

            for o in group["options"]:
                label = f"{o['name']} (+{o['cost']} pts)"
                labels.append(label)
                weapon_map[label] = o

            sel = st.radio("Arme", labels)
            if sel != "Arme de base":
                opt = weapon_map[sel]
                weapon = opt["weapon"]
                weapon_cost = opt["cost"]

        # MONTURES
        elif group["type"] == "mount":
            labels = ["Aucune monture"]
            mount_map = {}

            for o in group["options"]:
                label = f"{o['name']} (+{o['cost']} pts)"
                labels.append(label)
                mount_map[label] = o

            sel = st.radio("Monture", labels)
            if sel != "Aucune monture":
                mount = mount_map[sel]
                mount_cost = mount["cost"]

        # AMÉLIORATIONS → CHECKBOX (HÉROS COMPRIS)
        else:
            for o in group["options"]:
                key = f"{unit['name']}_{group['group']}_{o['name']}"
                if st.checkbox(f"{o['name']} (+{o['cost']} pts)", key=key):
                    selected_options.setdefault(group["group"], []).append(o)
                    upgrades_cost += o["cost"]

    cost = base_cost + weapon_cost + mount_cost + upgrades_cost

    total_coriace = calculate_total_coriace({
        "special_rules": unit.get("special_rules", []),
        "mount": mount,
        "options": selected_options
    })

    st.markdown(f"### Coût total : {cost} pts")
    if total_coriace:
        st.markdown(f"**Coriace total : {total_coriace}**")

    if st.button("Ajouter à l'armée"):
        st.session_state.army_list.append({
            "name": unit["name"],
            "cost": cost,
            "quality": unit["quality"],
            "defense": unit["defense"],
            "rules": unit.get("special_rules", []),
            "weapon": weapon,
            "options": selected_options,
            "mount": mount,
            "coriace": total_coriace
        })
        st.session_state.army_cost += cost
        st.rerun()

    st.divider()
    st.subheader("Liste de l'armée")

    for i, u in enumerate(st.session_state.army_list):
        st.markdown(f"### {u['name']} ({u['cost']} pts)")
        st.markdown(f"Q{u['quality']}+ / D{u['defense']}+")

        if u.get("rules"):
            st.markdown("**Règles spéciales :** " + ", ".join(u["rules"]))

        if u.get("weapon"):
            st.markdown(
                f"**Arme :** {u['weapon']['name']} "
                f"({format_weapon_details(u['weapon'])})"
            )

        if u.get("options"):
            for g, opts in u["options"].items():
                st.markdown(f"**{g} :**")
                for o in opts:
                    st.markdown(f"- {o['name']}")

        if u.get("mount"):
            st.markdown(f"**Monture :** {u['mount']['name']}")

        if u.get("coriace"):
            st.markdown(f"**Coriace : {u['coriace']}**")

        if st.button("Supprimer", key=f"del_{i}"):
            st.session_state.army_cost -= u["cost"]
            st.session_state.army_list.pop(i)
            st.rerun()

    # ==================================================
    # EXPORT / RESET
    # ==================================================
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
        st.download_button(
            "📄 Export JSON",
            json.dumps(army_data, indent=2, ensure_ascii=False),
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json"
        )

    with col2:
        html = "<h1>Liste d'armée</h1>"
        for u in st.session_state.army_list:
            html += f"<h2>{u['name']} ({u['cost']} pts)</h2>"
        st.download_button(
            "🌐 Export HTML",
            html,
            file_name=f"{st.session_state.list_name}.html",
            mime="text/html"
        )

    with col3:
        if st.button("🗑 Réinitialiser"):
            st.session_state.army_list = []
            st.session_state.army_cost = 0
            st.rerun()
