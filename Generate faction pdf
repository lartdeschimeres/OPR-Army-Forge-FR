"""
generate_faction_pdf.py
Génère un PDF de fiche de faction OPR à partir d'un JSON de faction.
Usage : generate_faction_pdf(data, output_path, history="")
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import HRFlowable
import json, os

# ── Palette ──────────────────────────────────────────────────────────────────
C = {
    'dark':      colors.HexColor('#1a1a2e'),
    'mid':       colors.HexColor('#16213e'),
    'accent':    colors.HexColor('#2c3e7a'),
    'hdr_bg':    colors.HexColor('#eef1f8'),
    'row_alt':   colors.HexColor('#f8f9fa'),
    'grey':      colors.HexColor('#6c757d'),
    'red':       colors.HexColor('#c0392b'),
    'white':     colors.white,
    'black':     colors.HexColor('#212529'),
    'border':    colors.HexColor('#dee2e6'),
    'border2':   colors.HexColor('#adb5bd'),
}

# ── Style factory ─────────────────────────────────────────────────────────────
def _S(name, **kw):
    d = dict(fontName='Helvetica', fontSize=8, textColor=C['black'],
             leading=10, spaceAfter=0, spaceBefore=0)
    d.update(kw)
    return ParagraphStyle(name, **d)

def _build_styles():
    return {
        # Page 1
        'main_title':  _S('main_title',  fontName='Helvetica-Bold', fontSize=22,
                           textColor=C['white'], leading=26, alignment=TA_CENTER),
        'version':     _S('version',     fontName='Helvetica', fontSize=9,
                           textColor=colors.HexColor('#aab4d4'), leading=11, alignment=TA_CENTER),
        'section_hdr': _S('section_hdr', fontName='Helvetica-Bold', fontSize=9,
                           textColor=C['black'], leading=11, spaceBefore=0, spaceAfter=3),
        'body':        _S('body',        fontName='Helvetica', fontSize=7.5,
                           textColor=C['black'], leading=10, spaceAfter=3, alignment=TA_JUSTIFY),
        'opr_link':    _S('opr_link',    fontName='Helvetica', fontSize=7.5,
                           textColor=C['grey'], leading=10, spaceAfter=3, alignment=TA_JUSTIFY),
        # Banners
        'banner':      _S('banner',      fontName='Helvetica-Bold', fontSize=11,
                           textColor=C['white'], leading=14),
        'cat_banner':  _S('cat_banner',  fontName='Helvetica-Bold', fontSize=9,
                           textColor=C['white'], leading=12),
        # Unité header
        'utitle':      _S('utitle',      fontName='Helvetica-Bold', fontSize=9,
                           textColor=C['black'], leading=11, alignment=TA_CENTER),
        'ucost':       _S('ucost',       fontName='Helvetica-Bold', fontSize=8.5,
                           textColor=C['red'], leading=10, alignment=TA_RIGHT),
        'stats':       _S('stats',       fontName='Helvetica-Bold', fontSize=6.5,
                           textColor=C['grey'], leading=8),
        'urules':      _S('urules',      fontName='Helvetica', fontSize=6.5,
                           textColor=C['black'], leading=8),
        # Tableau armes
        'th':          _S('th',          fontName='Helvetica-Bold', fontSize=6.5,
                           textColor=C['grey'], leading=8),
        'tw_b':        _S('tw_b',        fontName='Helvetica-Bold', fontSize=7,
                           textColor=C['black'], leading=9),
        'tw':          _S('tw',          fontName='Helvetica', fontSize=7,
                           textColor=C['black'], leading=9),
        'tw_sm':       _S('tw_sm',       fontName='Helvetica', fontSize=6.5,
                           textColor=C['black'], leading=8),
        # Options
        'opt_hdr':     _S('opt_hdr',     fontName='Helvetica-Bold', fontSize=6.5,
                           textColor=C['black'], leading=8, spaceBefore=2),
        'opt_line':    _S('opt_line',    fontName='Helvetica', fontSize=6.5,
                           textColor=C['black'], leading=8),
        'opt_cost':    _S('opt_cost',    fontName='Helvetica-Bold', fontSize=6.5,
                           textColor=C['red'], leading=8, alignment=TA_RIGHT),
        # Règles
        'rule_txt':    _S('rule_txt',    fontName='Helvetica', fontSize=6.5,
                           textColor=C['black'], leading=8.5, spaceAfter=3),
        # Récap
        'rec_hdr':     _S('rec_hdr',     fontName='Helvetica-Bold', fontSize=6.5,
                           textColor=C['black'], leading=8),
        'rec_name':    _S('rec_name',    fontName='Helvetica-Bold', fontSize=7,
                           textColor=C['black'], leading=9),
        'rec_cell':    _S('rec_cell',    fontName='Helvetica', fontSize=6.5,
                           textColor=C['black'], leading=8),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fr(r):
    s = str(r) if r is not None else '-'
    return s if s in ('Mêlée', '-') else f'{s}"'

def _pa(pa):
    return str(pa) if pa else '-'

def _wpstr(w):
    """Profil compact d'une arme : 12", A1, PA(1), Fiable"""
    rng = _fr(w.get('range'))
    att = w.get('attacks', '?')
    pa  = _pa(w.get('armor_piercing', 0))
    sr  = ', '.join(w.get('special_rules', [])) or ''
    parts = [rng, f'A{att}']
    if pa != '-': parts.append(f'PA({pa})')
    if sr: parts.append(sr)
    return ', '.join(parts)

def _banner(title, width, dark=True):
    bg  = C['dark'] if dark else C['accent']
    key = 'banner' if dark else 'cat_banner'
    t = Table([[Paragraph(title, ST[key])]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
    ]))
    return t

def _weapon_table(weapons, w):
    if not weapons: return None
    bw = weapons if isinstance(weapons, list) else [weapons]
    bw = [x for x in bw if isinstance(x, dict)]
    if not bw: return None
    cw = [w*0.36, w*0.12, w*0.09, w*0.08, w*0.35]
    rows = [[Paragraph(h, ST['th']) for h in ['Arme', 'Portée', 'Att', 'PA', 'Règles spé.']]]
    for x in bw:
        cnt = x.get('count', '')
        cn  = f'{cnt}x ' if cnt and cnt > 1 else ''
        rows.append([
            Paragraph(f"<b>{cn}{x.get('name','')}</b>", ST['tw_b']),
            Paragraph(_fr(x.get('range')),              ST['tw']),
            Paragraph(f"A{x.get('attacks','-')}",        ST['tw']),
            Paragraph(_pa(x.get('armor_piercing', 0)),   ST['tw']),
            Paragraph(', '.join(x.get('special_rules', [])) or '-', ST['tw_sm']),
        ])
    t = Table(rows, colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C['hdr_bg']),
        ('LINEBELOW',  (0,0), (-1,0), 0.4, C['border']),
        ('LINEBELOW',  (0,1), (-1,-1), 0.3, C['border']),
        ('LINEBEFORE', (1,0), (1,-1), 0.3, C['border']),
        ('TOPPADDING',    (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING',   (0,0), (-1,-1), 3),
        ('RIGHTPADDING',  (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t

def _upgrades_block(group, w):
    els = []
    desc = group.get('description', '')
    req  = group.get('requires', [])
    opts = group.get('options', [])
    req_str = f" <i>[{', '.join(req)}]</i>" if req else ''
    els.append(Paragraph(f'<b>{desc}</b>{req_str}', ST['opt_hdr']))
    cw2 = [w * 0.76, w * 0.24]
    for o in opts:
        name_o = o.get('name', '')
        cost_o = o.get('cost', 0)
        sr_o   = ', '.join(o.get('special_rules', []))
        w_o    = o.get('weapon')
        cost_s = f'+{cost_o} pts' if cost_o > 0 else 'Gratuit'
        det = ''
        if w_o:
            ws = w_o if isinstance(w_o, list) else [w_o]
            det = ', '.join(f"{x.get('name','')} ({_wpstr(x)})" for x in ws if isinstance(x, dict))
        elif sr_o:
            det = sr_o
        label = name_o if not det or det == name_o else f'{name_o} ({det})'
        row = Table([[
            Paragraph(label, ST['opt_line']),
            Paragraph(f"<font color='#c0392b'><b>{cost_s}</b></font>", ST['opt_cost']),
        ]], colWidths=cw2)
        row.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 0.2, colors.HexColor('#e9ecef')),
            ('TOPPADDING',    (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING',   (0,0), (-1,-1), 7),
            ('RIGHTPADDING',  (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        els.append(row)
    return els

def _unit_card(unit, w):
    """Retourne la Table complète d'une fiche unité."""
    rows_content = []
    name  = unit['name']
    cost  = unit.get('base_cost', '?')
    size  = unit.get('size', 1)
    qual  = unit.get('quality', '?')
    defe  = unit.get('defense', '?')
    cor   = unit.get('coriace')
    sr    = unit.get('special_rules', [])
    named = unit.get('unit_detail') == 'named_hero' or 'Unique' in sr

    # Titre
    star = '★ ' if named else ''
    hdr = Table([[
        Paragraph(f'<b>{star}{name} [{size}]</b>', ST['utitle']),
        Paragraph(f'<b>{cost} pts</b>', ST['ucost']),
    ]], colWidths=[w * 0.72, w * 0.28])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C['hdr_bg']),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.4, C['border']),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    rows_content.append(hdr)

    # Stats
    bs = [f'Qualité {qual}+', f'Défense {defe}+']
    if cor: bs.append(f'Coriace {cor}')
    stat_t = Table([[Paragraph(f"<b>{'  |  '.join(bs)}</b>", ST['stats'])]], colWidths=[w])
    stat_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C['hdr_bg']),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, C['border']),
    ]))
    rows_content.append(stat_t)

    # Règles spéciales
    if sr:
        sr_t = Table([[Paragraph(', '.join(sr), ST['urules'])]], colWidths=[w])
        sr_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C['hdr_bg']),
            ('TOPPADDING',    (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING',   (0,0), (-1,-1), 5),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, C['border']),
        ]))
        rows_content.append(sr_t)

    # Armes de base
    wt = _weapon_table(unit.get('weapon', []), w)
    if wt: rows_content.append(wt)

    # Upgrade groups
    for g in unit.get('upgrade_groups', []):
        rows_content += _upgrades_block(g, w)

    # Encadrement
    card = Table([[r] for r in rows_content], colWidths=[w])
    card.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, C['border']),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
    ]))
    return card

def _recap_table(units, w):
    cw = [w*0.21, w*0.05, w*0.05, w*0.31, w*0.28, w*0.07]
    rows = [[Paragraph(h, ST['rec_hdr'])
             for h in ['Nom [taille]', 'Qua', 'Déf', 'Équipement', 'Règles spéciales', 'Coût']]]
    for u in units:
        bw = u.get('weapon', [])
        if isinstance(bw, dict): bw = [bw]
        sz = u.get('size', 1)
        eq = []
        for x in bw:
            if isinstance(x, dict):
                cnt = x.get('count', '')
                cs  = f'{cnt}x ' if cnt and cnt > 1 else (f'{sz}x ' if sz > 1 else '1x ')
                eq.append(f"{cs}{x['name']} ({_wpstr(x)})")
        rows.append([
            Paragraph(f"<b>{u['name']} [{sz}]</b>", ST['rec_name']),
            Paragraph(f"{u.get('quality','?')}+",   ST['rec_cell']),
            Paragraph(f"{u.get('defense','?')}+",   ST['rec_cell']),
            Paragraph('\n'.join(eq),                ST['rec_cell']),
            Paragraph(', '.join(u.get('special_rules', [])), ST['rec_cell']),
            Paragraph(f"{u.get('base_cost','?')} pts", ST['rec_cell']),
        ])
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C['hdr_bg']),
        ('LINEBELOW',  (0,0), (-1,0), 0.5, C['border2']),
        ('GRID',       (0,0), (-1,-1), 0.3, C['border']),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [C['white'], C['row_alt']]),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING',   (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t

def _rules_3col(items, fn_row, cw3, gap):
    per = max(1, (len(items) + 2) // 3)
    cols = [items[i*per:(i+1)*per] for i in range(3)]
    cells = []
    for col in cols:
        cell = []
        for item in col:
            cell += fn_row(item)
        cells.append(cell if cell else [Spacer(1, 1)])
    while len(cells) < 3:
        cells.append([Spacer(1, 1)])
    t = Table([cells], colWidths=[cw3, cw3, cw3])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 4),
        ('RIGHTPADDING',  (0,0), (-1,-1), 4),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    return t

def _two_col_cards(cat_units, CW, GAP):
    """Renvoie les flowables pour les fiches en 2 colonnes."""
    els = []
    for i in range(0, len(cat_units), 2):
        L = _unit_card(cat_units[i], CW)
        if i + 1 < len(cat_units):
            R = _unit_card(cat_units[i+1], CW)
            row_data = [[L, Spacer(GAP, 1), R]]
        else:
            row_data = [[L, Spacer(GAP, 1), Spacer(CW, 1)]]
        row_t = Table(row_data, colWidths=[CW, GAP, CW])
        row_t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ]))
        els.append(row_t)
        els.append(Spacer(1, 3))
    return els


# ── Entrée principale ─────────────────────────────────────────────────────────
OPR_TEXT = (
    "OPR (www.onepagerules.com) héberge de nombreux jeux gratuits conçus pour "
    "être rapides à apprendre et faciles à jouer.\n\n"
    "Ce projet a été réalisé par des joueurs, pour des joueurs, et ne peut exister "
    "que grâce au généreux soutien de notre formidable communauté !\n\n"
    "Si vous souhaitez soutenir le développement de nos jeux, vous pouvez faire un "
    "don sur : www.patreon.com/onepagerules.\n\n"
    "<b>Merci de jouer à OPR !</b>"
)

def generate_faction_pdf(data, output_path, history=""):
    global ST
    ST = _build_styles()

    PW, PH = A4
    M   = 13 * mm
    GAP = 4  * mm
    CW  = (PW - 2*M - GAP) / 2   # largeur colonne 2-col
    FW  = PW - 2*M               # pleine largeur

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=M,
        title=f"{data['faction']} — {data['game']}",
    )

    story = []
    cw3 = (FW - 2*GAP) / 3

    # ── PAGE 1 : Titre + Introduction / Histoire ──────────────────────────────

    # Bandeau titre
    title_t = Table([[Paragraph(data['faction'].upper(), ST['main_title'])]], colWidths=[FW])
    title_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C['dark']),
        ('TOPPADDING',    (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ]))
    story.append(title_t)

    ver_t = Table([[Paragraph(f"{data['game']} — v{data['version']}", ST['version'])]], colWidths=[FW])
    ver_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C['mid']),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(ver_t)
    story.append(Spacer(1, 6))

    # Colonne gauche : Introduction + Au sujet d'OPR
    left_els = []
    left_els.append(HRFlowable(width=CW, thickness=1.5, color=C['dark'], spaceAfter=4))
    left_els.append(Paragraph('INTRODUCTION', ST['section_hdr']))
    desc = data.get('description', '')
    for para in desc.split('\n'):
        para = para.strip()
        if para:
            left_els.append(Paragraph(para, ST['body']))
    left_els.append(Spacer(1, 8))
    left_els.append(HRFlowable(width=CW, thickness=1.5, color=C['dark'], spaceAfter=4))
    left_els.append(Paragraph("AU SUJET D'OPR", ST['section_hdr']))
    for para in OPR_TEXT.split('\n\n'):
        para = para.strip()
        if para:
            left_els.append(Paragraph(para.replace('\n', ' '), ST['body']))

    # Colonne droite : Histoire de la faction
    right_els = []
    if history:
        right_els.append(HRFlowable(width=CW, thickness=1.5, color=C['dark'], spaceAfter=4))
        right_els.append(Paragraph('HISTOIRE DE LA FACTION', ST['section_hdr']))
        for para in history.split('\n'):
            para = para.strip()
            if para:
                right_els.append(Paragraph(para, ST['body']))

    # Assemblage 2 colonnes page 1
    intro_tbl = Table([[left_els, right_els]], colWidths=[CW, CW])
    intro_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('INNERGRID', (0,0), (-1,-1), 0, C['white']),
        # Légère séparation verticale entre colonnes
        ('LINEBEFORE', (1,0), (1,-1), 0.5, C['border']),
        ('LEFTPADDING', (1,0), (1,-1), 8),
    ]))
    story.append(intro_tbl)
    story.append(PageBreak())

    # ── PAGE 2 : Récapitulatif ────────────────────────────────────────────────
    story.append(_banner('RÉSUMÉ DE LA FACTION', FW))
    story.append(Spacer(1, 3))

    CATS_RECAP = [
        ('HÉROS',           ['hero', 'named_hero']),
        ('UNITÉS DE BASE',  ['unit']),
        ('VÉHICULES',       ['light_vehicle', 'vehicle', 'titan']),
    ]
    for cn, types in CATS_RECAP:
        us = [u for u in data['units'] if u.get('unit_detail', u.get('type')) in types]
        if not us: continue
        story.append(_banner(cn, FW, dark=False))
        story.append(_recap_table(us, FW))
        story.append(Spacer(1, 3))
    story.append(PageBreak())

    # ── PAGE 3 : Règles spéciales + Sorts ────────────────────────────────────
    story.append(_banner('RÈGLES SPÉCIALES', FW))
    story.append(Spacer(1, 3))

    rules  = data.get('faction_special_rules', [])
    spells = data.get('spells', {})

    def rule_row(r):
        return [Paragraph(f"<b>{r['name']}</b> : {r['description']}", ST['rule_txt'])]

    story.append(_rules_3col(rules, rule_row, cw3, GAP))

    if spells:
        story.append(Spacer(1, 6))
        story.append(_banner('SORTS', FW, dark=False))
        story.append(Spacer(1, 3))
        spell_list = [(k, v.get('description', v) if isinstance(v, dict) else v)
                      for k, v in spells.items()]
        def spell_row(s):
            return [Paragraph(f"<b>{s[0]}</b> : {s[1]}", ST['rule_txt'])]
        story.append(_rules_3col(spell_list, spell_row, cw3, GAP))

    story.append(PageBreak())

    # ── FICHES UNITÉS ─────────────────────────────────────────────────────────
    # Ordre : Héros → Unités → Véhicules légers → Véhicules → Titans → Nommés
    UNIT_CATS = [
        ('HÉROS',                ['hero']),
        ('UNITÉS DE BASE',       ['unit']),
        ('VÉHICULES LÉGERS',     ['light_vehicle']),
        ('VÉHICULES / MONSTRES', ['vehicle']),
        ('TITANS',               ['titan']),
        ('PERSONNAGES NOMMÉS',   ['named_hero']),
    ]

    for cat_name, types in UNIT_CATS:
        cat_units = [u for u in data['units']
                     if u.get('unit_detail', u.get('type')) in types]
        if not cat_units: continue
        story.append(_banner(cat_name, FW))
        story.append(Spacer(1, 4))
        story += _two_col_cards(cat_units, CW, GAP)

    doc.build(story)
    return output_path


# ── Test autonome ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    json_path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/soeurs_benies.json'
    out_path  = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/faction_out.pdf'
    with open(json_path, encoding='utf-8') as f:
        d = json.load(f)
    # Histoire extraite du PDF source (document index 3)
    history = (
        "L'ascension d'un généticien, connu dans l'histoire sous le nom du Père-Fondateur, "
        "au rang de chef suprême de l'humanité, a entraîné une guerre dévastatrice qui a "
        "rapidement englouti la Terre et ses colonies. La guerre devenant de plus en plus "
        "dévastatrice, de nombreux survivants ont commencé à chercher un moyen de s'échapper. "
        "Un groupe de réfugiés désespérés réquisitionna le vaisseau amiral du Père-Fondateur "
        "afin d'échapper au conflit, à la tête d'une flotte de survivants partageant les mêmes idées.\n\n"
        "Le Père-Fondateur rattrapa la flotte de réfugiés et la força à un engagement à la limite "
        "de l'espace connu. Cherchant à récupérer son vaisseau, ses forces mena un certain nombre "
        "d'attaques d'abordage contre la flotte de réfugiés. Les Frères de Bataille surpassèrent "
        "facilement la plupart des forces réfugiées, jusqu'à ce qu'une mystérieuse jeune femme "
        "commence à les rallier, faisant preuve d'une capacité presque surnaturelle à inspirer la "
        "confiance à ses forces et la peur à ses ennemis. Ensemble, ils repoussèrent l'attaque "
        "initiale et certains commencèrent à espérer qu'ils parviennent à s'échapper.\n\n"
        "Un énorme vortex se forma autour des deux flottes. En un instant, elles furent endommagées "
        "et séparées par le vortex. La flotte de colonie fut dispersée, mais beaucoup cherchèrent "
        "et suivirent la mystérieuse femme, à la recherche de mondes propices à l'installation. "
        "Sous son commandement, une flotte de fortune s'installa sur quelques mondes dispersés où "
        "ses talents de diplomate leur permirent de prospérer dans une paix relative.\n\n"
        "Peu après son arrivée sur Sirius, elle commença à développer des capacités psychiques. "
        "Ces capacités lui attirèrent de nombreux acolytes et adeptes, et beaucoup la nommèrent "
        "leur Reine-Déesse. Craignant le retour des Frères de Bataille, la Reine-Déesse décida "
        "de se concentrer sur la formation de son propre groupe de guerrières triés sur le volet. "
        "Celles-ci devinrent les Sœurs Bénies et nombre d'entre elles en vinrent à croire que la "
        "Reine-Déesse était divine.\n\n"
        "Après qu'elle se soit sacrifiée pour tuer un Avatar de la Luxure, le culte de la "
        "Reine-Déesse se répandit et de nombreux ordres se formèrent en son honneur. Ces ordres "
        "sont souvent appelés à protéger des mondes alliés en tant que gardiens de la paix et "
        "arbitres. Les Sœurs Bénies comptent sur des volontaires, des fournitures et d'autres "
        "dons de mondes et d'adeptes fidèles.\n\n"
        "Malheureusement de nombreux mondes considèrent leur aide comme désignée, ce qui rend "
        "les dons difficiles à obtenir et oblige les ordres à passer par de longues périodes de "
        "jeûne et de réflexion pour survivre. En cas d'échec, les ordres se voient contraints de "
        "se retourner contre ceux qu'ils cherchaient à protéger et d'instaurer la loi martiale "
        "pour survivre.\n\n"
        "Comment resterez-vous une lueur d'espoir dans ce sombre avenir ?"
    )
    generate_faction_pdf(d, out_path, history=history)
    size = os.path.getsize(out_path)
    print(f"✅ {out_path}  ({size//1024} Ko)")
