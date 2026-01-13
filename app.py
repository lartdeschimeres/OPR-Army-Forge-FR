import streamlit as st
import re
from copy import deepcopy

st.set_page_config(page_title="OPR Army Forge FR", layout="wide")

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "setup"

if "army" not in st.session_state:
    st.session_state.army = []

if "game" not in st.session_state:
    st.session_state.game = None

if "faction" not in st.session_state:
    st.session_state.faction = None

if "list_name" not in st.session_state:
    st.session_state.list_name = ""

if "points_limit" not in st.session_state:
    st.session_state.points_limit = 2000


# --------------------------------------------------
# UTILITAIRES
# --------------------------------------------------

def extract_coriace(rules):
    total = 0
    for r in rules:
        m = re.search(r"Coriace\s*\(?\+?(\d+)\)?", r)
        if m:
            total += int(m.group(1))
    return total


def format_rules(rules):
    return ", ".join(sorted(set(rules))) if rules else "Aucune"


# --------------------------------------------------
# DONNÉES EXEMPLE (stub faction)
# --------------------------------------------------

UNIT_TEMPLATE = {
    "name": "Maître de la Guerre Élu",
    "type": "Hero",
    "base_cost": 60,
    "quality": 4,
    "defense": 4,
    "base_rules": [
        "Héros",
        "Né pour la guerre",
        "Coriace (3)"
    ],
    "option_groups": {
        "role": [
            {"name": "Seigneur de Guerre", "cost": 35},
            {"name": "Conquérant", "cost": 20}
        ],
        "mount": [
            {
                "name": "Dragon du Ravage",
                "cost": 320,
                "rules": [
                    "Coriace (+12)",
                    "Volant",
                    "Effrayant (2)"
                ]
            }
        ]
    }
}


# ==================================================
# PAGE 1 – CONFIGURATION
# ==================================================

if st.session_state.page == "setup":
    st.title("⚙️ Création de la liste")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.game = st.selectbox(
            "Jeu",
            ["Age of Fantasy", "Grimdark Future"]
        )

        st.session_state.faction = st.selectbox(
            "Faction",
            ["Disciples de la Guerre", "Sœurs Bénies", "Autre faction"]
        )

    with col2:
        st.session_state.list_name = st.text_input(
            "Nom de la liste",
            value=st.session_state.list_name
        )

        st.session_state.points_limit = st.number_input(
            "Limite de points",
            min_value=250,
            step=250,
            value=st.session_state.points_limit
        )

    if st.button("➡️ Créer / Continuer la liste"):
        st.session_state.page = "army"
        st.rerun()


# ==================================================
# PAGE 2 – MA LISTE
# ==================================================

if st.session_state.page == "army":
    st.title(f"📜 {st.session_state.list_name or 'Ma liste'}")

    st.caption(
        f"Jeu : {st.session_state.game} | "
        f"Faction : {st.session_state.faction} | "
        f"Format : {st.session_state.points_limit} pts"
    )

    if st.button("⬅️ Retour configuration"):
        st.session_state.page = "setup"
        st.rerun()

    col_left, col_right = st.columns([1, 2])

    # --------------------------------------------------
    # AJOUT D’UNITÉ
    # --------------------------------------------------

    with col_left:
        st.header("Ajouter une unité")

        unit = deepcopy(UNIT_TEMPLATE)
        st.subheader(unit["name"])

        selected_options = []
        selected_mount = None
        extra_cost = 0

        for group, options in unit["option_groups"].items():
            names = ["Aucune"] + [o["name"] for o in options]
            choice = st.selectbox(group.capitalize(), names, key=f"{group}_select")

            if choice != "Aucune":
                opt = next(o for o in options if o["name"] == choice)
                extra_cost += opt["cost"]

                if group == "mount":
                    selected_mount = opt
                else:
                    selected_options.append(opt)

        total_cost = unit["base_cost"] + extra_cost

        if st.button("➕ Ajouter à l'armée"):
            st.session_state.army.append({
                "profile": unit,
                "options": selected_options,
                "mount": selected_mount,
                "cost": total_cost
            })
            st.rerun()

    # --------------------------------------------------
    # LISTE DE L’ARMÉE
    # --------------------------------------------------

    with col_right:
        st.header("Unités")

        if not st.session_state.army:
            st.info("Aucune unité ajoutée.")
        else:
            for i, u in enumerate(st.session_state.army):
                profile = u["profile"]

                with st.container(border=True):
                    cols = st.columns([3, 1])

                    with cols[0]:
                        st.subheader(profile["name"])

                        q, d, c = st.columns(3)

                        q.metric("Qualité", f"{profile['quality']}+")
                        d.metric("Défense", f"{profile['defense']}+")

                        base_coriace = extract_coriace(profile["base_rules"])
                        mount_coriace = extract_coriace(u["mount"]["rules"]) if u["mount"] else 0
                        c.metric("Coriace total", base_coriace + mount_coriace)

                        st.markdown("**Règles spéciales**")
                        st.caption(format_rules(profile["base_rules"]))

                        if u["options"]:
                            st.markdown("**Options sélectionnées**")
                            st.caption(", ".join(o["name"] for o in u["options"]))

                        if u["mount"]:
                            st.markdown("**Monture**")
                            st.caption(
                                f"{u['mount']['name']} — "
                                + format_rules(u["mount"]["rules"])
                            )

                    with cols[1]:
                        st.metric("Coût", u["cost"])
                        if st.button("🗑 Supprimer", key=f"del_{i}"):
                            st.session_state.army.pop(i)
                            st.rerun()
