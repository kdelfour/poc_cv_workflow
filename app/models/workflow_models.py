from pydantic import BaseModel
from typing import Dict, Optional

class WorkflowRequest(BaseModel):
    """Modèle pour les requêtes de workflow"""
    input_data: dict
    workflow_name: str = "default_workflow"

class WorkflowInfo(BaseModel):
    """Modèle pour les informations de workflow"""
    workflow_id: str
    workflow_name: str
    start_time: float
    status: str 