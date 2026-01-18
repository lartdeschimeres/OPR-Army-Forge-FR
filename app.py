import streamlit as st
import json
import os
import re
from pathlib import Path
from copy import deepcopy
import streamlit.components.v1 as components

# =============================
# CONFIG
# =============================

st.set_page_config(
    page_title="OPR Army Forge FR",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_PATH = BASE_DIR / "lists" / "data" / "factions"

# =============================
# LOCAL STORAGE
# =============================

def localstorage_get(key):
    js = f"""
    <script>
        const value = localStorage.getItem("{key}");
        const input = document.getElementById("{key}");
        if (input) {{
            input.value = value || "";
        }}
    </script>
    """
    components.html(js, height=0)
    return st.text_input("", key=key, label_visibility="collapsed") or None


def localstorage_set(key, value):
    js = f"""
    <script>
        localStorage.setItem("{key}", `{json.dumps(value, ensure_ascii=False)}`);
    </script>
    """
    components.html(js, height=0)

# =============================
# UTILITAIRES
# =============================

def extract_coriace(rules):
    total = 0
    for r in rules:
        match = re.search(r"Coriace\s*\(?\+?(\d+)\)?", r)
        if match:
            total += int(match.group(1))
    return total


def load_factions():
    factions = {}
    if not FACTIONS_PATH.exists():
        st.error(f"Dossier factions introuvable : {FACTIONS_PATH}")
        return factions

    for file in FACTIONS_PATH.glob("*.json"):
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
            factions[data["faction"]] = data
    return factions


def load_army_lists(player):
    data = localstorage_get(f"army_lists_{player}")
    if not data:
        return []

    try:
        parsed = json.loads(data)
        return parsed.get("army_lists", [])
    except Exception:
        return []


def save_army_list(player, army):
    lists = load_army_lists(player)
    lists.append(army)
    localstorage_set(
        f"army_lists_{player}",
        {"army_lists": lists}
    )

# =============================
# SESSION INIT
# =============================

if "page" not in st.session_state:
    st.session_state.page = "setup"

if "army" not in st.session_state:
    st.session_state.army = {
        "name": "",
        "game": "",
        "faction": "",
        "points": 2000,
        "units": []
    }

PLAYER = "default_player"

# =============================
# PAGE 1 — SETUP
# =============================

if st.session_state.page == "setup":
    st.title("⚔️ OPR Army Forge FR")

    factions = load_factions()
    if not factions:
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.army["name"] = st.text_input(
            "Nom de la liste",
            st.session_state.army["name"]
        )
        st.session_state.army["points"] = st.number_input(
            "Limite de points",
            min_value=100,
            step=100,
            value=st.session_state.army["points"]
        )

    with col2:
        st.session_state.army["game"] = st.selectbox(
            "Jeu",
            ["Grimdark Future", "Age of Fantasy"]
        )

        st.session_state.army["faction"] = st.selectbox(
            "Faction",
            list(factions.keys())
        )

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        if st.button("💾 Sauvegarder la liste"):
            save_army_list(PLAYER, deepcopy(st.session_state.army))
            st.success("Liste sauvegardée")

    with colB:
        if st.button("➡️ Ma liste"):
            st.session_state.page = "army"
            st.rerun()

# =============================
# PAGE 2 — ARMY BUILDER
# =============================

if st.session_state.page == "army":
    st.title(f"📜 {st.session_state.army['name']}")

    factions = load_factions()
    faction = factions[st.session_state.army["faction"]]

    st.subheader("➕ Ajouter une unité")

    unit_templates = faction.get("units", [])
    unit_names = [u["name"] for u in unit_templates]

    selected_unit = st.selectbox("Unité", unit_names)

    if st.button("Ajouter l’unité"):
        base = next(u for u in unit_templates if u["name"] == selected_unit)
        unit = deepcopy(base)
        unit["selected_options"] = []
        unit["selected_mount"] = None
        st.session_state.army["units"].append(unit)
        st.rerun()

    st.divider()

    total_points = 0

    for idx, u in enumerate(st.session_state.army["units"]):
        with st.container(border=True):
            colL, colR = st.columns([4, 1])

            with colL:
                st.subheader(u["name"])

                base_coriace = extract_coriace(u.get("special_rules", []))
                mount_coriace = extract_coriace(
                    u["selected_mount"]["special_rules"]
                ) if u.get("selected_mount") else 0

                st.markdown(
                    f"""
                    **Qualité :** Q{u['quality']}+  
                    **Défense :** D{u['defense']}+  
                    **Coriace total :** 🛡️ {base_coriace + mount_coriace}
                    """
                )

                st.markdown("### ✨ Règles spéciales")
                for r in u.get("special_rules", []):
                    st.markdown(f"- {r}")

                st.markdown("### 🔪 Armes")
                for w in u.get("weapons", []):
                    st.markdown(
                        f"- **{w['name']}** A{w['attacks']} PA({w['armor_piercing']})"
                    )

            with colR:
                if st.button("❌ Supprimer", key=f"del_{idx}"):
                    st.session_state.army["units"].pop(idx)
                    st.rerun()

    st.divider()
    st.subheader(f"🧮 Total : {total_points} pts")

    if st.button("⬅️ Retour"):
        st.session_state.page = "setup"
        st.rerun()
