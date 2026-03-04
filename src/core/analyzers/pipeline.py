"""Orquesta el pipeline: FileAnalysis → code.archivos_fuente + code.unidades_logicas + quality.escaneos."""
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from src.core.analyzers.project_analyzer import ProjectAnalyzerService
from src.core.analyzers import logical_unit_extractor
from src.core.enricher.llm_enricher import enrich_archivo, enrich_microservicio
from src.db import repository
from src.models.domain import UnidadLogica, Escaneo, RiskLevel
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _build_escaneo(activo_id: str, aplicacion_id: str | None, project, all_scores: list, all_risk_counts: dict, negocio: dict = None) -> Escaneo:
    avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else None
    nivel = "HIGH" if all_risk_counts.get("HIGH", 0) > 0 else ("MEDIUM" if all_risk_counts.get("MEDIUM", 0) > 0 else "LOW")
    return Escaneo(
        activo_id=activo_id,
        aplicacion_id=aplicacion_id,
        commit_hash=project.commit_hash,
        score_general=avg_score,
        nivel_riesgo=RiskLevel(nivel),
        archivos_total=project.total_files,
        metricas={
            "total_lines": project.total_lines,
            "languages": project.languages,
            "funciones_por_riesgo": all_risk_counts,
        },
        negocio=negocio or {},
    )


async def run(
    project_path: Path,
    activo_id: str,
    microservice_name: str,
    session: Session,
    aplicacion_id: str | None = None,
    llm_client=None,
    max_files: int | None = None,
    verbose: bool = False,
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
    if llm_client and max_files and len(files) > max_files:
        files = sorted(files, key=lambda f: f.complexity_score if hasattr(f, 'complexity_score') else 0, reverse=True)[:max_files]
        logger.info("max_files_applied", total=len(project.files), enriching=max_files)
        print(f"  ⚠️  max-files={max_files}: enriqueciendo los {max_files} archivos más complejos de {len(project.files)}")

    total = len(project.files)

    all_logicas: List[UnidadLogica] = []
    all_reglas = []
    all_owasp = []
    inventario_funciones = []
    all_scores: List[float] = []
    all_risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    enrich_set = {f.file_path for f in files} if (llm_client and max_files) else None

    for idx, file_analysis in enumerate(project.files, 1):
        archivo, logicas, scoring = logical_unit_extractor.extract(file_analysis, activo_id, aplicacion_id)
        print(f"  [{idx}/{total}] {archivo.nombre} ... ", end="", flush=True)
        saved_archivo = repository.insert_archivo(session, archivo)

        for u in logicas:
            u.archivo_id = saved_archivo.id

        saved_logicas = repository.insert_unidades(session, logicas)
        all_logicas.extend(saved_logicas)
        all_scores.extend(scoring["scores"])
        for k, v in scoring["risk_counts"].items():
            all_risk_counts[k] = all_risk_counts.get(k, 0) + v

        in_enrich = enrich_set is None or file_analysis.file_path in enrich_set
        if llm_client and saved_logicas and in_enrich:
            try:
                source = Path(file_analysis.file_path).read_text(encoding="utf-8", errors="ignore")
                unidades_input = [{"nombre": u.nombre, "tipo": u.tipo} for u in saved_logicas]
                result = enrich_archivo(llm_client, archivo.nombre, archivo.capa or "", unidades_input, source)

                resumen_map = {u["nombre"]: u["resumen"] for u in result.get("unidades", []) if "nombre" in u and "resumen" in u}
                for u in saved_logicas:
                    if u.nombre in resumen_map:
                        repository.update_resumen_unidad(session, u.id, resumen_map[u.nombre])

                for u in result.get("unidades", []):
                    if u.get("reglas_negocio"):
                        all_reglas.append({"archivo": archivo.nombre, "funcion": u["nombre"], "reglas": u["reglas_negocio"]})
                    if u.get("owasp"):
                        all_owasp.append({"archivo": archivo.nombre, "funcion": u["nombre"], "owasp": u["owasp"]})

                resumen_archivo = result.get("resumen_archivo", "")
                if resumen_archivo:
                    inventario_funciones.append(resumen_archivo)

                if verbose:
                    import json
                    print(f"\n    {json.dumps(result, ensure_ascii=False, indent=2)}")
                print("ok")
            except Exception as e:
                logger.warning("enrichment_skipped", file=file_analysis.file_path, error=str(e))
                print("skipped")
        else:
            print("skip" if llm_client else "ok")

    session.commit()

    # Resumen ejecutivo del microservicio completo
    negocio = {}
    if llm_client and inventario_funciones:
        print(f"  [resumen] generando resumen ejecutivo de '{microservice_name}' ... ", end="", flush=True)
        try:
            negocio = enrich_microservicio(llm_client, microservice_name, inventario_funciones)
            if all_reglas:
                negocio["reglas"] = all_reglas
            if all_owasp:
                negocio["owasp"] = all_owasp
            if verbose:
                import json
                print(f"\n  [resumen ejecutivo]\n  {json.dumps(negocio, ensure_ascii=False, indent=2)}")
            print("ok")
        except Exception as e:
            logger.warning("resumen_microservicio_skipped", error=str(e))
            print("skipped")

    funciones = [u for u in all_logicas if u.tipo == "FUNCION"]
    clases = [u for u in all_logicas if u.tipo == "CLASE"]
    escaneo = _build_escaneo(activo_id, aplicacion_id, project, all_scores, all_risk_counts, negocio)
    escaneo.funciones_total = len(funciones)
    escaneo.clases_total = len(clases)
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
        "enriquecido": llm_client is not None,
    }
