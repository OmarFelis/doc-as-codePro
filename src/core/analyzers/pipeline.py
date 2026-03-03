"""Orquesta el pipeline: FileAnalysis → code.archivos_fuente + code.unidades_logicas + quality.escaneos."""
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session

from src.core.analyzers.project_analyzer import ProjectAnalyzerService
from src.core.analyzers import logical_unit_extractor, business_rule_extractor
from src.db import repository
from src.models.domain import UnidadLogica, Escaneo, RiskLevel
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _build_escaneo(activo_id: str, project, all_logicas: List[UnidadLogica]) -> Escaneo:
    funciones = [u for u in all_logicas if u.tipo == "FUNCION"]
    clases = [u for u in all_logicas if u.tipo == "CLASE"]
    scores = [u.overall_score for u in all_logicas if u.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None
    high_count = sum(1 for u in all_logicas if u.risk_level == "HIGH")
    nivel = "HIGH" if high_count > 0 else ("MEDIUM" if any(u.risk_level == "MEDIUM" for u in all_logicas) else "LOW")

    return Escaneo(
        activo_id=activo_id,
        commit_hash=project.commit_hash,
        score_general=avg_score,
        nivel_riesgo=RiskLevel(nivel),
        archivos_total=project.total_files,
        funciones_total=len(funciones),
        clases_total=len(clases),
        metricas={
            "total_lines": project.total_lines,
            "languages": project.languages,
            "high_risk_count": high_count,
        },
    )


async def run(
    project_path: Path,
    activo_id: str,
    microservice_name: str,
    session: Session,
    llm_client=None,
) -> dict:
    """
    Pipeline completo:
    1. Analiza archivos del proyecto
    2. Por archivo: insert_archivo → insert_unidades
    3. Extrae reglas de negocio con LLM (capa DOMINIO, si llm_client disponible)
    4. Persiste quality.escaneos con score agregado
    """
    project = ProjectAnalyzerService().analyze_project(project_path, microservice_name)

    all_logicas: List[UnidadLogica] = []

    for file_analysis in project.files:
        archivo, logicas = logical_unit_extractor.extract(file_analysis, activo_id)
        saved_archivo = repository.insert_archivo(session, archivo)

        for u in logicas:
            u.archivo_id = saved_archivo.id

        saved_logicas = repository.insert_unidades(session, logicas)
        all_logicas.extend(saved_logicas)

        if llm_client:
            try:
                source = Path(file_analysis.file_path).read_text(encoding="utf-8", errors="ignore")
                await business_rule_extractor.extract(
                    unidades=saved_logicas,
                    source_code=source,
                    linked_application=microservice_name,
                    linked_component=file_analysis.file_path,
                    llm_client=llm_client,
                    lenguaje=archivo.lenguaje or "python",
                )
            except Exception as e:
                logger.warning("llm_enrichment_skipped", file=file_analysis.file_path, error=str(e))

    session.commit()

    escaneo = _build_escaneo(activo_id, project, all_logicas)
    saved_escaneo = repository.insert_escaneo(session, escaneo)
    session.commit()

    return {
        "escaneo_id": saved_escaneo.id,
        "activo_id": activo_id,
        "score_general": saved_escaneo.score_general,
        "nivel_riesgo": saved_escaneo.nivel_riesgo,
        "archivos_total": saved_escaneo.archivos_total,
        "clases_total": saved_escaneo.clases_total,
        "funciones_total": saved_escaneo.funciones_total,
    }
