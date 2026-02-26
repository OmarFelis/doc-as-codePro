"""Extrae unidades lógicas de un FileAnalysis y produce QualityAudit por función."""
from typing import List
from src.models.domain import FileAnalysis, QualityAudit, EntityType, RiskLevel, ArchitectureLayer

_ADAPTADOR_PATTERNS = {"fastapi", "flask", "handler", "router", "controller", "starlette", "django"}
_INFRA_PATTERNS = {"boto3", "dynamodb", "s3", "sqs", "sns", "psycopg2", "sqlalchemy", "pymongo", "redis", "rds"}
_AWS_SERVICES_MAP = {"s3": "S3", "sqs": "SQS", "sns": "SNS", "dynamodb": "DynamoDB", "rds": "RDS", "boto3": "AWS"}


def _classify_layer(imports: List[str]) -> ArchitectureLayer:
    normalized = {imp.lower().split(".")[0] for imp in imports}
    has_adaptador = bool(normalized & _ADAPTADOR_PATTERNS)
    has_infra = bool(normalized & _INFRA_PATTERNS)
    if has_adaptador and not has_infra:
        return ArchitectureLayer.ADAPTADOR
    if has_infra:
        return ArchitectureLayer.INFRAESTRUCTURA
    return ArchitectureLayer.DOMINIO


def _has_multi_layer_coupling(imports: List[str]) -> bool:
    normalized = {imp.lower().split(".")[0] for imp in imports}
    return bool(normalized & _ADAPTADOR_PATTERNS) and bool(normalized & _INFRA_PATTERNS)


def _detect_aws_services(imports: List[str]) -> List[str]:
    normalized = {imp.lower().split(".")[0] for imp in imports}
    return [_AWS_SERVICES_MAP[k] for k in normalized if k in _AWS_SERVICES_MAP]


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
    normalized = {imp.lower().split(".")[0] for imp in imports}
    if normalized & _INFRA_PATTERNS:
        score -= 0.3
    return max(0.0, round(score, 2))


def _calc_overall(atomicity: float, transparency: float, complexity: int) -> float:
    complexity_score = 1.0 / max(complexity, 1)
    raw = (atomicity * 0.4) + (transparency * 0.4) + (complexity_score * 0.2)
    return round(raw * 100, 2)


def _calc_risk(complexity: int) -> RiskLevel:
    if complexity > 15:
        return RiskLevel.HIGH
    if complexity >= 10:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def extract(file_analysis: FileAnalysis, parent_id: str | None = None) -> List[QualityAudit]:
    """Produce un QualityAudit por función detectada en el FileAnalysis."""
    audits = []
    imports = file_analysis.imports
    layer = _classify_layer(imports)
    aws_services = _detect_aws_services(imports)
    multi_layer = _has_multi_layer_coupling(imports)

    # Distribuimos LOC equitativamente entre funciones como aproximación
    func_count = max(len(file_analysis.functions), 1)
    loc_per_func = max(file_analysis.lines // func_count, 1)

    for func_name in file_analysis.functions:
        complexity = file_analysis.complexity  # complejidad del archivo completo como proxy
        atomicity = _calc_atomicity(loc_per_func, complexity)
        transparency = _calc_transparency(file_analysis.database_calls, imports)
        overall = _calc_overall(atomicity, transparency, complexity)
        risk = _calc_risk(complexity)

        audits.append(QualityAudit(
            parent_id=parent_id,
            entity_name=func_name,
            entity_type=EntityType.LOGIC_UNIT,
            language=file_analysis.language,
            risk_level=risk,
            overall_score=overall,
            metrics={
                "lines_of_code": loc_per_func,
                "cyclomatic_complexity": complexity,
                "external_dependencies_count": len(aws_services),
                "aws_services": aws_services,
                "architecture_layer": layer.value,
            },
            compliance={
                "has_multi_layer_coupling": multi_layer,
                "loc_ok": loc_per_func <= 30,
                "complexity_ok": complexity <= 10,
            },
        ))

    return audits
