"""
Package pour les tâches ETL (Extraction, Transformation, Chargement).
"""
from app.tasks.extraction import extraction
from app.tasks.transformation import transformation
from app.tasks.chargement import chargement

__all__ = ['extraction', 'transformation', 'chargement']

# Ce fichier permet à Python de reconnaître le répertoire comme un package 