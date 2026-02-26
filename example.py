"""Script de ejemplo para probar el nuevo sistema de análisis."""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.analyzers.project_analyzer import ProjectAnalyzerService
from src.utils.logging import setup_logging, get_logger
from src.config.settings import get_settings

# Configurar logging
setup_logging(debug=True)
logger = get_logger(__name__)


def main():
    """Función principal de ejemplo."""
    logger.info("starting_example", message="Iniciando análisis de ejemplo")
    
    # Obtener configuración
    settings = get_settings()
    logger.info("settings_loaded", environment=settings.environment)
    
    # Crear servicio de análisis
    analyzer = ProjectAnalyzerService()
    
    # Analizar el proyecto actual (solo archivos Python por ahora)
    project_path = Path(".")
    
    logger.info("analyzing_project", path=str(project_path))
    
    try:
        analysis = analyzer.analyze_project(
            project_path=project_path,
            repository_name="doc-as-code-service",
            repository_owner="alignet"
        )
        
        # Mostrar resultados
        logger.info(
            "analysis_completed",
            total_files=analysis.total_files,
            total_lines=analysis.total_lines,
            languages=analysis.languages,  # Ya son strings
            status=analysis.status  # Ya es string
        )
        
        # Mostrar componentes clasificados
        for component_type, files in analysis.components.items():
            if files:
                logger.info(
                    "component_classification",
                    component_type=component_type,  # Ya es string
                    file_count=len(files)
                )
        
        # Mostrar algunos archivos analizados
        logger.info("sample_files", message="Primeros 5 archivos analizados:")
        for file_analysis in analysis.files[:5]:
            logger.info(
                "file_details",
                file_path=file_analysis.file_path,
                language=file_analysis.language,  # Ya es string
                lines=file_analysis.lines,
                functions=len(file_analysis.functions),
                classes=len(file_analysis.classes)
            )
        
        logger.info("example_completed", message="✅ Ejemplo completado exitosamente")
        
    except Exception as e:
        logger.error("example_failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
