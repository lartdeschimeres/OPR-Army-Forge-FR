# Liste de l'armée (affichage sous forme de fiches avec le style de votre capture)
st.divider()
st.subheader("Liste de l'armée")

for i, u in enumerate(st.session_state.army_list):
    # Calcul de la valeur totale de Coriace
    coriace_value = calculate_coriace_value(u)

    # Génération du HTML pour la fiche avec le style de votre capture
    html_content = f"""
    <style>
    .army-card {{
        border: 2px solid #4a89dc;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    .unit-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    .unit-name {{
        font-size: 1.2em;
        font-weight: bold;
        color: #333;
        margin: 0;
    }}
    .unit-points {{
        color: #666;
        font-size: 0.9em;
    }}
    .badges-container {{
        display: flex;
        gap: 8px;
        margin-bottom: 15px;
        flex-wrap: wrap;
    }}
    .badge {{
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 500;
        color: white;
        text-align: center;
    }}
    .quality-badge {{
        background-color: #4a89dc;
    }}
    .defense-badge {{
        background-color: #4a89dc;
    }}
    .coriace-badge {{
        background-color: #4a89dc;
    }}
    .section {{
        margin-bottom: 12px;
    }}
    .section-title {{
        font-weight: bold;
        color: #4a89dc;
        margin-bottom: 5px;
        font-size: 0.95em;
    }}
    .section-content {{
        margin-left: 10px;
        font-size: 0.9em;
        color: #555;
    }}
    .delete-btn {{
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 15px;
        margin-top: 10px;
        cursor: pointer;
        font-weight: 500;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
    }}
    .delete-btn:hover {{
        background-color: #ff3333;
    }}
    </style>

    <div class="army-card">
        <div class="unit-header">
            <h3 class="unit-name">{u['name']}</h3>
            <span class="unit-points">{u['cost']} pts</span>
        </div>

        <div class="badges-container">
            <span class="badge quality-badge">Qualité {u['quality']}+</span>
            <span class="badge defense-badge">Défense {u['defense']}+</span>
    """

    if coriace_value > 0:
        html_content += f'<span class="badge coriace-badge">Coriace {coriace_value}</span>'

    html_content += """
        </div>
    """

    # Règles spéciales
    if u.get("base_rules"):
        rules = [r for r in u['base_rules'] if not r.startswith("Coriace")]
        if rules:
            html_content += f"""
            <div class="section">
                <div class="section-title">Règles spéciales</div>
                <div class="section-content">{', '.join(rules)}</div>
            </div>
            """

    # Arme équipée
    if 'current_weapon' in u:
        weapon = u['current_weapon']
        html_content += f"""
        <div class="section">
            <div class="section-title">Arme équipée</div>
            <div class="section-content">
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
            <div class="section-title">Options</div>
            <div class="section-content">{', '.join(other_options)}</div>
        </div>
        """

    # Monture (si elle existe)
    if u.get("mount"):
        mount = u['mount']
        mount_rules = []
        if 'special_rules' in mount:
            mount_rules = mount['special_rules']

        html_content += f"""
        <div class="section">
            <div class="section-title">Monture</div>
            <div class="section-content">
                <strong>{mount.get('name', '')}</strong>
        """

        if mount_rules:
            html_content += f"<br>{', '.join(mount_rules)}"

        html_content += """
            </div>
        </div>
        """

    # Améliorations (Sergent, Bannière, Musicien) UNIQUEMENT pour les unités non-héros
    if "Améliorations" in u.get("options", {}) and u.get("type", "").lower() != "hero":
        improvements = [opt["name"] for opt in u["options"]["Améliorations"]]
        if improvements:
            html_content += f"""
            <div class="section">
                <div class="section-title">Améliorations</div>
                <div class="section-content">{', '.join(improvements)}</div>
            </div>
            """

    # Bouton de suppression
    html_content += f"""
    <button class="delete-btn" onclick="document.getElementById('del_{i}').click()">
        ❌ Supprimer {u['name']}
    </button>
    <button id="del_{i}" style="display:none;"></button>
    """

    html_content += "</div>"

    components.html(html_content, height=300)

    # Bouton de suppression réel (caché, déclenché par le bouton dans le HTML)
    if st.button(f"Supprimer {u['name']}", key=f"del_{i}"):
        st.session_state.army_total_cost -= u["cost"]
        st.session_state.army_list.pop(i)
        st.rerun()
