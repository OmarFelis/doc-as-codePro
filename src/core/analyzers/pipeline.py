"""Orquesta el pipeline completo: FileAnalysis → QualityAudit → Postgres."""
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session

from src.core.analyzers.project_analyzer import ProjectAnalyzerService
from src.core.analyzers import logical_unit_extractor, business_rule_extractor
from src.db import repository
from src.models.domain import QualityAudit, BusinessRule, EntityType, RiskLevel
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def run(
    project_path: Path,
    microservice_name: str,
    session: Session,
    llm_client=None,
) -> dict:
    """
    Pipeline completo:
    1. Analiza archivos del proyecto
    2. Extrae unidades lógicas (QualityAudit LOGIC_UNIT)
    3. Extrae reglas de negocio con LLM (solo capa DOMINIO)
    4. Persiste todo en quality_audits
    Retorna quality_summary.
    """
    # 1 — Análisis de archivos
    analyzer = ProjectAnalyzerService()
    project = analyzer.analyze_project(project_path, microservice_name)

    # 2 — Upsert del microservicio padre
    parent_audit = repository.upsert(session, QualityAudit(
        entity_name=microservice_name,
        entity_type=EntityType.MICROSERVICE,
        language=project.languages[0] if project.languages else None,
        metrics={
            "total_files": project.total_files,
            "total_lines": project.total_lines,
            "languages": project.languages,
        },
    ))
    session.commit()

    # 3 — Extraer y persistir unidades lógicas por archivo
    all_units: List[QualityAudit] = []
    all_rules: List[BusinessRule] = []

    for file_analysis in project.files:
        units = logical_unit_extractor.extract(file_analysis, parent_id=parent_audit.id)
        if not units:
            continue

        saved_units = repository.upsert_all(session, units)
        all_units.extend(saved_units)

        # 4 — Extraer reglas de negocio si hay LLM disponible
        if llm_client:
            try:
                source = Path(file_analysis.file_path).read_text(encoding="utf-8", errors="ignore")
                rules = await business_rule_extractor.extract(
                    audits=saved_units,
                    source_code=source,
                    linked_application=microservice_name,
                    linked_component=file_analysis.file_path,
                    llm_client=llm_client,
                )
                all_rules.extend(rules)
            except Exception as e:
                logger.warning("business_rule_extraction_skipped", file=file_analysis.file_path, error=str(e))

    session.commit()

    # 5 — Calcular quality_summary
    high_count = sum(1 for u in all_units if u.risk_level == "HIGH")
    scores = [u.overall_score for u in all_units if u.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    overall_risk = "HIGH" if high_count > 0 else ("MEDIUM" if any(u.risk_level == "MEDIUM" for u in all_units) else "LOW")

    return {
        "microservice_id": parent_audit.id,
        "microservice_name": microservice_name,
        "overall_score": avg_score,
        "risk_level": overall_risk,
        "units_count": len(all_units),
        "business_rules_count": len(all_rules),
        "high_risk_units": high_count,
    }
