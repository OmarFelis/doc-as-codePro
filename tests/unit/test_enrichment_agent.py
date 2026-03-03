"""Tests Fase 2 — enrichment_agent (Strands + Bedrock)."""
import src  # activa el fix de AWS_CONFIG_FILE antes de boto3
import pytest
from unittest.mock import MagicMock, patch


def test_build_enrichment_agent_retorna_agent():
    """El agente se instancia correctamente con credenciales SSO."""
    from src.core.enricher.enrichment_agent import build_enrichment_agent
    agent = build_enrichment_agent()
    assert agent is not None, "build_enrichment_agent retornó None — verificar credenciales SSO"
    assert type(agent).__name__ == "Agent"


def test_fallback_graceful_si_bedrock_no_disponible():
    """Si las credenciales fallan, retorna None sin lanzar excepción."""
    from src.core.enricher.enrichment_agent import build_enrichment_agent
    with patch("boto3.Session") as mock_session:
        mock_session.return_value.get_credentials.return_value = None
        # Forzar que BedrockModel lance excepción
        with patch("strands.models.BedrockModel", side_effect=Exception("no credentials")):
            agent = build_enrichment_agent()
    assert agent is None


def test_parse_enrichment_result_json_valido():
    """parse_enrichment_result extrae dict de un resultado JSON."""
    from src.core.enricher.enrichment_agent import parse_enrichment_result
    result = parse_enrichment_result('{"summary": "Adaptador de pagos", "purpose": "mapeo"}')
    assert result["summary"] == "Adaptador de pagos"


def test_parse_enrichment_result_json_invalido_retorna_vacio():
    """parse_enrichment_result retorna {} si el resultado no es JSON válido."""
    from src.core.enricher.enrichment_agent import parse_enrichment_result
    result = parse_enrichment_result("texto libre sin json")
    assert result == {}


@pytest.mark.integration
def test_agent_llama_bedrock_real():
    """Llamada real a Bedrock via Strands — requiere SSO activo."""
    from src.core.enricher.enrichment_agent import build_enrichment_agent
    agent = build_enrichment_agent()
    assert agent is not None, "Credenciales SSO no disponibles"
    result = agent("Responde solo: OK")
    assert "OK" in str(result)
