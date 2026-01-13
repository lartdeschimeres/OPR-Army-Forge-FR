import json
import streamlit as st
import re
from pathlib import Path
from copy import deepcopy

st.set_page_config(page_title="OPR Army Forge FR", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# ==================================================
# SESSION
# ==================================================

if "page" not in st.session_state:
    st.session_state.page = "setup"
if "army" not in st.session_state:
    st.session_state.army = []
if "faction" not in st.session_state:
    st.session_state.faction = None
if "points" not in st.session_state:
    st.session_state.points = 2000

# ==================================================
# UTILITAIRES
# ==================================================

def extract_coriace(rules):
    total = 0
    for r in rules:
        m = re.search(r"Coriace\s*\(?\+?(\d+)\)?", r)
        if m:
            total += int(m.group(1))
    return total

def load_factions():
    data = []
    for fp in FACTIONS_DIR.glob("*.json"):
        with open(fp, encoding="utf-8") as f:
            data.append(json.load(f))
    return data

# ==================================================
# PAGE SETUP
# ==================================================

if st.session_state.page == "setup":
    st.title("⚙️ Création de la liste")

    factions = load_factions()
    games = sorted(set(f["game"] for f in factions))

    game = st.selectbox("Jeu", games)
    game_factions = [f for f in factions if f["game"] == game]

    faction_name = st.selectbox("Faction", [f["faction"] for f in game_factions])
    faction = next(f for f in game_factions if f["faction"] == faction_name)

    st.session_state.points = st.number_input("Limite de points", 250, 5000, st.session_state.points, 250)

    if st.button("➡️ Composer l’armée"):
        st.session_state.faction = faction
        st.session_state.page = "army"
        st.rerun()

# ==================================================
# PAGE ARMY
# ==================================================

if st.session_state.page == "army":
    faction = st.session_state.faction
    units = faction["units"]

    st.title(f"📜 {faction['faction']} – {st.session_state.points} pts")

    col_add, col_list = st.columns([1, 2])

    # ==================================================
    # AJOUT UNITÉ
    # ==================================================

    with col_add:
        st.header("Ajouter une unité")

        unit_name = st.selectbox("Unité", [u["name"] for u in units])
        base = next(u for u in units if u["name"] == unit_name)
        unit = deepcopy(base)

        cost = unit["base_cost"]
        rules = list(unit.get("special_rules", []))
        weapons = list(unit.get("weapons", []))

        selected_weapons = []
        selected_upgrades = []
        selected_mount = None

        # -------------------------
        # OPTIONS ESCQUADE
        # -------------------------
        st.subheader("Options d’escouade")
        sergent = st.checkbox("Sergent")
        banner = st.checkbox("Bannière")
        musician = st.checkbox("Musicien")

        if sergent:
            selected_upgrades.append("Sergent")
            cost += 10
        if banner:
            selected_upgrades.append("Bannière")
            cost += 10
        if musician:
            selected_upgrades.append("Musicien")
            cost += 10

        # -------------------------
        # GROUPES
        # -------------------------
        for group in unit.get("upgrade_groups", []):
            st.subheader(group["group"])

            for opt in group["options"]:
                checked = st.checkbox(f"{opt['name']} (+{opt['cost']} pts)", key=f"{unit_name}_{opt['name']}")

                if checked:
                    cost += opt["cost"]

                    if group["type"] == "weapon":
                        selected_weapons = [opt["weapon"]]
                    elif group["type"] == "mount":
                        selected_mount = opt
                        rules.extend(opt.get("special_rules", []))
                    else:
                        selected_upgrades.append(opt["name"])
                        rules.extend(opt.get("special_rules", []))

        if st.button("➕ Ajouter à l’armée"):
            st.session_state.army.append({
                "unit": unit,
                "weapons": selected_weapons or weapons,
                "rules": rules,
                "options": selected_upgrades,
                "mount": selected_mount,
                "cost": cost
            })
            st.rerun()

    # ==================================================
    # LISTE
    # ==================================================

    with col_list:
        st.header("Armée")

        for i, u in enumerate(st.session_state.army):
            unit = u["unit"]

            with st.container(border=True):
                st.subheader(unit["name"])

                q, d, c = st.columns(3)
                q.metric("Qualité", f"{unit['quality']}+")
                d.metric("Défense", f"{unit['defense']}+")
                c.metric("Coriace total", extract_coriace(u["rules"]))

                st.markdown("**Armes**")
                for w in u["weapons"]:
                    st.caption(f"{w['name']} – A{w['attacks']} PA({w['armor_piercing']})")

                st.markdown("**Règles spéciales**")
                st.caption(", ".join(sorted(set(u["rules"]))))

                if u["options"]:
                    st.markdown("**Options sélectionnées**")
                    st.caption(", ".join(u["options"]))

                if u["mount"]:
                    m = u["mount"]
                    st.markdown("**Monture**")
                    st.caption(
                        f"{m['name']} – "
                        + ", ".join(m.get("special_rules", []))
                    )

                st.metric("Coût", u["cost"])
                if st.button("🗑 Supprimer", key=f"del_{i}"):
                    st.session_state.army.pop(i)
                    st.rerun()
