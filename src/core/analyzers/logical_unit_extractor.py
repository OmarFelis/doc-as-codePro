"""Extrae ArchivoFuente y UnidadLogica con jerarquía clase→función desde FileAnalysis."""
import uuid as _uuid
from pathlib import Path
from typing import List, Tuple
from src.models.domain import (
    FileAnalysis, ArchivoFuente, UnidadLogica,
    TipoUnidad, RiskLevel, ArchitectureLayer,
)

_ADAPTADOR_PATTERNS = {
    "fastapi", "flask", "handler", "router", "controller", "starlette", "django",
    "org.springframework.web", "org.springframework.stereotype",
    "javax.ws.rs", "jakarta.ws.rs",
    "org.apache.struts", "org.apache.struts2",
    "javax.servlet", "jakarta.servlet",
}
_INFRA_PATTERNS = {
    "boto3", "dynamodb", "s3", "sqs", "sns", "psycopg2", "sqlalchemy", "pymongo", "redis", "rds",
    "org.springframework.data", "javax.persistence", "jakarta.persistence",
    "com.amazonaws", "software.amazon",
    "org.hibernate", "java.sql", "javax.sql",
}
_AWS_SERVICES_MAP = {
    "s3": "S3", "sqs": "SQS", "sns": "SNS", "dynamodb": "DynamoDB",
    "rds": "RDS", "boto3": "AWS", "com.amazonaws": "AWS", "software.amazon": "AWS",
}


def _normalize_imports(imports: List[str]) -> set:
    tokens = set()
    for imp in imports:
        parts = imp.lower().split(".")
        tokens.add(parts[0])
        if len(parts) >= 2:
            tokens.add(".".join(parts[:2]))
        if len(parts) >= 3:
            tokens.add(".".join(parts[:3]))
    return tokens


def _classify_layer(imports: List[str]) -> ArchitectureLayer:
    normalized = _normalize_imports(imports)
    has_adaptador = bool(normalized & _ADAPTADOR_PATTERNS)
    has_infra = bool(normalized & _INFRA_PATTERNS)
    if has_adaptador and not has_infra:
        return ArchitectureLayer.ADAPTADOR
    if has_infra:
        return ArchitectureLayer.INFRAESTRUCTURA
    return ArchitectureLayer.DOMINIO


def _detect_aws_services(imports: List[str]) -> int:
    normalized = _normalize_imports(imports)
    return len([k for k in normalized if k in _AWS_SERVICES_MAP])


def _calc_atomicity(loc: int, complexity: int) -> float:
    score = 1.0
    if loc > 30:
        score -= 0.3
    if complexity > 10:
        score -= 0.3
    return max(0.0, round(score, 2))


def _calc_transparency(database_calls: List[str], imports: List[str]) -> float:
    score = 1.0
    if database_calls:
        score -= 0.4
    if _normalize_imports(imports) & _INFRA_PATTERNS:
        score -= 0.3
    return max(0.0, round(score, 2))


def _calc_overall(atomicity: float, transparency: float, complexity: int) -> float:
    complexity_score = 1.0 / max(complexity, 1)
    return round(((atomicity * 0.4) + (transparency * 0.4) + (complexity_score * 0.2)) * 100, 2)


def _calc_risk(complexity: int, score: float) -> RiskLevel:
    if complexity > 15 or score < 50:
        return RiskLevel.HIGH
    if complexity >= 10 or score < 70:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def extract(
    file_analysis: FileAnalysis,
    activo_id: str,
    aplicacion_id: str | None = None,
) -> Tuple[ArchivoFuente, List[UnidadLogica], dict]:
    """Produce ArchivoFuente + List[UnidadLogica] + scoring_summary para metricas del escaneo."""
    imports = file_analysis.imports
    layer = _classify_layer(imports)
    aws_count = _detect_aws_services(imports)
    accede_bd = bool(file_analysis.database_calls)

    archivo = ArchivoFuente(
        activo_id=activo_id,
        aplicacion_id=aplicacion_id,
        nombre=Path(file_analysis.file_path).name,
        ruta_archivo=file_analysis.file_path,
        capa=layer.value,
        lenguaje=file_analysis.language if isinstance(file_analysis.language, str) else file_analysis.language.value,
        total_funciones=len(file_analysis.functions),
        total_clases=len(file_analysis.classes),
        endpoints=len(file_analysis.endpoints),
        operaciones_bd=len(file_analysis.database_calls),
        llamadas_externas=aws_count,
        complejidad_ciclomatica=file_analysis.complexity,
        lineas_codigo=file_analysis.lines,
    )

    unidades: List[UnidadLogica] = []
    clase_ids: dict[str, str] = {}
    scores: List[float] = []

    # 1 — Clases
    for clase_nombre in file_analysis.classes:
        uid = str(_uuid.uuid4())
        clase_ids[clase_nombre] = uid
        loc = file_analysis.lines // max(len(file_analysis.classes), 1)
        score = _calc_overall(
            _calc_atomicity(loc, file_analysis.complexity),
            _calc_transparency(file_analysis.database_calls, imports),
            file_analysis.complexity,
        )
        scores.append(score)
        unidades.append(UnidadLogica(
            id=uid,
            activo_id=activo_id,
            aplicacion_id=aplicacion_id,
            nombre=clase_nombre,
            tipo=TipoUnidad.CLASE,
            capa=layer.value,
            complejidad=file_analysis.complexity,
            lineas_codigo=loc,
            accede_bd=accede_bd,
            llamadas_externas=aws_count,
            metadata={"risk_level": _calc_risk(file_analysis.complexity, score).value, "overall_score": score},
        ))

    # 2 — Funciones
    func_count = max(len(file_analysis.functions), 1)
    loc_per_func = max(file_analysis.lines // func_count, 1)

    for func_name in file_analysis.functions:
        parent_id = None
        nombre = func_name
        if "." in func_name:
            clase_nombre, nombre = func_name.split(".", 1)
            parent_id = clase_ids.get(clase_nombre)

        func_complexity = file_analysis.func_complexity.get(func_name, file_analysis.complexity)
        score = _calc_overall(
            _calc_atomicity(loc_per_func, func_complexity),
            _calc_transparency(file_analysis.database_calls, imports),
            func_complexity,
        )
        scores.append(score)
        unidades.append(UnidadLogica(
            activo_id=activo_id,
            aplicacion_id=aplicacion_id,
            nombre=nombre,
            tipo=TipoUnidad.FUNCION,
            capa=layer.value,
            parent_id=parent_id,
            complejidad=func_complexity,
            lineas_codigo=loc_per_func,
            accede_bd=accede_bd,
            llamadas_externas=aws_count,
            metadata={
                "risk_level": _calc_risk(func_complexity, score).value,
                "overall_score": score,
                "loc_ok": loc_per_func <= 30,
                "complexity_ok": func_complexity <= 10,
            },
        ))

    # 3 — Scoring summary para metricas del escaneo
    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for u in unidades:
        rl = u.metadata.get("risk_level", "MEDIUM")
        risk_counts[rl] = risk_counts.get(rl, 0) + 1

    scoring_summary = {
        "scores": scores,
        "risk_counts": risk_counts,
    }

    return archivo, unidades, scoring_summary
