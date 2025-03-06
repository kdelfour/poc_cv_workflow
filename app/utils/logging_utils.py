"""
Module utilitaire pour centraliser la configuration des logs dans l'application.

Ce module fournit des fonctions et configurations pour standardiser le logging
à travers l'application. Il permet de :
- Configurer des loggers avec des paramètres cohérents
- Gérer les niveaux de log via des variables d'environnement
- Éviter la duplication des logs
- Formater les messages de log de manière uniforme

Configuration:
    Le niveau de log peut être configuré via la variable d'environnement LOG_LEVEL.
    Valeurs possibles : DEBUG, INFO, WARNING, ERROR, CRITICAL
    Valeur par défaut : INFO
"""
import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Types personnalisés pour améliorer la lisibilité
LogLevel = int
LoggerName = str
ConfigItems = Dict[str, Any]

# Mapper les niveaux de log en string vers les constantes de logging
LOG_LEVEL_MAP: Dict[str, LogLevel] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Récupérer le niveau de log depuis les variables d'environnement
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVEL = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL)
LOG_LEVEL_VALUE = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)

def setup_logger(
    logger_name: LoggerName,
    level: Optional[LogLevel] = None
) -> logging.Logger:
    """
    Configure un logger avec des paramètres optimisés pour l'application.
    
    Cette fonction :
    1. Crée ou récupère un logger avec le nom spécifié
    2. Configure son niveau de log
    3. Ajoute un handler de console avec formatage
    4. Évite la duplication des logs
    
    Args:
        logger_name (LoggerName): Nom unique du logger à configurer
        level (Optional[LogLevel]): Niveau de log spécifique à utiliser.
            Si non spécifié, utilise le niveau défini par LOG_LEVEL_VALUE
    
    Returns:
        logging.Logger: Logger configuré prêt à l'emploi
    
    Example:
        >>> logger = setup_logger("mon_module")
        >>> logger.info("Message de test")
        2024-03-06 15:30:00 - mon_module - INFO - Message de test
    """
    # Obtenir ou créer le logger
    logger = logging.getLogger(logger_name)
    
    # Définir le niveau de log
    log_level = level if level is not None else LOG_LEVEL_VALUE
    logger.setLevel(log_level)
    
    # Éviter les logs en double
    if logger.handlers:
        logger.handlers.clear()
    
    # Ajouter un gestionnaire de console avec formatage standardisé
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Empêcher la propagation des logs vers les loggers parents
    logger.propagate = False
    
    return logger

def get_log_level() -> LogLevel:
    """
    Renvoie le niveau de log actuellement configuré.
    
    Cette fonction permet de connaître le niveau de log par défaut
    utilisé dans l'application, tel que défini par la variable
    d'environnement LOG_LEVEL ou la valeur par défaut.
    
    Returns:
        LogLevel: Niveau de log sous forme de constante logging
            (e.g., logging.INFO, logging.DEBUG, etc.)
    """
    return LOG_LEVEL_VALUE

def log_config_info(logger: logging.Logger, config_items: ConfigItems) -> None:
    """
    Affiche les informations de configuration dans les logs de manière structurée.
    
    Cette fonction est utile pour logger l'état de la configuration
    au démarrage de l'application ou après un rechargement.
    
    Args:
        logger (logging.Logger): Logger à utiliser pour l'affichage
        config_items (ConfigItems): Dictionnaire des éléments de configuration
            à afficher, où les clés sont les noms des paramètres
            et les valeurs sont leurs valeurs actuelles
    
    Example:
        >>> logger = setup_logger("config")
        >>> config = {"db_host": "localhost", "port": 5432}
        >>> log_config_info(logger, config)
        2024-03-06 15:30:00 - config - INFO - Configuration chargée:
        2024-03-06 15:30:00 - config - INFO - - db_host: localhost
        2024-03-06 15:30:00 - config - INFO - - port: 5432
    """
    logger.info("Configuration chargée:")
    for key, value in config_items.items():
        logger.info(f"- {key}: {value}") 