# Checklist Pro - Application Flask

Une application web légère permettant de créer, remplir et consulter des checklists personnalisées.

## Fonctionnalités

1. **Création de modèles de checklist**
   - Nom personnalisé
   - Liste d'items à vérifier

2. **Remplissage de checklists**
   - Cocher les éléments réalisés
   - Ajouter un commentaire (optionnel)
   - Horodatage automatique

3. **Historique**
   - Liste chronologique des checklists remplies
   - Affichage du statut de validation pour chaque item
   - Consultation des commentaires

## Structure du projet
/
├── app.py                  # Point d'entrée de l'application
├── data/
│   ├── templates.json      # Modèles de checklists
│   └── history.json        # Historique des checklists remplies
├── static/                 # Fichiers statiques (CSS, JS)
├── templates/              # Templates HTML
└── README.md               # Documentation


## Installation

1. Cloner le dépôt
2. Installer les dépendances: `pip install -r requirements.txt`
3. Lancer l'application : `python app.py`
4. Accéder à l'application dans votre navigateur à l'adresse : `http://localhost:5000`

## Technologies utilisées

- Flask (framework web)
- Bootstrap (framework CSS)
- Font Awesome (icônes)
- JSON (stockage de données)

## Contraintes techniques

- Utilisation exclusive de Flask
- Stockage des données dans des fichiers JSON
- Interface utilisateur responsive avec Bootstrap
- Pas de système d'authentification (application publique)