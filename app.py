import json
import re
from pathlib import Path
from collections import defaultdict
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import os
import hashlib
import base64

# ======================
# Configuration
# ======================
st.set_page_config(
    page_title="OPR Army Builder FR",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================
# Gestion du LocalStorage (version optimisée)
# ======================

def generate_unique_key(base_key):
    """Génère une clé unique pour éviter les conflits"""
    return f"{base_key}_{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]}"

def localstorage_get(key):
    """Récupère une valeur du LocalStorage avec gestion d'erreur"""
    try:
        unique_key = generate_unique_key(f"localstorage_value_{key}")
        get_js = f"""
        <script>
        const value = localStorage.getItem('{key}');
        const input = document.createElement('input');
        input.style.display = 'none';
        input.id = '{unique_key}';
        input.value = value || 'null';
        document.body.appendChild(input);
        </script>
        """
        components.html(get_js, height=0)
        value = st.text_input(f"localstorage_value_{key}", key=unique_key, label_visibility="collapsed")
        return None if value == "null" else value
    except Exception as e:
        st.error(f"Erreur LocalStorage: {e}")
        return None

def localstorage_set(key, value):
    """Stocke une valeur dans le LocalStorage avec échappement"""
    try:
        if not isinstance(value, str):
            value_str = json.dumps(value)
        else:
            value_str = value

        escaped_value = value_str.replace("'", "\\'").replace('"', '\\"').replace("`", "\\`")
        set_js = f"""
        <script>
        localStorage.setItem('{key}', `{escaped_value}`);
        </script>
        """
        components.html(set_js, height=0)
    except Exception as e:
        st.error(f"Erreur LocalStorage: {e}")

def load_army_lists(player_name="Simon"):
    """Charge les listes d'armées avec vérification complète"""
    try:
        data = localstorage_get(f"army_lists_{player_name}")
        if data:
            try:
                loaded_data = json.loads(data)
                if isinstance(loaded_data, dict) and "army_lists" in loaded_data:
                    return loaded_data["army_lists"]
                elif isinstance(loaded_data, list):
                    return loaded_data
            except json.JSONDecodeError:
                st.error("Données corrompues. Réinitialisation...")
                localstorage_set(f"army_lists_{player_name}", [])
        return []
    except Exception as e:
        st.error(f"Erreur chargement: {e}")
        return []

def save_army_list(army_list_data, player_name="Simon"):
    """Sauvegarde une liste avec validation complète"""
    try:
        current_lists = load_army_lists(player_name) or []

        # Si c'est un export complet (avec army_lists)
        if isinstance(army_list_data, dict) and "army_lists" in army_list_data:
            current_lists = army_list_data["army_lists"]
        # Si c'est une liste directe
        elif isinstance(army_list_data, list):
            current_lists = army_list_data
        # Si c'est une seule liste à ajouter
        elif isinstance(army_list_data, dict):
            current_lists.append(army_list_data)

        localstorage_set(f"army_lists_{player_name}", {"army_lists": current_lists, "date": datetime.now().isoformat()})
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde: {e}")
        return False

def delete_army_list(player_name, list_index):
    """Supprime une liste avec vérification"""
    try:
        current_lists = load_army_lists(player_name)
        if current_lists and 0 <= list_index < len(current_lists):
            current_lists.pop(list_index)
            localstorage_set(f"army_lists_{player_name}", {"army_lists": current_lists, "date": datetime.now().isoformat()})
            return True
        return False
    except Exception as e:
        st.error(f"Erreur suppression: {e}")
        return False

# ======================
# Fonctions d'export/import (version corrigée)
# ======================

def format_special_rule(rule):
    """Formate les règles spéciales avec parenthèses"""
    if not isinstance(rule, str):
        return str(rule)
    if "(" in rule and ")" in rule:
        return rule
    match = re.search(r"(\D+)(\d+)", rule)
    if match:
        return f"{match.group(1)}({match.group(2)})"
    return rule

def generate_html(army_data):
    """Génère le HTML pour une liste d'armée"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Liste OPR - {army_data['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
            .unit-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; background: #f9f9f9; }}
            .weapons-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            .weapons-table td:first-child {{ text-align: left; }}
        </style>
    </head>
    <body>
        <h1>Liste d'armée OPR - {army_data['name']}</h1>
        <h2>{army_data['game']} • {army_data['faction']} • {army_data['total_cost']}/{army_data['points']} pts</h2>
    """

    for unit in army_data['army_list']:
        coriace = calculate_total_coriace(unit)
        html_content += f"""
        <div class="unit-card">
            <h3>{unit['name']} [{len(unit.get('models', ['10']))}] [{unit['cost']} pts]</h3>
            <div>Qua: {unit['quality']}+ • Déf: {unit['defense']}+{f' • Coriace: {coriace}' if coriace else ''}</div>
        """

        if 'base_rules' in unit:
            rules = [format_special_rule(r) for r in unit['base_rules']]
            html_content += f"<p><strong>Règles spéciales:</strong> {', '.join(rules)}</p>"

        if 'current_weapon' in unit:
            weapon = unit['current_weapon']
            html_content += """
            <p><strong>Armes:</strong></p>
            <table class="weapons-table">
                <tr>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                </tr>
                <tr>
                    <th>Nom</th>
                    <th>RNG</th>
                    <th>ATK</th>
                    <th>AP</th>
                    <th>SPE</th>
                </tr>
            </table>
            """.format(
                weapon.get('name', 'Arme de base'),
                weapon.get('range', '-'),
                weapon.get('attacks', '?'),
                weapon.get('armor_piercing', '?'),
                ', '.join(weapon.get('special_rules', [])) or '-'
            )

        if 'options' in unit:
            html_content += "<p><strong>Améliorations:</strong></p><ul>"
            for opts in unit['options'].values():
                if isinstance(opts, list):
                    for opt in opts:
                        html_content += f"<li>{format_special_rule(opt.get('name', ''))}</li>"
                elif isinstance(opts, dict):
                    html_content += f"<li>{format_special_rule(opts.get('name', ''))}</li>"
            html_content += "</ul>"

        html_content += "</div>"
    html_content += "</body></html>"
    return html_content

def auto_export(army_data, filename_prefix):
    """Exporte automatiquement HTML et JSON"""
    try:
        html_content = generate_html(army_data)
        html_filename = f"{filename_prefix}.html"

        json_data = {
            "name": army_data['name'],
            "game": army_data['game'],
            "faction": army_data['faction'],
            "points": army_data['points'],
            "army_list": army_data['army_list'],
            "total_cost": army_data['total_cost'],
            "date": datetime.now().isoformat()
        }
        json_filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.json"
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📄 Télécharger HTML", html_content, html_filename, "text/html")
        with col2:
            st.download_button("📁 Télécharger JSON", json_str, json_filename, "application/json")
    except Exception as e:
        st.error(f"Erreur export: {e}")

def import_data():
    """Import de données avec gestion complète des formats"""
    uploaded_file = st.file_uploader("📥 Importer un fichier JSON", type=["json"])

    if uploaded_file:
        try:
            file_content = uploaded_file.read().decode("utf-8")
            imported_data = json.loads(file_content)

            # Format 1: Export complet avec army_lists
            if isinstance(imported_data, dict) and "army_lists" in imported_data:
                if save_army_list(imported_data, st.session_state.current_player):
                    st.session_state.player_army_lists = imported_data["army_lists"]
                    st.success("✅ Fichier importé avec succès!")
                    st.rerun()

            # Format 2: Liste directe d'armées
            elif isinstance(imported_data, list):
                data_to_save = {
                    "player_name": st.session_state.current_player,
                    "army_lists": imported_data,
                    "date": datetime.now().isoformat()
                }
                if save_army_list(data_to_save, st.session_state.current_player):
                    st.session_state.player_army_lists = imported_data
                    st.success("✅ Liste importée avec succès!")
                    st.rerun()

            # Format 3: Liste individuelle
            elif isinstance(imported_data, dict) and all(k in imported_data for k in ["name", "army_list"]):
                current_lists = load_army_lists(st.session_state.current_player) or []
                current_lists.append(imported_data)
                data_to_save = {
                    "player_name": st.session_state.current_player,
                    "army_lists": current_lists,
                    "date": datetime.now().isoformat()
                }
                if save_army_list(data_to_save, st.session_state.current_player):
                    st.session_state.player_army_lists = current_lists
                    st.success("✅ Liste importée avec succès!")
                    st.rerun()

            else:
                st.error("Format JSON non reconnu")

        except json.JSONDecodeError:
            st.error("❌ Fichier JSON corrompu")
        except Exception as e:
            st.error(f"Erreur import: {e}")

# ======================
# Calculs et validations
# ======================

def extract_coriace(rules):
    """Extrait la valeur de Coriace"""
    if not isinstance(rules, list):
        return 0
    total = 0
    for rule in rules:
        if isinstance(rule, str):
            match = re.search(r"Coriace\s*\(?(\d+)\)?", rule)
            if match and int(match.group(1)) > 0:
                total += int(match.group(1))
    return total

def calculate_total_coriace(unit):
    """Calcule la Coriace totale"""
    total = 0
    if 'base_rules' in unit:
        total += extract_coriace(unit['base_rules'])
    if 'options' in unit:
        for opts in unit['options'].values():
            if isinstance(opts, list):
                for opt in opts:
                    if isinstance(opt, dict) and 'special_rules' in opt:
                        total += extract_coriace(opt['special_rules'])
            elif isinstance(opts, dict) and 'special_rules' in opts:
                total += extract_coriace(opts['special_rules'])
    if 'mount' in unit and isinstance(unit['mount'], dict):
        if 'special_rules' in unit['mount']:
            total += extract_coriace(unit['mount']['special_rules'])
    if 'current_weapon' in unit and isinstance(unit['current_weapon'], dict):
        if 'special_rules' in unit['current_weapon']:
            total += extract_coriace(unit['current_weapon']['special_rules'])
    return total if total > 0 else None

def validate_army(army_list, game_rules, total_cost, total_points):
    """Valide une liste d'armée"""
    errors = []
    if not army_list:
        errors.append("Aucune unité dans l'armée")
    if total_cost > total_points:
        errors.append(f"Dépassement de {total_cost - total_points} pts")
    return len(errors) == 0, errors

# ======================
# Application principale
# ======================

def main():
    # Initialisation
    if "page" not in st.session_state:
        st.session_state.page = "login"
        st.session_state.current_player = "Simon"
        st.session_state.player_army_lists = []

    # Chemins des données
    BASE_DIR = Path(__file__).resolve().parent
    FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"
    FACTIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Règles des jeux
    GAME_RULES = {
        "Age of Fantasy": {
            "hero_per_points": 375,
            "unit_copies": {750: 1},
            "max_unit_percentage": 35,
            "unit_per_points": 150,
        }
    }

    @st.cache_data
    def load_factions():
        """Charge les factions depuis les fichiers JSON"""
        factions = {}
        games = set()
        if not FACTIONS_DIR.exists():
            st.error(f"Dossier {FACTIONS_DIR} introuvable!")
            return {}, []

        for fp in FACTIONS_DIR.glob("*.json"):
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                    if "game" in data and "faction" in data:
                        game = data["game"]
                        faction = data["faction"]
                        if game not in factions:
                            factions[game] = {}
                        factions[game][faction] = data
                        games.add(game)
            except Exception as e:
                st.warning(f"Erreur chargement {fp.name}: {e}")

        return factions, sorted(games)

    # Charger les factions
    if "factions" not in st.session_state or "games" not in st.session_state:
        st.session_state.factions, st.session_state.games = load_factions()

    # PAGE 1: Accueil
    if st.session_state.page == "login":
        st.title("OPR Army Builder 🇫🇷")
        st.subheader(f"Bienvenue, Simon!")

        player_name = st.text_input("Pseudo", value=st.session_state.current_player)

        if st.button("Commencer"):
            st.session_state.current_player = player_name
            st.session_state.player_army_lists = load_army_lists(player_name)
            st.session_state.page = "setup"
            st.rerun()

    # PAGE 2: Configuration
    elif st.session_state.page == "setup":
        st.title("OPR Army Builder 🇫🇷")
        st.subheader(f"Bienvenue, {st.session_state.current_player}!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Changer de pseudo"):
                st.session_state.page = "login"
                st.rerun()

        with col2:
            if st.button("💾 Exporter toutes mes listes"):
                all_lists = load_army_lists(st.session_state.current_player)
                if not all_lists:
                    st.warning("Aucune liste à exporter")
                else:
                    data = {
                        "player_name": st.session_state.current_player,
                        "army_lists": all_lists,
                        "date": datetime.now().isoformat()
                    }
                    filename = f"OPR_All_Lists_{st.session_state.current_player}.json"
                    st.download_button(
                        label="Télécharger JSON",
                        data=json.dumps(data, indent=2, ensure_ascii=False),
                        file_name=filename,
                        mime="application/json"
                    )

        # Import de fichiers
        import_data()

        st.info("""
        💡 **Sauvegarde automatique**:
        Vos listes sont enregistrées dans votre navigateur.
        Pour les transférer:
        1. Exportez-les (bouton ci-dessus)
        2. Envoyez le fichier par e-mail/cloud
        3. Importez-le sur un autre appareil
        """)

        # Listes sauvegardées
        st.subheader("Mes listes sauvegardées")
        st.session_state.player_army_lists = load_army_lists(st.session_state.current_player)

        if st.session_state.player_army_lists:
            for i, army in enumerate(st.session_state.player_army_lists):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    with st.expander(f"{army.get('name', 'Liste sans nom')} ({army.get('total_cost', 0)}/{army.get('points', 0)} pts)"):
                        st.write(f"**Jeu**: {army.get('game', 'Inconnu')}")
                        st.write(f"**Faction**: {army.get('faction', 'Inconnue')}")
                        st.write(f"**Date**: {army.get('date', 'Inconnue')[:10] if isinstance(army.get('date'), str) else 'Inconnue'}")

                        if st.button(f"Charger cette liste", key=f"load_{i}"):
                            try:
                                if (army.get('game') in st.session_state.factions and
                                    army.get('faction') in st.session_state.factions[army.get('game')]):

                                    st.session_state.game = army.get('game')
                                    st.session_state.faction = army.get('faction')
                                    st.session_state.points = army.get('points')
                                    st.session_state.list_name = army.get('name')
                                    st.session_state.army_total_cost = army.get('total_cost')
                                    st.session_state.army_list = army.get('army_list', [])
                                    st.session_state.units = st.session_state.factions[army.get('game')][army.get('faction')]['units']
                                    st.session_state.page = "army"
                                    st.rerun()
                                else:
                                    st.error("Faction introuvable")
                            except Exception as e:
                                st.error(f"Erreur chargement: {e}")

                with col2:
                    if st.button(f"Exporter", key=f"export_{i}"):
                        auto_export(army, army.get('name', 'liste'))

                with col3:
                    if st.button(f"❌ Supprimer", key=f"delete_{i}"):
                        if delete_army_list(st.session_state.current_player, i):
                            st.session_state.player_army_lists = load_army_lists(st.session_state.current_player)
                            st.rerun()
        else:
            st.info("Aucune liste sauvegardée")

        # Création nouvelle liste
        st.divider()
        st.subheader("Créer une nouvelle liste")

        if not st.session_state.games:
            st.error("Aucun jeu disponible. Vérifiez le dossier 'lists/data/factions/'")
        else:
            game = st.selectbox("Jeu", st.session_state.games)
            factions = list(st.session_state.factions[game].keys()) if game in st.session_state.factions else []
            faction = st.selectbox("Faction", factions) if factions else None

            points = st.number_input("Points", min_value=250, max_value=5000, value=1000, step=250)
            list_name = st.text_input("Nom de la liste", value=f"Liste_{datetime.now().strftime('%Y%m%d')}")

            if st.button("Créer la liste") and game and faction:
                st.session_state.game = game
                st.session_state.faction = faction
                st.session_state.points = points
                st.session_state.list_name = list_name
                st.session_state.army_list = []
                st.session_state.army_total_cost = 0
                st.session_state.units = st.session_state.factions[game][faction]['units']
                st.session_state.page = "army"
                st.rerun()

    # PAGE 3: Composition de l'armée
    elif st.session_state.page == "army":
        st.title(st.session_state.list_name)
        st.caption(f"{st.session_state.game} • {st.session_state.faction} • {st.session_state.army_total_cost}/{st.session_state.points} pts")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅ Retour"):
                st.session_state.page = "setup"
                st.rerun()
        with col2:
            if st.button("🚪 Quitter"):
                st.session_state.page = "login"
                st.rerun()

        # Ajout d'une unité
        st.divider()
        st.subheader("Ajouter une unité")

        unit = st.selectbox(
            "Unité disponible",
            st.session_state.units,
            format_func=lambda u: f"{u['name']} ({u['base_cost']} pts)"
        )

        st.markdown(f"**{unit['name']}** - {unit['base_cost']} pts")
        col1, col2 = st.columns(2)
        col1.metric("Qua", f"{unit['quality']}+")
        col2.metric("Déf", f"{unit['defense']}+")

        combined = False
        if unit.get('type', '').lower() != 'hero':
            combined = st.checkbox("Unité combinée (+100% coût)", value=False)

        cost = unit["base_cost"] * 2 if combined else unit["base_cost"]
        base_rules = unit.get('special_rules', [])
        current_weapon = unit.get('weapons', [{}])[0].copy()
        selected_options = {}
        mount = None

        for group in unit.get("upgrade_groups", []):
            st.subheader(group["group"])

            if group.get("type") == "multiple":
                for opt in group.get("options", []):
                    opt_cost = opt["cost"] * (2 if combined else 1)
                    if st.checkbox(f"{opt['name']} (+{opt_cost} pts)", key=f"{unit['name']}_{group['group']}_{opt['name']}"):
                        if group["group"] not in selected_options:
                            selected_options[group["group"]] = []
                        selected_options[group["group"]].append(opt)
                        cost += opt_cost

            elif group.get("type") == "weapon":
                weapon_options = ["Arme de base"]
                for opt in group.get("options", []):
                    opt_cost = opt.get("cost", 0) * (2 if combined else 1)
                    weapon_options.append(f"{opt['name']} (+{opt_cost} pts)")

                selected = st.radio("Choisir une arme", weapon_options, key=f"{unit['name']}_weapon")
                if selected != "Arme de base":
                    opt_name = selected.split(" (+")[0]
                    opt = next(o for o in group["options"] if o["name"] == opt_name)
                    cost += opt.get("cost", 0) * (2 if combined else 1)
                    current_weapon = opt.get("weapon", {})

            elif group.get("type") == "mount":
                mount_options = ["Aucune monture"]
                for opt in group.get("options", []):
                    mount_options.append(f"{opt['name']} (+{opt.get('cost', 0)} pts)")

                selected = st.radio("Choisir une monture", mount_options, key=f"{unit['name']}_mount")
                if selected != "Aucune monture":
                    opt_name = selected.split(" (+")[0]
                    opt = next(o for o in group["options"] if o["name"] == opt_name)
                    cost += opt.get("cost", 0)
                    mount = opt.get("mount")

        st.markdown(f"**Coût total: {cost} pts**")

        if st.button("Ajouter à l'armée"):
            unit_data = {
                'name': unit['name'],
                'cost': cost,
                'quality': unit['quality'],
                'defense': unit['defense'],
                'type': unit.get('type', 'Infantry'),
                'base_rules': [format_special_rule(r) for r in base_rules],
                'current_weapon': current_weapon,
                'options': selected_options,
                'combined': combined,
                'models': ['10']
            }

            if mount:
                unit_data['mount'] = mount

            st.session_state.army_list.append(unit_data)
            st.session_state.army_total_cost += cost
            st.rerun()

        # Affichage de l'armée
        st.divider()
        st.subheader("Liste de l'armée")

        if not st.session_state.army_list:
            st.info("Ajoutez des unités pour commencer")

        for i, unit in enumerate(st.session_state.army_list):
            with st.container():
                coriace = calculate_total_coriace(unit)
                st.markdown(f"### {unit['name']} [{len(unit.get('models', ['10']))}] [{unit['cost']} pts]")

                stats_col1, stats_col2, stats_col3 = st.columns(3)
                stats_col1.metric("Qua", f"{unit['quality']}+")
                stats_col2.metric("Déf", f"{unit['defense']}+")
                if coriace:
                    stats_col3.metric("Coriace", coriace)

                if 'base_rules' in unit and unit['base_rules']:
                    st.markdown("**Règles spéciales**")
                    st.caption(", ".join(unit['base_rules']))

                if 'current_weapon' in unit:
                    weapon = unit['current_weapon']
                    st.markdown("**Armes**")
                    st.table({
                        "Nom": [weapon.get('name', 'Arme de base')],
                        "Por": [weapon.get('range', '-')],
                        "Att": [weapon.get('attacks', '?')],
                        "PA": [weapon.get('armor_piercing', '?')],
                        "Spé": [', '.join(weapon.get('special_rules', [])) or '-']
                    })

                if 'options' in unit and unit['options']:
                    st.markdown("**Améliorations**")
                    for opts in unit['options'].values():
                        if isinstance(opts, list):
                            for opt in opts:
                                st.caption(f"• {opt.get('name', '')}")
                        elif isinstance(opts, dict):
                            st.caption(f"• {opts.get('name', '')}")

                if st.button(f"Supprimer", key=f"del_{i}"):
                    st.session_state.army_total_cost -= unit['cost']
                    st.session_state.army_list.pop(i)
                    st.rerun()

        # Validation et boutons
        st.divider()
        game_rules = GAME_RULES.get(st.session_state.game, {})
        is_valid, errors = validate_army(
            st.session_state.army_list,
            game_rules,
            st.session_state.army_total_cost,
            st.session_state.points
        )

        progress = min(1.0, st.session_state.army_total_cost / st.session_state.points) if st.session_state.points else 0
        st.progress(progress)
        st.markdown(f"**{st.session_state.army_total_cost}/{st.session_state.points} pts**")

        if not is_valid:
            st.warning("Problèmes avec la liste:")
            for error in errors:
                st.error(f"- {error}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Sauvegarder"):
                if not st.session_state.list_name:
                    st.warning("Donnez un nom à votre liste")
                else:
                    army_data = {
                        "name": st.session_state.list_name,
                        "game": st.session_state.game,
                        "faction": st.session_state.faction,
                        "points": st.session_state.points,
                        "army_list": st.session_state.army_list,
                        "total_cost": st.session_state.army_total_cost,
                        "date": datetime.now().isoformat()
                    }
                    if save_army_list(army_data, st.session_state.current_player):
                        st.session_state.player_army_lists = load_army_lists(st.session_state.current_player)
                        st.success("Liste sauvegardée!")
                    else:
                        st.error("Erreur de sauvegarde")

        with col2:
            if st.button("Exporter"):
                army_data = {
                    "name": st.session_state.list_name,
                    "game": st.session_state.game,
                    "faction": st.session_state.faction,
                    "points": st.session_state.points,
                    "army_list": st.session_state.army_list,
                    "total_cost": st.session_state.army_total_cost,
                    "date": datetime.now().isoformat()
                }
                auto_export(army_data, st.session_state.list_name)

        with col3:
            if st.button("Réinitialiser"):
                st.session_state.army_list = []
                st.session_state.army_total_cost = 0
                st.rerun()

if __name__ == "__main__":
    main()
