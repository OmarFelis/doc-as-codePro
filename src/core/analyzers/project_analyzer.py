"""Servicio principal de análisis de proyectos."""
from pathlib import Path
from typing import List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.analyzers.factory import AnalyzerFactory
from src.models.domain import ProjectAnalysis, FileAnalysis, AnalysisStatus, ComponentType
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProjectAnalyzerService:
    """Servicio para analizar proyectos completos."""
    
    # Carpetas a ignorar
    IGNORED_FOLDERS: Set[str] = {
        'ci-scripts', 'service', 'docs', '.amazonq',
        '.git', '.github', '.vscode', '.idea', '__pycache__', 'node_modules',
        'venv', 'env', '.env', 'dist', 'build', 'target', 'bin', 'obj',
        '.pytest_cache', '.mypy_cache', '.ruff_cache', '.coverage', 'htmlcov',
        'vendor', 'tmp', 'temp', 'logs', 'log', 'out', 'output'
    }
    
    # Archivos a ignorar
    IGNORED_FILES: Set[str] = {
        '.DS_Store', '.gitignore', 'LICENSE', 'README.md', 'CHANGELOG.md',
        'package-lock.json', 'yarn.lock', 'requirements.txt', 'Dockerfile'
    }
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.analyzer_factory = AnalyzerFactory()
    
    def analyze_project(
        self,
        project_path: Path,
        repository_name: str,
        repository_owner: str = "unknown"
    ) -> ProjectAnalysis:
        """Analiza un proyecto completo."""
        logger.info(
            "starting_project_analysis",
            project_path=str(project_path),
            repository_name=repository_name
        )
        
        analysis = ProjectAnalysis(
            repository_name=repository_name,
            repository_owner=repository_owner,
            status=AnalysisStatus.PROCESSING
        )
        
        # Recolectar archivos a analizar
        files_to_analyze = self._collect_files(project_path)
        logger.info("files_collected", count=len(files_to_analyze))
        
        # Analizar archivos (paralelo o secuencial según config)
        if self.settings.analyzer.parallel_processing:
            file_analyses = self._analyze_files_parallel(files_to_analyze)
        else:
            file_analyses = self._analyze_files_sequential(files_to_analyze)
        
        # Agregar análisis al proyecto
        analysis.files = file_analyses
        analysis.total_files = len(file_analyses)
        analysis.total_lines = sum(f.lines for f in file_analyses)
        analysis.languages = list(set(f.language for f in file_analyses))
        
        # Clasificar componentes
        analysis.components = self._classify_components(file_analyses)
        
        analysis.status = AnalysisStatus.COMPLETED
        
        logger.info(
            "project_analysis_completed",
            total_files=analysis.total_files,
            total_lines=analysis.total_lines,
            languages=[lang.value for lang in analysis.languages]
        )
        
        return analysis
    
    def _collect_files(self, project_path: Path) -> List[Path]:
        """Recolecta archivos válidos para analizar."""
        files: List[Path] = []
        max_size = self.settings.analyzer.max_file_size_kb * 1024
        
        for file_path in project_path.rglob('*'):
            # Ignorar directorios
            if file_path.is_dir():
                continue
            
            # Ignorar carpetas en el path
            if any(ignored in file_path.parts for ignored in self.IGNORED_FOLDERS):
                continue
            
            # Ignorar archivos específicos
            if file_path.name in self.IGNORED_FILES:
                continue
            
            # Ignorar archivos muy grandes
            try:
                if file_path.stat().st_size > max_size:
                    logger.debug("file_too_large", file_path=str(file_path))
                    continue
            except OSError:
                continue
            
            # Verificar si tenemos analizador
            if self.analyzer_factory.get_analyzer(file_path):
                files.append(file_path)
        
        return files
    
    def _analyze_files_sequential(self, files: List[Path]) -> List[FileAnalysis]:
        """Analiza archivos secuencialmente."""
        analyses: List[FileAnalysis] = []
        
        for file_path in files:
            try:
                analyzer = self.analyzer_factory.get_analyzer(file_path)
                if analyzer:
                    analysis = analyzer.analyze_file(file_path)
                    analyses.append(analysis)
            except Exception as e:
                logger.error("file_analysis_failed", file_path=str(file_path), error=str(e))
        
        return analyses
    
    def _analyze_files_parallel(self, files: List[Path]) -> List[FileAnalysis]:
        """Analiza archivos en paralelo."""
        analyses: List[FileAnalysis] = []
        max_workers = self.settings.analyzer.max_workers
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_single_file, file_path): file_path
                for file_path in files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    analysis = future.result()
                    if analysis:
                        analyses.append(analysis)
                except Exception as e:
                    logger.error("file_analysis_failed", file_path=str(file_path), error=str(e))
        
        return analyses
    
    def _analyze_single_file(self, file_path: Path) -> FileAnalysis | None:
        """Analiza un archivo individual."""
        analyzer = self.analyzer_factory.get_analyzer(file_path)
        if analyzer:
            return analyzer.analyze_file(file_path)
        return None
    
    def _classify_components(self, file_analyses: List[FileAnalysis]) -> dict[ComponentType, List[str]]:
        """Clasifica archivos en componentes."""
        components: dict[ComponentType, List[str]] = {
            ComponentType.API: [],
            ComponentType.DATABASE: [],
            ComponentType.SECURITY: [],
            ComponentType.UTILITY: [],
            ComponentType.INTEGRATION: []
        }
        
        for analysis in file_analyses:
            file_lower = analysis.file_path.lower()
            
            # Clasificar por características
            if analysis.endpoints:
                components[ComponentType.API].append(analysis.file_path)
            elif analysis.database_calls:
                components[ComponentType.DATABASE].append(analysis.file_path)
            elif any(keyword in file_lower for keyword in ['auth', 'security', 'crypto']):
                components[ComponentType.SECURITY].append(analysis.file_path)
            elif any(keyword in file_lower for keyword in ['client', 'integration', 'external']):
                components[ComponentType.INTEGRATION].append(analysis.file_path)
            else:
                components[ComponentType.UTILITY].append(analysis.file_path)
        
        return components
