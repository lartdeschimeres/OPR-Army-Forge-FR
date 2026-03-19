# OPR Army Builder FR 🇫🇷

**Un outil complet pour créer et gérer vos listes d'armées pour les jeux One Page Rules (OPR)**

_Auteur : Simon Joinville Fouquet_

---

## 📋 Fonctionnalités principales

✅ **Création de listes d'armées** pour tous les jeux OPR

✅ **Validation automatique** des règles spécifiques à chaque jeu

✅ **Système de comptes joueurs** pour sauvegarder et retrouver vos listes

✅ **Export HTML** pour partager ou imprimer vos listes

✅ **Calcul automatique** des valeurs de Coriace et autres statistiques

✅ **Interface intuitive** avec visualisation claire des unités

---

## 🛠️ Prérequis

- Python 3.7 ou supérieur
- Streamlit

---

## 🚀 Installation et lancement

1. Clonez ce dépôt :

```bash
git clone https://github.com/votre-utilisateur/opr-army-forge-fr.git
```

```bash
cd opr-army-forge-fr
```

2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

3. Lancez l'application :

```bash
streamlit run app.py
```

4. (optionnel) Lancez les tests unitaires avec :

```bash
python -m unittest discover -s tests -v
```

---

## 📂 Structure du projet

```bash
opr-army-forge-fr/
├── app.py                  # Code principal
├── lists/
│   └── data/
│       └── factions/       # Fichiers JSON des factions
├── players/                # Comptes joueurs (créé automatiquement)
├── saves/                  # Listes sauvegardées
└── README.md               # Ce fichier
```

---

## 🎮 Utilisation pas à pas

Créez un compte (ou connectez-vous si vous en avez déjà un)

1. Configurez une nouvelle liste :

- Sélectionnez un jeu (Age of Fantasy, etc.)
- Choisissez une faction
- Définissez le format de points

2. Composez votre armée :

- Ajoutez des unités avec leurs options
- Visualisez les statistiques en temps réel
- Vérifiez la validation des règles

3. Sauvegardez votre liste pour la retrouver plus tard

4. Exportez en HTML pour partager ou imprimer

---

## 📜 Règles spécifiques implémentées

Pour Age of Fantasy :

- 1 héros par tranche de 375 pts
- 1+X copies de la même unité (X=1 pour 750 pts)
- Aucune unité ne peut valoir plus de 35% du total des points
- 1 unité max par tranche de 150 pts

---

## 📦 Déploiement (Streamlit Cloud)

- Créez un compte sur Streamlit Community Cloud
- Liez votre dépôt GitHub
- Configurez les paramètres de déploiement

---

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer veuillez nous conctacer ;)

---

## 📜 Licence

Ce projet est sous licence MIT.

---

## 🙏 Remerciements

- À la communauté OPR pour les règles et l'univers
- À tous les testeurs et contributeurs
- Dernière mise à jour : 11/01/2026
- Version : 1.0

```bash
pip install streamlit
```
