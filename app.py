import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import hashlib
import re
import base64
import math
import os

# ======================================================
# CONFIGURATION POUR SIMON
# ======================================================
st.set_page_config(
    page_title="OPR Army Forge FR - Simon Joinville Fouquet",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chemins des fichiers
BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
os.makedirs(FACTIONS_DIR, exist_ok=True)

# ======================================================
# CONFIGURATION DES JEUX ET LEURS LIMITATIONS
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "display_name": "Age of Fantasy",
        "max_points": 10000,
        "min_points": 250,
        "default_points": 1000,
        "point_step": 250,
        "description": "Jeu de bataille rangée dans un univers fantasy médiéval",
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    }
}

# ======================================================
# FONCTIONS POUR LES RÈGLES SPÉCIFIQUES (corrigées)
# ======================================================
def check_army_points(army_list, army_points, game_config):
    """Vérifie que le total des points ne dépasse pas la limite choisie par le joueur"""
    total = sum(unit["cost"] for unit in army_list)
    return total <= army_points

def check_hero_limit(army_list, army_points, game_config):
    """Vérifie la limite de héros"""
    if game_config.get("hero_limit"):
        max_heroes = math.floor(army_points / game_config["hero_limit"])
        hero_count = sum(1 for unit in army_list if unit.get("type") == "hero")
        return hero_count <= max_heroes
    return True

def check_unit_max_cost(army_list, army_points, game_config, new_unit_cost=None):
    """Vérifie qu'aucune unité ne dépasse le ratio maximum de coût"""
    if not game_config.get("unit_max_cost_ratio"):
        return True

    max_cost = army_points * game_config["unit_max_cost_ratio"]

    # Vérifier les unités existantes
    for unit in army_list:
        if unit["cost"] > max_cost:
            return False

    # Vérifier la nouvelle unité si fournie
    if new_unit_cost and new_unit_cost > max_cost:
        return False

    return True

def check_unit_copy_rule(army_list, army_points, game_config):
    """Vérifie la règle des copies d'unités"""
    if game_config.get("unit_copy_rule"):
        x_value = math.floor(army_points / game_config["unit_copy_rule"])
        max_copies = 1 + x_value

        # Compter les copies de chaque unité
        unit_counts = {}
        for unit in army_list:
            unit_name = unit["name"]
            if unit_name in unit_counts:
                unit_counts[unit_name] += 1
            else:
                unit_counts[unit_name] = 1

        # Vérifier les limites
        for unit_name, count in unit_counts.items():
            if count > max_copies:
                return False
    return True

def check_unit_per_points(army_list, army_points, game_config):
    """Vérifie le nombre maximum d'unités par tranche de points"""
    if game_config.get("unit_per_points"):
        max_units = math.floor(army_points / game_config["unit_per_points"])
        return len(army_list) <= max_units
    return True

def validate_army_rules(army_list, army_points, game, new_unit_cost=None):
    """Valide toutes les règles spécifiques au jeu"""
    game_config = GAME_CONFIG.get(game, {})

    if game in GAME_CONFIG:
        # Vérification de la limite de points TOTALE (corrigée)
        if not check_army_points(army_list, army_points, game_config):
            st.error(f"Limite de points dépassée! Maximum autorisé: {army_points} pts")
            return False

        if not check_hero_limit(army_list, army_points, game_config):
            st.error(f"Limite de héros dépassée! Maximum autorisé: {math.floor(army_points / game_config['hero_limit'])} (1 héros par {game_config['hero_limit']} pts)")
            return False

        if not check_unit_copy_rule(army_list, army_points, game_config):
            x_value = math.floor(army_points / game_config["unit_copy_rule"])
            st.error(f"Trop de copies de la même unité! Maximum autorisé: {1 + x_value} (1+{x_value} pour {game_config['unit_copy_rule']} pts)")
            return False

        if not check_unit_max_cost(army_list, army_points, game_config, new_unit_cost):
            max_cost = army_points * game_config["unit_max_cost_ratio"]
            if new_unit_cost and new_unit_cost > max_cost:
                st.error(f"Cette unité ({new_unit_cost} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
            else:
                for unit in army_list:
                    if unit["cost"] > max_cost:
                        st.error(f"L'unité {unit['name']} ({unit['cost']} pts) dépasse la limite de {int(max_cost)} pts ({int(game_config['unit_max_cost_ratio']*100)}% du total)")
                        return False
            return False

        if not check_unit_per_points(army_list, army_points, game_config):
            max_units = math.floor(army_points / game_config["unit_per_points"])
            st.error(f"Trop d'unités! Maximum autorisé: {max_units} (1 unité par {game_config['unit_per_points']} pts)")
            return False

    return True

# ======================================================
# FONCTIONS UTILITAIRES
# ======================================================
def format_unit_option(u):
    """Formate l'affichage des unités dans la liste déroulante"""
    name_part = f"{u['name']}"

    # Pour les héros, toujours afficher [1]
    if u.get('type') == "hero":
        name_part += " [1]"
    else:
        # Pour les unités normales, afficher la taille de base
        base_size = u.get('size', 10)
        name_part += f" [{base_size}]"

    qua_def = f"Qua {u['quality']}+ / Déf {u.get('defense', '?')}"

    weapons_part = ""
    if 'weapons' in u and u['weapons']:
        weapon = u['weapons'][0]
        weapons_part = f"{weapon.get('name', 'Arme')} (A{weapon.get('attacks', '?')}, PA({weapon.get('armor_piercing', '?')}))"

    rules_part = ""
    if 'special_rules' in u and u['special_rules']:
        rules_part = ", ".join(u['special_rules'])

    result = f"{name_part} - {qua_def}"

    if weapons_part:
        result += f" - {weapons_part}"

    if rules_part:
        result += f" - {rules_part}"

    result += f" {u['base_cost']}pts"
    return result

# ======================================================
# LOCAL STORAGE
# ======================================================
def ls_get(key):
    """Récupère une valeur du LocalStorage"""
    try:
        unique_key = f"{key}_{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}"
        st.markdown(
            f"""
            <script>
            const value = localStorage.getItem("{key}");
            const input = document.createElement("input");
            input.type = "hidden";
            input.id = "{unique_key}";
            input.value = value || "";
            document.body.appendChild(input);
            </script>
            """,
            unsafe_allow_html=True
        )
        return st.text_input("", key=unique_key, label_visibility="collapsed")
    except Exception:
        return None

def ls_set(key, value):
    """Stocke une valeur dans le LocalStorage"""
    try:
        if not isinstance(value, str):
            value = json.dumps(value)
        escaped_value = value.replace("'", "\\'").replace('"', '\\"')
        st.markdown(
            f"""
            <script>
            localStorage.setItem("{key}", `{escaped_value}`);
            </script>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        pass

# ======================================================
# CHARGEMENT DES FACTIONS
# ======================================================
@st.cache_data
def load_factions():
    """Charge les factions depuis les fichiers JSON"""
    factions = {}
    games = set()

    # Création d'un fichier de faction par défaut si le dossier est vide
    if not list(FACTIONS_DIR.glob("*.json")):
        default_faction = {
            "game": "Age of Fantasy",
            "faction": "Disciples de la Guerre",
            "special_rules_descriptions": {
                "Éclaireur": "Cette unité peut se déplacer à travers les terrains difficiles sans pénalité et ignore les obstacles lors de ses déplacements.",
                "Furieux": "Cette unité relance les dés de 1 lors des tests d'attaque au corps à corps.",
                "Né pour la guerre": "Cette unité peut relancer un dé de 1 lors des tests de moral.",
                "Héros": "Cette unité est un personnage important qui peut inspirer les troupes autour de lui. Les héros ne peuvent pas être combinés.",
                "Coriace(1)": "Cette unité ignore 1 point de dégât par phase.",
                "Magique(1)": "Les armes de cette unité ignorent 1 point de défense grâce à leur nature magique.",
                "Contre-charge": "Cette unité obtient +1 à ses jets de dégât lors d'une charge."
            },
            "units": [
                {
                    "name": "Barbares de la Guerre",
                    "type": "unit",
                    "size": 10,
                    "base_cost": 50,
                    "quality": 3,
                    "defense": 5,
                    "special_rules": ["Éclaireur", "Furieux", "Né pour la guerre"],
                    "weapons": [{
                        "name": "Armes à une main",
                        "attacks": 1,
                        "armor_piercing": 0,
                        "special_rules": []
                    }]
                },
                {
                    "name": "Maître de la Guerre Élu",
                    "type": "hero",
                    "size": 1,
                    "base_cost": 150,
                    "quality": 3,
                    "defense": 5,
                    "special_rules": ["Héros", "Éclaireur", "Furieux"],
                    "weapons": [{
                        "name": "Arme héroïque",
                        "attacks": 2,
                        "armor_piercing": 1,
                        "special_rules": ["Magique(1)"]
                    }]
                }
            ]
        }
        with open(FACTIONS_DIR / "default.json", "w", encoding="utf-8") as f:
            json.dump(default_faction, f, indent=2)

    # Chargement des factions existantes
    for fp in FACTIONS_DIR.glob("*.json"):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
                game = data.get("game")
                faction = data.get("faction")
                if game and faction:
                    if game not in factions:
                        factions[game] = {}
                    factions[game][faction] = data
                    games.add(game)
        except Exception as e:
            st.warning(f"Erreur chargement {fp.name}: {e}")

    if not games:
        games = ["Age of Fantasy"]
        factions = {
            "Age of Fantasy": {
                "Disciples de la Guerre": {
                    "game": "Age of Fantasy",
                    "faction": "Disciples de la Guerre",
                    "special_rules_descriptions": {
                        "Éclaireur": "Cette unité peut se déplacer à travers les terrains difficiles sans pénalité et ignore les obstacles lors de ses déplacements.",
                        "Furieux": "Cette unité relance les dés de 1 lors des tests d'attaque au corps à corps.",
                        "Né pour la guerre": "Cette unité peut relancer un dé de 1 lors des tests de moral.",
                        "Héros": "Cette unité est un personnage important qui peut inspirer les troupes autour de lui. Les héros ne peuvent pas être combinés.",
                        "Coriace(1)": "Cette unité ignore 1 point de dégât par phase.",
                        "Magique(1)": "Les armes de cette unité ignorent 1 point de défense grâce à leur nature magique.",
                        "Contre-charge": "Cette unité obtient +1 à ses jets de dégât lors d'une charge."
                    },
                    "units": [
                        {
                            "name": "Barbares de la Guerre",
                            "type": "unit",
                            "size": 10,
                            "base_cost": 50,
                            "quality": 3,
                            "defense": 5,
                            "special_rules": ["Éclaireur", "Furieux", "Né pour la guerre"],
                            "weapons": [{
                                "name": "Armes à une main",
                                "attacks": 1,
                                "armor_piercing": 0,
                                "special_rules": []
                            }]
                        }
                    ]
                }
            }
        }

    return factions, sorted(games)

# ======================================================
# FONCTIONS D'AFFICHAGE AVEC ONGLETS
# ======================================================
def show_rules_legend(faction_data):
    """Affiche la légende des règles spéciales"""
    rules_descriptions = faction_data.get('special_rules_descriptions', {})

    with st.expander("📖 Légende des règles spéciales"):
        for rule, description in rules_descriptions.items():
            with st.expander(f"**{rule}**"):
                st.markdown(description)

def show_unit_with_tabs(unit, rules_descriptions):
    """Affiche une unité avec des onglets pour les descriptions des règles"""
    with st.expander(f"{unit['name']} [{unit.get('size', 10)}] ({unit['cost']} pts)"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Qualité:** {unit['quality']}+")
            st.markdown(f"**Défense:** {unit.get('defense', '?')}+")

            if 'rules' in unit and unit['rules']:
                st.markdown("**Règles spéciales:**")
                for rule in unit['rules']:
                    with st.expander(f"📖 {rule}"):
                        description = rules_descriptions.get(rule, "Description non disponible")
                        st.markdown(description)

        with col2:
            if 'weapon' in unit and unit['weapon']:
                weapon = unit['weapon']
                st.markdown(f"**Arme:** {weapon.get('name', 'Arme non nommée')}")
                st.markdown(f"ATK: {weapon.get('attacks', '?')}, PA: {weapon.get('armor_piercing', '?')}")

                if 'special_rules' in weapon and weapon['special_rules']:
                    st.markdown("**Règles spéciales de l'arme:**")
                    for rule in weapon['special_rules']:
                        with st.expander(f"📖 {rule}"):
                            description = rules_descriptions.get(rule, "Description non disponible")
                            st.markdown(description)

# ======================================================
# INITIALISATION
# ======================================================
try:
    factions_by_game, games = load_factions()
except Exception as e:
    st.error(f"Erreur de chargement des factions: {str(e)}")
    factions_by_game = {
        "Age of Fantasy": {
            "Disciples de la Guerre": {
                "game": "Age of Fantasy",
                "faction": "Disciples de la Guerre",
                "special_rules_descriptions": {
                    "Éclaireur": "Cette unité peut se déplacer à travers les terrains difficiles sans pénalité et ignore les obstacles lors de ses déplacements.",
                    "Furieux": "Cette unité relance les dés de 1 lors des tests d'attaque au corps à corps.",
                    "Né pour la guerre": "Cette unité peut relancer un dé de 1 lors des tests de moral.",
                    "Héros": "Cette unité est un personnage important qui peut inspirer les troupes autour de lui. Les héros ne peuvent pas être combinés.",
                    "Coriace(1)": "Cette unité ignore 1 point de dégât par phase.",
                    "Magique(1)": "Les armes de cette unité ignorent 1 point de défense grâce à leur nature magique.",
                    "Contre-charge": "Cette unité obtient +1 à ses jets de dégât lors d'une charge."
                },
                "units": [
                    {
                        "name": "Barbares de la Guerre",
                        "type": "unit",
                        "size": 10,
                        "base_cost": 50,
                        "quality": 3,
                        "defense": 5,
                        "special_rules": ["Éclaireur", "Furieux", "Né pour la guerre"],
                        "weapons": [{
                            "name": "Armes à une main",
                            "attacks": 1,
                            "armor_piercing": 0,
                            "special_rules": []
                        }]
                    }
                ]
            }
        }
    }
    games = ["Age of Fantasy"]

if "page" not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.army_list = []
    st.session_state.army_cost = 0

# ======================================================
# PAGE 1 – CONFIGURATION (corrigée)
# ======================================================
if st.session_state.page == "setup":
    st.title("OPR Army Forge FR")

    # Affichage des informations sur les jeux disponibles
    st.subheader("Jeux disponibles")
    for game_key, config in GAME_CONFIG.items():
        with st.expander(f"📖 {config['display_name']}"):
            st.markdown(f"""
            **Description**: {config['description']}
            - **Points**: {config['min_points']} à {config['max_points']} (défaut: {config['default_points']})
            - **Règles spécifiques**:
              - 1 Héros par tranche de {config['hero_limit']} pts
              - 1+X copies de la même unité (X=1 pour {config['unit_copy_rule']} pts)
              - Aucune unité ne peut valoir plus de {int(config['unit_max_cost_ratio']*100)}% du total des points
              - 1 unité maximum par tranche de {config['unit_per_points']} pts
            """)

    # Liste des listes sauvegardées
    st.subheader("Mes listes sauvegardées")

    # Chargement des listes sauvegardées
    saved_lists = ls_get("opr_saved_lists")
    if saved_lists:
        try:
            saved_lists = json.loads(saved_lists)
            if isinstance(saved_lists, list):
                for i, saved_list in enumerate(saved_lists):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{saved_list.get('name', 'Liste sans nom')}**")
                        st.caption(f"{saved_list.get('game', 'Inconnu')} • {saved_list.get('faction', 'Inconnue')} • {saved_list.get('total_cost', 0)}/{saved_list.get('points', 0)} pts")
                    with col2:
                        if st.button(f"Charger", key=f"load_{i}"):
                            st.session_state.game = saved_list["game"]
                            st.session_state.faction = saved_list["faction"]
                            st.session_state.points = saved_list["points"]
                            st.session_state.list_name = saved_list["name"]
                            st.session_state.army_list = saved_list["army_list"]
                            st.session_state.army_cost = saved_list["total_cost"]
                            st.session_state.units = factions_by_game[saved_list["game"]][saved_list["faction"]]["units"]
                            st.session_state.page = "army"
                            st.rerun()
        except Exception as e:
            st.error(f"Erreur chargement listes: {e}")

    if not games:
        st.error("Aucun jeu trouvé")
        st.stop()

    # Sélection du jeu
    game = st.selectbox("Jeu", games)
    game_config = GAME_CONFIG.get(game, GAME_CONFIG["Age of Fantasy"])

    # Sélection des points avec validation
    points = st.number_input(
        "Points",
        min_value=game_config["min_points"],
        max_value=game_config["max_points"],
        value=game_config["default_points"],
        step=game_config["point_step"]
    )

    # Stockage des points dans la session pour utilisation ultérieure
    st.session_state.selected_points = points

    list_name = st.text_input("Nom de la liste", f"Liste_{datetime.now().strftime('%Y%m%d')}")

    # Import JSON
    uploaded = st.file_uploader("Importer une liste JSON", type=["json"])
    if uploaded:
        try:
            data = json.load(uploaded)
            if not all(key in data for key in ["game", "faction", "army_list", "points"]):
                st.error("Format JSON invalide: les clés 'game', 'faction', 'army_list' et 'points' sont requises")
                st.stop()

            # Vérification que les points de la liste importée ne dépassent pas la limite
            total_cost = data.get("total_cost", sum(u["cost"] for u in data["army_list"]))
            if total_cost > data["points"]:
                st.error(f"La liste importée dépasse sa limite de points ({data['points']} pts). Total actuel: {total_cost} pts")
                st.stop()

            st.session_state.game = data["game"]
            st.session_state.faction = data["faction"]
            st.session_state.points = data["points"]
            st.session_state.list_name = data["name"]
            st.session_state.army_list = data["army_list"]
            st.session_state.army_cost = total_cost
            st.session_state.units = factions_by_game[data["game"]][data["faction"]]["units"]
            st.session_state.page = "army"
            st.rerun()
        except Exception as e:
            st.error(f"Erreur d'import: {str(e)}")

    if st.button("Créer une nouvelle liste"):
        st.session_state.game = game
        st.session_state.faction = st.selectbox("Faction", list(factions_by_game[game].keys()))
        st.session_state.points = points  # Utilisation des points sélectionnés
        st.session_state.list_name = list_name
        st.session_state.units = factions_by_game[game][st.session_state.faction]["units"]
        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.session_state.page = "army"
        st.rerun()

# ======================================================
# PAGE 2 – CONSTRUCTEUR D'ARMÉE (corrigée)
# ======================================================
elif st.session_state.page == "army":
    st.title(st.session_state.list_name)
    st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_cost}/{st.session_state.points} pts")

    # Affichage de la progression des points
    progress = st.session_state.army_cost / st.session_state.points
    st.progress(progress)
    st.markdown(f"**Points utilisés:** {st.session_state.army_cost}/{st.session_state.points} pts")

    # Charger les données de faction pour les descriptions des règles
    faction_data = factions_by_game[st.session_state.game][st.session_state.faction]
    rules_descriptions = faction_data.get('special_rules_descriptions', {})

    # Afficher la légende des règles spéciales
    show_rules_legend(faction_data)

    if st.button("⬅ Retour"):
        st.session_state.page = "setup"
        st.rerun()

    # Ajout d'une unité
    st.divider()
    st.subheader("Ajouter une unité")

    # Sélection de l'unité
    unit = st.selectbox(
        "Unité disponible",
        st.session_state.units,
        format_func=format_unit_option,
        index=0,
        key="unit_select"
    )

    # Récupération des données de base
    base_size = unit.get('size', 10)
    base_cost = unit["base_cost"]

    # Vérification du coût maximum AVANT les améliorations
    max_cost = st.session_state.points * GAME_CONFIG[st.session_state.game]["unit_max_cost_ratio"]
    if base_cost > max_cost:
        st.error(f"Cette unité ({base_cost} pts) dépasse la limite de {int(max_cost)} pts ({int(GAME_CONFIG[st.session_state.game]['unit_max_cost_ratio']*100)}% du total)")
        st.stop()

    # Gestion des unités combinées
    if unit.get("type") == "hero":
        combined = False  # Les héros ne peuvent JAMAIS être combinés
        st.markdown("**Les héros ne peuvent pas être combinés**")
    else:
        combined = st.checkbox("Unité combinée", value=False)

    # Calcul du coût final
    if combined and unit.get("type") != "hero":
        final_cost = base_cost * 2  # On double le coût de base pour les unités combinées
        unit_size = base_size * 2
    else:
        final_cost = base_cost
        unit_size = base_size

    # Vérification que l'ajout de cette unité ne dépasse pas la limite de points
    if st.session_state.army_cost + final_cost > st.session_state.points:
        st.error(f"Ajouter cette unité dépasserait votre limite de {st.session_state.points} pts. Il vous reste {st.session_state.points - st.session_state.army_cost} pts.")
        st.stop()

    st.markdown(f"**Coût total: {final_cost} pts**")
    st.markdown(f"**Taille de l'unité: {unit_size} figurines**")

    if st.button("Ajouter à l'armée"):
        try:
            # Vérification finale avant ajout
            test_army = st.session_state.army_list.copy()
            test_army.append({
                "name": unit["name"],
                "type": unit.get("type", "unit"),
                "cost": final_cost,
                "size": unit_size,
            })

            test_total = st.session_state.army_cost + final_cost

            if not validate_army_rules(test_army, st.session_state.points, st.session_state.game, final_cost):
                st.stop()  # Les erreurs sont déjà affichées par validate_army_rules

            # Si tout est valide, on ajoute l'unité
            unit_data = {
                "name": unit["name"],
                "type": unit.get("type", "unit"),
                "cost": final_cost,
                "base_cost": base_cost,
                "size": unit_size,
                "quality": unit["quality"],
                "defense": unit.get("defense", 3),
                "rules": unit.get("special_rules", []),
                "weapon": unit.get("weapons", [{}])[0],
                "combined": combined and unit.get("type") != "hero",
            }

            st.session_state.army_list.append(unit_data)
            st.session_state.army_cost += final_cost
            st.rerun()

        except Exception as e:
            st.error(f"Erreur lors de la création de l'unité: {str(e)}")

    # Liste de l'armée
    st.divider()
    st.subheader("Liste de l'armée")

    if not st.session_state.army_list:
        st.info("Ajoutez des unités pour commencer")

    for i, u in enumerate(st.session_state.army_list):
        show_unit_with_tabs(u, rules_descriptions)

        if st.button(f"Supprimer {u['name']}", key=f"del_{i}"):
            st.session_state.army_cost -= u["cost"]
            st.session_state.army_list.pop(i)
            st.rerun()

    # Sauvegarde/Export
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
        if st.button("Sauvegarder"):
            saved_lists = []
            try:
                existing_lists = ls_get("opr_saved_lists")
                if existing_lists:
                    saved_lists = json.loads(existing_lists)
            except:
                pass

            saved_lists.append(army_data)
            try:
                ls_set("opr_saved_lists", saved_lists)
            except:
                st.warning("La sauvegarde locale n'est pas disponible, mais vous pouvez exporter en JSON.")
            st.success("Liste sauvegardée!")

    with col2:
        st.download_button(
            "Exporter en JSON",
            json.dumps(army_data, indent=2, ensure_ascii=False),
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json"
        )

    with col3:
        # EXPORT HTML avec descriptions des règles
        html_content = generate_html_export(army_data, rules_descriptions)
        st.download_button(
            "Exporter en HTML",
            html_content,
            file_name=f"{st.session_state.list_name}.html",
            mime="text/html"
        )

def generate_html_export(army_data, rules_descriptions):
    """Génère le contenu HTML pour l'export avec descriptions des règles"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Liste OPR - {army_data['name']}</title>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            .army-title {{
                text-align: center;
                margin-bottom: 20px;
                color: #2c3e50;
            }}
            .army-info {{
                text-align: center;
                margin-bottom: 30px;
                color: #666;
            }}
            .unit-container {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                padding: 20px;
                page-break-inside: avoid;
            }}
            .unit-header {{
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 10px;
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .hero-badge {{
                background-color: gold;
                color: black;
                padding: 2px 8px;
                border-radius: 10px;
                margin-left: 10px;
                font-weight: bold;
                font-size: 0.9em;
            }}
            .unit-stats {{
                display: flex;
                margin-bottom: 15px;
            }}
            .stat-badge {{
                background-color: #3498db;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                margin-right: 10px;
                font-weight: bold;
                text-align: center;
                min-width: 80px;
            }}
            .stat-value {{
                font-size: 1.2em;
            }}
            .stat-label {{
                font-size: 0.8em;
                display: block;
                margin-bottom: 3px;
            }}
            .section-title {{
                font-weight: bold;
                margin: 15px 0 10px 0;
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }}
            .weapon-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            .weapon-table th {{
                background-color: #f8f9fa;
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }}
            .weapon-table td {{
                padding: 8px;
                border-bottom: 1px solid #eee;
            }}
            .rules-list {{
                margin: 10px 0;
            }}
            .special-rules {{
                font-style: italic;
                color: #555;
                margin-bottom: 15px;
            }}
            .rule-item {{
                margin-bottom: 8px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }}
            .rule-description {{
                margin-left: 10px;
                font-size: 0.9em;
                color: #666;
            }}
            .unit-cost {{
                float: right;
                background-color: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }}
            .progress-container {{
                width: 100%;
                background-color: #e0e0e0;
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            .progress-bar {{
                height: 20px;
                background-color: #4CAF50;
                border-radius: 4px;
                text-align: center;
                line-height: 20px;
                color: white;
            }}
            @media print {{
                .unit-container {{
                    page-break-inside: avoid;
                }}
            }}
        </style>
    </head>
    <body>
        <h1 class="army-title">Liste d'armée OPR - {army_data['name']}</h1>
        <div class="army-info">
            <strong>Jeu:</strong> {army_data['game']} |
            <strong>Faction:</strong> {army_data['faction']} |
            <strong>Points:</strong> {army_data['total_cost']}/{army_data['points']} pts
        </div>

        <div class="progress-container">
            <div class="progress-bar" style="width: {int((army_data['total_cost']/army_data['points'])*100)}%">
                {int((army_data['total_cost']/army_data['points'])*100)}% ({army_data['total_cost']}/{army_data['points']} pts)
            </div>
        </div>

        <div class="section-title">Légende des règles spéciales</div>
        <div class="rules-legend">
    """

    # Ajouter une légende des règles spéciales utilisées dans cette armée
    used_rules = set()
    for unit in army_data['army_list']:
        if 'rules' in unit:
            used_rules.update(unit['rules'])
        if 'weapon' in unit and 'special_rules' in unit['weapon']:
            used_rules.update(unit['weapon']['special_rules'])

    # Ajouter les règles spéciales utilisées dans cette armée
    if used_rules:
        html_content += "<ul>"
        for rule in sorted(used_rules):
            description = rules_descriptions.get(rule, "Description non disponible")
            html_content += f"<li><strong>{rule}:</strong> {description}</li>"
        html_content += "</ul>"
    else:
        html_content += "<p>Aucune règle spéciale dans cette armée.</p>"

    html_content += """
        </div>
    """

    for unit in army_data['army_list']:
        rules = unit.get('rules', [])
        special_rules = ", ".join(rules) if rules else "Aucune"

        weapon_info = unit.get('weapon', {})
        if not isinstance(weapon_info, dict):
            weapon_info = {
                "name": "Arme non spécifiée",
                "attacks": "?",
                "ap": "?",
                "special": []
            }

        unit_name = f"{unit['name']} [{unit.get('size', 10)}]"
        unit_name = str(unit_name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        weapon_name = str(weapon_info.get('name', 'Arme non spécifiée')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        weapon_attacks = str(weapon_info.get('attacks', '?')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        weapon_ap = str(weapon_info.get('armor_piercing', '?')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        weapon_special = ', '.join(weapon_info.get('special_rules', [])) if weapon_info.get('special_rules') else '-'
        weapon_special = str(weapon_special).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        hero_badge = ""
        if unit.get('type') == "hero":
            hero_badge = '<span class="hero-badge">HÉROS</span>'

        html_content += f"""
        <div class="unit-container">
            <div class="unit-header">
                {unit_name}
                {hero_badge}
                <span class="unit-cost">{unit['cost']} pts</span>
            </div>

            <div class="unit-stats">
                <div class="stat-badge">
                    <div class="stat-label">Qualité</div>
                    <div class="stat-value">{unit['quality']}+</div>
                </div>
                <div class="stat-badge">
                    <div class="stat-label">Défense</div>
                    <div class="stat-value">{unit.get('defense', '?')}+</div>
                </div>
        """

        if 'coriace' in unit and unit.get('coriace'):
            html_content += f"""
                <div class="stat-badge">
                    <div class="stat-label">Coriace</div>
                    <div class="stat-value">{unit['coriace']}</div>
                </div>
            """

        html_content += """
            </div>
        """

        if rules:
            html_content += '<div class="section-title">Règles spéciales</div>'
            for rule in rules:
                description = rules_descriptions.get(rule, "Description non disponible")
                html_content += f"""
                <div class="rule-item">
                    <strong>{rule}:</strong>
                    <div class="rule-description">{description}</div>
                </div>
                """

        html_content += f"""
            <div class="section-title">Arme</div>
            <table class="weapon-table">
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>ATK</th>
                        <th>PA</th>
                        <th>Règles spéciales</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{weapon_name}</td>
                        <td>{weapon_attacks}</td>
                        <td>{weapon_ap}</td>
                        <td>{weapon_special}</td>
                    </tr>
                </tbody>
            </table>
        """

        if weapon_special and weapon_special != '-':
            html_content += '<div class="section-title">Règles spéciales de l\'arme</div>'
            for rule in weapon_info.get('special_rules', []):
                description = rules_descriptions.get(rule, "Description non disponible")
                html_content += f"""
                <div class="rule-item">
                    <strong>{rule}:</strong>
                    <div class="rule-description">{description}</div>
                </div>
                """

        html_content += "</div>"

    html_content += """
    </body>
    </html>
    """
    return html_content
