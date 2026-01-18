import streamlit as st
import json
import os
import re
from copy import deepcopy
import streamlit.components.v1 as components

# =============================
# CONFIG
# =============================

st.set_page_config(
    page_title="OPR Army Forge FR",
    layout="wide"
)

FACTIONS_PATH = "data/factions"

# =============================
# LOCAL STORAGE (STABLE)
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
    value_str = json.dumps(value, ensure_ascii=False)
    js = f"""
    <script>
        localStorage.setItem("{key}", `{value_str}`);
    </script>
    """
    components.html(js, height=0)


# =============================
# UTILITAIRES
# =============================

def slugify(text):
    return re.sub(r"[^a-z0-9_]", "_", text.lower())


def extract_coriace(rules):
    total = 0
    for r in rules:
        match = re.search(r"Coriace\s*\(?\+?(\d+)\)?", r)
        if match:
            total += int(match.group(1))
    return total


def load_factions():
    factions = {}
    if not os.path.isdir(FACTIONS_PATH):
        return factions

    for file in os.listdir(FACTIONS_PATH):
        if file.endswith(".json"):
            with open(os.path.join(FACTIONS_PATH, file), encoding="utf-8") as f:
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
        "points": 0,
        "units": []
    }

PLAYER = "default_player"

# =============================
# PAGE 1 — SETUP
# =============================

if st.session_state.page == "setup":
    st.title("⚔️ OPR Army Forge FR")

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
            value=2000
        )

    with col2:
        st.session_state.army["game"] = st.selectbox(
            "Jeu",
            ["Grimdark Future", "Age of Fantasy"]
        )

        factions = load_factions()
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

    # =============================
    # AJOUT D’UNITÉ
    # =============================

    st.subheader("➕ Ajouter une unité")

    unit_templates = faction["units"]
    unit_names = [u["name"] for u in unit_templates]

    chosen_unit = st.selectbox("Unité", unit_names)

    if st.button("Ajouter"):
        template = next(u for u in unit_templates if u["name"] == chosen_unit)
        unit = deepcopy(template)
        unit["selected_options"] = []
        unit["selected_mount"] = None
        st.session_state.army["units"].append(unit)
        st.rerun()

    st.divider()

    # =============================
    # LISTE DES UNITÉS
    # =============================

    total_points = 0

    for idx, u in enumerate(st.session_state.army["units"]):
        with st.container(border=True):
            colL, colR = st.columns([4, 1])

            with colL:
                st.subheader(u["name"])

                # PROFIL
                base_coriace = extract_coriace(u.get("special_rules", []))
                mount_coriace = extract_coriace(
                    u["selected_mount"]["special_rules"]
                ) if u.get("selected_mount") else 0

                st.markdown(
                    f"""
                    **Qualité :** Q{u["quality"]}+  
                    **Défense :** D{u["defense"]}+  
                    **Coriace total :** 🛡️ {base_coriace + mount_coriace}
                    """
                )

                # ARMES
                st.markdown("### 🔪 Armes")
                for w in u["weapons"]:
                    st.markdown(
                        f"- **{w['name']}** A{w['attacks']} PA({w['armor_piercing']})"
                    )

                # RÈGLES SPÉCIALES DE BASE
                st.markdown("### ✨ Règles spéciales")
                for r in u.get("special_rules", []):
                    st.markdown(f"- {r}")

                # OPTIONS (CHECKBOX)
                if "upgrade_groups" in u:
                    st.markdown("### ⚙️ Options")
                    for g in u["upgrade_groups"]:
                        if g["type"] != "upgrade":
                            continue
                        for opt in g["options"]:
                            key = f"opt_{idx}_{opt['name']}"
                            checked = st.checkbox(
                                f"{opt['name']} (+{opt['cost']} pts)",
                                key=key
                            )
                            if checked and opt not in u["selected_options"]:
                                u["selected_options"].append(opt)
                            if not checked and opt in u["selected_options"]:
                                u["selected_options"].remove(opt)

                # MONTURE
                mounts = [
                    g for g in u.get("upgrade_groups", [])
                    if g["type"] == "mount"
                ]

                if mounts:
                    st.markdown("### 🐎 Monture")
                    mount_names = ["Aucune"] + [m["name"] for m in mounts[0]["options"]]
                    selected = st.selectbox(
                        "Choix de monture",
                        mount_names,
                        index=0,
                        key=f"mount_{idx}"
                    )
                    if selected != "Aucune":
                        u["selected_mount"] = next(
                            m for m in mounts[0]["options"] if m["name"] == selected
                        )
                    else:
                        u["selected_mount"] = None

                # COÛT
                cost = u["base_cost"]
                cost += sum(o["cost"] for o in u["selected_options"])
                if u.get("selected_mount"):
                    cost += u["selected_mount"]["cost"]

                total_points += cost

                st.markdown(f"**Coût : {cost} pts**")

            with colR:
                if st.button("❌ Supprimer", key=f"del_{idx}"):
                    st.session_state.army["units"].pop(idx)
                    st.rerun()

    st.divider()
    st.subheader(f"🧮 Total : {total_points} pts")

    if st.button("⬅️ Retour"):
        st.session_state.page = "setup"
        st.rerun()
