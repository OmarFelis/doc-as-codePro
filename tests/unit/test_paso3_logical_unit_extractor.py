"""Paso 3 — Tests del LogicalUnitExtractor."""
import pytest
from src.models.domain import FileAnalysis, LanguageType, EntityType, RiskLevel
from src.core.analyzers.logical_unit_extractor import extract, _classify_layer, _has_multi_layer_coupling


def _make_analysis(**kwargs) -> FileAnalysis:
    defaults = dict(
        file_path="payments.py",
        language=LanguageType.PYTHON,
        lines=50,
        functions=["calcular_comision", "validar_monto"],
        imports=[],
        database_calls=[],
        complexity=5,
        classes=[],
    )
    defaults.update(kwargs)
    return FileAnalysis(**defaults)


# --- Clasificación de capas ---

def test_layer_adaptador():
    assert _classify_layer(["fastapi", "pydantic"]).value == "adaptador"


def test_layer_infraestructura_boto3():
    assert _classify_layer(["boto3", "json"]).value == "infraestructura"


def test_layer_infraestructura_sqlalchemy():
    assert _classify_layer(["sqlalchemy.orm", "os"]).value == "infraestructura"


def test_layer_dominio_sin_imports():
    assert _classify_layer([]).value == "dominio"


def test_layer_dominio_imports_puros():
    assert _classify_layer(["datetime", "decimal", "typing"]).value == "dominio"


# --- Multi-layer coupling ---

def test_multi_layer_coupling_detectado():
    assert _has_multi_layer_coupling(["fastapi", "boto3"]) is True


def test_multi_layer_coupling_no_detectado():
    assert _has_multi_layer_coupling(["fastapi"]) is False
    assert _has_multi_layer_coupling(["boto3"]) is False
    assert _has_multi_layer_coupling([]) is False


# --- Producción de QualityAudit ---

def test_extract_produce_un_audit_por_funcion():
    fa = _make_analysis(functions=["f1", "f2", "f3", "f4", "f5"])
    audits = extract(fa)
    assert len(audits) == 5


def test_extract_entity_type_es_logic_unit():
    audits = extract(_make_analysis())
    assert all(a.entity_type == "LOGIC_UNIT" for a in audits)


def test_extract_risk_low_complejidad_baja():
    audits = extract(_make_analysis(complexity=5))
    assert all(a.risk_level == "LOW" for a in audits)


def test_extract_risk_medium():
    audits = extract(_make_analysis(complexity=12))
    assert all(a.risk_level == "MEDIUM" for a in audits)


def test_extract_risk_high_complejidad_alta():
    audits = extract(_make_analysis(complexity=16))
    assert all(a.risk_level == "HIGH" for a in audits)


def test_extract_overall_score_calculado():
    audits = extract(_make_analysis())
    assert all(a.overall_score is not None for a in audits)
    assert all(0 <= a.overall_score <= 100 for a in audits)


def test_extract_metrics_poblados():
    audits = extract(_make_analysis(imports=["boto3"]))
    m = audits[0].metrics
    assert "lines_of_code" in m
    assert "cyclomatic_complexity" in m
    assert "aws_services" in m
    assert "S3" not in m["aws_services"]  # boto3 genérico → "AWS"
    assert "AWS" in m["aws_services"]


def test_extract_compliance_multi_layer():
    audits = extract(_make_analysis(imports=["fastapi", "boto3"]))
    assert audits[0].compliance["has_multi_layer_coupling"] is True


def test_extract_compliance_sin_multi_layer():
    audits = extract(_make_analysis(imports=["datetime"]))
    assert audits[0].compliance["has_multi_layer_coupling"] is False


def test_extract_parent_id_propagado():
    audits = extract(_make_analysis(), parent_id="uuid-acs-123")
    assert all(a.parent_id == "uuid-acs-123" for a in audits)


def test_extract_archivo_sin_funciones_retorna_vacio():
    audits = extract(_make_analysis(functions=[]))
    assert audits == []
