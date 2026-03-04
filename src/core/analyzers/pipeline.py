"""Orquesta el pipeline: FileAnalysis → code.archivos_fuente + code.unidades_logicas + quality.escaneos."""
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from src.core.analyzers.project_analyzer import ProjectAnalyzerService
from src.core.analyzers import logical_unit_extractor
from src.db import repository
from src.models.domain import UnidadLogica, Escaneo, RiskLevel
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _build_escaneo(activo_id: str, project, all_logicas: List[UnidadLogica], negocio: dict = None) -> Escaneo:
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
        negocio=negocio or {},
    )


async def run(
    project_path: Path,
    activo_id: str,
    microservice_name: str,
    session: Session,
    enrichment_agent=None,
    max_files: Optional[int] = None,
) -> dict:
    """
    Pipeline completo:
    1. Analiza archivos del proyecto
    2. Por archivo: insert_archivo → insert_unidades
    3. Enriquece con Strands Agent (resumen + reglas de negocio + OWASP) si disponible
    4. Persiste quality.escaneos con score agregado y resumen ejecutivo
    """
    project = ProjectAnalyzerService().analyze_project(project_path, microservice_name)

    files = project.files
    if enrichment_agent and max_files and len(files) > max_files:
        files = sorted(files, key=lambda f: f.complexity_score if hasattr(f, 'complexity_score') else 0, reverse=True)[:max_files]
        logger.info("max_files_applied", total=len(project.files), enriching=max_files)
        print(f"  ⚠️  max-files={max_files}: enriqueciendo los {max_files} archivos más complejos de {len(project.files)}")

    total = len(project.files)

    all_logicas: List[UnidadLogica] = []
    all_reglas = []
    all_owasp = []
    inventario_funciones = []

    enrich_set = {f.file_path for f in files} if (enrichment_agent and max_files) else None

    for idx, file_analysis in enumerate(project.files, 1):
        archivo, logicas = logical_unit_extractor.extract(file_analysis, activo_id)
        print(f"  [{idx}/{total}] {archivo.nombre} ... ", end="", flush=True)
        saved_archivo = repository.insert_archivo(session, archivo)

        for u in logicas:
            u.archivo_id = saved_archivo.id

        saved_logicas = repository.insert_unidades(session, logicas)
        all_logicas.extend(saved_logicas)

        in_enrich = enrich_set is None or file_analysis.file_path in enrich_set
        if enrichment_agent and saved_logicas and in_enrich:
            try:
                source = Path(file_analysis.file_path).read_text(encoding="utf-8", errors="ignore")
                capa = archivo.capa or ""
                nombres = [u.nombre for u in saved_logicas]
                inventario_funciones.extend(nombres)

                prompt = (
                    f"Archivo: {archivo.nombre}\n"
                    f"Capa: {capa}\n"
                    f"Unidades: {nombres}\n"
                    f"Código:\n{source[:3000]}"
                )
                result = enrichment_agent(prompt)
                result_text = str(result)

                # Actualizar resúmenes en unidades persistidas
                from src.core.enricher.enrichment_agent import parse_enrichment_result
                parsed = parse_enrichment_result(result_text)
                if isinstance(parsed, list):
                    resumen_map = {r["nombre"]: r["resumen"] for r in parsed if "nombre" in r and "resumen" in r}
                    for u in saved_logicas:
                        if u.nombre in resumen_map:
                            repository.update_resumen_unidad(session, u.id, resumen_map[u.nombre])

                # Acumular reglas y OWASP del resultado
                if "reglas" in result_text:
                    all_reglas.append({"archivo": archivo.nombre, "resultado": result_text})
                if "owasp" in result_text.lower() or "A0" in result_text:
                    all_owasp.append({"archivo": archivo.nombre, "resultado": result_text})

            except Exception as e:
                logger.warning("enrichment_skipped", file=file_analysis.file_path, error=str(e))
                print("skipped")
        else:
            print("skip" if enrichment_agent else "ok")

    session.commit()

    # Resumen ejecutivo del microservicio completo
    negocio = {}
    if enrichment_agent and inventario_funciones:
        print(f"  [resumen] generando resumen ejecutivo de '{microservice_name}' ... ", end="", flush=True)
        try:
            resumen_result = enrichment_agent(
                f"Genera el resumen ejecutivo del microservicio '{microservice_name}' "
                f"con estas funciones: {inventario_funciones[:50]}"
            )
            from src.core.enricher.enrichment_agent import parse_enrichment_result
            negocio = parse_enrichment_result(str(resumen_result))
            if all_reglas:
                negocio["reglas"] = all_reglas
            if all_owasp:
                negocio["owasp"] = all_owasp
            print("ok")
        except Exception as e:
            logger.warning("resumen_microservicio_skipped", error=str(e))
            print("skipped")

    escaneo = _build_escaneo(activo_id, project, all_logicas, negocio)
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
        "enriquecido": enrichment_agent is not None,
    }
