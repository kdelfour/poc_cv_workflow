"""
Module pour l'extraction de données structurées à partir de CV en utilisant GPT-4o-mini via l'API OpenAI.
Ce module se concentre sur l'extraction des formations et des expériences professionnelles.
"""
import time
import os
import json
import logging
from typing import Dict, Any, List, Optional
from prefect import task
from openai import OpenAI
from dotenv import load_dotenv

# Import du module utilitaire de logging centralisé
from app.utils.logging_utils import setup_logger

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration du logger via le module centralisé
logger = setup_logger(__name__)

# Constantes pour les messages d'erreur fréquents
ERROR_NO_PDF_DATA = "Pas de données PDF disponibles ou erreur lors de l'extraction initiale"
ERROR_NO_TEXT_CONTENT = "Aucun contenu textuel disponible pour l'analyse"
ERROR_API_KEY_MISSING = "Clé API OpenAI non configurée dans le fichier .env"

# Schémas de validation pour les données extraites
FORMATION_SCHEMA = ["periode", "diplome", "etablissement", "description"]
EXPERIENCE_SCHEMA = ["periode", "poste", "entreprise", "description", "competences"]

@task
def openai_extraction(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraction des formations et expériences professionnelles à partir du texte d'un CV
    en utilisant GPT-4o-mini via l'API OpenAI.
    
    Args:
        data: Dictionnaire contenant les données extraites du PDF, notamment le texte du CV
        
    Returns:
        Dictionnaire contenant les formations et expériences professionnelles extraites
    """
    # Vérifier si nous avons des données extraites
    if not data.get("pdf_available", False) or "extraction_error" in data:
        return _create_error_response(ERROR_NO_PDF_DATA, data)
    
    extracted_data = data.get("extracted", {})
    text_content = extracted_data.get("text_content", "")
    
    if not text_content:
        return _create_error_response(ERROR_NO_TEXT_CONTENT, data)
    
    try:
        # Récupérer la clé API OpenAI depuis les variables d'environnement
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "votre_clé_api_openai_ici":
            logger.error(ERROR_API_KEY_MISSING)
            return _create_error_response(ERROR_API_KEY_MISSING, data)
        
        # Initialiser le client OpenAI et effectuer l'extraction
        extracted_data = _perform_openai_extraction(api_key, text_content)
        
        return {
            "openai_extracted": {
                "formations": extracted_data.get("formations", []),
                "experiences_professionnelles": extracted_data.get("experiences_professionnelles", []),
                "status": "success",
                "extraction_time": time.time()
            },
            "step": "openai_extraction",
            "success": True,
            **data  # Conserver les données précédentes
        }
        
    except Exception as e:
        error_message = f"Erreur lors de l'extraction avec OpenAI: {str(e)}"
        logger.error(error_message)
        return _create_error_response(error_message, data)

def _create_error_response(error_message: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée une réponse d'erreur standardisée.
    
    Args:
        error_message: Message d'erreur à inclure
        original_data: Données originales à conserver
        
    Returns:
        Dictionnaire formaté avec l'erreur
    """
    return {
        "openai_extracted": {
            "error": error_message,
            "status": "error"
        },
        "step": "openai_extraction",
        "success": False,
        **original_data  # Conserver les données précédentes
    }

def _perform_openai_extraction(api_key: str, text_content: str) -> Dict[str, Any]:
    """
    Effectue l'extraction des données via l'API OpenAI.
    
    Args:
        api_key: Clé API OpenAI
        text_content: Contenu textuel du CV
        
    Returns:
        Données extraites et structurées
        
    Raises:
        ValueError: Si la réponse de l'API est vide
    """
    # Initialiser le client OpenAI
    logger.info("Initialisation du client OpenAI")
    client = OpenAI(api_key=api_key)
    
    # Préparer le prompt pour l'extraction
    logger.info("Préparation du prompt pour l'extraction")
    prompt = prepare_extraction_prompt(text_content)
    
    # Appeler l'API OpenAI
    logger.info("Appel de l'API OpenAI avec GPT-4o-mini")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Tu es un assistant spécialisé dans l'extraction d'informations structurées à partir de CV. Tu dois extraire les formations et les expériences professionnelles et les retourner au format JSON selon un schéma précis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  # Température basse pour des réponses plus déterministes
        max_tokens=2000
    )
    
    # Extraire la réponse
    logger.info("Traitement de la réponse de l'API OpenAI")
    response_content = response.choices[0].message.content
    if response_content is None:
        logger.error("La réponse de l'API OpenAI est vide")
        raise ValueError("La réponse de l'API OpenAI est vide")
        
    return parse_openai_response(response_content)

def prepare_extraction_prompt(text_content: str) -> str:
    """
    Prépare le prompt pour l'extraction des informations du CV.
    
    Args:
        text_content: Texte brut du CV
        
    Returns:
        Prompt formaté pour l'API OpenAI
    """
    return f"""
Voici le texte d'un CV:

```
{text_content}
```

Extrais les informations suivantes du CV et retourne-les au format JSON selon ce schéma précis:

{{
  "formations": [
    {{
      "periode": "string", // La période de la formation (ex: "2018-2020")
      "diplome": "string", // Le nom du diplôme ou de la formation
      "etablissement": "string", // Le nom de l'établissement
      "description": "string" // Description supplémentaire si disponible
    }}
  ],
  "experiences_professionnelles": [
    {{
      "periode": "string", // La période de l'expérience (ex: "2020-2022")
      "poste": "string", // L'intitulé du poste
      "entreprise": "string", // Le nom de l'entreprise
      "description": "string", // Description des responsabilités et réalisations
      "competences": ["string", "string"] // Liste des compétences mentionnées dans cette expérience
    }}
  ]
}}

Tous les champs sont obligatoires. Si une information n'est pas disponible, utilise une chaîne vide ou un tableau vide pour les compétences.
Assure-toi que le format JSON est strictement respecté et que toutes les clés requises sont présentes.
"""

def parse_openai_response(response_content: str) -> Dict[str, Any]:
    """
    Parse la réponse de l'API OpenAI pour extraire les données structurées.
    
    Args:
        response_content: Contenu de la réponse de l'API OpenAI
        
    Returns:
        Dictionnaire contenant les formations et expériences professionnelles extraites
    """
    try:
        # Essayer de parser la réponse JSON
        extracted_data = json.loads(response_content)
        
        # Valider la structure des données
        if not isinstance(extracted_data, dict):
            logger.warning("La réponse n'est pas un dictionnaire JSON valide")
            return {"formations": [], "experiences_professionnelles": []}
        
        # Extraire et valider les formations et expériences
        validated_formations = _validate_formations(extracted_data.get("formations", []))
        validated_experiences = _validate_experiences(extracted_data.get("experiences_professionnelles", []))
        
        return {
            "formations": validated_formations,
            "experiences_professionnelles": validated_experiences
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du parsing de la réponse JSON: {str(e)}")
        return {"formations": [], "experiences_professionnelles": []}
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement de la réponse: {str(e)}")
        return {"formations": [], "experiences_professionnelles": []} 

def _validate_formations(formations: List[Any]) -> List[Dict[str, str]]:
    """
    Valide et nettoie les formations selon le schéma défini.
    
    Args:
        formations: Liste des formations extraites
        
    Returns:
        Liste des formations validées et nettoyées
    """
    validated_formations = []
    
    for formation in formations:
        if not isinstance(formation, dict):
            continue
            
        # Créer une formation avec les champs par défaut
        validated_formation = {
            "periode": formation.get("periode", ""),
            "diplome": formation.get("diplome", ""),
            "etablissement": formation.get("etablissement", ""),
            "description": formation.get("description", "")
        }
        
        # S'assurer que tous les champs requis sont présents
        if all(key in validated_formation for key in FORMATION_SCHEMA):
            validated_formations.append(validated_formation)
    
    return validated_formations

def _validate_experiences(experiences: List[Any]) -> List[Dict[str, Any]]:
    """
    Valide et nettoie les expériences professionnelles selon le schéma défini.
    
    Args:
        experiences: Liste des expériences extraites
        
    Returns:
        Liste des expériences validées et nettoyées
    """
    validated_experiences = []
    
    for experience in experiences:
        if not isinstance(experience, dict):
            continue
            
        # Vérifier et normaliser le champ compétences
        competences = experience.get("competences", [])
        if not isinstance(competences, list):
            competences = []
        
        # Créer une expérience avec les champs par défaut
        validated_experience = {
            "periode": experience.get("periode", ""),
            "poste": experience.get("poste", ""),
            "entreprise": experience.get("entreprise", ""),
            "description": experience.get("description", ""),
            "competences": competences
        }
        
        # S'assurer que tous les champs requis sont présents
        if all(key in validated_experience for key in EXPERIENCE_SCHEMA):
            validated_experiences.append(validated_experience)
    
    return validated_experiences 