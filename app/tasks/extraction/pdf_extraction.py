"""
Module pour l'extraction de données à partir de fichiers PDF.
"""
import time
import base64
import io
from prefect import task
import PyPDF2

@task
def extraction(data):
    """
    Extraction des données du PDF
    
    Args:
        data: Dictionnaire contenant les données d'entrée, notamment le contenu du PDF en base64
        
    Returns:
        Dictionnaire contenant les données extraites du PDF
    """
    # Vérifier si nous avons un PDF
    if "pdf_content_b64" in data:
        try:
            # Décoder le contenu du PDF depuis base64
            pdf_bytes = base64.b64decode(data["pdf_content_b64"])
            
            # Utiliser PyPDF2 pour extraire le texte
            pdf_text = ""
            pdf_metadata = {}
            
            with io.BytesIO(pdf_bytes) as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extraire les métadonnées
                if pdf_reader.metadata:
                    pdf_metadata = {k.lower().replace('/', '_'): v for k, v in pdf_reader.metadata.items()}
                
                # Extraire le texte de chaque page
                num_pages = len(pdf_reader.pages)
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    pdf_text += page.extract_text() + "\n\n"
            
            return {
                "extracted": {
                    "pdf_filename": data.get("pdf_filename", "document.pdf"),
                    "content_type": data.get("content_type", "application/pdf"),
                    "pdf_size_bytes": len(pdf_bytes),
                    "num_pages": num_pages,
                    "text_content": pdf_text,
                    "metadata": {
                        **pdf_metadata,
                        "source": "pdf_upload",
                        "extraction_time": time.time()
                    }
                },
                "step": "extraction",
                "pdf_available": True
            }
        except Exception as e:
            return {
                "extracted": {
                    "pdf_filename": data.get("pdf_filename", "document.pdf"),
                    "error": str(e),
                    "metadata": {
                        "source": "pdf_upload",
                        "extraction_time": time.time(),
                        "extraction_success": False
                    }
                },
                "step": "extraction",
                "pdf_available": True,
                "extraction_error": str(e)
            }
    
    return {"extracted": data, "step": "extraction", "pdf_available": False} 