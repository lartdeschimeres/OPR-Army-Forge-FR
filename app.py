import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import math

# ======================================================
# CSS global
# ======================================================
st.markdown("""
<style>

/* --- Nettoyage Streamlit --- */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* --- Fond général --- */
.stApp {
    background: radial-gradient(circle at top, #1b1f2a, #0e1016);
    color: #e6e6e6;
}

/* --- Titres --- */
h1, h2, h3 {
    letter-spacing: 0.04em;
}

/* --- Cartes --- */
.card {
    background: linear-gradient(180deg, #23283a, #191d2b);
    border: 1px solid #303650;
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.25s ease;
}

/* --- Inputs visibles --- */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input {
    background-color: #f3f4f6 !important;
    color: #111827 !important;
    border-radius: 10px !important;
    font-weight: 500;
}

/* --- Bouton principal --- */
button[kind="primary"] {
    background: linear-gradient(135deg, #4da6ff, #2563eb) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
}

/* --- Texte secondaire --- */
.muted {
    color: #9aa4bf;
    font-size: 0.9rem;
}

/* --- Badge --- */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 8px;
    background: #2a3042;
    font-size: 0.75rem;
    margin-bottom: 0.6rem;
}

</style>
""", unsafe_allow_html=True)

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

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.title("🛡️ Army Forge")
    st.markdown(f"**Jeu :** {st.session_state.get('game','—')}")
    st.markdown(f"**Faction :** {st.session_state.get('faction','—')}")
    st.markdown(f"**Format :** {st.session_state.get('points',0)} pts")

# ======================================================
# CONFIG DES JEUX
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {"hero_limit": 375, "unit_copy_rule": 750, "unit_max_cost_ratio": 0.35, "unit_per_points": 150},
    "Grimdark Future": {"hero_limit": 375, "unit_copy_rule": 750, "unit_max_cost_ratio": 0.35, "unit_per_points": 150},
}

# ======================================================
# EXPORTS
# ======================================================
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

def export_army_html():
    html = f"""
    <html><head><meta charset="utf-8">
    <style>
    body {{ background:#0e1016; color:#e6e6e6; font-family:Arial; }}
    .unit {{ border:1px solid #2a3042; padding:12px; border-radius:12px; margin-bottom:10px; }}
    h1 {{ color:#4da6ff; }}
    </style></head><body>
    <h1>{st.session_state.list_name}</h1>
    <p>{st.session_state.game} – {st.session_state.faction}</p>
    <p>{st.session_state.army_cost} / {st.session_state.points} pts</p>
    """
    for u in st.session_state.army_list:
        html += f"<div class='unit'><b>{u['name']}</b> – {u['cost']} pts</div>"
    html += "</body></html>"
    return html

# ======================================================
# CHARGEMENT DES FACTIONS
# ======================================================
@st.cache_data
def load_factions():
    factions = {}
    games = set()
    base = Path(__file__).resolve().parent / "lists" / "data" / "factions"
    for fp in base.glob("*.json"):
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            factions.setdefault(data["game"], {})[data["faction"]] = data
            games.add(data["game"])
    return factions, sorted(games)

# ======================================================
# PAGE SETUP
# ======================================================
if st.session_state.page == "setup":

    st.markdown("## 🛡️ OPR Army Forge")
    st.markdown("<p class='muted'>Forgez vos armées One Page Rules.</p>", unsafe_allow_html=True)

    factions_by_game, games = load_factions()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card'><span class='badge'>Jeu</span>", unsafe_allow_html=True)
        game = st.selectbox("", games, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'><span class='badge'>Faction</span>", unsafe_allow_html=True)
        faction = st.selectbox("", factions_by_game[game].keys(), label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='card'><span class='badge'>Format</span>", unsafe_allow_html=True)
        points = st.number_input("", 250, 10000, 1000, 250, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    colA, colB = st.columns([2,1])
    with colA:
        st.markdown("<div class='card'><span class='badge'>Liste</span>", unsafe_allow_html=True)
        list_name = st.text_input("", f"Liste_{datetime.now().strftime('%Y%m%d')}", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='card'><span class='badge'>Action</span>", unsafe_allow_html=True)
        if st.button("🔥 Construire l’armée", use_container_width=True, type="primary"):
            st.session_state.update({
                "game": game,
                "faction": faction,
                "points": points,
                "list_name": list_name,
                "units": factions_by_game[game][faction]["units"],
                "faction_rules": factions_by_game[game][faction].get("special_rules", []),
                "faction_spells": factions_by_game[game][faction].get("spells", []),
                "army_list": [],
                "army_cost": 0,
                "page": "army"
            })
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ======================================================
# PAGE ARMÉE
# ======================================================
elif st.session_state.page == "army":

    st.title(f"{st.session_state.list_name} – {st.session_state.army_cost}/{st.session_state.points} pts")

    colE1, colE2 = st.columns(2)
    with colE1:
        st.download_button("📄 Export JSON",
            data=json.dumps(export_army_json(), indent=2, ensure_ascii=False),
            file_name=f"{st.session_state.list_name}.json")
    with colE2:
        st.download_button("🌐 Export HTML",
            data=export_army_html(),
            file_name=f"{st.session_state.list_name}.html")

    st.divider()
    st.info("Le reste du constructeur reste inchangé 👌")
