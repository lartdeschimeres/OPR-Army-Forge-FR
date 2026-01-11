# Dans la partie "Ajouter une unité", remplacez la section des améliorations de figurines par :

# Section pour les améliorations d'unité (Sergent, Bannière, Musicien) en colonnes UNIQUEMENT pour les unités non-héros
if unit.get("type", "").lower() != "hero":
    st.divider()
    st.subheader("Améliorations d'unité")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("Sergent (+5 pts)"):
            total_cost += 5
            if "Améliorations" not in options_selected:
                options_selected["Améliorations"] = []
            options_selected["Améliorations"].append({"name": "Sergent", "cost": 5})

    with col2:
        if st.checkbox("Bannière (+5 pts)"):
            total_cost += 5
            if "Améliorations" not in options_selected:
                options_selected["Améliorations"] = []
            options_selected["Améliorations"].append({"name": "Bannière", "cost": 5})

    with col3:
        if st.checkbox("Musicien (+10 pts)"):
            total_cost += 10
            if "Améliorations" not in options_selected:
                options_selected["Améliorations"] = []
            options_selected["Améliorations"].append({"name": "Musicien", "cost": 10})
