# PAGE 3 — Composition de l'armée (partie modifiée pour l'affichage)
if st.session_state.page == "army":
    # ... (le reste du code reste inchangé jusqu'à la partie d'affichage)

    # Liste de l'armée (affichage sous forme de fiches synthétiques)
    st.divider()
    st.subheader("Liste de l'armée")

    for i, u in enumerate(st.session_state.army_list):
        # Calcul de la valeur totale de Coriace
        coriace_value = 0
        if u.get('coriace', 0) > 0:
            coriace_value = u.get('coriace', 0)

        # Calcul des règles spéciales de Coriace
        coriace_rules = []
        for rule in u.get("base_rules", []):
            match = re.search(r'Coriace \((\d+)\)', rule)
            if match:
                coriace_value += int(match.group(1))
                coriace_rules.append(rule)

        # Calcul de la hauteur en fonction des éléments à afficher
        height = 200
        if u.get("mount"):
            height += 40
        if u.get("options"):
            height += 20 * len([k for k in u["options"].keys() if k != "Améliorations"])
        if "Améliorations" in u.get("options", {}) and u.get("type", "").lower() != "hero":
            height += 20
        if u.get("mount"):
            height += 20

        # Génération du HTML pour la fiche
        html_content = f"""
        <style>
        .army-card {{
            border:1px solid #4a89dc;
            border-radius:8px;
            padding:15px;
            margin-bottom:15px;
            background:#f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .badge {{
            display:inline-block;
            background:#4a89dc;
            color:white;
            padding:6px 12px;
            border-radius:15px;
            margin-right:8px;
            margin-bottom:5px;
            font-size: 0.9em;
        }}
        .title {{
            font-weight:bold;
            color:#4a89dc;
            margin-top:10px;
            margin-bottom:5px;
        }}
        .section {{
            margin-bottom:10px;
        }}
        .valid {{
            border-left: 4px solid #2ecc71;
        }}
        .invalid {{
            border-left: 4px solid #e74c3c;
        }}
        </style>

        <div class="army-card {'valid' if st.session_state.is_army_valid else 'invalid'}">
            <h4 style="margin-top:0; margin-bottom:10px;">{u['name']} — {u['cost']} pts</h4>

            <div class="section">
                <span class="badge">Qualité {u['quality']}+</span>
                <span class="badge">Défense {u['defense']}+</span>
        """

        if coriace_value > 0:
            html_content += f'<span class="badge">Coriace {coriace_value}</span>'

        html_content += """
            </div>
        """

        # Règles spéciales
        if u.get("base_rules"):
            rules = [r for r in u['base_rules'] if not r.startswith("Coriace")]
            if rules:
                html_content += f"""
                <div class="section">
                    <div class="title">Règles spéciales</div>
                    <div style="margin-left:15px; margin-bottom:5px; font-size:0.9em;">
                        {', '.join(rules)}
                    </div>
                </div>
                """

        # Arme équipée
        if 'current_weapon' in u:
            weapon = u['current_weapon']
            html_content += f"""
            <div class="section">
                <div class="title">Arme équipée</div>
                <div style="margin-left:15px; margin-bottom:5px; font-size:0.9em;">
                    {weapon.get('name', 'Arme de base')} | A{weapon.get('attacks', '?')} | PA({weapon.get('armor_piercing', '?')})
                </div>
            </div>
            """

        # Options (sauf Améliorations)
        other_options = []
        for group_name, opt_group in u.get("options", {}).items():
            if group_name != "Améliorations":
                if isinstance(opt_group, list):
                    other_options.extend([opt["name"] for opt in opt_group])
                else:
                    other_options.append(opt_group["name"])

        if other_options:
            html_content += f"""
            <div class="section">
                <div class="title">Options</div>
                <div style="margin-left:15px; margin-bottom:5px; font-size:0.9em;">
                    {', '.join(other_options)}
                </div>
            </div>
            """

        # Monture (si elle existe)
        if u.get("mount"):
            mount = u['mount']
            html_content += f"""
            <div class="section">
                <div class="title">Monture</div>
                <div style="margin-left:15px; margin-bottom:5px; font-size:0.9em;">
                    <strong>{mount.get('name', '')}</strong>
                </div>
            </div>
            """

        # Améliorations (Sergent, Bannière, Musicien) UNIQUEMENT pour les unités non-héros
        if "Améliorations" in u.get("options", {}) and u.get("type", "").lower() != "hero":
            improvements = [opt["name"] for opt in u["options"]["Améliorations"]]
            if improvements:
                html_content += f"""
                <div class="section">
                    <div class="title">Améliorations</div>
                    <div style="margin-left:15px; margin-bottom:5px; font-size:0.9em;">
                        {', '.join(improvements)}
                    </div>
                </div>
                """

        html_content += "</div>"

        components.html(html_content, height=height)

        if st.button(f"❌ Supprimer {u['name']}", key=f"del_{i}"):
            st.session_state.army_total_cost -= u["cost"]
            st.session_state.army_list.pop(i)
            st.rerun()

    # ... (le reste du code reste inchangé)
