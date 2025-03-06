"""
Module pour la correspondance entre les postes extraits des CV et les métiers de référence
en utilisant OpenAI pour le traitement du langage naturel en français.
"""
import os
import json
import logging
import csv
import time
from functools import lru_cache
from typing import Dict, Any, List, Optional, Tuple, cast
from prefect import task
from openai import OpenAI
from dotenv import load_dotenv

# Import du module utilitaire de logging centralisé
from app.utils.logging_utils import setup_logger, log_config_info

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logger via le module centralisé
logger = setup_logger(__name__)

# Constantes et configuration depuis .env
DEFAULT_METIERS_FILE_PATH = "datas/unix_cr_gd_dp_v458_utf8.csv"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_CACHE_TTL = 3600  # Durée de vie du cache en secondes (1 heure)

# Récupération des valeurs depuis .env avec valeurs par défaut
METIERS_FILE_PATH = os.environ.get("METIERS_FILE_PATH", DEFAULT_METIERS_FILE_PATH)
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", DEFAULT_TEMPERATURE))
CACHE_TTL = int(os.environ.get("METIERS_CACHE_TTL", DEFAULT_CACHE_TTL))

# Affichage de la configuration au démarrage avec la fonction utilitaire
log_config_info(logger, {
    "Fichier des métiers": METIERS_FILE_PATH,
    "Modèle OpenAI": OPENAI_MODEL,
    "Température OpenAI": OPENAI_TEMPERATURE,
    "Durée de vie du cache (TTL)": f"{CACHE_TTL} secondes",
    "Niveau de log": os.environ.get("LOG_LEVEL", "INFO")
})

# Type pour les métiers
MetierType = Dict[str, Any]

# Variables globales pour le cache
_metiers_cache: List[MetierType] = []
_metiers_cache_timestamp: float = 0

@task
def openai_matching(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Utilise OpenAI pour faire correspondre les postes extraits des expériences professionnelles
    avec les métiers de référence.
    
    Args:
        data: Dictionnaire contenant les données extraites par OpenAI
        
    Returns:
        Dictionnaire enrichi avec les correspondances de métiers
    """
    # Vérification des données d'entrée
    if not data.get("success", False) or "openai_extracted" not in data:
        logger.warning("Aucune donnée extraite par OpenAI disponible")
        return {
            "openai_matching": {
                "error": "Aucune donnée extraite par OpenAI disponible",
                "status": "error",
                "metiers_matches": []
            },
            "step": "openai_matching",
            "success": False,
            **data
        }
    
    openai_data = data.get("openai_extracted", {})
    experiences = openai_data.get("experiences_professionnelles", [])
    
    # Vérification de la présence d'expériences professionnelles
    if not experiences:
        logger.warning("Aucune expérience professionnelle trouvée dans les données OpenAI")
        return {
            "openai_matching": {
                "error": "Aucune expérience professionnelle trouvée",
                "status": "warning",
                "metiers_matches": []
            },
            "step": "openai_matching",
            "success": True,
            **data 
        }
    
    try:
        # Chargement des métiers de référence (avec cache)
        logger.info("Chargement des métiers de référence...")
        metiers_reference = get_metiers_reference()
        
        if not metiers_reference:
            logger.error("Impossible de charger les métiers de référence")
            return {
                "openai_matching": {
                    "error": "Impossible de charger les métiers de référence",
                    "status": "error",
                    "metiers_matches": []
                },
                "step": "openai_matching",
                "success": False,
                **data 
            }
        
        logger.info(f"Nombre de métiers de référence chargés: {len(metiers_reference)}")
        
        # Traitement de chaque expérience professionnelle
        metiers_matches: List[Dict[str, Any]] = []
        
        for i, experience in enumerate(experiences):
            logger.info(f"Traitement de l'expérience {i+1}/{len(experiences)}")
            
            poste = experience.get("poste")
            entreprise = experience.get("entreprise", "")
            description = experience.get("description", "")
            
            if not poste:
                logger.warning(f"Expérience {i+1}: Poste non défini, ignoré")
                continue
                
            logger.info(f"Traitement du poste: {poste}")
            
            try:
                # Recherche des métiers correspondants via OpenAI
                matches = find_matching_metiers_openai(
                    poste=poste,
                    entreprise=entreprise,
                    description=description, 
                    metiers=metiers_reference
                )
                
                if matches:
                    logger.info(f"Métiers trouvés pour '{poste}': {len(matches)}")
                    metiers_matches.append({
                        "poste": poste,
                        "matches": matches
                    })
                else:
                    logger.warning(f"Aucun métier correspondant trouvé pour '{poste}'")
                    metiers_matches.append({
                        "poste": poste,
                        "matches": []
                    })
            except Exception as e:
                logger.error(f"Erreur lors de la recherche de métiers pour '{poste}': {str(e)}")
                metiers_matches.append({
                    "poste": poste,
                    "matches": [],
                    "error": str(e)
                })
        
        # Résumé des correspondances trouvées
        logger.info(f"Correspondances trouvées pour {len(metiers_matches)} postes")
        
        for match in metiers_matches:
            poste = match.get("poste", "")
            nb_matches = len(match.get("matches", []))
            logger.info(f"Poste '{poste}': {nb_matches} correspondances trouvées")
            if nb_matches > 0:
                top_match = match.get("matches", [])[0]
                logger.info(f"  Meilleure correspondance: {top_match.get('libelle', '')} (score: {top_match.get('score', 0):.4f})")
        
        # Retour des résultats
        return {
            "openai_matching": {
                "metiers_matches": metiers_matches,
                "status": "success"
            },
            "step": "openai_matching",
            "success": True,
            **data 
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction avec OpenAI: {str(e)}")
        return {
            "openai_matching": {
                "error": f"Erreur lors de l'extraction avec OpenAI: {str(e)}",
                "status": "error",
                "metiers_matches": []
            },
            "step": "openai_matching",
            "success": False,
            **data 
        }

def get_metiers_reference() -> List[MetierType]:
    """
    Récupère les métiers de référence, en utilisant le cache si disponible et valide.
    
    Returns:
        Liste des métiers de référence avec leurs attributs
    """
    global _metiers_cache, _metiers_cache_timestamp
    
    current_time = time.time()
    
    # Vérifier si le fichier a été modifié depuis le dernier chargement
    try:
        file_mtime = os.path.getmtime(METIERS_FILE_PATH)
    except OSError:
        # Si le fichier n'existe pas ou n'est pas accessible, on considère qu'il n'a pas été modifié
        file_mtime = 0
    
    # Vérifier si le cache est valide (non vide, pas expiré, fichier non modifié)
    cache_valid = (
        len(_metiers_cache) > 0 and
        (current_time - _metiers_cache_timestamp) < CACHE_TTL and
        file_mtime <= _metiers_cache_timestamp
    )
    
    if cache_valid:
        logger.info(f"Utilisation du cache pour les métiers de référence ({len(_metiers_cache)} métiers, âge: {int(current_time - _metiers_cache_timestamp)}s)")
        return _metiers_cache
    
    # Si le cache n'est pas valide, recharger les données
    logger.info("Cache invalide ou expiré, rechargement des métiers de référence")
    _metiers_cache = load_metiers_reference()
    _metiers_cache_timestamp = current_time
    
    return _metiers_cache

def load_metiers_reference() -> List[MetierType]:
    """
    Charge les métiers de référence depuis le fichier CSV.
    
    Returns:
        Liste des métiers de référence avec leurs attributs
    """
    try:
        # Vérification de l'existence du fichier
        if not os.path.exists(METIERS_FILE_PATH):
            logger.error(f"Fichier des métiers de référence non trouvé: {METIERS_FILE_PATH}")
            return []
        
        # Information sur la taille du fichier
        file_size = os.path.getsize(METIERS_FILE_PATH) / (1024 * 1024)  # Taille en Mo
        logger.info(f"Fichier des métiers trouvé: {METIERS_FILE_PATH} ({file_size:.2f} Mo)")
        
        # Liste des encodages à essayer pour ouvrir le fichier
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        metiers_data = []
        
        # Tentative d'ouverture avec différents encodages
        for encoding in encodings:
            try:
                logger.info(f"Tentative de chargement avec l'encodage: {encoding}")
                with open(METIERS_FILE_PATH, 'r', encoding=encoding) as f:
                    csv_reader = csv.DictReader(f)
                    metiers_data = list(csv_reader)
                logger.info(f"Chargement réussi avec l'encodage: {encoding}")
                break
            except UnicodeDecodeError as e:
                logger.warning(f"Échec du chargement avec l'encodage {encoding}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du CSV avec l'encodage {encoding}: {str(e)}")
                continue
        
        # Vérification du succès du chargement
        if not metiers_data:
            logger.error("Impossible de charger le fichier CSV avec les encodages essayés")
            return []
        
        logger.info(f"Nombre d'éléments dans le fichier CSV: {len(metiers_data)}")
        
        # Analyse du format des données
        if metiers_data and len(metiers_data) > 0:
            sample = metiers_data[0]
            logger.info(f"Format du premier élément: {type(sample).__name__}")
            if isinstance(sample, dict):
                logger.info(f"Clés disponibles: {', '.join(sample.keys())}")
        
        # Transformation des données en format standardisé
        metiers: List[MetierType] = []
        error_count = 0
        
        for i, metier in enumerate(metiers_data):
            try:
                # Vérification du type de l'élément
                if not isinstance(metier, dict):
                    logger.warning(f"Élément {i} ignoré car ce n'est pas un dictionnaire: {type(metier).__name__}")
                    error_count += 1
                    continue
                
                # Vérification des clés requises
                if "code_rome" not in metier:
                    logger.warning(f"Élément {i} ignoré car il n'a pas de code_rome")
                    error_count += 1
                    continue
                
                # Ajout du métier au format standardisé
                metiers.append({
                    "id": metier.get("code_rome"),
                    "code_rome": metier.get("code_rome"),
                    "libelle": metier.get("libelle_rome"),
                    "definition": "",  # Pas de définition dans le CSV
                    "appellations": []  # Pas d'appellations dans le CSV
                })
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'élément {i}: {str(e)}")
                error_count += 1
        
        logger.info(f"Chargement réussi de {len(metiers)} métiers de référence ({error_count} éléments ignorés)")
        
        # Afficher quelques exemples (commenté pour réduire le bruit dans les logs)
        # if metiers:
        #     logger.info("Exemples de métiers chargés:")
        #     for i, metier in enumerate(metiers[:3]):
        #         logger.info(f"{i+1}. ID: {metier.get('id')}, Code ROME: {metier.get('code_rome')}, Libellé: {metier.get('libelle')}")
        
        return metiers
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des métiers de référence: {str(e)}")
        return []

def find_matching_metiers_openai(poste: str, entreprise: str, description: str, metiers: List[MetierType], top_n: int = 1) -> List[MetierType]:
    """
    Trouve les métiers les plus similaires à un poste donné en utilisant OpenAI.
    
    Args:
        poste: Intitulé du poste
        entreprise: Nom de l'entreprise (peut être vide)
        description: Description du poste (peut être vide)
        metiers: Liste des métiers de référence
        top_n: Nombre de métiers à retourner (par défaut 1 pour ne retourner que le meilleur match)
        
    Returns:
        Liste des métiers les plus similaires avec leur score
    """
    # Vérification des paramètres d'entrée
    if not poste:
        logger.warning("Poste vide ou None, impossible de trouver des métiers correspondants")
        return []
    
    # Récupération de la clé API OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("Clé API OpenAI non configurée dans le fichier .env")
        return []
    
    try:
        # Initialisation du client OpenAI
        client = OpenAI(api_key=api_key)
        
        # Préparation des données pour le prompt
        metiers_text = ""
        for i, metier in enumerate(metiers):
            metiers_text += f"{i+1}. ID: {metier.get('id')}, Code ROME: {metier.get('code_rome')}, Libellé: {metier.get('libelle')}\n"
        
        # Construction du prompt pour OpenAI
        prompt = f"""
Voici un intitulé de poste extrait d'un CV : "{poste}" dans l'entreprise "{entreprise}" avec la description de poste suivante: "{description}"

Je dois trouver le métier correspondant dans la nomenclature ROME (Répertoire Opérationnel des Métiers et des Emplois).
Voici un échantillon des métiers disponibles dans la base ROME:

{metiers_text}

INSTRUCTIONS IMPORTANTES:
1. Prends en compte les spécificités du marché du travail ivoirien et les formulations locales des intitulés de poste.
3. En cas de doute entre plusieurs métiers, choisis celui qui a la portée la plus large.

Trouve le métier qui correspond le mieux à ce poste. Retourne uniquement le métier avec la plus forte probabilité de correspondance.
Réponds au format JSON avec les champs suivants:
- id: l'identifiant du métier
- code_rome: le code ROME du métier
- libelle: le libellé du métier
- score: un score de confiance entre 0 et 1 (1 étant une correspondance parfaite)

Si aucun métier ne correspond, retourne un tableau vide.
"""
        
        # Appel à l'API OpenAI
        logger.info(f"Envoi de la requête à OpenAI pour le poste: {poste}")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé dans la correspondance entre des intitulés de postes de CV et la nomenclature ROME des métiers. Tu privilégies les métiers génériques quand le contexte est insuffisant."},
                {"role": "user", "content": prompt}
            ],
            temperature=OPENAI_TEMPERATURE  # Température configurable
        )
        
        # Extraction et traitement de la réponse
        response_content = response.choices[0].message.content
        
        # Vérification que la réponse n'est pas None
        if response_content is None:
            logger.error("Réponse vide reçue d'OpenAI")
            return []
            
        try:
            # Parsing de la réponse JSON
            result = json.loads(cast(str, response_content))
            
            # Validation du format de la réponse
            if isinstance(result, dict) and all(k in result for k in ["id", "code_rome", "libelle", "score"]):
                # Conversion en liste pour compatibilité avec l'interface existante
                return [{
                    "id": result.get("id"),
                    "code_rome": result.get("code_rome"),
                    "libelle": result.get("libelle"),
                    "score": float(result.get("score", 0)),
                }]
            else:
                logger.warning(f"Format de réponse OpenAI invalide: {response_content}")
                return []
                
        except json.JSONDecodeError:
            logger.error(f"Erreur lors du parsing de la réponse JSON: {response_content}")
            return []
            
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à OpenAI: {str(e)}")
        return [] 