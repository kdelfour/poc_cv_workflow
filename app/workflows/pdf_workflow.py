"""
Module définissant les workflows de traitement de PDF.

Ce module implémente les workflows de traitement des documents PDF en utilisant Prefect
pour l'orchestration des tâches. Il gère le cycle de vie complet du traitement :
- Extraction des données brutes
- Analyse avec OpenAI
- Transformation des données
- Chargement des résultats

Les workflows sont suivis en mémoire via le dictionnaire `active_workflows`.
"""
from prefect import flow
from typing import Dict, Any, Optional, Union
from app.tasks import extraction, transformation, chargement
from app.tasks.extraction.openai_matching import openai_matching
from app.tasks.extraction.openai_extraction import openai_extraction

# Types personnalisés pour améliorer la lisibilité
WorkflowId = str
WorkflowData = Dict[str, Any]
WorkflowResult = Dict[str, Any]

# Stockage en mémoire des workflows actifs (dans un projet réel, utilisez une BD)
active_workflows: Dict[WorkflowId, WorkflowData] = {}

@flow
def workflow_process(
    workflow_id: WorkflowId,
    input_data: Optional[WorkflowData] = None,
    name: str = "default_workflow"
) -> WorkflowResult:
    """
    Workflow principal pour le traitement des documents PDF.
    
    Ce workflow orchestre l'ensemble du processus de traitement :
    1. Extraction des données brutes du PDF
    2. Extraction d'informations via OpenAI
    3. Matching des métiers via OpenAI
    4. Transformation des données
    5. Chargement des résultats
    
    Args:
        workflow_id (WorkflowId): Identifiant unique du workflow
        input_data (Optional[WorkflowData]): Données d'entrée pour le workflow,
            contenant le contenu du PDF et les métadonnées
        name (str): Nom du workflow pour le suivi et le logging
    
    Returns:
        WorkflowResult: Résultat du workflow après traitement complet,
            incluant les données extraites et transformées
    
    Raises:
        Exception: En cas d'erreur pendant l'une des étapes du workflow.
            Le statut du workflow sera mis à jour en conséquence.
    """
    try:
        if input_data is None:
            input_data = {"initial": "data"}
        
        # Extraction des données brutes du PDF
        active_workflows[workflow_id]["status"] = "extraction"
        data = extraction(input_data)
        
        # Extraction d'informations via OpenAI
        active_workflows[workflow_id]["status"] = "openai_extraction"
        data_with_extraction = openai_extraction(data)
        
        # Matching des métiers via OpenAI
        active_workflows[workflow_id]["status"] = "openai_matching"
        data_with_metiers = openai_matching(data_with_extraction)
        
        # Transformation des données
        active_workflows[workflow_id]["status"] = "transformation"
        transformed = transformation(data_with_metiers)
        
        # Chargement des résultats
        active_workflows[workflow_id]["status"] = "chargement"
        result = chargement(transformed)
        
        # Mise à jour du statut final
        active_workflows[workflow_id]["status"] = "completed"
        return result
    except Exception as e:
        active_workflows[workflow_id]["status"] = "failed"
        active_workflows[workflow_id]["error"] = str(e)
        raise 