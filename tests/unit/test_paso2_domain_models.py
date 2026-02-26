"""Paso 2 — Tests de modelos de dominio nuevos (QualityAudit, BusinessRule, enums)."""
import pytest
from src.models.domain import (
    EntityType, RiskLevel, ArchitectureLayer, LogicalUnitType,
    QualityAudit, BusinessRule,
)


def test_entity_type_values():
    assert EntityType.MICROSERVICE == "MICROSERVICE"
    assert EntityType.LOGIC_UNIT == "LOGIC_UNIT"


def test_risk_level_values():
    assert RiskLevel.LOW == "LOW"
    assert RiskLevel.MEDIUM == "MEDIUM"
    assert RiskLevel.HIGH == "HIGH"


def test_architecture_layer_values():
    assert ArchitectureLayer.ADAPTADOR == "adaptador"
    assert ArchitectureLayer.DOMINIO == "dominio"
    assert ArchitectureLayer.INFRAESTRUCTURA == "infraestructura"


def test_logical_unit_type_values():
    assert LogicalUnitType.FUNCION == "UNIDAD_LOGICA_FUNCION"
    assert LogicalUnitType.REGLA_NEGOCIO == "UNIDAD_LOGICA_REGLA_NEGOCIO"


def test_quality_audit_minimal():
    audit = QualityAudit(entity_name="ACS", entity_type=EntityType.MICROSERVICE)
    assert audit.entity_name == "ACS"
    assert audit.risk_level == "MEDIUM"
    assert audit.id is None
    assert audit.parent_id is None
    assert audit.metrics == {}
    assert audit.compliance == {}


def test_quality_audit_logic_unit():
    audit = QualityAudit(
        entity_name="calcular_iva",
        entity_type=EntityType.LOGIC_UNIT,
        parent_id="some-uuid",
        language="python",
        risk_level=RiskLevel.HIGH,
        overall_score=42.5,
        metrics={"lines_of_code": 45, "cyclomatic_complexity": 16},
        compliance={"has_multi_layer_coupling": True},
    )
    assert audit.entity_type == "LOGIC_UNIT"
    assert audit.risk_level == "HIGH"
    assert audit.overall_score == 42.5
    assert audit.metrics["cyclomatic_complexity"] == 16
    assert audit.compliance["has_multi_layer_coupling"] is True


def test_business_rule_fields():
    rule = BusinessRule(
        description="Valida que el monto sea mayor a cero antes de procesar el pago",
        linked_application="ACS",
        linked_component="payments.py",
        linked_unit_name="procesar_pago",
    )
    assert rule.linked_application == "ACS"
    assert rule.linked_unit_name == "procesar_pago"
    assert "monto" in rule.description
