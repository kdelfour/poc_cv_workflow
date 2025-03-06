"""
Package pour les tâches d'extraction de données.
"""
from app.tasks.extraction.pdf_extraction import extraction
from app.tasks.extraction.openai_matching import openai_matching
from app.tasks.extraction.openai_extraction import openai_extraction

__all__ = ['extraction', 'openai_matching', 'openai_extraction'] 