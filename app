import json
import streamlit as st

# Chargement des données
with open("data/factions/sisters_blessed.json", encoding="utf-8") as f:
    faction = json.load(f)

with open("data/rules/opr_limits.json") as f:
    rules = json.load(f)

# État de la liste
if "army" not in st.session_state:
    st.session_state.army = []

st.title("OPR Army Builder 🇫🇷")
st.subheader(f"Faction : {faction['faction']}")

# Ajouter une unité
unit_names = [u["name"] for u in faction["units"]]
selected = st.selectbox("Ajouter une unité", unit_names)

if st.button("➕ Ajouter"):
    unit = next(u for u in faction["units"] if u["name"] == selected)
    st.session_state.army.append(unit)

# Affichage de la liste
st.subheader("🧾 Liste actuelle")

total_points = 0
for u in st.session_state.army:
    st.write(f"- {u['name']} ({u['base_cost']} pts)")
    total_points += u["base_cost"]

st.markdown(f"### Total : **{total_points} pts**")

# Règle simple visible
max_units = total_points // rules["unit_per_points"]
if len(st.session_state.army) > max_units:
    st.error("❌ Trop d’unités selon les règles OPR")
else:
    st.success("✅ Nombre d’unités OK")
