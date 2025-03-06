"""
Module pour la transformation des données extraites de fichiers PDF.
"""
import time
from prefect import task
from collections import Counter

@task
def transformation(data):
    """
    Transformation des données extraites du PDF
    
    Args:
        data: Dictionnaire contenant les données extraites du PDF et les données extraites par OpenAI
        
    Returns:
        Dictionnaire contenant les données transformées
    """
    extracted_data = data.get("extracted", {})
    openai_data = data.get("openai_extracted", {})
    openai_matching_data = data.get("openai_matching", {})
    
    # Vérifier si nous avons des données PDF extraites
    if data.get("pdf_available", False):
        # Si une erreur s'est produite lors de l'extraction, la propager
        if "extraction_error" in data:
            return {
                "transformed": {
                    "error": f"Erreur lors de l'extraction: {data['extraction_error']}",
                    "status": "error"
                },
                "step": "transformation",
                "success": False
            }
        
        # Traiter le texte extrait
        text_content = extracted_data.get("text_content", "")
        
        # Exemple de transformation simple: statistiques sur le texte
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        # Analyse basique du contenu (exemple simplifié)
        keywords = []
        if word_count > 0:
            # Extraire les mots les plus fréquents (exemple simple)
            words = [word.lower() for word in text_content.split() if len(word) > 3]
            word_freq = Counter(words).most_common(10)
            keywords = [word for word, _ in word_freq]
        
        cv_data = {}
        if openai_data and openai_data.get("status") != "error":
            cv_data = {
                "formations": openai_data.get("formations", []),
                "experiences_professionnelles": openai_data.get("experiences_professionnelles", []),
                "extracteur": "openai"
            }
       
        if openai_matching_data and openai_matching_data.get("status") != "error":
            cv_data["metiers_matches"] = openai_matching_data.get("metiers_matches", [])
        
        return {
            "transformed": {
                "original_filename": extracted_data.get("pdf_filename", "document.pdf"),
                "statistics": {
                    "word_count": word_count,
                    "character_count": char_count,
                    "page_count": extracted_data.get("num_pages", 0)
                },
                "content_analysis": {
                    "keywords": keywords,
                    "language": "fr" if "fr" in extracted_data.get("metadata", {}).get("language", "").lower() else "en"  # Simplification
                },
                "cv_data": cv_data,
                "metadata": extracted_data.get("metadata", {}),
                "transformation_time": time.time()
            },
            "step": "transformation",
            "success": True
        }
    
    # Comportement par défaut si ce n'est pas un PDF
    return {"transformed": data, "step": "transformation"} 