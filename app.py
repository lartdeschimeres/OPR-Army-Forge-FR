import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib
import copy

# Configuration initiale
st.set_page_config(
    page_title="OPR Army Forge FR - Simon Joinville Fouquet",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chemins des fichiers
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
FACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration des jeux
GAME_CONFIG = {
    "Age of Fantasy": {
        "display_name": "Age of Fantasy",
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "point_step": 250,
        "description": "Jeu de bataille dans un univers fantasy médiéval",
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    }
}

# CSS global pour l'esthétique
st.markdown("""
<style>
    /* Style général */
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Style des cartes */
    .card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Style des boutons */
    .stButton>button {
        background-color: #4a6fa5;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        font-weight: bold;
        margin-top: 10px;
    }

    .stButton>button:hover {
        background-color: #3a5a8f;
    }

    /* Style des titres */
    .title {
        color: #2c3e50;
        margin-bottom: 20px;
    }

    /* Style des sous-titres */
    .subtitle {
        color: #
