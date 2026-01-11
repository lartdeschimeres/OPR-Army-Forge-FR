# Liste de l'armée (partie corrigée)
st.divider()
st.subheader("Liste de l'armée")

# Regrouper les unités avec leurs héros rattachés
army_display = []
for unit in st.session_state.army_list:
    if unit.get("attached_to_unit"):
        continue  # On affichera les héros rattachés avec leurs unités

    army_display.append({
        "type": "unit",
        "data": unit,
        "heroes": []
    })

# Ajouter les héros rattachés à leurs unités
for hero in st.session_state.army_list:
    if hero.get("attached_to_unit"):
        unit_name = hero["attached_to_unit"]
        for item in army_display:
            if item["data"]["name"] == unit_name:
                item["heroes"].append(hero)
                break

# Ajouter les héros indépendants
for unit in st.session_state.army_list:
    if unit.get("type", "").lower() == "hero" and not unit.get("attached_to_unit", False):
        army_display.append({
            "type": "hero",
            "data": unit
        })

# Affichage des unités et héros
for i, item in enumerate(army_display):
    if item["type"] == "unit":
        u = item["data"]
        height = 200
        if u.get("mount"):
            height += 40
        if u.get("options"):
            height += 20 * len(u["options"])
        if item["heroes"]:
            height += 60 * len(item["heroes"])

        base_rules = u.get("base_rules", [])
        weapon_rules = []
        option_rules = []
        mount_rules = []

        if 'current_weapon' in u and 'special_rules' in u['current_weapon']:
            weapon_rules = u['current_weapon']['special_rules']

        for opt_group in u.get("options", {}).values():
            if isinstance(opt_group, list):
                for opt in opt_group:
                    if 'special_rules' in opt:
                        option_rules.extend(opt['special_rules'])
            elif 'special_rules' in opt_group:
                option_rules.extend(opt_group['special_rules'])

        if 'mount' in u and 'special_rules' in u['mount']:
            mount_rules = u['mount']['special_rules']

        components.html(f"""
        <style>
        .card {{
            border:1px solid #ccc;
            border-radius:8px;
            padding:15px;
            margin-bottom:15px;
            background:#f9f9f9;
        }}
        .hero-card {{
            border:1px solid #e74c3c;
            border-radius:8px;
            padding:15px;
            margin-bottom:15px;
            background:#fff0f0;
            margin-left: 20px;
            margin-top: 10px;
        }}
        .badge {{
            display:inline-block;
            background:#4a89dc;
            color:white;
            padding:6px 12px;
            border-radius:15px;
            margin-right:8px;
            margin-bottom: 5px;
        }}
        .title {{
            font-weight:bold;
            color:#4a89dc;
            margin-top:10px;
        }}
        .valid {{
            border-left: 4px solid #2ecc71;
        }}
        .invalid {{
            border-left: 4px solid #e74c3c;
        }}
        </style>

        <div class="card {'valid' if st.session_state.is_army_valid else 'invalid'}" id="unit_{i}">
            <h4>{u['name']} — {u['cost']} pts</h4>

            <div style="margin-bottom: 10px;">
                <span class="badge">Qualité {u['quality']}+</span>
                <span class="badge">Défense {u['defense']}+</span>
                {'<span class="badge">Coriace {}</span>'.format(u.get('coriace', 0)) if u.get('coriace', 0) > 0 else ''}
            </div>

            {f'''
            <div class="title">Règles spéciales de base</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                {', '.join(base_rules) if base_rules else "Aucune"}
            </div>
            ''' if base_rules else ''}

            {f'''
            <div class="title">Arme équipée</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                {u.get('current_weapon', {}).get('name', 'Arme de base')} |
                A{u.get('current_weapon', {}).get('attacks', '?')} |
                PA({u.get('current_weapon', {}).get('armor_piercing', '?')})
                {" | " + ", ".join(weapon_rules) if weapon_rules else ""}
            </div>
            ''' if 'current_weapon' in u else ''}

            {f'''
            <div class="title">Options sélectionnées</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                {', '.join([opt['name'] for opt_group in u['options'].values() for opt in (opt_group if isinstance(opt_group, list) else [opt_group])])}
                {" | " + ", ".join(option_rules) if option_rules else ""}
            </div>
            ''' if u.get("options") else ''}

            {f'''
            <div class="title">Monture</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                <strong>{u.get('mount', {}).get('name', '')}</strong> (+{u.get('mount', {}).get('cost', 0)} pts)<br>
                {', '.join(mount_rules) if mount_rules else 'Aucune règle spéciale'}
            </div>
            ''' if u.get("mount") else ''}
        </div>
        """, height=height)

        # Afficher les héros rattachés à cette unité
        for j, hero in enumerate(item["heroes"]):
            hero_data = hero
            hero_rules = hero_data.get("base_rules", [])
            weapon_rules = []

            if 'current_weapon' in hero_data and 'special_rules' in hero_data['current_weapon']:
                weapon_rules = hero_data['current_weapon']['special_rules']

            components.html(f"""
            <div class="hero-card" id="hero_{i}_{j}">
                <h4>⚔️ {hero_data['name']} (Héros rattaché) — {hero_data['cost']} pts</h4>
                <div>
                    <span class="badge">Qualité {hero_data['quality']}+</span>
                    <span class="badge">Défense {hero_data['defense']}+</span>
                    {'<span class="badge">Coriace {}</span>'.format(hero_data.get('coriace', 0)) if hero_data.get('coriace', 0) > 0 else ''}
                </div>

                {f'''
                <div class="title">Règles spéciales</div>
                <div style="margin-left: 15px; margin-bottom: 10px;">
                    {', '.join(hero_rules) if hero_rules else "Aucune"}
                </div>
                ''' if hero_rules else ''}

                {f'''
                <div class="title">Arme équipée</div>
                <div style="margin-left: 15px; margin-bottom: 10px;">
                    {hero_data.get('current_weapon', {}).get('name', 'Arme de base')} |
                    A{hero_data.get('current_weapon', {}).get('attacks', '?')} |
                    PA({hero_data.get('current_weapon', {}).get('armor_piercing', '?')})
                    {" | " + ", ".join(weapon_rules) if weapon_rules else ""}
                </div>
                ''' if 'current_weapon' in hero_data else ''}
            </div>
            """, height=120)

        if st.button("❌ Supprimer", key=f"del_{i}"):
            st.session_state.army_total_cost -= u["cost"]
            st.session_state.army_list = [unit for unit in st.session_state.army_list if unit["name"] != u["name"] or unit.get("attached_to_unit") != u["name"]]
            st.rerun()

    else:  # Hero indépendant
        u = item["data"]
        height = 180
        if u.get("mount"):
            height += 40

        base_rules = u.get("base_rules", [])
        weapon_rules = []
        mount_rules = []

        if 'current_weapon' in u and 'special_rules' in u['current_weapon']:
            weapon_rules = u['current_weapon']['special_rules']

        if 'mount' in u and 'special_rules' in u['mount']:
            mount_rules = u['mount']['special_rules']

        components.html(f"""
        <div class="card {'valid' if st.session_state.is_army_valid else 'invalid'}" id="hero_{i}">
            <h4>{u['name']} — {u['cost']} pts (Héros indépendant)</h4>

            <div style="margin-bottom: 10px;">
                <span class="badge">Qualité {u['quality']}+</span>
                <span class="badge">Défense {u['defense']}+</span>
                {'<span class="badge">Coriace {}</span>'.format(u.get('coriace', 0)) if u.get('coriace', 0) > 0 else ''}
            </div>

            {f'''
            <div class="title">Règles spéciales</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                {', '.join(base_rules) if base_rules else "Aucune"}
            </div>
            ''' if base_rules else ''}

            {f'''
            <div class="title">Arme équipée</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                {u.get('current_weapon', {}).get('name', 'Arme de base')} |
                A{u.get('current_weapon', {}).get('attacks', '?')} |
                PA({u.get('current_weapon', {}).get('armor_piercing', '?')})
                {" | " + ", ".join(weapon_rules) if weapon_rules else ""}
            </div>
            ''' if 'current_weapon' in u else ''}

            {f'''
            <div class="title">Monture</div>
            <div style="margin-left: 15px; margin-bottom: 10px;">
                <strong>{u.get('mount', {}).get('name', '')}</strong> (+{u.get('mount', {}).get('cost', 0)} pts)<br>
                {', '.join(mount_rules) if mount_rules else 'Aucune règle spéciale'}
            </div>
            ''' if u.get("mount") else ''}
        </div>
        """, height=height)

        if st.button("❌ Supprimer", key=f"del_hero_{i}"):
            st.session_state.army_total_cost -= u["cost"]
            st.session_state.army_list = [unit for unit in st.session_state.army_list if unit["name"] != u["name"] or unit.get("type", "").lower() != "hero"]
            st.rerun()
