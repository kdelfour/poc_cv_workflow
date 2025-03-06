"""
Utilitaires pour la manipulation et le traitement des fichiers PDF.

Ce module fournit des fonctions utilitaires pour préparer et manipuler
les fichiers PDF avant leur traitement par les workflows.
"""

import base64
import json
from typing import Dict, Any, Optional, Union

# Types personnalisés pour améliorer la lisibilité
PDFContent = bytes
PDFMetadata = Dict[str, Any]

def prepare_pdf_input_data(
    pdf_content: PDFContent,
    filename: str,
    content_type: str,
    additional_data: Optional[str] = None
) -> PDFMetadata:
    """
    Prépare les données d'entrée pour le traitement d'un PDF.
    
    Cette fonction :
    1. Encode le contenu binaire du PDF en base64
    2. Organise les métadonnées du fichier
    3. Intègre des données supplémentaires si fournies
    
    Args:
        pdf_content (PDFContent): Contenu binaire du fichier PDF
        filename (str): Nom du fichier PDF avec son extension
        content_type (str): Type MIME du fichier (e.g., 'application/pdf')
        additional_data (Optional[str]): Données JSON supplémentaires au format string
            Ces données seront parsées et intégrées au dictionnaire de sortie
    
    Returns:
        PDFMetadata: Dictionnaire contenant :
            - pdf_filename: Nom du fichier
            - pdf_content_b64: Contenu du PDF encodé en base64
            - content_type: Type MIME du fichier
            - [clés supplémentaires]: Si additional_data est fourni
    
    Raises:
        json.JSONDecodeError: Si additional_data est fourni mais n'est pas un JSON valide
    """
    # Encoder le contenu du PDF en base64
    pdf_content_b64 = base64.b64encode(pdf_content).decode('utf-8')
    
    # Préparer les données d'entrée avec les champs requis
    input_data: PDFMetadata = {
        "pdf_filename": filename,
        "pdf_content_b64": pdf_content_b64,
        "content_type": content_type
    }
    
    # Ajouter des données supplémentaires si fournies
    if additional_data:
        try:
            additional_json = json.loads(additional_data)
            input_data.update(additional_json)
        except json.JSONDecodeError:
            # Si le parsing JSON échoue, stocker la chaîne brute
            input_data["additional_data"] = additional_data
            
    return input_data 