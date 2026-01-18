import json
from pathlib import Path
from datetime import datetime
import streamlit as st

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(
    page_title="OPR Army Builder FR",
    layout="wide"
)

st.title("OPR Army Builder 🇫🇷")

# ==================================================
# CHEMINS
# ==================================================
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# ==================================================
# CHARGEMENT DES FACTIONS
# ==================================================
@st.cache_data
def load_factions():
    factions = {}
    games = set()

    if not FACTIONS_DIR.exists():
        return {}, []

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
            st.warning(f"Erreur {fp.name}: {e}")

    return factions, sorted(games)

factions_by_game, games = load_factions()

if not games:
    st.error("Aucun jeu trouvé dans lists/data/factions/")
    st.stop()

# ==================================================
# SESSION STATE
# ==================================================
if "page" not in st.session_state:
    st.session_state.page = "setup"

if "army_list" not in st.session_state:
    st.session_state.army_list = []

if "army_cost" not in st.session_state:
    st.session_state.army_cost = 0

# ==================================================
# PAGE 1 – SETUP
# ==================================================
if st.session_state.page == "setup":

    st.subheader("Créer une liste")

    col1, col2 = st.columns(2)

    with col1:
        game = st.selectbox("Jeu", games)

    with col2:
        faction = st.selectbox(
            "Faction",
            list(factions_by_game[game].keys())
        )

    points = st.number_input("Points de la liste", 250, 5000, 1000, 250)
    list_name = st.text_input("Nom de la liste", "Ma Liste")

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

# ==================================================
# PAGE 2 – ARMY BUILDER
# ==================================================
elif st.session_state.page == "army":

    st.header(st.session_state.list_name)
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
        format_func=lambda u: f"{u['name']} ({u['base_cost']} pts)"
    )

    cost = unit["base_cost"]
    selected_options = []
    selected_weapon = unit.get("weapons", [{}])[0]
    selected_mount = None

    st.markdown(f"**Qualité**: {unit['quality']}+ | **Défense**: {unit['defense']}+")

    # OPTIONS
    for group in unit.get("upgrade_groups", []):
        st.markdown(f"**{group['group']}**")

        # OPTIONS MULTIPLES
        if group.get("type") == "multiple":
            for opt in group["options"]:
                if st.checkbox(f"{opt['name']} (+{opt['cost']} pts)"):
                    selected_options.append(opt)
                    cost += opt["cost"]

        # ARMES
        elif group.get("type") == "weapon":
            weapon_names = ["Arme de base"] + [
                f"{o['name']} (+{o['cost']} pts)" for o in group["options"]
            ]
            choice = st.radio("Arme", weapon_names)
            if choice != "Arme de base":
                name = choice.split(" (+")[0]
                opt = next(o for o in group["options"] if o["name"] == name)
                selected_weapon = opt["weapon"]
                cost += opt["cost"]

        # MONTURES
        elif group.get("type") == "mount":
            mount_names = ["Aucune"] + [
                f"{o['name']} (+{o['cost']} pts)" for o in group["options"]
            ]
            choice = st.radio("Monture", mount_names)
            if choice != "Aucune":
                name = choice.split(" (+")[0]
                opt = next(o for o in group["options"] if o["name"] == name)
                selected_mount = opt
                cost += opt["cost"]

    st.markdown(f"### 💰 Coût: {cost} pts")

    if st.button("➕ Ajouter à l'armée"):
        st.session_state.army_list.append({
            "name": unit["name"],
            "quality": unit["quality"],
            "defense": unit["defense"],
            "cost": cost,
            "weapon": selected_weapon,
            "options": selected_options,
            "mount": selected_mount,
            "rules": unit.get("special_rules", [])
        })
        st.session_state.army_cost += cost
        st.rerun()

    # ==================================================
    # AFFICHAGE DE LA LISTE
    # ==================================================
    st.divider()
    st.subheader("Liste de l'armée")

    if not st.session_state.army_list:
        st.info("Aucune unité ajoutée.")
    else:
        for i, u in enumerate(st.session_state.army_list):
            st.markdown(
                f"### {u['name']} — {u['cost']} pts"
            )
            st.caption(f"Q{u['quality']}+ / D{u['defense']}+")

            if u["rules"]:
                st.write("**Règles spéciales**:", ", ".join(u["rules"]))

            st.write(
                "**Arme**:",
                u["weapon"].get("name", "Arme de base"),
                f"A{u['weapon'].get('attacks','?')} PA({u['weapon'].get('armor_piercing','?')})"
            )

            if u["options"]:
                st.write(
                    "**Options**:",
                    ", ".join(o["name"] for o in u["options"])
                )

            if u["mount"]:
                st.write("**Monture**:", u["mount"]["name"])

            if st.button("❌ Supprimer", key=f"del_{i}"):
                st.session_state.army_cost -= u["cost"]
                st.session_state.army_list.pop(i)
                st.rerun()

    # ==================================================
    # BOUTONS DE GESTION
    # ==================================================
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Sauvegarder (JSON)"):
            data = {
                "name": st.session_state.list_name,
                "game": st.session_state.game,
                "faction": st.session_state.faction,
                "points": st.session_state.points,
                "total_cost": st.session_state.army_cost,
                "army_list": st.session_state.army_list,
                "date": datetime.now().isoformat()
            }
            st.download_button(
                "Télécharger",
                json.dumps(data, indent=2, ensure_ascii=False),
                file_name=f"{st.session_state.list_name}.json"
            )

    with col2:
        st.progress(
            min(1.0, st.session_state.army_cost / st.session_state.points)
        )

    with col3:
        if st.button("♻ Réinitialiser"):
            st.session_state.army_list = []
            st.session_state.army_cost = 0
            st.rerun()
