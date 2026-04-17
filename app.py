
import json
import copy
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from generate_faction_pdf import generate_faction_pdf as _gen_faction_pdf
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False
import math
import base64

st.set_page_config(page_title="OPR ArmyBuilder FR", layout="wide", initial_sidebar_state="auto")

# URL de l'app (pour le QR code de partage)
APP_URL = "https://armybuilder-fra.streamlit.app/"

# ── Couleur d'accent par jeu ──────────────────────────────────────────────────
# Recalculé ICI, après set_page_config, en lisant session_state.game correctement.
# Chaque jeu a une couleur bien distincte et lisible sur fond clair.
_GAME_COLORS = {
    "Age of Fantasy":            "#2980b9",   # bleu
    "Age of Fantasy Regiments":  "#8e44ad",   # violet
    "Grimdark Future":           "#e74c3c",   # rouge vif (était #c0392b, trop sombre)
    "Grimdark Future Firefight": "#e67e22",   # orange
    "Age of Fantasy Skirmish":   "#27ae60",   # vert
}
_current_game = st.session_state.get("game") or ""
_acc_color = _GAME_COLORS.get(_current_game, "#c0392b")

# Palette grimdark par jeu
_GAME_COLORS = {
    "Age of Fantasy":            "#4a90d9",
    "Age of Fantasy Regiments":  "#9b59b6",
    "Grimdark Future":           "#c0392b",
    "Grimdark Future Firefight": "#d35400",
    "Age of Fantasy Skirmish":   "#27ae60",
}
_current_game = st.session_state.get("game") or ""
_acc_color = _GAME_COLORS.get(_current_game, "#c0392b")

st.markdown(f"""<style>
:root {{
  --acc:      {_acc_color};
  --bg:       #1a1a1f;
  --bg2:      #23232a;
  --bg3:      #2c2c35;
  --border:   #3a3a45;
  --text:     #d4d0c8;
  --text-dim: #8a8680;
  --text-hdr: #e8e0d0;
}}

#MainMenu {{visibility:hidden;}} footer {{visibility:hidden;}} header {{background:transparent;}}

/* ══ Base ══ */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"] {{
  color-scheme: dark !important;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}}

/* ══ Titres ══ */
h1, h2, h3 {{
  color: var(--text-hdr) !important;
  letter-spacing: 0.06em;
  font-weight: 700;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
  padding-bottom: 4px;
}}
h1 {{ font-size: clamp(1.2rem,4vw,1.6rem) !important; color: var(--acc) !important; }}
h2 {{ font-size: clamp(1rem,3vw,1.25rem) !important; }}
h3 {{ font-size: clamp(.9rem,2.5vw,1.05rem) !important; color: var(--text-dim) !important; border:none; }}

/* ══ Markdown texte ══ */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div {{
  color: var(--text) !important;
}}
strong, b {{ color: var(--text-hdr) !important; }}

/* ══ Widgets : labels ══ */
label, .stRadio label, .stCheckbox label,
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,
[data-testid="stFileUploader"] label {{
  color: var(--text-dim) !important;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: .06em;
}}

/* ══ Inputs ══ */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="select"] div,
[data-baseweb="textarea"] textarea {{
  background-color: var(--bg3) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}}

/* ══ Selectbox / dropdown ══ */
[data-testid="stSelectbox"] > div > div,
[data-baseweb="select"] {{
  background-color: var(--bg3) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}}
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"] {{
  background-color: var(--bg2) !important;
  border: 1px solid var(--border) !important;
}}
[role="option"] {{
  background-color: var(--bg2) !important;
  color: var(--text) !important;
}}
[role="option"]:hover {{
  background-color: var(--bg3) !important;
  color: var(--acc) !important;
}}

/* ══ Radio ══ */
[data-testid="stRadio"] > div {{
  background: transparent !important;
  gap: 6px;
}}
[data-testid="stRadio"] label {{
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px;
  padding: 5px 10px !important;
  color: var(--text) !important;
  font-size: 0.85rem !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  cursor: pointer;
  transition: border-color .15s, color .15s;
}}
[data-testid="stRadio"] label:hover {{
  border-color: var(--acc) !important;
  color: var(--acc) !important;
}}

/* ══ Checkbox ══ */
[data-testid="stCheckbox"] label {{
  color: var(--text) !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  font-size: 0.9rem !important;
}}

/* ══ Expander ══ */
[data-testid="stExpander"] {{
  background-color: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px;
}}
[data-testid="stExpander"] summary {{
  color: var(--text-hdr) !important;
  font-weight: 600;
  letter-spacing: .04em;
}}
[data-testid="stExpanderDetails"] {{
  background-color: var(--bg2) !important;
  color: var(--text) !important;
}}

/* ══ Divider ══ */
hr {{ border-color: var(--border) !important; opacity: .6; }}

/* ══ Alertes ══ */
[data-testid="stAlert"] {{
  background-color: rgba(192,57,43,.15) !important;
  border-left: 3px solid var(--acc) !important;
  color: var(--text) !important;
}}

/* ══ Progress bar ══ */
[data-testid="stProgress"] > div > div > div {{
  background-color: var(--acc) !important;
}}
[data-testid="stProgress"] > div > div {{
  background-color: var(--bg3) !important;
}}

/* ══ Boutons ══ */
.stButton > button {{
  background-color: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px;
  color: var(--text) !important;
  font-weight: 600;
  letter-spacing: .05em;
  text-transform: uppercase;
  font-size: .82rem;
  min-height: 40px;
  transition: border-color .15s, color .15s;
}}
.stButton > button:hover {{
  border-color: var(--acc) !important;
  color: var(--acc) !important;
}}
button[kind="primary"],
.stButton > button[kind="primary"] {{
  background: var(--acc) !important;
  border-color: var(--acc) !important;
  color: #fff !important;
}}
button[kind="primary"]:hover {{
  filter: brightness(1.15);
}}

/* ══ Sidebar ══ */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  background-color: var(--bg2) !important;
  border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] .stMarkdown {{
  color: var(--text) !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
  color: var(--acc) !important;
  border-color: var(--border) !important;
}}
section[data-testid="stSidebar"] .stButton > button {{
  background-color: var(--bg3) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}

/* ══ Composants custom ══ */
.badge {{
  display: inline-block;
  padding: .25rem .65rem;
  border-radius: 2px;
  background: transparent;
  border: 1px solid var(--acc);
  color: var(--acc);
  font-size: .75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: .6rem;
}}
.section-header {{
  font-size: clamp(9px,2vw,10px);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--acc);
  margin: 14px 0 5px;
  padding: 3px 8px;
  background: rgba(192,57,43,.08);
  border-left: 2px solid var(--acc);
}}

/* ══ Responsive ══ */
@media (max-width: 640px) {{
  [data-testid="column"] {{width:100% !important;flex:1 1 100% !important;min-width:100% !important;}}
  .stButton>button {{width:100%;min-height:48px;font-size:14px;}}
  section[data-testid="stSidebar"] {{box-shadow:none;}}
}}
@media (max-width: 480px) {{
  h1 {{font-size:clamp(1.1rem,5vw,1.5rem) !important;}}
  h2 {{font-size:clamp(.95rem,4vw,1.2rem) !important;}}
}}
</style>""", unsafe_allow_html=True)

@st.cache_data
def export_faction_html(data):
    """Génère un HTML complet de la fiche de faction (toutes unités, règles, sorts)."""
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
        named  = u.get("unit_detail") == "named_hero"
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
                _mdata = o.get("mount",{})
                if _mdata and gtype == "mount":
                    _msr = list(_mdata.get("special_rules",[]))
                    _mws = _mdata.get("weapon",[])
                    if isinstance(_mws,dict): _mws=[_mws]
                    _mw_parts=[]
                    for _mw in _mws:
                        if isinstance(_mw,dict) and _mw.get('name'):
                            _mp=f"{_mw['name']} (A{_mw.get('attacks','?')}"
                            if _mw.get('armor_piercing'): _mp+=f", PA({_mw['armor_piercing']})"
                            _msr2=', '.join(_mw.get('special_rules',[]))
                            if _msr2: _mp+=f", {_msr2}"
                            _mp+=")"; _mw_parts.append(esc(_mp))
                    _mcor=_mdata.get('coriace_bonus',0)
                    _mcor_s=[f"Coriace (+{_mcor})"] if _mcor else []
                    osr = ", ".join(_mw_parts + _mcor_s + [esc(r) for r in _msr])
                else:
                    osr   = ", ".join(o.get("special_rules",[]))
                ow    = o.get("weapon") if gtype != "mount" else None
                det   = ""
                if ow:
                    ws = ow if isinstance(ow,list) else [ow]
                    parts = []
                    for w in ws:
                        if isinstance(w,dict):
                            rng = fmt_r(w.get("range"))
                            att = w.get("attacks","?")
                            pa  = w.get("armor_piercing",0) or 0
                            sr2 = ", ".join(w.get("special_rules",[])) or ""
                            _wname = w.get('name','')
                            _inner = f"{rng}, A{att}"
                            if pa: _inner += f", PA({pa})"
                            if sr2: _inner += f", {sr2}"
                            p = f"{_wname} ({_inner})" if _wname != o.get('name','') else f"({_inner})"
                            parts.append(esc(p))
                    det = ", ".join(parts)
                elif osr:
                    det = esc(osr)
                label = oname if not det else (
                    f"{oname} {det}" if det.startswith("(") else f"{oname} ({det})")
                html += (f"<div class='ol'>{label}"
                         f"<span class='oc'>{esc(cost_s)}</span></div>")
        html += "</div>"
        return html

    CATS = [
        ("Héros",                              ["hero"]),
        ("Unités de base",                    ["unit"]),
        ("Véhicules légers / Petits monstres", ["light_vehicle"]),
        ("Véhicules / Monstres",               ["vehicle"]),
        ("Titans",                             ["titan"]),
        ("Personnages nommés",                 ["named_hero"]),
    ]

    rules = data.get("faction_special_rules",[])
    spells = data.get("spells",{})

    army_rules = []
    aura_rules = []
    other_rules = []
    for r in rules:
        n = r.get("name","").lower()
        if r.get("army_rule") or (len(rules) > 0 and rules.index(r) == 0 and r.get("army_rule") is not False and "aura" not in n):
            if not army_rules and "aura" not in n:
                army_rules.append(r)
                continue
        if "aura" in n:
            aura_rules.append(r)
        else:
            other_rules.append(r)

    def rules_section(title, rule_list, color="#1a1a2e"):
        if not rule_list: return ""
        items = ""
        for r in rule_list:
            items += (f"<div class='ri-blk'>"
                      f"<b>{esc(r.get('name',''))}</b> : {esc(r.get('description',''))}"
                      f"</div>")
        return (f"<div class='rs-hdr' style='border-color:{color};color:{color};'>"
                f"{esc(title)}</div>{items}")

    spells_html = ""
    if spells:
        items = ""
        for sname, sdata in spells.items():
            sdesc = sdata.get("description",sdata) if isinstance(sdata,dict) else sdata
            items += f"<div class='ri-blk'><b>{esc(sname)}</b> : {esc(sdesc)}</div>"
        spells_html = f"<div class='rules-cols spells-section'><div class='rs-hdr spells-hdr' style='color:#fff;border-color:#2c3e7a;'>Sorts</div>{items}</div>"

    units_html = ""
    for cat_name, types in CATS:
        cat_units = [u for u in data["units"] if u.get("unit_detail",u.get("type")) in types]
        if not cat_units: continue
        cards = "".join(unit_card(u) for u in cat_units)
        units_html += f"<div class='cat-banner'>{esc(cat_name)}</div><div class='grid'>{cards}</div><div class='page-gap'></div>"

    css = """
body{font-family:'Segoe UI',Helvetica,sans-serif;margin:0;padding:12px;background:#fff;color:#212529;font-size:11px;}
.page{max-width:210mm;margin:0 auto;}
.main-title{background:#1a1a2e;color:#fff;text-align:center;padding:14px 8px 8px;font-size:20px;font-weight:700;letter-spacing:1px;}
.main-sub{background:#16213e;color:#aab4d4;text-align:center;padding:3px;font-size:9px;}
.intro{padding:8px 4px;font-size:10px;color:#444;border-bottom:1px solid #dee2e6;margin-bottom:8px;}
.section-hdr{font-weight:700;font-size:9px;text-transform:uppercase;letter-spacing:.8px;
  color:#1a1a2e;border-bottom:2px solid #1a1a2e;padding-bottom:3px;margin-bottom:5px;}
.intro-txt{font-size:8px;color:#333;line-height:1.45;margin:0;}
.rules-wrap{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px;}
.rules-cols{column-count:3;column-gap:10px;column-rule:1px solid #dee2e6;margin:8px 0 10px;font-size:7.5px;}
.spells-section{column-count:1;margin-top:6px;border-top:2px solid #2c3e7a;padding-top:4px;}
.spells-hdr{background:#2c3e7a;padding:2px 6px;font-weight:700;font-size:8px;text-transform:uppercase;letter-spacing:.5px;display:inline-block;width:100%;box-sizing:border-box;margin-bottom:4px;}
.rs-hdr{font-weight:700;font-size:8px;text-transform:uppercase;letter-spacing:.6px;
  border-bottom:2px solid currentColor;padding-bottom:2px;margin:8px 0 4px;
  break-after:avoid;column-span:none;}
.rs-hdr:first-child{margin-top:0;}
.ri-blk{break-inside:avoid;margin-bottom:3px;line-height:1.35;}
.recap-wrap{margin-bottom:8px;}
.recap-banner{background:#2c3e7a;color:#fff;font-weight:700;font-size:9px;padding:3px 6px;margin-top:4px;}
.recap-table{width:100%;border-collapse:collapse;font-size:8.5px;}
.recap-table th{background:#eef1f8;padding:2px 4px;border:1px solid #dee2e6;font-weight:700;color:#6c757d;font-size:8px;}
.recap-table td{padding:2px 4px;border:1px solid #dee2e6;vertical-align:top;}
.recap-table tr:nth-child(even)td{background:#f8f9fa;}
.cat-banner{background:#1a1a2e;color:#fff;font-weight:700;font-size:11px;padding:4px 8px;margin:10px 0 4px;letter-spacing:.5px;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:4px;}
.uc{border:1px solid #dee2e6;border-radius:3px;overflow:hidden;}
.uh{background:#eef1f8;display:flex;justify-content:space-between;align-items:center;padding:3px 5px;border-bottom:1px solid #dee2e6;}
.uh b{font-size:9px;}
.uc-cost{font-size:8.5px;font-weight:700;color:#c0392b;}
.us{background:#eef1f8;font-size:7.5px;color:#6c757d;font-weight:700;padding:2px 5px;border-bottom:1px solid #dee2e6;}
.ur{background:#eef1f8;font-size:7px;padding:2px 5px;border-bottom:1px solid #dee2e6;}
.wt{width:100%;border-collapse:collapse;font-size:8px;}
.wt th{background:#eef1f8;padding:1px 3px;border-bottom:1px solid #dee2e6;color:#6c757d;font-size:7px;}
.wt td{padding:1px 3px;border-bottom:1px solid #dee2e6;vertical-align:top;}
.wt tr:last-child td{border-bottom:none;}
.wn{font-size:8px;font-weight:700;}
.ws{font-size:7px;color:#444;}
.og{font-size:7.5px;font-weight:700;padding:2px 5px 1px;background:#f8f9fa;border-top:1px solid #dee2e6;margin-top:1px;}
.ol{font-size:7px;padding:1px 5px 1px 12px;display:flex;justify-content:space-between;border-bottom:1px solid #f0f0f0;}
.oc{color:#c0392b;font-weight:700;white-space:nowrap;margin-left:4px;}
@media print{
  body{margin:0;padding:4px;}
  .page{max-width:100%;}
  .cat-banner{page-break-before:always;break-before:page;}
  .cat-banner:first-of-type{page-break-before:always;break-before:page;}
  .uc{page-break-inside:avoid;break-inside:avoid;}
  .grid{page-break-inside:auto;}
  .rules-cols,.spells-section,.recap-wrap{page-break-inside:avoid;}
  .main-title,.main-sub{page-break-after:avoid;}
  .page-gap{page-break-after:always;break-after:page;height:0;}
  .page-gap:last-child{page-break-after:auto;break-after:auto;}
}
"""

    def recap_row(u):
        bw = u.get("weapon",[])
        if isinstance(bw,dict): bw=[bw]
        sz = u.get("size",1)
        eq = []
        for w in bw:
            if isinstance(w, dict):
                cnt = w.get("count","")
                cs  = f"{cnt}x " if cnt and cnt>1 else (f"{sz}x " if sz>1 else "1x ")
                rng = fmt_r(w.get("range"))
                att = w.get("attacks","?")
                pa  = w.get("armor_piercing",0) or 0
                sr2 = ", ".join(w.get("special_rules",[])) or ""
                p   = f"{cs}{w['name']} ({rng}, A{att}"
                if pa: p += f", PA({pa})"
                if sr2: p += f", {sr2}"
                p += ")"
                eq.append(esc(p))
        return (f"<tr><td><b>{esc(u['name'])} [{sz}]</b></td>"
                f"<td>{u.get('quality','?')}</td>"
                f"<td>{u.get('defense','?')}</td>"
                f"<td>{' | '.join(eq)}</td>"
                f"<td>{esc(', '.join(u.get('special_rules',[]))[:80])}</td>"
                f"<td><b>{u.get('base_cost','?')}</b></td></tr>")

    recap_html = "<div class='recap-wrap'>"
    for cat_name, types in [("Héros",["hero","named_hero"]),("Unités de base",["unit"]),("Véhicules légers / Monstres / Titans",["light_vehicle","vehicle","titan"])]:
        cu = [u for u in data["units"] if u.get("unit_detail",u.get("type")) in types]
        if not cu: continue
        rows = "".join(recap_row(u) for u in cu)
        recap_html += (f"<div class='recap-banner'>{esc(cat_name)}</div>"
                       f"<table class='recap-table'><thead><tr>"
                       f"<th>Nom [taille]</th><th>Qua</th><th>Déf</th>"
                       f"<th>Équipement</th><th>Règles spéciales</th><th>Coût</th>"
                       f"</tr></thead><tbody>{rows}</tbody></table>")
    recap_html += "</div>"

    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>{esc(faction)} — {esc(game)}</title>
<style>{css}</style></head><body><div class="page">
<div class="main-title">{esc(faction.upper())}</div>
<div class="main-sub">{esc(game)} — v{esc(version)}</div>
{f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0 10px;">
  <div>
    <div class="section-hdr">Introduction</div>
    <div class="intro-txt">{esc(desc)}</div>
    <div class="section-hdr" style="margin-top:8px;">Au sujet d'OPR</div>
    <div class="intro-txt">OPR (www.onepagerules.com) héberge de nombreux jeux gratuits conçus pour être rapides à apprendre et faciles à jouer. Ce projet a été réalisé par des joueurs, pour des joueurs, et ne peut exister que grâce au généreux soutien de notre formidable communauté ! Si vous souhaitez soutenir le développement de nos jeux, vous pouvez faire un don sur : www.patreon.com/onepagerules. Merci de jouer à OPR !</div>
  </div>
  <div>
    <div class="section-hdr">Histoire de la faction</div>
    <div class="intro-txt">{esc(history).replace(chr(10)+chr(10), "</p><p class=\'intro-txt\'>")}</div>
  </div>
</div>''' if desc or history else ""}
<div class='rules-cols'>
{rules_section("Règle spéciale de l'armée", army_rules)}
{rules_section("Règles spéciales", other_rules, "#2c3e7a")}
{rules_section("Règles spéciales d'aura", aura_rules, "#555")}
</div>
{spells_html}
{recap_html}
{units_html}
</div></body></html>"""



with st.sidebar:
    st.markdown("<div style='height:1px;'></div>", unsafe_allow_html=True)
with st.sidebar:
    st.title("OPR ArmyBuilder FRA")
    st.subheader("📋 Armée")
    game = st.session_state.get("game", "—")
    faction = st.session_state.get("faction", "—")
    points = st.session_state.get("points", 0)
    army_cost = st.session_state.get("army_cost", 0)
    st.markdown(f"**Jeu :** {game}")
    st.markdown(f"**Faction :** {faction}")
    st.markdown(f"**Format :** {points} pts")
    if points > 0:
        st.progress(min(army_cost / points, 1.0))
        st.markdown(f"**Coût :** {army_cost} / {points} pts")
        if army_cost > points:
            st.error("⚠️ Dépassement de points")
        if st.session_state.get("page") == "army" and "army_list" in st.session_state:
            units_cap = math.floor(points / 150)
            heroes_cap = math.floor(points / 375)
            units_now = len([u for u in st.session_state.army_list if u.get("type") != "hero"])
            heroes_now = len([u for u in st.session_state.army_list if u.get("type") == "hero"])
            st.markdown(f"**Unités :** {units_now} / {units_cap}")
            st.markdown(f"**Héros :** {heroes_now} / {heroes_cap}")
    if st.session_state.get("faction_data"):
        st.subheader("📘 Fiche de faction")
        _fdata = st.session_state.faction_data
        _faction_slug = re.sub(r'[^a-z0-9]', '_', _fdata.get("faction","faction").lower()).strip('_')
        _html_faction = export_faction_html(_fdata)
        st.download_button(
            "📄 Exporter fiche faction (HTML)",
            data=_html_faction,
            file_name=f"{_faction_slug}_fiche.html",
            mime="text/html",
            use_container_width=True,
            key="dl_faction_html"
        )
    st.divider()

if "page" not in st.session_state: st.session_state.page = "setup"
if "army_list" not in st.session_state: st.session_state.army_list = []
if "army_cost" not in st.session_state: st.session_state.army_cost = 0
if "unit_selections" not in st.session_state: st.session_state.unit_selections = {}
if "draft_counter" not in st.session_state: st.session_state.draft_counter = 0
if "draft_unit_name" not in st.session_state: st.session_state.draft_unit_name = ""

# ── Lecture du paramètre ?list= (QR code de partage) ────────────────────────
if not st.session_state.get("_qr_loaded"):
    st.session_state["_qr_loaded"] = True
    try:
        _qp = st.query_params.get("list", "")
        if _qp:
            import zlib as _z, base64 as _b64q, urllib.parse as _uq
            _raw  = _b64q.urlsafe_b64decode(_uq.unquote(_qp).encode() + b"==")
            _data = json.loads(_z.decompress(_raw).decode())
            if _data.get("game"):    st.session_state["game"]    = _data["game"]
            if _data.get("faction"): st.session_state["faction"] = _data["faction"]
            if _data.get("pts"):     st.session_state["points"]  = _data["pts"]
            if _data.get("army_list"):
                st.session_state["_qr_army_list"] = _data["army_list"]
                st.session_state["_qr_army_cost"] = _data.get("army_cost", 0)
            st.session_state["_qr_game"]    = _data.get("game", "")
            st.session_state["_qr_faction"] = _data.get("faction", "")
            st.session_state["_qr_pts"]     = _data.get("pts", 1000)
            st.session_state["_qr_units"]   = _data.get("units", [])
            st.session_state["_qr_pending"] = True
            st.query_params.clear()
            st.rerun()
    except Exception:
        pass

if "game" not in st.session_state: st.session_state.game = None
if "faction" not in st.session_state: st.session_state.faction = None
if "points" not in st.session_state: st.session_state.points = 0
if "list_name" not in st.session_state: st.session_state.list_name = ""
if "units" not in st.session_state: st.session_state.units = []
if "faction_special_rules" not in st.session_state: st.session_state.faction_special_rules = []
if "faction_spells" not in st.session_state: st.session_state.faction_spells = {}

GAME_CONFIG = {
    "Age of Fantasy": {"min_points": 500, "max_points": 20000, "default_points": 2000, "hero_limit": 500, "unit_copy_rule": 1000, "unit_max_cost_ratio": 0.4, "unit_per_points": 200},
    "Age of Fantasy Regiments": {"min_points": 500, "max_points": 20000, "default_points": 2000, "hero_limit": 500, "unit_copy_rule": 1000, "unit_max_cost_ratio": 0.4, "unit_per_points": 200},
    "Grimdark Future": {"min_points": 500, "max_points": 20000, "default_points": 2000, "hero_limit": 500, "unit_copy_rule": 1000, "unit_max_cost_ratio": 0.4, "unit_per_points": 200},
    "Grimdark Future Firefight": {"min_points": 150, "max_points": 1000, "default_points": 300, "hero_limit": 300, "unit_copy_rule": 300, "unit_max_cost_ratio": 0.6, "unit_per_points": 100},
    "Age of Fantasy Skirmish": {"min_points": 150, "max_points": 1000, "default_points": 300, "hero_limit": 300, "unit_copy_rule": 300, "unit_max_cost_ratio": 0.6, "unit_per_points": 100}
}

def check_hero_limit(army_list, army_points, game_config):
    max_heroes = math.floor(army_points / game_config["hero_limit"])
    hero_count = sum(1 for unit in army_list if unit.get("type") == "hero")
    if hero_count > max_heroes:
        st.error(f"Limite de héros dépassée! Max: {max_heroes} (1 héros/{game_config['hero_limit']} pts)")
        return False
    return True

def check_unit_max_cost(army_list, army_points, game_config, new_unit_cost=None):
    max_cost = army_points * game_config["unit_max_cost_ratio"]
    for unit in army_list:
        if unit["cost"] > max_cost:
            st.error(f"Unité {unit['name']} dépasse {int(max_cost)} pts (35% du total)")
            return False
    if new_unit_cost and new_unit_cost > max_cost:
        st.error(f"Cette unité dépasse {int(max_cost)} pts (35% du total)")
        return False
    return True

def check_unit_copy_rule(army_list, army_points, game_config):
    x_value = math.floor(army_points / game_config["unit_copy_rule"])
    max_copies = 1 + x_value
    unit_counts = {}
    for unit in army_list:
        name = unit["name"]
        unit_counts[name] = unit_counts.get(name, 0) + 1
    for unit_name, count in unit_counts.items():
        if count > max_copies:
            st.error(f"Trop de copies de {unit_name}! Max: {max_copies}")
            return False
    return True

def validate_army_rules(army_list, army_points, game):
    game_config = GAME_CONFIG.get(game, {})
    return (check_hero_limit(army_list, army_points, game_config) and
            check_unit_max_cost(army_list, army_points, game_config) and
            check_unit_copy_rule(army_list, army_points, game_config))

def check_weapon_conditions(unit_key, requires, unit=None):
    if not requires:
        return True
    current_weapons = []
    selections = st.session_state.unit_selections.get(unit_key, {})

    for v in selections.values():
        if isinstance(v, str) and v not in ("Aucune amélioration", "Aucune arme", "Aucun rôle",
                                             "Aucune monture", "Aucune option de mobilité"):
            current_weapons.append({"name": v.split(" (")[0]})

    if unit is not None:
        replaced_by_weapon_group = False
        for gi, g in enumerate(unit.get("upgrade_groups", [])):
            if g.get("type") != "weapon":
                continue
            g_key = f"group_{gi}"
            sel = selections.get(g_key, "")
            if not sel:
                continue
            bw = unit.get("weapon", [])
            if isinstance(bw, list) and bw:
                lbls = [w.get("name", "Arme") for w in bw if isinstance(w, dict)]
                default_lbl = lbls[0] if len(lbls) == 1 else " et ".join(lbls)
            elif isinstance(bw, dict):
                default_lbl = bw.get("name", "Arme")
            else:
                default_lbl = ""
            if sel != default_lbl:
                replaced_by_weapon_group = True
                break

        if not replaced_by_weapon_group:
            for w in unit.get("weapon", []):
                if isinstance(w, dict):
                    current_weapons.append(w)

    for req in requires:
        if not any(w.get("name") == req or req in w.get("tags", []) for w in current_weapons):
            return False
    return True

def format_unit_option(u):
    name_part = u["name"] + (" [1]" if u.get("type") == "hero" else f" [{u.get('size', 10)}]")
    return f"{name_part} | Qual {u.get('quality','?')}+ | Déf {u.get('defense','?')}+ | {u.get('base_cost',0)} pts"

def weapon_profile_md(weapon):
    if not weapon or not isinstance(weapon, dict): return ""
    rng = weapon.get("range", "Mêlée")
    if rng in (None, "-", "mêlée", "Mêlée") or str(rng).lower() == "mêlée":
        rng_str = "Mêlée"
    elif isinstance(rng, (int, float)):
        rng_str = f'{int(rng)}"'
    else:
        s = str(rng).strip(); rng_str = s if s.endswith('"') else f'{s}"'
    att = weapon.get("attacks", "?")
    ap  = weapon.get("armor_piercing", "?")
    sr  = weapon.get("special_rules", [])
    parts = [f"{rng_str} | A{att} | PA{ap}"]
    if sr: parts.append(", ".join(sr))
    return " | ".join(parts)

def format_weapon_option(weapon, cost=0):
    if not weapon or not isinstance(weapon, dict): return "Aucune arme"
    rng = weapon.get("range","Mêlée")
    if rng in (None,"-","mêlée","Mêlée") or str(rng).lower()=="mêlée": rng_str="Mêlée"
    elif isinstance(rng,(int,float)): rng_str=f'{int(rng)}"'
    else: s=str(rng).strip(); rng_str=s if s.endswith('"') else f'{s}"'
    sr = weapon.get("special_rules",[])
    profile_inner = f"{rng_str}/A{weapon.get('attacks','?')}/PA{weapon.get('armor_piercing','?')}"
    if sr: profile_inner += f", {', '.join(sr)}"
    profile = f"{weapon.get('name','Arme')} ({profile_inner})"
    if cost > 0: profile += f" (+{cost} pts)"
    return profile

def format_mobility_option(opt):
    if not opt or not isinstance(opt, dict): return "Aucune option"
    name = opt.get("name", "Option")
    cost = opt.get("cost", 0)
    sr = [s for s in opt.get("special_rules", []) if "Coriace" not in s]
    coriace = opt.get("coriace_bonus", 0)
    stats = []
    if coriace > 0: stats.append(f"Coriace+{coriace}")
    w = opt.get("weapon")
    if w and isinstance(w, dict):
        stats.append(f"{w.get('name','Arme')} A{w.get('attacks','?')}/PA{w.get('armor_piercing','?')}")
    if sr: stats.extend(sr)
    label = name
    if stats: label += f" ({', '.join(stats)})"
    return label + f" (+{cost} pts)"

def format_mount_option(mount):
    if not mount or not isinstance(mount, dict): return "Aucune monture"
    name = mount.get("name", "Monture")
    cost = mount.get("cost", 0)
    mount_data = mount.get("mount", {})
    weapons = mount_data.get("weapon", [])
    if isinstance(weapons, dict): weapons = [weapons]
    coriace = mount_data.get("coriace_bonus", 0)
    stats = []
    for w in weapons:
        if isinstance(w, dict):
            p = f"{w.get('name','Arme')} A{w.get('attacks','?')}/PA{w.get('armor_piercing','?')}"
            sp = ", ".join(w.get("special_rules", []))
            if sp: p += f" ({sp})"
            stats.append(p)
    if coriace > 0: stats.append(f"Coriace+{coriace}")
    sr = mount_data.get("special_rules", [])
    if sr:
        rt = ", ".join([r for r in sr if not r.startswith(("Griffes", "Sabots"))])
        if rt: stats.append(rt)
    label = name
    if stats: label += f" ({', '.join(stats)})"
    return label + f" (+{cost} pts)"

# ======================================================
# EXPORT HTML — STYLE ARMYFORGE
# ======================================================
def export_html(army_list, army_name, army_limit):

    def esc(txt):
        if txt is None: return ""
        return str(txt).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    def get_priority(unit):
        d = unit.get("unit_detail", unit.get("type","unit"))
        order = {"named_hero": 1, "hero": 2, "unit": 3, "light_vehicle": 4, "vehicle": 5, "titan": 6}
        return order.get(d, 7)

    def fmt_range(rng):
        if rng in (None, "-", "mêlée", "Mêlée") or str(rng).lower() == "mêlée": return "-"
        if isinstance(rng, (int, float)): return f'{int(rng)}"'
        s = str(rng).strip()
        return s if s.endswith('"') else f'{s}"'

    def collect_weapons(unit):
        result = []
        bw = unit.get("weapon", [])
        if isinstance(bw, dict): bw = [bw]
        _unit_size = unit.get("size", 1)
        for w in bw:
            if isinstance(w, dict):
                wc = w.copy(); wc.setdefault("range", "Mêlée")
                if not wc.get("_upgraded") and not wc.get("_mount_weapon"):
                    wc["_is_base"] = True
                    if "_count" in wc and wc["_count"] <= 1:
                        del wc["_count"]
                    if "_count" not in wc and "count" not in wc and _unit_size > 1:
                        wc["_count"] = _unit_size
                result.append(wc)
        if unit.get("mount"):
            m = unit["mount"]
            if isinstance(m, dict):
                md = m.get("mount", {})
                if isinstance(md, dict):
                    mws = md.get("weapon", [])
                    if isinstance(mws, dict): mws = [mws]
                    for w in mws:
                        if isinstance(w, dict):
                            wc = w.copy(); wc.setdefault("range", "Mêlée"); wc["_mount_weapon"] = True; result.append(wc)
        return result

    def group_weapons(weapons, unit_size=1):
        wmap = {}
        for w in weapons:
            if not isinstance(w, dict): continue
            wc = w.copy(); wc.setdefault("range","Mêlée")
            key = (wc.get("name",""), wc.get("range",""), wc.get("attacks",""),
                   wc.get("armor_piercing",""), tuple(sorted(wc.get("special_rules",[]))))
            cnt = wc.get("_count", wc.get("count", 1)) or 1
            if key not in wmap:
                wmap[key] = wc; wmap[key]["_display_count"] = cnt
            else:
                wmap[key]["_display_count"] += cnt
        return [v for v in wmap.values() if v.get("_display_count", 1) > 0]

    def get_rules(unit):
        rules = set()
        for r in unit.get("special_rules", []):
            if isinstance(r, str): rules.add(r)
        if "options" in unit and isinstance(unit["options"], dict):
            for group in unit["options"].values():
                opts = group if isinstance(group, list) else [group]
                for opt in opts:
                    if isinstance(opt, dict):
                        for r in opt.get("special_rules", []):
                            if isinstance(r, str): rules.add(r)
        if unit.get("mount"):
            m = unit["mount"]
            if isinstance(m, dict):
                md = m.get("mount", {})
                if isinstance(md, dict):
                    for r in md.get("special_rules", []):
                        if isinstance(r, str) and not r.startswith(("Griffes","Sabots")): rules.add(r)
        return sorted(rules)

    def render_weapon_rows(final_weapons, unit_size=1):
        rows = ""
        for w in final_weapons:
            name     = esc(w.get("name","Arme"))
            cnt      = w.get("_display_count", 1) or 1
            is_base  = w.get("_is_base", False)
            upgraded = w.get("_upgraded", False)
            is_mount = w.get("_mount_weapon", False)

            if cnt > 1:
                nd = f"{cnt}x {name}"
            elif cnt == 1:
                if is_mount:
                    nd = name
                elif unit_size > 1:
                    nd = f"1x {name}"
                elif upgraded:
                    nd = f"1x {name}"
                else:
                    nd = name
            else:
                nd = name

            rng = fmt_range(w.get("range","Mêlée"))
            att = w.get("attacks","-"); ap = w.get("armor_piercing","-")
            spe = ", ".join(w.get("special_rules",[])) or "-"
            rows += f"<tr><td class='weapon-name'>{nd}</td><td>{rng}</td><td>{att}</td><td>{ap}</td><td>{spe}</td></tr>"
        return rows

    def render_upgrade_rows(unit):
        return ""

    def render_upgrades_section(unit):
        upgrades = []
        if "options" in unit and isinstance(unit["options"], dict):
            for group_opts in unit["options"].values():
                opts = group_opts if isinstance(group_opts, list) else [group_opts]
                for opt in opts:
                    if not isinstance(opt, dict): continue
                    rules = ", ".join(opt.get("special_rules", []))
                    upgrades.append((opt.get("name","Amélioration"), rules))
        if not upgrades: return ""
        items = ""
        for n, r in upgrades:
            items += f'<span class="rule-tag" style="background:#e8f4fd;border-color:#b8d9f0;">{esc(n)}'
            if r: items += f' <span style="font-weight:400;color:#555;">({esc(r)})</span>'
            items += '</span>'
        return (
            '<div style="border-top:1px solid var(--brd);margin-top:8px;padding-top:8px;">'
            '<div class="rules-title">Améliorations</div>'
            f'<div style="margin-bottom:4px;">{items}</div>'
            '</div>'
        )

    def render_mount_section(unit):
        if not unit.get("mount"): return ""
        mount = unit["mount"]
        if not isinstance(mount, dict) or "mount" not in mount: return ""
        md = mount["mount"]; mname = esc(mount.get("name","Monture")); mcost = mount.get("cost",0)
        mws = md.get("weapon",[]); 
        if isinstance(mws, dict): mws = [mws]
        wrows = ""
        for w in mws:
            if not isinstance(w, dict): continue
            spe = ", ".join(w.get("special_rules",[])) or "-"
            wrows += f"<tr><td class='weapon-name'>{esc(w.get('name','Arme'))}</td><td>{fmt_range(w.get('range','-'))}</td><td>{w.get('attacks','-')}</td><td>{w.get('armor_piercing','-')}</td><td>{spe}</td></tr>"
        mrules = [r for r in md.get("special_rules",[]) if not r.startswith(("Griffes","Sabots","Coriace"))]
        rhtml = " ".join(f'<span class="rule-tag">{esc(r)}</span>' for r in mrules) if mrules else ""
        return f"""<div class="mount-section"><div class="section-title">🐴 {mname} (+{mcost} pts)</div>
{('<div style="margin-bottom:8px;">' + rhtml + '</div>') if rhtml else ""}
<table class="weapon-table"><thead><tr><th>Arme</th><th>Por</th><th>Att</th><th>PA</th><th>Spé</th></tr></thead><tbody>{wrows}</tbody></table></div>"""

    _rules_dict = dict(load_generic_rules())
    _rules_dict.update(load_faction_rules_dict())

    sorted_units = sorted(army_list, key=get_priority)
    total_cost = sum(u.get("cost",0) for u in sorted_units)

    html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Liste d'Armée OPR - {esc(army_name)}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fff;--hdr:#f8f9fa;--accent:#3498db;--txt:#212529;--muted:#6c757d;--brd:#dee2e6;--red:#e74c3c;--rule:#e9ecef;--mount:#f3e5f5;--badge:#e9ecef;}}
*{{box-sizing:border-box;}}
body{{background:var(--bg);color:var(--txt);font-family:'Inter',sans-serif;margin:0;padding:12px;line-height:1.3;font-size:12px;}}
.army{{max-width:210mm;margin:0 auto;}}
.army-title{{text-align:center;font-size:18px;font-weight:700;margin-bottom:8px;border-bottom:2px solid var(--accent);padding-bottom:6px;}}
.army-summary{{display:flex;justify-content:space-between;align-items:center;background:var(--hdr);padding:8px 12px;border-radius:6px;margin:8px 0 12px;border:1px solid var(--brd);font-size:12px;}}
.summary-cost{{font-family:monospace;font-size:16px;font-weight:bold;color:var(--red);}}
.units-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;}}
.unit-card{{background:var(--bg);border:1px solid var(--brd);border-radius:6px;break-inside:avoid;page-break-inside:avoid;font-size:11px;}}
.unit-header{{padding:6px 8px 4px;background:var(--hdr);border-bottom:1px solid var(--brd);border-radius:6px 6px 0 0;}}
.unit-name-container{{display:flex;justify-content:space-between;align-items:flex-start;}}
.unit-name{{font-size:13px;font-weight:700;margin:0;line-height:1.2;}}
.unit-cost{{font-family:monospace;font-size:12px;font-weight:700;color:var(--red);white-space:nowrap;margin-left:6px;}}
.unit-type{{font-size:10px;color:var(--muted);margin-top:1px;}}
.unit-stats{{display:flex;gap:6px;padding:4px 0 2px;flex-wrap:wrap;}}
.stat-badge{{background:var(--badge);padding:2px 7px;border-radius:12px;font-weight:600;display:flex;align-items:center;gap:4px;border:1px solid var(--brd);}}
.stat-value{{font-weight:700;font-size:11px;}}
.stat-label{{font-size:9px;color:var(--muted);}}
.section{{padding:4px 8px 6px;}}
.section-title{{font-weight:600;margin:4px 0 3px;font-size:11px;display:flex;align-items:center;gap:5px;border-bottom:1px solid var(--brd);padding-bottom:2px;color:var(--accent);}}
.weapon-table{{width:100%;border-collapse:collapse;margin:0 0 4px;font-size:10px;}}
.weapon-table th{{background:var(--hdr);padding:2px 5px;text-align:left;font-weight:600;border-bottom:1px solid var(--brd);border-right:1px solid var(--brd);font-size:9px;color:var(--muted);}}
.weapon-table th:last-child{{border-right:none;}}
.weapon-table td{{padding:2px 5px;border-bottom:1px solid var(--brd);border-right:1px solid var(--brd);vertical-align:top;line-height:1.3;}}
.weapon-table td:last-child{{border-right:none;}} .weapon-table tr:last-child td{{border-bottom:none;}}
.weapon-name{{font-weight:600;}}
.rules-section{{margin:3px 0 0;}}
.rules-title{{font-weight:600;margin-bottom:3px;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em;}}
.rule-tag{{background:var(--rule);padding:1px 6px;border-radius:3px;font-size:9px;border:1px solid var(--brd);margin-right:3px;margin-bottom:3px;display:inline-block;line-height:1.5;cursor:pointer;}}
#opr-tooltip{{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#222;color:#fff;padding:12px 16px;border-radius:8px;font-size:11px;line-height:1.6;max-width:300px;white-space:pre-wrap;z-index:9999;text-align:left;box-shadow:0 4px 24px rgba(0,0,0,.5);}}
#opr-overlay{{display:none;position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,.2);cursor:pointer;}}
.mount-section{{background:var(--mount);border:1px solid var(--brd);border-radius:4px;padding:4px 8px;margin:4px 0;font-size:10px;}}
.mount-section .section-title{{font-size:10px;}}
.legend-page{{page-break-before:always;break-before:page;padding:12px 0;}}
.faction-rules{{padding:8px;border-radius:6px;border:1px solid var(--brd);}}
.legend-title{{text-align:center;color:var(--accent);border-bottom:2px solid var(--accent);padding-bottom:6px;margin-bottom:12px;font-size:14px;font-weight:700;}}
.rule-item{{margin-bottom:4px;padding-bottom:4px;border-bottom:1px solid var(--brd);}}
.rule-item:last-child{{border-bottom:none;margin-bottom:0;padding-bottom:0;}}
.rule-name{{color:var(--accent);font-weight:600;font-size:8px;margin-bottom:1px;}}
.rule-desc{{font-size:7.5px;line-height:1.28;color:#555;}}
@media print{{
  body{{padding:6px;}}
  .army{{max-width:100%;}}
  .unit-card{{border:0.5px solid #ccc;box-shadow:none;background:white;}}
  .faction-rules{{border:0.5px solid #ccc;}}
  .legend-page{{page-break-before:always;}}
}}
</style></head><body><div class="army">
<div class="army-title">{esc(army_name)} — {total_cost}/{army_limit} pts</div>
<div class="army-summary">
  <div><span style="color:var(--muted);">Unités :</span> <strong>{len(sorted_units)}</strong></div>
  <div class="summary-cost">{total_cost}/{army_limit} pts</div>
</div>
<div class="units-grid">
"""

    for unit in sorted_units:
        if not isinstance(unit, dict): continue
        name = esc(unit.get("name","Unité")); cost = unit.get("cost",0)
        quality = esc(unit.get("quality","-")); defense = esc(unit.get("defense","-"))
        size = unit.get("size",10); coriace = unit.get("coriace",0)

        rules = get_rules(unit)
        def _get_rule_desc(r, rd):
            d = rd.get(r, "")
            if not d:
                for k, v in rd.items():
                    if r.startswith(k + " ") or r.startswith(k + "("):
                        return v
            return d
        def _safe_tip(txt):
            return txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&#34;").replace("'", "&#39;")
        def _rule_tag(r):
            desc = _get_rule_desc(r, _rules_dict)
            if desc:
                return (f'<span class="rule-tag" data-tip="{_safe_tip(desc)}"'
                        f' onclick="showTip(this)">{esc(r)}</span>')
            return f'<span class="rule-tag">{esc(r)}</span>'
        rules_html = " ".join(_rule_tag(r) for r in rules) if rules else '<span class="rule-tag">Aucune</span>'

        weapons = collect_weapons(unit)
        final_weapons = group_weapons(weapons, unit_size=size)
        weapon_rows = render_weapon_rows(final_weapons, unit_size=size)
        upgrade_rows     = render_upgrade_rows(unit)
        upgrades_section = render_upgrades_section(unit)
        mount_section    = render_mount_section(unit)

        detail_labels = {
            "named_hero":    "Héros nommé",
            "hero":          "Héros",
            "unit":          "Unité de base",
            "light_vehicle": "Véhicule léger / Petit monstre",
            "vehicle":       "Véhicule / Monstre",
            "titan":         "Titan",
        }
        detail_label = detail_labels.get(unit.get("unit_detail", unit.get("type","unit")), "")

        html += f"""<div class="unit-card">
  <div class="unit-header">
    <div class="unit-name-container">
      <div class="unit-name">{name}{'<div class="unit-type">' + detail_label + '</div>' if detail_label else ''}</div>
      <div class="unit-cost">{cost} pts</div>
    </div>
    <div class="unit-stats">
      <div class="stat-badge"><span class="stat-label">QUAL</span><span class="stat-value">{quality}+</span></div>
      <div class="stat-badge"><span class="stat-label">DÉF</span><span class="stat-value">{defense}+</span></div>
      {'<div class="stat-badge"><span class="stat-label">CORIACE</span><span class="stat-value">' + str(coriace) + '</span></div>' if coriace > 0 else ''}
      <div class="stat-badge"><span class="stat-label">TAILLE</span><span class="stat-value">{size}</span></div>
    </div>
  </div>
  <div class="section">
    <div class="rules-section">
      <div class="rules-title">Règles spéciales</div>
      <div style="margin-bottom:4px;">{rules_html}</div>
      {upgrades_section}
    </div>
    <div class="section-title">⚔️ Armes</div>
    <table class="weapon-table">
      <thead><tr><th>Arme</th><th>Por</th><th>Att</th><th>PA</th><th>Spé</th></tr></thead>
      <tbody>{weapon_rows}</tbody>
    </table>
    {mount_section}
  </div>
</div>"""

    html += "</div>\n"

    try:
        faction_rules = st.session_state.get("faction_special_rules", [])
        faction_spells = st.session_state.get("faction_spells", {})
        all_rules = [r for r in faction_rules if isinstance(r, dict)]
        if all_rules or faction_spells:
            html += """<div class="legend-page"><div class="faction-rules">"""
            html += """<div class="legend-title">📜 Règles spéciales &amp; Sorts</div>"""
            html += """<div style="columns:3;column-gap:12px;column-rule:1px solid #dee2e6;font-size:9px;">"""

            if all_rules:
                for rule in sorted(all_rules, key=lambda x: x.get("name","").lower()):
                    html += (
                        f'<div class="rule-item" style="break-inside:avoid;">'
                        f'<div class="rule-name">{esc(rule.get("name",""))}</div>'
                        f'<div class="rule-desc">{esc(rule.get("description",""))}</div>'
                        f'</div>'
                    )

            if faction_spells:
                if all_rules:
                    html += '<div class="rule-item" style="break-inside:avoid;border-bottom:2px solid var(--accent);margin-bottom:8px;"><div style="font-size:10px;font-weight:700;color:var(--accent);">✨ Sorts</div></div>'
                for spell_name, spell_data in faction_spells.items():
                    if isinstance(spell_data, dict):
                        desc = spell_data.get("description","")
                    else:
                        desc = str(spell_data)
                    html += (
                        f'<div class="rule-item" style="break-inside:avoid;">'
                        f'<div class="rule-name">{esc(spell_name)}</div>'
                        f'<div class="rule-desc">{esc(desc)}</div>'
                        f'</div>'
                    )

            html += "</div></div></div>"
    except Exception as e:
        html += f'<div style="color:red;padding:10px;">Erreur règles faction : {esc(str(e))}</div>'

    import urllib.parse as _urlp
    import zlib as _zlib
    _list_data = json.dumps({
        "game": st.session_state.get("game",""),
        "faction": army_name, "pts": army_limit,
        "list_name": army_name,
        "army_list": army_list,
        "army_cost": sum(u.get("cost",0) for u in army_list),
        "units": [{"n": u.get("name",""), "c": u.get("cost",0)} for u in army_list]
    }, ensure_ascii=False, separators=(',',':'))
    _compressed = _zlib.compress(_list_data.encode(), level=9)
    import base64 as _b64u, urllib.parse as _urlp
    _b64_data = _b64u.urlsafe_b64encode(_compressed).decode()
    _payload = APP_URL + "?list=" + _urlp.quote(_b64_data)

    _qr_img_tag = ""
    try:
        import qrcode as _qrc, io as _io, base64 as _b64
        _qr = _qrc.QRCode(version=None, error_correction=_qrc.constants.ERROR_CORRECT_M, box_size=4, border=2)
        _qr.add_data(_payload); _qr.make(fit=True)
        _img = _qr.make_image(fill_color="black", back_color="white")
        _buf = _io.BytesIO(); _img.save(_buf, format="PNG"); _buf.seek(0)
        _qr_b64 = _b64.b64encode(_buf.read()).decode()
        _qr_img_tag = f'<img src="data:image/png;base64,{_qr_b64}" style="width:96px;height:96px;display:block;margin:0 auto;border:1px solid var(--brd);border-radius:4px;" alt="QR code">'
    except Exception:
        _qr_url = "https://api.qrserver.com/v1/create-qr-code/?data=" + _urlp.quote(_payload) + "&size=96x96&margin=2"
        _qr_img_tag = f'<img src="{_qr_url}" style="width:96px;height:96px;display:block;margin:0 auto;border:1px solid var(--brd);border-radius:4px;" alt="QR code">'

    html += (
        '<div style="text-align:center;margin-top:28px;padding:16px 0;border-top:1px solid var(--brd);">'
        '<div style="font-size:10px;color:var(--muted);margin-bottom:8px;letter-spacing:.06em;text-transform:uppercase;">Scanner pour partager</div>'
        + _qr_img_tag +
        '</div>'
    )
    html += '''<div id="opr-overlay" onclick="hideTip()"></div>
<div id="opr-tooltip"></div>
<script>
function showTip(el){
  var tip=document.getElementById("opr-tooltip");
  var ov=document.getElementById("opr-overlay");
  tip.textContent=el.getAttribute("data-tip");
  tip.style.display="block";
  ov.style.display="block";
}
function hideTip(){
  document.getElementById("opr-tooltip").style.display="none";
  document.getElementById("opr-overlay").style.display="none";
}
</script>'''
    html += f'<div style="text-align:center;margin-top:16px;font-size:11px;color:var(--muted);">Généré par OPR ArmyBuilder FRA — {datetime.now().strftime("%d/%m/%Y %H:%M")}</div></div></body></html>'
    return html

def load_generic_rules():
    try:
        _BASE = Path(__file__).resolve().parent
        for _p in [
            _BASE / "repositories" / "data" / "generic_rules.json",
            _BASE / "generic_rules.json",
        ]:
            if _p.exists():
                with open(_p, encoding="utf-8") as f:
                    data = json.load(f)
                result = {}
                for r in data.get("rules", []):
                    if "name" not in r: continue
                    desc = r.get("description", "")
                    for k in r.get("key", [r["name"]]):
                        result[k] = desc
                return result
    except Exception:
        pass
    return {}

def load_faction_rules_dict():
    result = {}
    for r in st.session_state.get("faction_special_rules", []):
        if not isinstance(r, dict): continue
        desc = r.get("description", "")
        for k in r.get("key", [r.get("name", "")]):
            if k: result[k] = desc
    return result

@st.cache_data
def load_factions():
    factions = {}; games = set()
    try:
        FACTIONS_DIR = Path(__file__).resolve().parent / "repositories" / "data" / "factions"
        for fp in FACTIONS_DIR.glob("*.json"):
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                game = data.get("game"); faction = data.get("faction")
                if game and faction:
                    if game not in factions: factions[game] = {}
                    data.setdefault("faction_special_rules", []); data.setdefault("spells", {}); data.setdefault("units", [])
                    factions[game][faction] = data; games.add(game)
            except Exception as e:
                st.warning(f"Erreur chargement {fp.name}: {e}")
    except Exception as e:
        st.error(f"Erreur chargement des factions: {e}"); return {}, []
    return factions, sorted(games) if games else list(GAME_CONFIG.keys())

if st.session_state.page == "setup":
    factions_by_game, games = load_factions()
    if not games: st.error("Aucun jeu trouvé"); st.stop()

    if st.session_state.get("_qr_pending"):
        _qf = st.session_state.get("_qr_faction", "")
        _qg = st.session_state.get("_qr_game", "")
        _qu = st.session_state.get("_qr_units", [])
        _qp = st.session_state.get("_qr_pts", 0)
        _unit_lines = " · ".join(f"{u['n']} ({u['c']} pts)" for u in _qu)
        st.info(
            f"📲 **Liste reçue via QR code** — {_qg} / {_qf} / {_qp} pts\n\n"
            f"{_unit_lines}\n\n"
            f"Vérifiez le jeu et la faction puis cliquez **Construire l'armée**."
        )
        del st.session_state["_qr_pending"]

    current_game = st.session_state.get("game", games[0] if games else "")

    game_meta = {
        "Age of Fantasy":            {"color": "#2980b9", "short": "AoF"},
        "Age of Fantasy Regiments": {"color": "#8e44ad", "short": "AoF:R"},
        "Grimdark Future":           {"color": "#e74c3c", "short": "GDF"},
        "Grimdark Future Firefight":{"color": "#e67e22", "short": "GDF:FF"},
        "Age of Fantasy Skirmish":  {"color": "#27ae60", "short": "AoF:S"},
    }
    _BASE = Path(__file__).resolve().parent
    game_images = {
        "Age of Fantasy":            str(_BASE / "assets/games/aof_cover.jpg"),
        "Age of Fantasy Regiments": str(_BASE / "assets/games/aofr_cover.jpg"),
        "Grimdark Future":           str(_BASE / "assets/games/gf_cover.jpg"),
        "Grimdark Future Firefight":str(_BASE / "assets/games/gff_cover.jpg"),
        "Age of Fantasy Skirmish":  str(_BASE / "assets/games/aofs_cover.jpg"),
    }
    meta  = game_meta.get(current_game, {"color": "#2980b9", "short": "OPR"})
    acc   = meta["color"]
    short = meta["short"]

    vignette_html = ""
    img_path = game_images.get(current_game, "")
    if img_path and Path(img_path).exists():
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            vignette_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;height:100%;object-fit:cover;border-radius:8px;">'
        except Exception:
            pass
    if not vignette_html:
        vignette_html = f"""<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="32,6 58,54 6,54" stroke="{acc}" stroke-width="2.5" fill="none"/>
          <polygon points="32,16 50,48 14,48" stroke="{acc}" stroke-width="1.5" fill="{acc}" fill-opacity=".12"/>
          <polygon points="32,28 42,44 22,44" fill="{acc}" fill-opacity=".7"/>
        </svg>"""

    game_subtitles = {
        "Age of Fantasy":             "Construisez vos armées pour les batailles fantastiques",
        "Age of Fantasy Regiments":  "Forgez vos régiments pour la guerre des âges",
        "Grimdark Future":            "Forgez vos escouades pour les guerres du futur",
        "Grimdark Future Firefight": "Constituez vos escouades pour les combats rapprochés",
        "Age of Fantasy Skirmish":   "Composez vos bandes pour l'escarmouche fantastique",
    }
    game_subtitle = game_subtitles.get(current_game, "Construisez et commandez vos armées")

    tri_svg = f"""<svg style="position:absolute;inset:0;width:100%;height:100%;opacity:.18;"
        viewBox="0 0 900 220" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="tp" x="0" y="0" width="32" height="28" patternUnits="userSpaceOnUse">
          <polygon points="16,2 30,26 2,26" fill="none" stroke="white" stroke-width="1"/>
          <polygon points="0,28 14,4 28,28" fill="none" stroke="white" stroke-width=".6" opacity=".5"/>
        </pattern>
        <radialGradient id="rfade" cx="65%" cy="45%" r="58%">
          <stop offset="0%" stop-color="white" stop-opacity="1"/>
          <stop offset="55%" stop-color="white" stop-opacity=".25"/>
          <stop offset="100%" stop-color="white" stop-opacity="0"/>
        </radialGradient>
        <mask id="tm"><rect width="900" height="220" fill="url(#rfade)"/></mask>
      </defs>
      <rect width="900" height="220" fill="url(#tp)" mask="url(#tm)"/>
    </svg>"""
