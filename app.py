import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import streamlit.components.v1 as components

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="OPR Army Builder FR",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# ======================================================
# LOCAL STORAGE (simple & fiable)
# ======================================================
def ls_get(key):
    components.html(
        f"""
        <script>
        const value = localStorage.getItem("{key}");
        const input = document.createElement("input");
        input.type = "hidden";
        input.id = "{key}";
        input.value = value || "";
        document.body.appendChild(input);
        </script>
        """,
        height=0
    )
    return st.text_input("", key=key, label_visibility="collapsed")

def ls_set(key, value):
    components.html(
        f"""
        <script>
        localStorage.setItem("{key}", `{json.dumps(value)}`);
        </script>
        """,
        height=0
    )

# ======================================================
# CHARGEMENT DES FACTIONS
# ======================================================
@st.cache_data
def load_factions():
    factions = {}
    games = set()

    if not FACTIONS_DIR.exists():
        return {}, []

    for fp in FACTIONS_DIR.glob("*.json"):
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            game = data.get("game")
            faction = data.get("faction")
            if game and faction:
                factions.setdefault(game, {})[faction] = data
                games.add(game)

    return factions, sorted(games)

factions_by_game, games = load_factions()

# ======================================================
# SESSION INIT
# ======================================================
if "page" not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.army_list = []
    st.session_state.army_cost = 0

# ======================================================
# PAGE 1 – SETUP
# ======================================================
if st.session_state.page == "setup":
    st.title("OPR Army Builder 🇫🇷")

    if not games:
        st.error("Aucune faction trouvée dans lists/data/factions/")
        st.stop()

    game = st.selectbox("Jeu", games)
    faction = st.selectbox("Faction", factions_by_game[game].keys())
    points = st.number_input("Points", 250, 5000, 1000, 250)
    list_name = st.text_input("Nom de la liste", f"Liste_{datetime.now().strftime('%Y%m%d')}")

    # -------- IMPORT JSON --------
    st.divider()
    uploaded = st.file_uploader("Importer une liste JSON", type="json")
    if uploaded:
        data = json.load(uploaded)
        st.session_state.game = data["game"]
        st.session_state.faction = data["faction"]
        st.session_state.points = data["points"]
        st.session_state.list_name = data["name"]
        st.session_state.army_list = data["army_list"]
        st.session_state.army_cost = data["total_cost"]
        st.session_state.units = factions_by_game[data["game"]][data["faction"]]["units"]
        st.session_state.page = "army"
        st.rerun()

    if st.button("Créer la liste"):
        st.session_state.game = game
        st.session_state.faction = faction
        st.session_state.points = points
        st.session_state.list_name = list_name
        st.session_state.units = factions_by_game[game][faction]["units"]
        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.session_state.page = "army"
        st.rerun()

# ======================================================
# PAGE 2 – ARMY BUILDER
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

    # -------- AJOUT UNITÉ --------
    st.divider()
    st.subheader("Ajouter une unité")

    unit = st.selectbox(
        "Unité",
        st.session_state.units,
        format_func=lambda u: f"{u['name']} ({u['base_cost']} pts)"
    )

    cost = unit["base_cost"]
    weapon = unit.get("weapons", [{}])[0]
    options = []
    mount = None

    for group in unit.get("upgrade_groups", []):
        st.markdown(f"**{group['group']}**")

        if group["type"] == "weapon":
            names = ["Arme de base"] + [o["name"] for o in group["options"]]
            sel = st.radio("Choix", names, key=f"{unit['name']}_weapon")
            if sel != "Arme de base":
                opt = next(o for o in group["options"] if o["name"] == sel)
                weapon = opt["weapon"]
                cost += opt["cost"]

        elif group["type"] == "mount":
            names = ["Aucune"] + [o["name"] for o in group["options"]]
            sel = st.radio("Monture", names, key=f"{unit['name']}_mount")
            if sel != "Aucune":
                opt = next(o for o in group["options"] if o["name"] == sel)
                mount = opt
                cost += opt["cost"]

        else:
            for opt in group["options"]:
                if st.checkbox(opt["name"], key=f"{unit['name']}_{opt['name']}"):
                    options.append(opt)
                    cost += opt["cost"]

    st.markdown(f"### 💰 Coût : {cost} pts")

    if st.button("➕ Ajouter à l’armée"):
        st.session_state.army_list.append({
            "name": unit["name"],
            "cost": cost,
            "quality": unit["quality"],
            "defense": unit["defense"],
            "rules": unit.get("special_rules", []),
            "weapon": weapon,
            "options": options,
            "mount": mount
        })
        st.session_state.army_cost += cost
        st.rerun()

    # -------- LISTE ARMÉE --------
    st.divider()
    st.subheader("Liste de l’armée")

    for i, u in enumerate(st.session_state.army_list):
        st.markdown(f"### {u['name']} – {u['cost']} pts")
        c1, c2 = st.columns(2)
        c1.metric("Qualité", f"{u['quality']}+")
        c2.metric("Défense", f"{u['defense']}+")

        if u["rules"]:
            st.markdown("**Règles spéciales**")
            st.caption(", ".join(u["rules"]))

        st.markdown("**Armes**")
        st.caption(
            f"{u['weapon'].get('name','-')} | "
            f"A{u['weapon'].get('attacks','?')} "
            f"PA({u['weapon'].get('armor_piercing','?')})"
        )

        if u["options"]:
            st.markdown("**Options sélectionnées**")
            for o in u["options"]:
                st.caption(f"• {o['name']}")

        if u["mount"]:
            st.markdown("**Monture**")
            st.caption(u["mount"]["name"])

        if st.button("❌ Supprimer", key=f"del_{i}"):
            st.session_state.army_cost -= u["cost"]
            st.session_state.army_list.pop(i)
            st.rerun()

    # -------- SAUVEGARDE / EXPORT --------
    st.divider()
    col1, col2, col3 = st.columns(3)

    army_data = {
        "name": st.session_state.list_name,
        "game": st.session_state.game,
        "faction": st.session_state.faction,
        "points": st.session_state.points,
        "total_cost": st.session_state.army_cost,
        "army_list": st.session_state.army_list
    }

    with col1:
        if st.button("💾 Sauvegarder"):
            ls_set("opr_last_list", army_data)
            st.success("Liste sauvegardée dans le navigateur")

    with col2:
        st.download_button(
            "📁 Export JSON",
            json.dumps(army_data, indent=2, ensure_ascii=False),
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json"
        )

    with col3:
        if st.button("♻ Réinitialiser"):
            st.session_state.army_list = []
            st.session_state.army_cost = 0
            st.rerun()
