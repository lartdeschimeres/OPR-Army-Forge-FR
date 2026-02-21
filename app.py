# ======================================================
# EXPORT HTML - VERSION MODIFIÉE POUR GÉRER LES RÔLES AVEC ARMES
# ======================================================
def export_html(army_list, army_name, army_limit):
    def esc(txt):
        return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def format_weapon(weapon):
        """Formate une arme pour l'affichage"""
        if not weapon:
            return "Aucune arme"

        range_text = weapon.get('range', '-')
        attacks = weapon.get('attacks', '-')
        ap = weapon.get('armor_piercing', '-')
        special_rules = weapon.get('special_rules', [])

        if range_text == "-" or range_text is None or range_text.lower() == "mêlée":
            range_text = "Mêlée"
        else:
            range_text = range_text.replace('"', '').replace("'", "")

        result = f"{range_text} | A{attacks}"

        if ap not in ("-", 0, "0", None):
            result += f" | PA{ap}"

        if special_rules:
            result += f" | {', '.join(special_rules)}"

        return result

    def get_special_rules(unit):
        """Extraire toutes les règles spéciales de l'unité SAUF celles des armes"""
        rules = set()

        # 1. Règles spéciales de base de l'unité
        if "special_rules" in unit:
            for rule in unit["special_rules"]:
                if isinstance(rule, str):
                    rules.add(rule)

        # 2. Règles spéciales des améliorations (hors armes)
        if "options" in unit:
            for group_name, opts in unit["options"].items():
                if isinstance(opts, list):
                    for opt in opts:
                        # Ajouter les règles spéciales des rôles (mais pas celles des armes)
                        if "special_rules" in opt:
                            for rule in opt["special_rules"]:
                                if isinstance(rule, str):
                                    # Vérifier si cette règle n'est pas déjà dans une arme
                                    is_weapon_rule = False
                                    if "weapon" in opt:
                                        weapons = opt["weapon"]
                                        if isinstance(weapons, list):
                                            for weapon in weapons:
                                                if isinstance(weapon, dict) and "special_rules" in weapon:
                                                    if rule in weapon["special_rules"]:
                                                        is_weapon_rule = True
                                                        break
                                        elif isinstance(weapons, dict) and "special_rules" in weapons:
                                            if rule in weapons["special_rules"]:
                                                is_weapon_rule = True

                                    if not is_weapon_rule:
                                        rules.add(rule)

        # 3. Règles spéciales de la monture
        if "mount" in unit and unit.get("mount"):
            mount_data = unit["mount"].get("mount", {})
            if "special_rules" in mount_data:
                for rule in mount_data["special_rules"]:
                    if isinstance(rule, str):
                        rules.add(rule)

        return sorted(rules, key=lambda x: x.lower().replace('é', 'e').replace('è', 'e'))

    def get_french_type(unit):
        """Retourne le type français basé sur unit_detail"""
        if unit.get('type') == 'hero':
            return 'Héros'
        unit_detail = unit.get('unit_detail', 'unit')
        type_mapping = {
            'hero': 'Héros',
            'named_hero': 'Héros nommé',
            'unit': 'Unité de base',
            'light_vehicle': 'Véhicule léger',
            'vehicle': 'Véhicule/Monstre',
            'titan': 'Titan'
        }
        return type_mapping.get(unit_detail, 'Unité')

    # Trier la liste pour afficher les héros en premier
    sorted_army_list = sorted(army_list, key=lambda x: 0 if x.get("type") == "hero" else 1)

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Liste d'Armée OPR - {esc(army_name)}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-dark: #f8f9fa;
  --bg-card: #ffffff;
  --bg-header: #e9ecef;
  --accent: #3498db;
  --text-main: #212529;
  --text-muted: #6c757d;
  --border: #dee2e6;
  --cost-color: #ff6b6b;
  --tough-color: #e74c3c;
}}

body {{
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: 'Inter', sans-serif;
  margin: 0;
  padding: 20px;
  line-height: 1.5;
}}

.army {{
  max-width: 800px;
  margin: 0 auto;
}}

.army-title {{
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}}

.army-summary {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  padding: 16px;
  border-radius: 8px;
  margin: 20px 0;
  border: 1px solid var(--border);
}}

.unit-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.unit-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}}

.unit-name {{
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.unit-cost {{
  font-family: monospace;
  font-size: 18px;
  font-weight: bold;
  color: var(--cost-color);
}}

.unit-type {{
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}}

.stats-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  background: var(--bg-header);
  padding: 12px;
  border-radius: 6px;
  text-align: center;
  font-size: 12px;
  margin: 12px 0;
}}

.stat-item {{
  padding: 5px;
  display: flex;
  flex-direction: column;
  align-items: center;
}}

.stat-label {{
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 5px;
}}

.stat-value {{
  font-weight: bold;
  font-size: 16px;
  color: var(--text-main);
}}

.section-title {{
  font-weight: 600;
  margin: 15px 0 8px 0;
  color: var(--text-main);
  font-size: 14px;
}}

.weapon-item {{
  background: var(--bg-header);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
}}

.weapon-name {{
  font-weight: 500;
  color: var(--text-main);
  flex: 1;
}}

.weapon-stats {{
  text-align: right;
  white-space: nowrap;
  flex: 1;
}}

.rules-section {{
  margin: 12px 0;
}}

.rules-title {{
  font-weight: 600;
  margin-bottom: 6px;
  color: #3498db;
  font-size: 14px;
}}

.rules-list {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}}

.rule-tag {{
  background: var(--bg-header);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-main);
}}

.summary-cost {{
  font-family: monospace;
  font-size: 24px;
  font-weight: bold;
  color: var(--cost-color);
}}

.faction-rules h3, .spells-section h3 {{
  color: #3498db !important;
}}

.rule-name {{
  color: #3498db;
  font-weight: bold;
}}

.spell-name {{
  color: #3498db;
  font-weight: bold;
}}

.role-section {{
  background: rgba(240, 248, 255, 0.5);
  padding: 10px;
  border-radius: 6px;
  margin: 15px 0;
  border-left: 4px solid #3498db;
}}

.role-title {{
  font-weight: 600;
  color: #3498db;
  margin-bottom: 5px;
}}

@media print {{
  body {{
    background: white;
    color: black;
  }}
  .unit-card, .army-summary {{
    background: white;
    border: 1px solid #ccc;
    page-break-inside: avoid;
  }}
}}
</style>
</head>
<body>
<div class="army">
  <!-- Titre de la liste -->
  <div class="army-title">
    {esc(army_name)} - {sum(unit['cost'] for unit in sorted_army_list)}/{army_limit} pts
  </div>

  <!-- Résumé de l'armée -->
  <div class="army-summary">
    <div style="font-size: 14px; color: var(--text-main);">
      <span style="color: var(--text-muted);">Nombre d'unités:</span>
      <strong style="margin-left: 8px; font-size: 18px;">{len(sorted_army_list)}</strong>
    </div>
    <div class="summary-cost">
      {sum(unit['cost'] for unit in sorted_army_list)}/{army_limit} pts
    </div>
  </div>
"""

    for unit in sorted_army_list:
        name = esc(unit.get("name", "Unité"))
        cost = unit.get("cost", 0)
        quality = esc(unit.get("quality", "-"))
        defense = esc(unit.get("defense", "-"))
        unit_type_french = get_french_type(unit)
        unit_size = unit.get("size", 10)

        if unit.get("type") == "hero":
            unit_size = 1

        # Calcul de la valeur de Coriace
        tough_value = unit.get("coriace", 0)

        # Récupération des armes
        weapons = unit.get("weapon", [])
        if not isinstance(weapons, list):
            weapons = [weapons]

        # Récupération des règles spéciales (sans celles des armes)
        special_rules = get_special_rules(unit)

        # Récupération des options et montures
        options = unit.get("options", {})
        mount = unit.get("mount", None)

        html += f'''
<div class="unit-card">
  <div class="unit-header">
    <div>
      <h3 class="unit-name">
        {name}
        <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">[{unit_size}]</span>
      </h3>
      <div class="unit-type">
        {"★" if unit.get("type") == "hero" else "🛡️"} {unit_type_french}
      </div>
    </div>
    <div class="unit-cost">{cost} pts</div>
  </div>

  <div class="stats-grid">
    <div class="stat-item">
      <div class="stat-label"><span>⚔️</span> Qualité</div>
      <div class="stat-value">{quality}+</div>
    </div>
    <div class="stat-item">
      <div class="stat-label"><span>🛡️</span> Défense</div>
      <div class="stat-value">{defense}+</div>
    </div>
'''

        # Affichage de la Coriace
        if tough_value > 0:
            html += f'''
    <div class="stat-item">
      <div class="stat-label"><span>❤️</span> Coriace</div>
      <div class="stat-value" style="color: var(--tough-color);">{tough_value}</div>
    </div>
'''

        html += '</div>'  # Fermeture du stats-grid

        # Armes (incluant les armes des rôles)
        if weapons:
            html += '<div class="section-title">Armes:</div>'
            for weapon in weapons:
                if weapon and isinstance(weapon, dict):
                    html += f'''
    <div class="weapon-item">
      <div class="weapon-name">{esc(weapon.get('name', 'Arme'))}</div>
      <div class="weapon-stats">{format_weapon(weapon)}</div>
    </div>
'''

        # Rôles (pour les héros et titans)
        if options:
            for group_name, opts in options.items():
                if isinstance(opts, list) and opts:
                    for opt in opts:
                        if "weapon" in opt:  # C'est un rôle avec des armes
                            role_name = opt.get("name", "Rôle")
                            role_weapons = opt.get("weapon", [])
                            role_special_rules = opt.get("special_rules", [])

                            html += f'''
    <div class="role-section">
      <div class="role-title">Rôle: {esc(role_name)}</div>
'''

                            # Armes du rôle
                            if role_weapons:
                                if isinstance(role_weapons, list):
                                    for weapon in role_weapons:
                                        if isinstance(weapon, dict):
                                            html += f'''
        <div class="weapon-item" style="margin-left: 15px;">
          <div class="weapon-name">{esc(weapon.get('name', 'Arme du rôle'))}</div>
          <div class="weapon-stats">{format_weapon(weapon)}</div>
        </div>
'''
                                else:
                                    html += f'''
        <div class="weapon-item" style="margin-left: 15px;">
          <div class="weapon-name">{esc(role_weapons.get('name', 'Arme du rôle'))}</div>
          <div class="weapon-stats">{format_weapon(role_weapons)}</div>
        </div>
'''

                            # Règles spéciales du rôle (hors armes)
                            role_rules_to_show = []
                            for rule in role_special_rules:
                                if isinstance(rule, str):
                                    is_weapon_rule = False
                                    if isinstance(role_weapons, list):
                                        for weapon in role_weapons:
                                            if isinstance(weapon, dict) and "special_rules" in weapon:
                                                if rule in weapon["special_rules"]:
                                                    is_weapon_rule = True
                                                    break
                                    elif isinstance(role_weapons, dict) and "special_rules" in role_weapons:
                                        if rule in role_weapons["special_rules"]:
                                            is_weapon_rule = True

                                    if not is_weapon_rule:
                                        role_rules_to_show.append(rule)

                            if role_rules_to_show:
                                html += '''
      <div style="margin-left: 15px; margin-top: 5px;">
        <div style="font-weight: 600; color: #3498db; font-size: 12px;">Règles spéciales du rôle:</div>
        <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 3px;">
'''
                                for rule in role_rules_to_show:
                                    html += f'<span class="rule-tag">{esc(rule)}</span>'
                                html += '''
        </div>
      </div>
'''
                            html += '''
    </div>
'''

        # Règles spéciales (hors armes et hors règles des rôles déjà affichées)
        if special_rules:
            html += '''
  <div class="rules-section">
    <div class="rules-title">Règles spéciales:</div>
    <div class="rules-list">
'''
            for rule in special_rules:
                html += f'<span class="rule-tag">{esc(rule)}</span>'
            html += '''
    </div>
  </div>
'''

        # Améliorations sélectionnées (hors rôles)
        if options:
            has_non_role_options = False
            for group_name, opts in options.items():
                if isinstance(opts, list) and opts:
                    for opt in opts:
                        if "weapon" not in opt:  # Ce n'est pas un rôle
                            has_non_role_options = True
                            break
                    if has_non_role_options:
                        break

            if has_non_role_options:
                html += '''
  <div class="upgrades-section">
    <div class="rules-title">Améliorations sélectionnées:</div>
'''
                for group_name, opts in options.items():
                    if isinstance(opts, list) and opts:
                        for opt in opts:
                            if "weapon" not in opt:  # Ce n'est pas un rôle
                                html += f'''
    <div class="upgrade-item">
      <div class="upgrade-name">{esc(opt.get("name", ""))}</div>
'''
                                if 'special_rules' in opt and opt['special_rules']:
                                    html += f'<div style="font-size: 10px; color: var(--text-muted);">({", ".join(opt["special_rules"])})</div>'
                                html += '''
    </div>
'''
                html += '''
  </div>
'''

        # Monture
        if mount:
            mount_data = mount.get("mount", {})
            mount_name = esc(mount.get("name", "Monture"))
            mount_weapons = mount_data.get("weapon", [])

            html += f'''
    <div class="mount-section" style="background: rgba(150, 150, 150, 0.1); border: 1px solid rgba(150, 150, 150, 0.3);">
        <div class="mount-title">
          <span>🐴</span>
          <span style="color: var(--text-main);">{mount_name}</span>
        </div>
'''

            stats_parts = []
            if 'quality' in mount_data:
                stats_parts.append(f"Qualité {mount_data['quality']}+")
            if 'defense' in mount_data:
                stats_parts.append(f"Défense {mount_data['defense']}+")
            if stats_parts:
                html += f'''
    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">
      {', '.join(stats_parts)}
    </div>
'''

            if mount_weapons:
                html += '''
    <div style="margin-top: 8px;">
      <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-main);">Armes:</div>
      <div class="weapon-list">
'''
                for weapon in mount_weapons:
                    if weapon:
                        html += f'''
        <div class="weapon-item">
          <div class="weapon-name">{esc(weapon.get('name', 'Arme'))}</div>
          <div class="weapon-stats">{format_weapon(weapon)}</div>
        </div>
'''
                html += '''
      </div>
    </div>
'''

            html += '''
  </div>
'''

        html += '</div>'

    # Légende des règles spéciales de la faction
    if sorted_army_list and hasattr(st.session_state, 'faction_special_rules') and st.session_state.faction_special_rules:
        faction_rules = st.session_state.faction_special_rules
        all_rules = [rule for rule in faction_rules if isinstance(rule, dict)]

        if all_rules:
            html += '''
<div class="faction-rules">
  <h3 style="text-align: center; color: #3498db; border-top: 1px solid var(--border); padding-top: 10px; margin-bottom: 15px;">
    Légende des règles spéciales de la faction
  </h3>
  <div style="display: flex; flex-wrap: wrap;">
'''

            half = len(all_rules) // 2
            if len(all_rules) % 2 != 0:
                half += 1

            html += '<div class="rule-column" style="flex: 1; min-width: 300px; padding-right: 15px;">'
            for rule in sorted(all_rules[:half], key=lambda x: x.get('name', '').lower().replace('é', 'e').replace('è', 'e')):
                if isinstance(rule, dict):
                    html += f'''
    <div class="rule-item">
      <div class="rule-name" style="color: #3498db; font-weight: bold;">{esc(rule.get('name', ''))}:</div>
      <div class="rule-description">{esc(rule.get('description', ''))}</div>
    </div>
'''
            html += '</div>'

            html += '<div class="rule-column" style="flex: 1; min-width: 300px; padding-left: 15px;">'
            for rule in sorted(all_rules[half:], key=lambda x: x.get('name', '').lower().replace('é', 'e').replace('è', 'e')):
                if isinstance(rule, dict):
                    html += f'''
    <div class="rule-item">
      <div class="rule-name" style="color: #3498db; font-weight: bold;">{esc(rule.get('name', ''))}:</div>
      <div class="rule-description">{esc(rule.get('description', ''))}</div>
    </div>
'''
            html += '</div>'

            html += '''
  </div>
</div>
'''

    # Légende des sorts de la faction
    if sorted_army_list and hasattr(st.session_state, 'faction_spells') and st.session_state.faction_spells:
        spells = st.session_state.faction_spells
        all_spells = [{"name": name, "details": details} for name, details in spells.items() if isinstance(details, dict)]

        if all_spells:
            html += '''
<div class="spells-section">
  <h3 style="text-align: center; color: #3498db; border-top: 1px solid var(--border); padding-top: 10px; margin-bottom: 15px;">
    Légende des sorts de la faction
  </h3>
  <div style="display: flex; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 100%;">
'''
            for spell in sorted(all_spells, key=lambda x: x['name'].lower().replace('é', 'e').replace('è', 'e')):
                if isinstance(spell, dict):
                    html += f'''
      <div class="spell-item" style="margin-bottom: 12px;">
        <div>
          <span class="spell-name" style="color: #3498db; font-weight: bold;">{esc(spell.get('name', ''))}</span>
          <span class="spell-cost"> ({spell.get('details', {}).get('cost', '?')})</span>
        </div>
        <div class="rule-description">{esc(spell.get('details', {}).get('description', ''))}</div>
      </div>
'''
            html += '''
    </div>
  </div>
</div>
'''

    html += '''
<div style="text-align: center; margin-top: 20px; font-size: 12px; color: var(--text-muted);">
  Généré par OPR ArmyBuilder FR
</div>
</div>
</body>
</html>
'''
    return html
