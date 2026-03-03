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
    
    # Carpetas a ignorar (dependencias, cache, build artifacts)
    IGNORED_FOLDERS: Set[str] = {
        # Control de versiones
        '.git', '.github', '.gitignore',
        # IDEs
        '.vscode', '.idea', '.amazonq',
        # Python
        '__pycache__', '.venv', 'venv', 'env', '.env', 'site-packages',
        '.pytest_cache', '.mypy_cache', '.ruff_cache', '.coverage', 'htmlcov',
        # Node / JS
        'node_modules', '.npm', '.yarn', '.pnp',
        # Java / Kotlin
        'target', 'bin', 'obj', '.gradle', '.mvn',
        # Build / dist
        'dist', 'build', 'out', 'output',
        # Misc
        'vendor', 'tmp', 'temp', 'logs', 'log',
        'ci-scripts', 'docs', '.amazonq',
        # Java test dirs
        'test', 'tests', 'it', 'integration-test',
        # Java web frontend (no es código de negocio)
        'WebRoot', 'WebContent', 'webapp', 'web', 'static', 'public', 'assets', 'resources',
    }

    # Extensiones de archivos a ignorar (binarios, assets, no código fuente)
    IGNORED_EXTENSIONS: Set[str] = {
        '.lock', '.log',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        '.pdf', '.docx', '.xlsx',
        '.zip', '.tar', '.gz', '.whl', '.egg',
        '.pyc', '.pyo', '.class', '.map',
        '.min.js',  # minificados JS
    }

    # Archivos a ignorar (lockfiles y archivos de packaging, NO configs)
    IGNORED_FILES: Set[str] = {
        '.DS_Store', '.gitignore', 'LICENSE',
        'package-lock.json', 'yarn.lock', 'poetry.lock',
        'Pipfile.lock',
    }

    # Patrones de nombre de archivo a ignorar (vendor libs conocidas)
    IGNORED_FILE_PATTERNS: Set[str] = {
        'jquery', 'prototype', 'bootstrap', 'angular', 'react', 'vue',
        'lodash', 'underscore', 'moment', 'axios', 'popper',
    }

    # Prefijos de archivos a ignorar (scripts de utilidad, no código de producción)
    IGNORED_FILE_PREFIXES: Set[str] = {
        'test_', 'check_', 'verify_', 'debug_', 'seed_',
        'generate_', 'setup_phase', 'run_migrations', 'create_test',
        'initial_data', 'init_db',
        # Java: clases generadas por Hibernate/JPA
        'Abstract', 'Tvf',
    }

    # Sufijos de stem a ignorar (backups, versiones alternativas) — sin extensión
    IGNORED_FILE_STEM_SUFFIXES: Set[str] = {
        '_ok', '_bak', '_backup', '_old', '_copy', '_orig', '_tmp',
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
            languages=analysis.languages  # Ya son strings gracias a use_enum_values=True
        )
        
        return analysis
    
    def _collect_files(self, project_path: Path) -> List[Path]:
        """Recolecta archivos válidos para analizar."""
        files: List[Path] = []
        max_size = self.settings.analyzer.max_file_size_kb * 1024
        self._walk_dir(project_path, files, max_size)
        return files

    # Carpetas a ignorar solo cuando su padre tiene este nombre
    IGNORED_CHILD_FOLDERS: dict[str, Set[str]] = {
        'hibernate': {'data'},
    }

    def _walk_dir(self, directory: Path, files: List[Path], max_size: int) -> None:
        """Walk recursivo con pruning de directorios ignorados."""
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                if entry.name in self.IGNORED_FOLDERS:
                    continue
                parent_name = entry.parent.name
                if entry.name in self.IGNORED_CHILD_FOLDERS.get(parent_name, set()):
                    continue
                self._walk_dir(entry, files, max_size)
                continue

            if entry.name in self.IGNORED_FILES:
                continue
            if any(entry.name.startswith(p) for p in self.IGNORED_FILE_PREFIXES):
                continue
            if any(entry.stem.endswith(s) for s in self.IGNORED_FILE_STEM_SUFFIXES):
                continue
            # Ignorar vendor libs JS por nombre (jquery-x.x.x.js, prototype-x.js, etc.)
            name_lower = entry.name.lower()
            if any(pat in name_lower for pat in self.IGNORED_FILE_PATTERNS):
                continue
            # Ignorar minificados JS (.min.js)
            if name_lower.endswith('.min.js'):
                continue
            if entry.suffix.lower() in self.IGNORED_EXTENSIONS:
                continue
            try:
                if entry.stat().st_size > max_size:
                    continue
            except OSError:
                continue
            if self.analyzer_factory.get_analyzer(entry):
                files.append(entry)
    
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
