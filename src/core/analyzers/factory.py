"""Factory para crear analizadores de código."""
from pathlib import Path
from typing import Optional, List

from src.core.analyzers.base import CodeAnalyzer
from src.core.analyzers.python_analyzer import PythonAnalyzer
from src.core.analyzers.java_analyzer import JavaAnalyzer
from src.core.analyzers.javascript_analyzer import JavaScriptAnalyzer
from src.core.analyzers.typescript_analyzer import TypeScriptAnalyzer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AnalyzerFactory:
    """Factory para crear analizadores según el tipo de archivo."""
    
    def __init__(self) -> None:
        self._analyzers: List[CodeAnalyzer] = [
            PythonAnalyzer(),
            JavaAnalyzer(),
            JavaScriptAnalyzer(),
            TypeScriptAnalyzer(),
        ]
    
    def get_analyzer(self, file_path: Path) -> Optional[CodeAnalyzer]:
        """Obtiene el analizador apropiado para el archivo."""
        for analyzer in self._analyzers:
            if analyzer.can_analyze(file_path):
                logger.debug("analyzer_found", file_path=str(file_path), analyzer=type(analyzer).__name__)
                return analyzer
        
        logger.debug("no_analyzer_found", file_path=str(file_path))
        return None
    
    def register_analyzer(self, analyzer: CodeAnalyzer) -> None:
        """Registra un nuevo analizador."""
        self._analyzers.append(analyzer)
        logger.info("analyzer_registered", analyzer=type(analyzer).__name__)
