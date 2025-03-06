"""
Module pour le chargement des données transformées de fichiers PDF.
"""
import time
import uuid
from prefect import task

@task
def chargement(data):
    """
    Chargement des données transformées du PDF
    
    Args:
        data: Dictionnaire contenant les données transformées du PDF
        
    Returns:
        Dictionnaire contenant les résultats du chargement
    """
    transformed_data = data.get("transformed", {})
    
    # Vérifier si la transformation a réussi
    if data.get("success", True):
        # Simuler le chargement des données dans une base de données ou un système de stockage
        result = {
            "loaded": {
                "original_data": transformed_data,
                "load_status": "success",
                "load_time": time.time(),
                "storage_reference": f"pdf_analysis_{uuid.uuid4()}"
            },
            "step": "load_complete",
            "success": True
        }
        
        # Si nous avons des statistiques (cas du PDF), les inclure dans le résultat
        if "statistics" in transformed_data:
            result["loaded"]["analysis_summary"] = {
                "filename": transformed_data.get("original_filename", "document.pdf"),
                "word_count": transformed_data.get("statistics", {}).get("word_count", 0),
                "page_count": transformed_data.get("statistics", {}).get("page_count", 0),
                "top_keywords": transformed_data.get("content_analysis", {}).get("keywords", [])[:5],
                "language": transformed_data.get("content_analysis", {}).get("language", "unknown")
            }
            
            # Inclure les correspondances de métiers si disponibles
            cv_data = transformed_data.get("cv_data", {})
            if "metiers_matches" in cv_data:
                result["loaded"]["metiers_matches"] = cv_data["metiers_matches"]
        
        return result
    else:
        # En cas d'échec de la transformation
        return {
            "loaded": {
                "error": "Échec de la transformation des données",
                "original_error": transformed_data.get("error", "Erreur inconnue"),
                "load_status": "failed",
                "load_time": time.time()
            },
            "step": "load_complete",
            "success": False
        } 