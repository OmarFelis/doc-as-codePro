"""Interfaz base para analizadores de código."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

from src.models.domain import FileAnalysis, LanguageType


class CodeAnalyzer(ABC):
    """Interfaz base para analizadores de código."""
    
    @property
    @abstractmethod
    def supported_languages(self) -> List[LanguageType]:
        """Lenguajes soportados por este analizador."""
        pass
    
    @abstractmethod
    def can_analyze(self, file_path: Path) -> bool:
        """Determina si puede analizar el archivo."""
        pass
    
    @abstractmethod
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analiza un archivo y retorna el análisis."""
        pass
    
    def _count_lines(self, file_path: Path) -> int:
        """Cuenta líneas de código (sin comentarios ni líneas vacías)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        except Exception:
            return 0
    
    def _read_file_content(self, file_path: Path) -> str:
        """Lee el contenido del archivo."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error leyendo archivo {file_path}: {e}")
