from fastapi import FastAPI
import uvicorn
import logging
from app.api.workflow_endpoints import router as workflow_router
from app.utils.logging_utils import setup_logger

# Configuration du logger principal via le module centralisé
logger = setup_logger("main")
logger.info("Démarrage de l'application")

# Création de l'application FastAPI
app = FastAPI(
    title="API Workflow PDF",
    description="API pour le traitement de fichiers PDF via des workflows",
    version="1.0.0"
)

# Inclusion des routers
app.include_router(workflow_router)

# Route racine
@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Bienvenue sur l'API de traitement de PDF",
        "documentation": "/docs",
        "endpoints": {
            "workflow_run": "/workflow/run",
            "workflow_run_sync": "/workflow/run/sync",
            "workflow_status": "/workflow/status/{workflow_id}",
            "active_workflows": "/workflow/active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)