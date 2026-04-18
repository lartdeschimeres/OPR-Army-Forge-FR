APP_URL = "https://armybuilder-fra.streamlit.app/"

GAME_COLORS = {
    "Age of Fantasy": "#2980b9",
    "Age of Fantasy Regiments": "#8e44ad",
    "Grimdark Future": "#c0392b",
    "Grimdark Future Firefight": "#e67e22",
    "Age of Fantasy Skirmish": "#27ae60",
}


GAME_CONFIG = {
    "Age of Fantasy": {
        "min_points": 500,
        "max_points": 20000,
        "default_points": 2000,
        "hero_limit": 500,
        "unit_copy_rule": 1000,
        "unit_max_cost_ratio": 0.4,
        "unit_per_points": 200,
    },
    "Age of Fantasy Regiments": {
        "min_points": 500,
        "max_points": 20000,
        "default_points": 2000,
        "hero_limit": 500,
        "unit_copy_rule": 1000,
        "unit_max_cost_ratio": 0.4,
        "unit_per_points": 200,
    },
    "Grimdark Future": {
        "min_points": 500,
        "max_points": 20000,
        "default_points": 2000,
        "hero_limit": 500,
        "unit_copy_rule": 1000,
        "unit_max_cost_ratio": 0.4,
        "unit_per_points": 200,
    },
    "Grimdark Future Firefight": {
        "min_points": 150,
        "max_points": 1000,
        "default_points": 300,
        "hero_limit": 300,
        "unit_copy_rule": 300,
        "unit_max_cost_ratio": 0.6,
        "unit_per_points": 100,
    },
    "Age of Fantasy Skirmish": {
        "min_points": 150,
        "max_points": 1000,
        "default_points": 300,
        "hero_limit": 300,
        "unit_copy_rule": 300,
        "unit_max_cost_ratio": 0.6,
        "unit_per_points": 100,
    },
}

DEFAULT_SESSION_STATE = {
    "page": "setup",
    "army_list": [],
    "army_cost": 0,
    "unit_selections": {},
    "draft_counter": 0,
    "draft_unit_name": "",
    "game": None,
    "faction": None,
    "points": 0,
    "list_name": "",
    "units": [],
    "faction_special_rules": [],
    "faction_spells": {},
}
