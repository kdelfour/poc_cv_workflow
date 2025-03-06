# API de Traitement de PDF avec Workflows

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)
![Licence](https://img.shields.io/badge/licence-MIT-green)

Cette API permet de traiter des fichiers PDF via des workflows ETL (Extraction, Transformation, Chargement) en utilisant FastAPI et Prefect. Elle offre une solution robuste et scalable pour l'analyse automatisée de documents PDF.

## 📑 Table des matières

- [Prérequis](#-prérequis)
- [Structure du Projet](#structure-du-projet)
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Configuration avancée](#-configuration-avancée)
- [API Reference](#-api-reference)
- [Contribution](#-contribution)
- [Support](#-support)
- [Licence](#-licence)

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Compte OpenAI (pour les fonctionnalités d'analyse avancée)
- Système d'exploitation : Linux, macOS ou Windows

## Structure du Projet

Le projet est organisé selon les principes du Software Craftsmanship pour une meilleure lisibilité et maintenabilité :

```
.
├── app/                    # Package principal
│   ├── api/                # Endpoints de l'API
│   │   └── workflow_endpoints.py
│   ├── models/             # Modèles de données
│   │   └── workflow_models.py
│   ├── tasks/              # Tâches ETL
│   │   ├── extraction/     # Tâches d'extraction
│   │   │   └── pdf_extraction.py
│   │   ├── transformation/ # Tâches de transformation
│   │   │   └── pdf_transformation.py
│   │   └── chargement/     # Tâches de chargement
│   │       └── pdf_chargement.py
│   ├── utils/              # Utilitaires
│   │   └── pdf_utils.py
│   └── workflows/          # Définition des workflows
│       └── pdf_workflow.py
├── main.py                 # Point d'entrée de l'application
├── requirements.txt        # Dépendances du projet
├── test_pdf_upload.py      # Script de test
├── .gitignore             # Fichiers et dossiers ignorés par Git
└── README.md               # Documentation
```

## Fonctionnalités

- Upload et traitement de fichiers PDF
- Extraction de texte et métadonnées des PDF
- Analyse statistique du contenu (nombre de mots, pages, mots-clés)
- Exécution de workflows en mode asynchrone ou synchrone
- Suivi de l'état des workflows

## Endpoints API

- `POST /workflow/run` : Exécute un workflow en arrière-plan
- `POST /workflow/run/sync` : Exécute un workflow de manière synchrone
- `GET /workflow/status/{workflow_id}` : Récupère le statut d'un workflow
- `GET /workflow/active` : Liste tous les workflows actifs

## Installation

1. Cloner le dépôt
2. Créer et activer un environnement virtuel :
   ```bash
   # Création de l'environnement virtuel
   python -m venv venv

   # Activation de l'environnement virtuel
   # Sur Linux/macOS
   source venv/bin/activate
   # Sur Windows
   .\venv\Scripts\activate
   ```
3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Configurer les variables d'environnement :
   - Créer un fichier `.env` à la racine du projet
   - Ajouter votre clé API OpenAI :
     ```
     OPENAI_API_KEY=votre_clé_api_openai_ici
     ```

## Utilisation

### 🚀 Démarrer l'API

```bash
# Option 1 : Démarrage simple
python main.py

# Option 2 : Démarrage avec rechargement automatique pour le développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible à l'adresse http://localhost:8000 et la documentation Swagger à http://localhost:8000/docs.

### 🧪 Tester l'API

Plusieurs options s'offrent à vous pour tester l'API :

#### 1. Interface Swagger
Rendez-vous sur http://localhost:8000/docs pour une interface interactive permettant de :
- Visualiser tous les endpoints disponibles
- Tester les endpoints directement depuis votre navigateur
- Consulter la documentation détaillée de chaque endpoint

#### 2. Collection Postman
Une collection Postman est disponible dans le dossier `docs/postman` pour tester rapidement tous les endpoints.

#### 3. Script de test Python
```python
import requests

# Test du mode asynchrone
response = requests.post(
    "http://localhost:8000/workflow/run",
    files={
        "pdf_file": ("document.pdf", open("chemin/vers/fichier.pdf", "rb"))
    },
    data={
        "workflow_name": "analyse_document",
        "additional_data": '{"description": "Analyse complète", "priority": "high"}'
    }
)
print(f"Workflow ID: {response.json()['workflow_id']}")
```

## Exemple d'utilisation avec cURL

### Mode asynchrone

```bash
curl -X POST "http://localhost:8000/workflow/run" \
  -F "pdf_file=@chemin/vers/fichier.pdf" \
  -F "workflow_name=mon_workflow" \
  -F "additional_data={\"description\":\"Test d'analyse\",\"user\":\"utilisateur\"}"
```

### Mode synchrone

```bash
curl -X POST "http://localhost:8000/workflow/run/sync" \
  -F "pdf_file=@chemin/vers/fichier.pdf" \
  -F "workflow_name=mon_workflow" \
  -F "additional_data={\"description\":\"Test d'analyse\",\"user\":\"utilisateur\"}"
```

## Dépendances principales

- FastAPI : Framework API web moderne
- Prefect : Orchestration de workflows
- PyPDF2 : Traitement de fichiers PDF
- Uvicorn : Serveur ASGI pour FastAPI

## Principes de conception

Ce projet suit plusieurs principes de Software Craftsmanship :

1. **Séparation des préoccupations (SoC)** : Chaque composant a une responsabilité unique et bien définie.
2. **Principe de responsabilité unique (SRP)** : Chaque classe ou module n'a qu'une seule raison de changer.
3. **Modularité** : Le code est organisé en modules indépendants qui peuvent être développés et testés séparément.
4. **Lisibilité** : Le code est écrit pour être compréhensible par d'autres développeurs.
5. **Maintenabilité** : La structure facilite les modifications et les extensions futures.

## Améliorations possibles

- Stockage persistant des workflows (base de données)
- Authentification et autorisation
- Traitement plus avancé des PDF (extraction d'images, tableaux)
- Interface utilisateur pour le suivi des workflows
- Tests unitaires et d'intégration 

## 🔧 Configuration avancée

### Configuration de Prefect

Pour configurer Prefect avec des paramètres personnalisés :

```bash
prefect config set PREFECT_API_URL="http://localhost:4200/api"
prefect orion start
```

### Variables d'environnement supplémentaires

Créez un fichier `.env` avec les variables suivantes :

```env
OPENAI_API_KEY=votre_clé_api_openai_ici
PDF_STORAGE_PATH=/chemin/vers/stockage
MAX_UPLOAD_SIZE=10485760
DEBUG_MODE=False
```

## 📚 API Reference

### Endpoints principaux

| Méthode | Endpoint | Description | Paramètres |
|---------|----------|-------------|------------|
| POST | `/workflow/run` | Exécution asynchrone | `pdf_file`, `workflow_name`, `additional_data` |
| POST | `/workflow/run/sync` | Exécution synchrone | `pdf_file`, `workflow_name`, `additional_data` |
| GET | `/workflow/status/{workflow_id}` | Statut du workflow | `workflow_id` |
| GET | `/workflow/active` | Liste des workflows actifs | - |

### Codes de retour

| Code | Description |
|------|-------------|
| 200 | Succès |
| 400 | Requête invalide |
| 404 | Workflow non trouvé |
| 500 | Erreur serveur |

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Guide de style

- Suivez PEP 8 pour le code Python
- Documentez les nouvelles fonctionnalités
- Ajoutez des tests unitaires pour les nouvelles fonctionnalités
- Mettez à jour la documentation si nécessaire

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🔍 Statut du Projet

- ✅ Version stable : 1.0.0
- 🚀 Dernière mise à jour : Mars 2024
- 📈 Statut : Maintenance active

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la [documentation en ligne](http://localhost:8000/docs)
- Contactez l'équipe de maintenance 