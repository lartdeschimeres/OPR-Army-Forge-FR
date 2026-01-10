import json
from pathlib import Path
import streamlit as st

# -------------------------------------------------
# CONFIG GÉNÉRALE
# -------------------------------------------------
st.set_page_config(page_title="OPR Army Builder FR", layout="centered")
st.title("OPR Army Builder 🇫🇷")

BASE_DIR = Path(__file__).resolve().parent
FACTIONS_DIR = BASE_DIR / "lists" / "data" / "factions"

# -------------------------------------------------
# CHARGEMENT DES FACTIONS
# -------------------------------------------------
if not FACTIONS_DIR.exists():
    st.error(f"Dossier factions introuvable : {FACTIONS_DIR}")
    st.stop()

faction_files = sorted(FACTIONS_DIR.glob("*.json"))
if not faction_files:
    st.error("Aucun fichier faction trouvé")
    st.stop()

games = set()
faction_map = {}

for fp in faction_files:
    try:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            game = data.get("game", "Inconnu")
            faction = data.get("faction", fp.stem)
            games.add(game)
            faction_map[faction] = {"file": fp, "game": game}
    except Exception as e:
        st.warning(f"Erreur lecture {fp.name} : {e}")

# -------------------------------------------------
# SÉLECTEURS JEU / FACTION
# -------------------------------------------------
selected_game = st.selectbox("Sélectionner le jeu", sorted(games))

game_factions = {
    name: info for name, info in faction_map.items()
    if info["game"] == selected_game
}

selected_faction = st.selectbox(
    "Sélectionner la faction",
    sorted(game_factions.keys())
)

# -------------------------------------------------
# OBJECTIF D'ARMÉE
# -------------------------------------------------
army_target_cost = st.number_input(
    "Coût total souhaité de l’armée (pts)",
    min_value=0,
    value=1000,
    step=50
)

# -------------------------------------------------
# CHARGEMENT FACTION
# -------------------------------------------------
with open(game_factions[selected_faction]["file"], encoding="utf-8") as f:
    faction = json.load(f)

st.subheader(f"Faction : {faction.get('faction')}")
st.caption(f"Jeu : {faction.get('game')}")

units = faction.get("units", [])
if not units:
    st.warning("Aucune unité dans cette faction.")
    st.stop()

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
st.session_state.setdefault("army_list", [])
st.session_state.setdefault("army_total_cost", 0)

# -------------------------------------------------
# SÉLECTEUR D’UNITÉ
# -------------------------------------------------
st.divider()
st.subheader("Configurer une unité")

unit_names = [u["name"] for u in units]

def unit_label(u):
    return f"{u['name']} ({u['base_cost']} pts | Q{u['quality']}+ / D{u['defense']}+)"

selected_name = st.selectbox(
    "Choisir une unité",
    unit_names,
    format_func=lambda n: unit_label(next(u for u in units if u["name"] == n))
)

unit = next(u for u in units if u["name"] == selected_name)

# -------------------------------------------------
# INIT PROFIL
# -------------------------------------------------
total_cost = unit.get("base_cost", 0)
final_rules = list(unit.get("special_rules", []))

base_tough = unit.get("tough", 0)
mount_tough = 0
mount_def_bonus = 0
selected_mount = None

current_weapon = unit.get("weapons", [{
    "name": "Arme non définie",
    "attacks": "?",
    "armor_piercing": "?"
}])[0]

selected_options = {}

# -------------------------------------------------
# ARMES DE BASE
# -------------------------------------------------
st.subheader("Armes de base")
for w in unit.get("weapons", []):
    st.write(f"- **{w['name']}** | A{w['attacks']} | PA({w.get('armor_piercing', 0)})")

# -------------------------------------------------
# OPTIONS
# -------------------------------------------------
st.subheader("Options")

for group in unit.get("upgrade_groups", []):
    key = f"{unit['name']}_{group['group']}"
    choices = ["— Aucun —"] + [o["name"] for o in group["options"]]

    choice = st.selectbox(group["group"], choices, key=key)

    if choice != "— Aucun —":
        opt = next(o for o in group["options"] if o["name"] == choice)
        total_cost += opt.get("cost", 0)

        if opt.get("type") == "mount":
            selected_mount = opt
            mount_tough += opt.get("tough_bonus", 0)
            mount_def_bonus += opt.get("defense_bonus", 0)
            final_rules.extend(opt.get("special_rules", []))
        else:
            selected_options[group["group"]] = opt
            final_rules.extend(opt.get("special_rules", []))

        if "weapon" in opt:
            current_weapon = opt["weapon"]
            current_weapon["name"] = opt["name"]

# -------------------------------------------------
# CALCUL FINAL
# -------------------------------------------------
final_defense = unit.get("defense", "?")
if isinstance(final_defense, int):
    final_defense += mount_def_bonus

final_tough = base_tough + mount_tough

# -------------------------------------------------
# PROFIL FINAL
# -------------------------------------------------
st.divider()
st.subheader("Profil final")
st.markdown(f"### 💰 **Coût total : {total_cost} pts**")
st.write(
    f"**Qualité :** {unit['quality']}+ | "
    f"**Défense :** {final_defense}+"
    f"{f' | Coriace ({final_tough})' if final_tough > 0 else ''}"
)

# -------------------------------------------------
# AJOUT À L’ARMÉE
# -------------------------------------------------
if st.button("➕ Ajouter à l’armée"):
    st.session_state.army_list.append({
        "name": unit["name"],
        "cost": total_cost,
        "quality": unit["quality"],
        "defense": final_defense,
        "tough": final_tough,
        "rules": sorted(set(final_rules)),
        "options": selected_options,
        "mount": selected_mount,
        "weapon": current_weapon
    })
    st.session_state.army_total_cost += total_cost
    st.success("Unité ajoutée à l’armée")

# -------------------------------------------------
# AFFICHAGE ARMÉE
# -------------------------------------------------
st.divider()
st.subheader("Liste de l’armée")

for i, u in enumerate(st.session_state.army_list, 1):
    st.markdown(f"""
    <div style="border:1px solid #ccc;padding:10px;border-radius:8px;margin-bottom:10px">
    <strong>{u['name']} [{i}]</strong> – {u['cost']} pts<br>
    Qualité {u['quality']}+ | Défense {u['defense']}+
    {" | Coriace (" + str(u['tough']) + ")" if u['tough'] > 0 else ""}
    <br><br>
    <strong>Arme :</strong> {u['weapon']['name']} – A{u['weapon']['attacks']} PA({u['weapon'].get('armor_piercing',0)})
    <br><br>
    <strong>Options :</strong>
    {", ".join([f"{k}: {v['name']}" for k, v in u['options'].items()]) or "Aucune"}
    """, unsafe_allow_html=True)

    if u.get("mount"):
        m = u["mount"]
        st.markdown(
            f"<div style='color:#4a89dc'><strong>Monture :</strong> {m['name']} "
            f"(+{m.get('tough_bonus',0)} Coriace"
            f"{f', Défense +{m.get('defense_bonus')}' if m.get('defense_bonus') else ''}"
            f"{f', {', '.join(m.get('special_rules',[]))}' if m.get('special_rules') else ''})</div>",
            unsafe_allow_html=True
        )

    if st.button("❌ Supprimer", key=f"del_{i}"):
        st.session_state.army_total_cost -= u["cost"]
        st.session_state.army_list.pop(i - 1)
        st.rerun()

st.markdown(f"### 💰 Coût total de l’armée : {st.session_state.army_total_cost} pts")
st.progress(
    min(st.session_state.army_total_cost / army_target_cost, 1.0)
)
