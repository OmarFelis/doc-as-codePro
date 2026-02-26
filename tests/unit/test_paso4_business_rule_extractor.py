"""Paso 4 — Tests del BusinessRuleExtractor con mock del LLM."""
import json
import pytest
from unittest.mock import AsyncMock
from src.models.domain import QualityAudit, EntityType, RiskLevel
from src.core.analyzers.business_rule_extractor import extract, _is_dominio

_DOMINIO_AUDIT = QualityAudit(
    entity_name="calcular_comision",
    entity_type=EntityType.LOGIC_UNIT,
    language="python",
    risk_level=RiskLevel.LOW,
    metrics={"architecture_layer": "dominio"},
)

_INFRA_AUDIT = QualityAudit(
    entity_name="guardar_en_db",
    entity_type=EntityType.LOGIC_UNIT,
    language="python",
    risk_level=RiskLevel.MEDIUM,
    metrics={"architecture_layer": "infraestructura"},
)

_ADAPTADOR_AUDIT = QualityAudit(
    entity_name="handle_request",
    entity_type=EntityType.LOGIC_UNIT,
    language="python",
    risk_level=RiskLevel.LOW,
    metrics={"architecture_layer": "adaptador"},
)

_LLM_RESPONSE = json.dumps([
    {"description": "Valida que el monto sea mayor a cero", "condition": "monto <= 0", "result": "lanza ValueError"},
    {"description": "Aplica tasa del 3.5% para pagos con tarjeta de crédito", "condition": "tipo == 'credito'", "result": "retorna monto * 0.035"},
])

_SOURCE = "def calcular_comision(monto, tipo):\n    if monto <= 0: raise ValueError\n    return monto * 0.035 if tipo == 'credito' else monto * 0.015"


def _mock_llm(response: str = _LLM_RESPONSE):
    m = AsyncMock()
    m.generate_text = AsyncMock(return_value=response)
    return m


# --- _is_dominio ---

def test_is_dominio_true():
    assert _is_dominio(_DOMINIO_AUDIT) is True

def test_is_dominio_false_infra():
    assert _is_dominio(_INFRA_AUDIT) is False

def test_is_dominio_false_adaptador():
    assert _is_dominio(_ADAPTADOR_AUDIT) is False


# --- extract ---

@pytest.mark.asyncio
async def test_extract_retorna_reglas_para_dominio():
    rules = await extract([_DOMINIO_AUDIT], _SOURCE, "ACS", "payments.py", _mock_llm())
    assert len(rules) == 2
    assert rules[0].linked_application == "ACS"
    assert rules[0].linked_component == "payments.py"
    assert rules[0].linked_unit_name == "calcular_comision"
    assert "monto" in rules[0].description


@pytest.mark.asyncio
async def test_extract_vacio_si_no_hay_dominio():
    rules = await extract([_INFRA_AUDIT, _ADAPTADOR_AUDIT], _SOURCE, "ACS", "payments.py", _mock_llm())
    assert rules == []


@pytest.mark.asyncio
async def test_extract_trazabilidad_completa():
    rules = await extract([_DOMINIO_AUDIT], _SOURCE, "ACS", "payments.py", _mock_llm())
    for rule in rules:
        assert rule.linked_application
        assert rule.linked_component
        assert rule.linked_unit_name
        assert rule.description


@pytest.mark.asyncio
async def test_extract_maneja_json_malformado():
    rules = await extract([_DOMINIO_AUDIT], _SOURCE, "ACS", "payments.py", _mock_llm("no es json"))
    assert rules == []


@pytest.mark.asyncio
async def test_extract_maneja_llm_exception():
    llm = AsyncMock()
    llm.generate_text = AsyncMock(side_effect=RuntimeError("Bedrock unavailable"))
    rules = await extract([_DOMINIO_AUDIT], _SOURCE, "ACS", "payments.py", llm)
    assert rules == []


@pytest.mark.asyncio
async def test_extract_multiples_unidades_dominio():
    segunda_unit = QualityAudit(
        entity_name="validar_monto",
        entity_type=EntityType.LOGIC_UNIT,
        language="python",
        risk_level=RiskLevel.LOW,
        metrics={"architecture_layer": "dominio"},
    )
    rules = await extract([_DOMINIO_AUDIT, segunda_unit], _SOURCE, "ACS", "payments.py", _mock_llm())
    unit_names = {r.linked_unit_name for r in rules}
    assert "calcular_comision" in unit_names
    assert "validar_monto" in unit_names
