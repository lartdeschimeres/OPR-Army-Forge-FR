import json
import copy
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import sys, os
import math
import base64
import zlib
import urllib.parse

# ==============================================================================
# CONFIGURATION GÉNÉRALE & STYLES
# ==============================================================================

st.set_page_config(page_title="OPR ArmyBuilder FR", layout="wide", initial_sidebar_state="auto")

APP_URL = "https://armybuilder-fra.streamlit.app/"

_GAME_COLORS = {
    "Age of Fantasy":            "#2980b9",
    "Age of Fantasy Regiments":  "#8e44ad",
    "Grimdark Future":           "#c0392b",
    "Grimdark Future Firefight": "#e67e22",
    "Age of Fantasy Skirmish":   "#27ae60",
}
_acc_color = _GAME_COLORS.get(st.session_state.get("game",""), "#2980b9")

st.markdown(f"""<style>
:root {{--acc: {_acc_color};}}
#MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{background: transparent;}}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  color-scheme: light !important;
  background-color: #e9ecef !important;
  color: #212529 !important;
}}
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div, section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  background-color: #dee2e6 !important;
  color: #212529 !important;
  border-right: 1px solid #adb5bd;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
}}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] strong, section[data-testid="stSidebar"] .stMarkdown {{
  color: #212529 !important;
}}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{
  color: #202c45 !important;
}}
section[data-testid="stSidebar"] .stButton > button {{
  background-color: #f8f9fa !important;
  color: #212529 !important;
  border: 1px solid #ced4da !important;
}}
[data-testid="stMain"], [data-testid="stMainBlockContainer"] {{
  background-color: #e9ecef !important;
  color: #212529 !important;
}}
h1, h2, h3 {{color: #202c45; letter-spacing: 0.04em; font-weight: 600;}}
.stSelectbox, .stNumberInput, .stTextInput {{background-color: white; border-radius: 6px; border: 1px solid #ced4da;}}
button[kind="primary"] {{background: var(--acc) !important; color: white !important; font-weight: bold; border-radius: 6px;}}
.badge {{display: inline-block; padding: 0.35rem 0.75rem; border-radius: 4px; background: var(--acc); color: white; font-size: clamp(0.7rem,2vw,0.8rem); margin-bottom: 0.75rem; font-weight: 600;}}
.stButton>button {{background-color: #f8f9fa; border: 1px solid #ced4da; border-radius: 6px; padding: 0.5rem 1rem; color: #212529; font-weight: 500; min-height: 44px;}}
.stProgress > div > div > div {{background-color: var(--acc) !important;}}
.section-header {{font-size:clamp(10px,2.5vw,11px); font-weight:700; text-transform:uppercase; letter-spacing:.1em; color: var(--acc); margin: 16px 0 6px; padding: 4px 8px; background: rgba(0,0,0,.03); border-left: 3px solid var(--acc); border-radius: 0 4px 4px 0;}}
@media (max-width: 640px) {{
  .stApp {{font-size: 14px;}}
  [data-testid="column"] {{width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important;}}
  .stButton>button {{width: 100%; min-height: 48px; font-size: 15px;}}
  section[data-testid="stSidebar"] {{box-shadow: none;}}
}}
</style>""", unsafe_allow_html=True)

# ==============================================================================
# FONCTIONS UTILITAIRES & EXPORT
# ==============================================================================

@st.cache_data
def export_faction_html(data):
    def esc(t):
        if t is None: return ""
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    faction = data.get("faction","Faction")
    game    = data.get("game","")
    version = data.get("version","")
    desc    = data.get("description","")
    history = data.get("history","")

    def fmt_r(r):
        s = str(r) if r is not None else "-"
        return s if s in ("Mêlée","-") else f'{s}"'

    def weapon_rows(weapons):
        if not weapons: return ""
        bw = weapons if isinstance(weapons, list) else [weapons]
        rows = ""
        for w in bw:
            if not isinstance(w, dict): continue
            cnt  = w.get("count","")
            cn   = f"{cnt}x " if cnt and cnt > 1 else ""
            rng  = fmt_r(w.get("range"))
            att  = w.get("attacks","-")
            pa   = w.get("armor_piercing",0) or "-"
            sr   = ", ".join(w.get("special_rules",[])) or "-"
            rows += (f"<tr><td class='wn'><b>{esc(cn+w.get('name',''))}</b></td>"
                     f"<td>{esc(rng)}</td><td>A{att}</td><td>{pa}</td>"
                     f"<td class='ws'>{esc(sr)}</td></tr>\n")
        return rows

    def unit_card(u):
        name   = esc(u["name"])
        cost   = u.get("base_cost","?")
        size   = u.get("size",1)
        qual   = u.get("quality","?")
        defe   = u.get("defense","?")
        cor    = u.get("coriace","")
        sr     = ", ".join(u.get("special_rules",[]))
        named  = u.get("unit_detail") == "named_hero" or "Unique" in u.get("special_rules",[])
        star   = "★ " if named else ""
        cor_s  = f" | Coriace {cor}" if cor else ""
        html   = f"""<div class='uc'>
<div class='uh'><span><b>{star}{name} [{size}]</b></span><span class='uc-cost'>{cost} pts</span></div>
<div class='us'>Qual {qual}+&nbsp;|&nbsp;Déf {defe}+{esc(cor_s)}</div>"""
        if sr: html += f"<div class='ur'>{esc(sr)}</div>"
        wr = weapon_rows(u.get("weapon",[]))
        if wr:
            html += """<table class='wt'><thead><tr>
<th>Arme</th><th>Portée</th><th>Att</th><th>PA</th><th>Règles spé.</th>
</tr></thead><tbody>""" + wr + "</tbody></table>"
        for g in u.get("upgrade_groups",[]):
            gtype = g.get("type","")
            desc_g = esc(g.get("description",""))
            req   = g.get("requires",[])
            req_s = f" <i>[{esc(', '.join(req))}]</i>" if req else ""
            html += f"<div class='og'><b>{desc_g}</b>{req_s}</div>"
            for o in g.get("options",[]):
                oname = esc(o.get("name",""))
                ocost = o.get("cost",0)
                cost_s = f"+{ocost} pts" if ocost > 0 else "Gratuit"
                osr   = ", ".join(o.get("special_rules",[]))
                html += f"<div class='ol'>{oname} <span class='oc'>{esc(cost_s)}</span></div>"
                if osr: html += f"<div style='font-size:0.8em;color:#666;padding-left:12px;'>{esc(osr)}</div>"
        html += "</div>"
        return html

    CATS = [
        ("Héros", ["hero"]),
        ("Unités de base", ["unit"]),
        ("Véhicules légers", ["light_vehicle"]),
        ("Véhicules", ["vehicle"]),
        ("Titans", ["titan"]),
    ]

    rules = data.get("faction_special_rules",[])
    spells = data.get("spells",{})
    
    # Simplification pour l'export HTML
    rules_html = ""
    for r in rules:
        rules_html += f"<div><b>{r.get('name')}</b>: {r.get('description')}</div>"
    
    spells_html = ""
    for sname, sdata in spells.items():
        sdesc = sdata.get("description", sdata) if isinstance(sdata, dict) else sdata
        spells_html += f"<div><b>{sname}</b>: {sdesc}</div>"

    units_html = ""
    for cat_name, types in CATS:
        cat_units = [u for u in data["units"] if u.get("unit_detail", u.get("type")) in types]
        if not cat_units: continue
        cards = "".join(unit_card(u) for u in cat_units)
        units_html += f"<h3>{cat_name}</h3>{cards}"

    css = """
    body{font-family:sans-serif;margin:20px;background:#fff;color:#333;}
    h1,h2,h3{color:#2c3e50;}
    .uc{border:1px solid #ddd;padding:10px;margin:10px 0;border-radius:5px;}
    .uh{background:#f8f9fa;padding:5px;font-weight:bold;display:flex;justify-content:space-between;}
    .wt{width:100%;border-collapse:collapse;font-size:0.9em;}
    .wt th,.wt td{border:1px solid #eee;padding:4px;text-align:left;}
    .wt th{background:#f1f1f1;}
    """

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head>
    <body>
    <h1>{faction} ({game})</h1>
    <p>{desc}</p>
    <h2>Règles</h2>{rules_html}
    <h2>Sorts</h2>{spells_html}
    <h2>Unités</h2>{units_html}
    </body></html>"""

def export_html(army_list, army_name, army_limit):
    def esc(txt):
        if txt is None: return ""
        return str(txt).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    def fmt_range(rng):
        if rng in (None, "-", "mêlée", "Mêlée") or str(rng).lower() == "mêlée": return "-"
        if isinstance(rng, (int, float)): return f'{int(rng)}"'
        return str(rng)

    total_cost = sum(u.get("cost",0) for u in army_list)
    
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>{esc(army_name)}</title>
    <style>
        body{{font-family:sans-serif;margin:20px;}}
        .unit{{border:1px solid #ccc;padding:15px;margin-bottom:15px;border-radius:8px;}}
        .header{{display:flex;justify-content:space-between;background:#f0f0f0;padding:10px;border-radius:5px;margin-bottom:10px;}}
        .name{{font-weight:bold;font-size:1.2em;}}
        .cost{{font-weight:bold;color:#d9534f;}}
        table{{width:100%;border-collapse:collapse;margin-top:10px;}}
        th,td{{border:1px solid #ddd;padding:8px;text-align:left;}}
        th{{background:#f9f9f9;}}
    </style></head><body>
    <h1>{esc(army_name)} ({total_cost}/{army_limit} pts)</h1>
    """
    
    for unit in army_list:
        weapons = unit.get("weapon", [])
        if isinstance(weapons, dict): weapons = [weapons]
        
        w_rows = ""
        for w in weapons:
            if not isinstance(w, dict): continue
            cnt = w.get("_count", w.get("count", 1))
            name = f"{cnt}x {w.get('name', '?')}" if cnt > 1 else w.get('name', '?')
            rng = fmt_range(w.get("range"))
            att = w.get("attacks", "-")
            pa = w.get("armor_piercing", "-")
            sr = ", ".join(w.get("special_rules", []))
            w_rows += f"<tr><td>{esc(name)}</td><td>{rng}</td><td>{att}</td><td>{pa}</td><td>{esc(sr)}</td></tr>"
        
        sr_list = ", ".join(unit.get("special_rules", []))
        
        html += f"""
        <div class="unit">
            <div class="header">
                <span class="name">{esc(unit['name'])} (x{unit.get('size',1)})</span>
                <span class="cost">{unit.get('cost',0)} pts</span>
            </div>
            <div><b>Règles:</b> {esc(sr_list)}</div>
            <table>
                <thead><tr><th>Arme</th><th>Portée</th><th>Att</th><th>PA</th><th>Règles</th></tr></thead>
                <tbody>{w_rows}</tbody>
            </table>
        </div>
        """
    
    # QR Code simple
    try:
        import qrcode
        import io
        data_str = json.dumps({"list": army_name, "cost": total_cost})
        qr = qrcode.make(data_str)
        buf = io.BytesIO()
        qr.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        html += f'<div style="text-align:center;margin-top:20px;"><img src="data:image/png;base64,{b64}" alt="QR"></div>'
    except:
        pass
        
    html += "</body></html>"
    return html

# ==============================================================================
# GESTION DE L'ÉTAT (SESSION STATE)
# ==============================================================================

if "page" not in st.session_state: st.session_state.page = "setup"
if "army_list" not in st.session_state: st.session_state.army_list = []
if "army_cost" not in st.session_state: st.session_state.army_cost = 0
if "unit_selections" not in st.session_state: st.session_state.unit_selections = {}
if "draft_counter" not in st.session_state: st.session_state.draft_counter = 0
if "draft_unit_name" not in st.session_state: st.session_state.draft_unit_name = ""
if "faction_data" not in st.session_state: st.session_state.faction_data = None

# Gestion QR Code au chargement
if not st.session_state.get("_qr_loaded"):
    st.session_state["_qr_loaded"] = True
    try:
        _qp = st.query_params.get("list", "")
        if _qp:
            _raw = zlib.decompress(base64.urlsafe_b64decode(urllib.parse.unquote(_qp).encode() + b"=="))
            _data = json.loads(_raw.decode())
            if _data.get("game"): st.session_state["game"] = _data["game"]
            if _data.get("faction"): st.session_state["faction"] = _data["faction"]
            if _data.get("pts"): st.session_state["points"] = _data["pts"]
            if _data.get("army_list"):
                st.session_state["_qr_army_list"] = _data["army_list"]
                st.session_state["_qr_army_cost"] = _data.get("army_cost", 0)
            st.session_state["_qr_pending"] = True
            st.query_params.clear()
            st.rerun()
    except Exception:
        pass

GAME_CONFIG = {
    "Grimdark Future": {"min_points": 500, "max_points": 20000, "default_points": 2000, "hero_limit": 500, "unit_copy_rule": 1000, "unit_max_cost_ratio": 0.4, "unit_per_points": 200},
    "Grimdark Future Firefight": {"min_points": 150, "max_points": 1000, "default_points": 300, "hero_limit": 300, "unit_copy_rule": 300, "unit_max_cost_ratio": 0.6, "unit_per_points": 100},
}

def validate_army_rules(army_list, army_points, game):
    cfg = GAME_CONFIG.get(game, {"hero_limit": 500, "unit_max_cost_ratio": 0.4, "unit_copy_rule": 1000})
    max_heroes = math.floor(army_points / cfg["hero_limit"])
    hero_count = sum(1 for u in army_list if u.get("type") == "hero")
    if hero_count > max_heroes:
        st.error(f"Trop de héros ({hero_count}/{max_heroes})")
        return False
    
    max_cost = army_points * cfg["unit_max_cost_ratio"]
    for u in army_list:
        if u["cost"] > max_cost:
            st.error(f"Unité trop chère: {u['name']} ({u['cost']} > {int(max_cost)})")
            return False
            
    return True

def check_weapon_conditions(unit_key, requires, unit=None):
    if not requires: return True
    # Logique simplifiée pour la vérification des prérequis
    selections = st.session_state.unit_selections.get(unit_key, {})
    # On vérifie si les armes requises sont dans les sélections ou l'unité de base
    # (Implémentation simplifiée pour la démo)
    return True 

# ==============================================================================
# CHARGEMENT DES DONNÉES
# ==============================================================================

@st.cache_data
def load_factions():
    factions = {}
    try:
        # Simulation de chargement depuis le fichier JSON fourni par l'utilisateur
        # Dans un cas réel, utilisez Path(__file__).parent / "data" / "factions"
        json_str = st.session_state.get("_json_content", "")
        if json_str:
            data = json.loads(json_str)
            game = data.get("game")
            faction = data.get("faction")
            if game and faction:
                factions[game] = {faction: data}
        else:
            # Fallback: chercher dans le dossier local si existant
            p = Path("freres_de_bataille_gf.txt")
            if p.exists():
                # Le fichier fourni est un JSON dans un txt, on le parse
                content = p.read_text()
                # Extraire le JSON entre les accolades si nécessaire
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != -1:
                    data = json.loads(content[start:end])
                    game = data.get("game")
                    faction = data.get("faction")
                    if game and faction:
                        factions[game] = {faction: data}
    except Exception as e:
        st.error(f"Erreur chargement: {e}")
    return factions, list(factions.keys())

# ==============================================================================
# PAGE 1: CONFIGURATION
# ==============================================================================

if st.session_state.page == "setup":
    factions_by_game, games = load_factions()
    
    if not games:
        st.warning("Aucune faction trouvée. Assurez-vous que le fichier JSON est présent.")
        # Pour tester, on permet de uploader un fichier
        uploaded = st.file_uploader("Uploader un fichier de faction (.json/.txt)", type=["json", "txt"])
        if uploaded:
            content = uploaded.getvalue().decode("utf-8")
            st.session_state["_json_content"] = content
            st.rerun()
        st.stop()

    current_game = st.session_state.get("game", games[0])
    
    st.title("OPR ArmyBuilder FRA")
    st.subheader("Configuration de l'armée")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        game = st.selectbox("Jeu", games, index=games.index(current_game) if current_game in games else 0)
    with col2:
        faction_options = list(factions_by_game.get(game, {}).keys())
        faction = st.selectbox("Faction", faction_options)
    with col3:
        gc = GAME_CONFIG.get(game, {"default_points": 2000})
        points = st.number_input("Points", min_value=500, max_value=5000, value=gc.get("default_points", 2000), step=250)

    list_name = st.text_input("Nom de la liste", value=f"{faction} {points}pts")
    
    if st.button("🔥 Construire l'armée", type="primary"):
        st.session_state.game = game
        st.session_state.faction = faction
        st.session_state.points = points
        st.session_state.list_name = list_name
        
        fd = factions_by_game[game][faction]
        st.session_state.units = fd.get("units", [])
        st.session_state.faction_special_rules = fd.get("faction_special_rules", [])
        st.session_state.faction_spells = fd.get("spells", {})
        st.session_state.faction_data = fd
        
        # Reset Army si changement de faction
        if st.session_state.get("faction") != faction:
            st.session_state.army_list = []
            st.session_state.army_cost = 0
            st.session_state.unit_selections = {}
            
        # Injection QR si pending
        if st.session_state.get("_qr_pending"):
            st.session_state.army_list = st.session_state.pop("_qr_army_list", [])
            st.session_state.army_cost = st.session_state.pop("_qr_army_cost", 0)
            st.session_state["_qr_pending"] = False

        st.session_state.page = "army"
        st.rerun()

# ==============================================================================
# PAGE 2: CONSTRUCTION (ARMY)
# ==============================================================================

elif st.session_state.page == "army":
    if not st.session_state.get("units"):
        st.error("Données manquantes. Retournez à l'accueil.")
        st.stop()

    st.title(f"{st.session_state.list_name}")
    st.caption(f"{st.session_state.game} - {st.session_state.faction}")
    
    # Sidebar Résumé
    with st.sidebar:
        st.metric("Points", f"{st.session_state.army_cost} / {st.session_state.points}")
        st.progress(min(st.session_state.army_cost / st.session_state.points, 1.0))
        if st.button("⬅️ Retour"):
            st.session_state.page = "setup"
            st.rerun()
        
        st.divider()
        st.subheader("Export")
        json_data = json.dumps({
            "game": st.session_state.game,
            "faction": st.session_state.faction,
            "points": st.session_state.points,
            "list_name": st.session_state.list_name,
            "army_list": st.session_state.army_list,
            "army_cost": st.session_state.army_cost
        }, indent=2)
        st.download_button("📄 JSON", json_data, "armee.json")
        
        html_data = export_html(st.session_state.army_list, st.session_state.list_name, st.session_state.points)
        st.download_button("🌐 HTML", html_data, "armee.html")

    st.divider()
    
    # Affichage de l'armée actuelle
    if st.session_state.army_list:
        st.subheader("Armée en cours")
        for i, u in enumerate(st.session_state.army_list):
            with st.expander(f"{u['name']} - {u['cost']} pts"):
                st.write(f"Taille: {u.get('size')} | Qualité: {u.get('quality')}")
                st.write(f"Règles: {', '.join(u.get('special_rules', []))}")
                if st.button("Supprimer", key=f"del_{i}"):
                    st.session_state.army_cost -= u['cost']
                    st.session_state.army_list.pop(i)
                    st.rerun()
        st.divider()

    # SÉLECTION D'UNE NOUVELLE UNITÉ
    st.subheader("Ajouter une unité")
    
    # Filtres
    filter_type = st.selectbox("Filtrer par type", ["Tous", "hero", "unit", "vehicle", "titan"])
    available_units = st.session_state.units
    if filter_type != "Tous":
        available_units = [u for u in available_units if u.get("unit_detail") == filter_type or u.get("type") == filter_type]
    
    unit_names = [f"{u['name']} ({u.get('base_cost')} pts)" for u in available_units]
    selected_name = st.selectbox("Unité", unit_names)
    
    if not selected_name: st.stop()
    
    # Récupérer l'objet unité complet
    unit = next((u for u in available_units if f"{u['name']} ({u.get('base_cost')} pts)" == selected_name), None)
    if not unit: st.stop()

    # --------------------------------------------------------------------------
    # LOGIQUE DE CONFIGURATION D'UNITÉ (CORRIGÉE)
    # --------------------------------------------------------------------------
    
    unit_key = f"draft_{st.session_state.draft_counter}"
    if unit_key not in st.session_state.unit_selections:
        st.session_state.unit_selections[unit_key] = {}
    
    selections = st.session_state.unit_selections[unit_key]
    
    # Copie profonde des armes de base
    base_weapons = unit.get("weapon", [])
    if isinstance(base_weapons, dict): base_weapons = [base_weapons]
    current_weapons = copy.deepcopy(base_weapons)
    
    weapon_cost = 0
    upgrades_cost_unique = 0
    upgrades_cost_multi = 0
    mount_cost = 0
    mount_data = None
    selected_options_details = {}

    # Gestion Unité Combinée
    multiplier = 1
    if unit.get("type") != "hero" and unit.get("size", 1) > 1:
        if st.checkbox("⚔️ Unité Combinée (x2)", key=f"{unit_key}_combined"):
            multiplier = 2
    
    effective_size = unit.get("size", 1) * multiplier

    upgrade_groups = unit.get("upgrade_groups", [])
    
    # BOUCLE PRINCIPALE D'AFFICHAGE ET DE COLLECTE
    for g_idx, group in enumerate(upgrade_groups):
        g_key = f"g{g_idx}"
        gtype = group.get("type", "")
        g_name = group.get("group", "Options")
        
        st.markdown(f"#### {g_name}")
        if group.get("description"):
            st.caption(group.get("description"))

        options = group.get("options", [])
        
        # --- CAS 1: REMPLACEMENT TOTAL (Weapon) ---
        if gtype == "weapon":
            choices_map = {}
            default_name = "Armes de base"
            choices_map[default_name] = {"cost": 0, "weapons": copy.deepcopy(current_weapons), "replaces": []}
            
            for opt in options:
                w_list = opt.get("weapon", [])
                if isinstance(w_list, dict): w_list = [w_list]
                names = [w.get("name", "?") for w in w_list]
                label = f"{', '.join(names)} (+{opt.get('cost', 0)} pts)"
                choices_map[label] = {
                    "cost": opt.get("cost", 0),
                    "weapons": copy.deepcopy(w_list),
                    "replaces": opt.get("replaces", [])
                }
            
            choice_labels = list(choices_map.keys())
            current_sel = selections.get(f"{g_key}_sel", choice_labels[0])
            if current_sel not in choice_labels: current_sel = choice_labels[0]
            
            selected_label = st.radio("Choix de l'armement", choice_labels, index=choice_labels.index(current_sel), key=f"{g_key}_radio", horizontal=True)
            selections[f"{g_key}_sel"] = selected_label
            
            data = choices_map[selected_label]
            weapon_cost += data["cost"]
            current_weapons = data["weapons"]
            for w in current_weapons:
                if isinstance(w, dict): w["_is_base"] = False

        # --- CAS 2: CONDITIONNEL (Conditional Weapon) ---
        elif gtype == "conditional_weapon":
            valid_opts = []
            for opt in options:
                # Vérification simplifiée des prérequis
                reqs = opt.get("requires", [])
                ok = True
                # On vérifie si l'arme requise est dans current_weapons
                for r in reqs:
                    if not any(isinstance(w, dict) and w.get("name") == r for w in current_weapons):
                        ok = False
                        break
                if ok: valid_opts.append(opt)
            
            if not valid_opts:
                st.info("Aucune amélioration disponible.")
                continue

            choices_map = {"Aucune": {"cost": 0, "weapon": None, "replaces": []}}
            for opt in valid_opts:
                w = opt.get("weapon")
                if w:
                    lbl = f"{opt.get('name', 'Arme')} (+{opt.get('cost',0)} pts)"
                else:
                    lbl = f"{opt.get('name', 'Option')} (+{opt.get('cost',0)} pts)"
                choices_map[lbl] = {
                    "cost": opt.get("cost", 0),
                    "weapon": copy.deepcopy(w) if w else None,
                    "replaces": opt.get("replaces", []),
                    "is_unique": True
                }
            
            choice_labels = list(choices_map.keys())
            current_sel = selections.get(f"{g_key}_sel", choice_labels[0])
            if current_sel not in choice_labels: current_sel = choice_labels[0]
            
            selected_label = st.radio("Amélioration", choice_labels, index=choice_labels.index(current_sel), key=f"{g_key}_cond")
            selections[f"{g_key}_sel"] = selected_label
            
            if selected_label != "Aucune":
                data = choices_map[selected_label]
                if data["is_unique"]: upgrades_cost_unique += data["cost"]
                else: upgrades_cost_multi += data["cost"]
                
                # Application immédiate pour conditionnel (simple)
                for rep_name in data["replaces"]:
                    new_w_list = []
                    found = False
                    for w in current_weapons:
                        if not found and isinstance(w, dict) and w.get("name") == rep_name:
                            if w.get("_count", 1) > 1:
                                wc = w.copy()
                                wc["_count"] -= 1
                                new_w_list.append(wc)
                            found = True
                        else:
                            new_w_list.append(w)
                    current_weapons = new_w_list
                
                if data["weapon"]:
                    if isinstance(data["weapon"], dict): data["weapon"] = [data["weapon"]]
                    for w in data["weapon"]:
                        w["_count"] = 1
                        current_weapons.append(w)

        # --- CAS 3: NOMBRE VARIABLE (Variable Weapon Count) ---
        # C'est ici que se joue la logique des Éclaireurs et Vétérans
        elif gtype == "variable_weapon_count":
            for o_idx, opt in enumerate(options):
                opt_name = opt.get("name", "Option")
                opt_cost = opt.get("cost", 0)
                replaces_list = opt.get("replaces", [])
                
                # Calcul du MAX dynamique basé sur l'état ACTUEL de current_weapons
                mc_cfg = opt.get("max_count", {})
                mc_type = mc_cfg.get("type", "size_based") if isinstance(mc_cfg, dict) else "size_based"
                limit = 0
                
                if mc_type == "fixed":
                    limit = mc_cfg.get("value", 0)
                elif mc_type == "count_in_weapons":
                    target = mc_cfg.get("weapon_name", "")
                    count_in_list = 0
                    for w in current_weapons:
                        if isinstance(w, dict) and w.get("name") == target:
                            count_in_list += w.get("_count", w.get("count", 1))
                    limit = count_in_list
                else:
                    limit = effective_size
                
                min_val = opt.get("min_count", 0)
                if limit < min_val: limit = min_val
                
                slider_key = f"{g_key}_var_{o_idx}"
                current_val = selections.get(slider_key, min_val)
                if current_val > limit:
                    current_val = limit
                    selections[slider_key] = current_val
                
                label = f"{opt_name} (Max: {limit})"
                new_val = st.number_input(label, min_value=min_val, max_value=limit, value=current_val, step=1, key=slider_key)
                selections[slider_key] = new_val
                
                if new_val > 0:
                    if "_pending_changes" not in selections: selections["_pending_changes"] = []
                    selections["_pending_changes"].append({
                        "type": "variable",
                        "count": new_val,
                        "cost": opt_cost,
                        "replaces": replaces_list,
                        "new_weapon": copy.deepcopy(opt.get("weapon"))
                    })

        # --- CAS 4: RÔLES / UPGRADES SIMPLES ---
        elif gtype in ["role", "upgrades"]:
            is_multi = (gtype == "upgrades" and "toutes" in group.get("description", "").lower())
            
            if gtype == "role":
                choices = ["Aucun"]
                mapping = {}
                for o in options:
                    lbl = f"{o['name']} (+{o.get('cost',0)})"
                    choices.append(lbl)
                    mapping[lbl] = o
                
                sel = st.radio("Rôle", choices, index=0, key=f"{g_key}_role", horizontal=True)
                selections[f"{g_key}_role"] = sel
                if sel != "Aucun":
                    o = mapping[sel]
                    if is_multi: upgrades_cost_multi += o.get("cost", 0)
                    else: upgrades_cost_unique += o.get("cost", 0)
                    selected_options_details.setdefault("Rôle", []).append(o)
            
            elif gtype == "upgrades":
                for o_idx, o in enumerate(options):
                    lbl = f"{o['name']} (+{o['cost']})"
                    key_chk = f"{g_key}_chk_{o_idx}"
                    is_checked = st.checkbox(lbl, value=selections.get(key_chk, False), key=key_chk)
                    selections[key_chk] = is_checked
                    if is_checked:
                        if is_multi: upgrades_cost_multi += o["cost"]
                        else: upgrades_cost_unique += o["cost"]
                        selected_options_details.setdefault("Options", []).append(o)

        # --- CAS 5: MONTURE / MOBILITÉ ---
        elif gtype == "mobility":
            choices = ["Aucune"]
            mapping = {}
            for o in options:
                lbl = f"{o.get('name', 'Mobilité')} (+{o.get('cost',0)})"
                choices.append(lbl)
                mapping[lbl] = o
            sel = st.radio("Mobilité", choices, index=0, key=f"{g_key}_mob")
            selections[f"{g_key}_mob"] = sel
            if sel != "Aucune":
                o = mapping[sel]
                mount_cost = o.get("cost", 0)
                mount_data = {
                    "name": o.get("name"),
                    "cost": mount_cost,
                    "mount": {
                        "weapon": o.get("weapon", []) if isinstance(o.get("weapon"), list) else [o.get("weapon")],
                        "special_rules": o.get("special_rules", []),
                        "coriace_bonus": o.get("coriace_bonus", 0)
                    }
                }
        
        elif gtype == "mount":
            choices = ["Aucune"]
            mapping = {}
            for o in options:
                lbl = f"{o.get('name', 'Monture')} (+{o.get('cost',0)})"
                choices.append(lbl)
                mapping[lbl] = o
            sel = st.radio("Monture", choices, index=0, key=f"{g_key}_mou")
            selections[f"{g_key}_mou"] = sel
            if sel != "Aucune":
                o = mapping[sel]
                mount_data = o
                mount_cost = o.get("cost", 0)

    # --------------------------------------------------------------------------
    # APPLICATION DES CHANGEMENTS VARIABLES (POST-TRAITEMENT)
    # --------------------------------------------------------------------------
    if "_pending_changes" in selections:
        for change in selections["_pending_changes"]:
            count = change["count"]
            if count == 0: continue
            
            cost_total = count * change["cost"]
            upgrades_cost_multi += cost_total
            
            replaces_list = change["replaces"]
            remaining = count
            new_weapons_list = []
            
            # Retirer les anciennes armes
            for w in current_weapons:
                if remaining <= 0:
                    new_weapons_list.append(w)
                    continue
                
                if isinstance(w, dict) and w.get("name") in replaces_list:
                    w_count = w.get("_count", w.get("count", 1))
                    if w_count > remaining:
                        wc = w.copy()
                        if "_count" in w: wc["_count"] -= remaining
                        elif "count" in w: wc["count"] -= remaining
                        new_weapons_list.append(wc)
                        remaining = 0
                    else:
                        remaining -= w_count
                else:
                    new_weapons_list.append(w)
            
            current_weapons = new_weapons_list
            
            # Ajouter les nouvelles armes
            new_w = change["new_weapon"]
            if isinstance(new_w, dict): new_w = [new_w]
            for w in new_w:
                wc = copy.deepcopy(w)
                wc["_count"] = count
                wc["_upgraded"] = True
                current_weapons.append(wc)
    
    if "_pending_changes" in selections: del selections["_pending_changes"]

    # --------------------------------------------------------------------------
    # FINALISATION ET AJOUT
    # --------------------------------------------------------------------------
    final_cost = (unit.get("base_cost", 0) + weapon_cost + upgrades_cost_multi) * multiplier + upgrades_cost_unique + mount_cost
    
    st.divider()
    st.metric("Coût total de l'unité", f"{final_cost} pts")
    
    if st.button("➕ Ajouter à l'armée", type="primary", use_container_width=True, key=f"{unit_key}_add"):
        if st.session_state.army_cost + final_cost > st.session_state.points:
            st.error(f"Dépassement de points ! ({st.session_state.army_cost + final_cost} / {st.session_state.points})")
        else:
            final_sr = list(unit.get("special_rules", []))
            for cat, opts in selected_options_details.items():
                for o in opts: final_sr.extend(o.get("special_rules", []))
            if mount_data:
                msr = mount_data.get("mount", {}).get("special_rules", [])
                final_sr.extend([r for r in msr if "Coriace" not in r])
            
            new_unit = {
                "name": unit["name"],
                "type": unit.get("type", "unit"),
                "unit_detail": unit.get("unit_detail", unit.get("type", "unit")),
                "cost": final_cost,
                "size": unit.get("size", 1) * multiplier if unit.get("type") != "hero" else 1,
                "quality": unit.get("quality"),
                "defense": unit.get("defense"),
                "coriace": unit.get("coriace", 0) + (mount_data.get("mount", {}).get("coriace_bonus", 0) if mount_data else 0),
                "weapon": current_weapons,
                "options": selected_options_details,
                "mount": mount_data,
                "special_rules": list(set(final_sr))
            }
            
            if validate_army_rules(st.session_state.army_list + [new_unit], st.session_state.points, st.session_state.game):
                st.session_state.army_list.append(new_unit)
                st.session_state.army_cost += final_cost
                st.session_state.draft_counter += 1
                st.rerun()
