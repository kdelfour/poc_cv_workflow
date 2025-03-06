import uuid
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, File, UploadFile, Form, HTTPException
from app.models.workflow_models import WorkflowInfo
from app.workflows.pdf_workflow import workflow_process, active_workflows
from app.utils.pdf_utils import prepare_pdf_input_data

# Création du router pour les endpoints de workflow
router = APIRouter(
    prefix="/workflow",
    tags=["workflow"]  # Tag pour regrouper les endpoints dans la documentation
)

@router.post("/run", response_model=Dict[str, str])
async def run_workflow(
    workflow_name: str = Form("default_workflow"),
    pdf_file: UploadFile = File(...),
    additional_data: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, str]:
    """
    Lance l'exécution d'un workflow en mode asynchrone.
    
    Args:
        workflow_name (str): Nom du workflow à exécuter
        pdf_file (UploadFile): Fichier PDF à traiter
        additional_data (Optional[str]): Données supplémentaires pour le workflow
        background_tasks (BackgroundTasks): Gestionnaire de tâches en arrière-plan
    
    Returns:
        Dict[str, str]: Informations sur le workflow lancé, incluant:
            - status: État du lancement
            - workflow_name: Nom du workflow
            - workflow_id: Identifiant unique du workflow
    
    Raises:
        HTTPException: En cas d'erreur lors de la lecture du fichier ou de l'initialisation
    """
    workflow_id = str(uuid.uuid4())
    
    # Lire le contenu du fichier PDF
    pdf_content = await pdf_file.read()
    
    if not pdf_file.filename or not pdf_file.content_type:
        raise HTTPException(
            status_code=400,
            detail="Le fichier PDF doit avoir un nom et un type de contenu valides"
        )
    
    # Préparer les données d'entrée
    input_data = prepare_pdf_input_data(
        pdf_content=pdf_content,
        filename=pdf_file.filename,
        content_type=pdf_file.content_type,
        additional_data=additional_data
    )
    
    # Enregistrer le workflow
    active_workflows[workflow_id] = {
        "workflow_name": workflow_name,
        "start_time": time.time(),
        "status": "initializing",
        "input_data": {
            "pdf_filename": pdf_file.filename,
            "content_type": pdf_file.content_type,
            # Ne pas stocker le contenu complet du PDF dans les logs
        }
    }
    
    def execute_workflow():
        try:
            workflow_process(workflow_id, input_data, name=workflow_name)
        except Exception as e:
            # Déjà géré dans le flow
            pass
    
    background_tasks.add_task(execute_workflow)
    return {"status": "Workflow lancé", "workflow_name": workflow_name, "workflow_id": workflow_id}

@router.post("/run/sync", response_model=Dict[str, Any])
async def run_workflow_sync(
    workflow_name: str = Form("default_workflow"),
    pdf_file: UploadFile = File(...),
    additional_data: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Exécute un workflow de manière synchrone et attend le résultat.
    
    Args:
        workflow_name (str): Nom du workflow à exécuter
        pdf_file (UploadFile): Fichier PDF à traiter
        additional_data (Optional[str]): Données supplémentaires pour le workflow
    
    Returns:
        Dict[str, Any]: Résultat complet du workflow, incluant:
            - workflow_info: Informations sur l'exécution du workflow
            - [autres clés]: Résultats spécifiques au workflow
    
    Raises:
        HTTPException: En cas d'erreur pendant l'exécution du workflow
    """
    workflow_id = str(uuid.uuid4())
    
    # Lire le contenu du fichier PDF
    pdf_content = await pdf_file.read()
    
    if not pdf_file.filename or not pdf_file.content_type:
        raise HTTPException(
            status_code=400,
            detail="Le fichier PDF doit avoir un nom et un type de contenu valides"
        )
    
    # Préparer les données d'entrée
    input_data = prepare_pdf_input_data(
        pdf_content=pdf_content,
        filename=pdf_file.filename,
        content_type=pdf_file.content_type,
        additional_data=additional_data
    )
    
    # Enregistrer le workflow
    active_workflows[workflow_id] = {
        "workflow_name": workflow_name,
        "start_time": time.time(),
        "status": "initializing",
        "input_data": {
            "pdf_filename": pdf_file.filename,
            "content_type": pdf_file.content_type,
            # Ne pas stocker le contenu complet du PDF dans les logs
        }
    }
    
    try:
        # Exécuter le workflow de manière synchrone
        result = workflow_process(workflow_id, input_data, name=workflow_name)
        
        # Ajouter des informations sur le workflow au résultat
        if result is not None:
            result["workflow_info"] = {
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "execution_time": time.time() - active_workflows[workflow_id]["start_time"],
                "status": active_workflows[workflow_id]["status"]
            }
        else:
            # Si result est None, créer un dictionnaire de résultat
            result = {
                "workflow_info": {
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "execution_time": time.time() - active_workflows[workflow_id]["start_time"],
                    "status": active_workflows[workflow_id]["status"],
                    "error": "Le workflow n'a pas retourné de résultat"
                }
            }
        
        return result
    except Exception as e:
        # En cas d'erreur, retourner les détails de l'erreur
        return {
            "error": str(e),
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "status": active_workflows[workflow_id]["status"] if workflow_id in active_workflows else "failed"
        }

@router.get("/status/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """
    Récupère le statut détaillé d'un workflow spécifique.
    
    Args:
        workflow_id (str): Identifiant unique du workflow
    
    Returns:
        Dict[str, Any]: Informations sur le statut du workflow, incluant:
            - workflow_id: Identifiant du workflow
            - status: État actuel du workflow
            - workflow_name: Nom du workflow
            - start_time: Timestamp de début d'exécution
    
    Raises:
        HTTPException: Si le workflow n'est pas trouvé
    """
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail=f"Workflow non trouvé: {workflow_id}")
    
    return {
        "workflow_id": workflow_id,
        "status": active_workflows[workflow_id]["status"],
        "workflow_name": active_workflows[workflow_id]["workflow_name"],
        "start_time": active_workflows[workflow_id]["start_time"]
    }

# Endpoint pour récupérer la liste des workflows actifs
@router.get("/active", response_model=List[WorkflowInfo])
async def get_active_workflows() -> List[WorkflowInfo]:
    """
    Récupère la liste de tous les workflows actuellement actifs.
    
    Returns:
        List[WorkflowInfo]: Liste des workflows actifs avec leurs informations:
            - workflow_id: Identifiant unique
            - workflow_name: Nom du workflow
            - start_time: Timestamp de début
            - status: État actuel
    """
    return [
        WorkflowInfo(
            workflow_id=wf_id,
            workflow_name=info["workflow_name"],
            start_time=info["start_time"],
            status=info["status"]
        )
        for wf_id, info in active_workflows.items()
    ] 