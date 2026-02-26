"""Paso 1 — Smoke tests: verifica que los módulos corregidos importan sin errores."""
import pytest


def test_api_app_imports():
    from src.api.main import app
    assert app is not None


def test_bedrock_client_imports():
    from src.core.llm.bedrock_client import BedrockClient
    assert BedrockClient is not None


def test_openai_client_imports():
    from src.core.llm.openai_client import OpenAIClient
    assert OpenAIClient is not None


def test_bedrock_uses_correct_field_names():
    """Verifica que BedrockClient usa aws_access_key_id (no access_key_id)."""
    import inspect
    from src.core.llm import bedrock_client
    source = inspect.getsource(bedrock_client)
    assert "aws_access_key_id" in source
    assert "aws_secret_access_key" in source
    assert "settings.bedrock.access_key_id" not in source
    assert "settings.bedrock.secret_access_key" not in source


def test_main_uses_lifespan():
    """Verifica que main.py usa lifespan y no on_event deprecado."""
    import inspect
    from src.api import main
    source = inspect.getsource(main)
    assert "lifespan" in source
    assert "on_event" not in source


def test_openai_client_uses_env_var():
    """Verifica que OpenAIClient usa os.environ y no settings.openai."""
    import inspect
    from src.core.llm import openai_client
    source = inspect.getsource(openai_client)
    assert "OPENAI_API_KEY" in source
    assert "settings.openai" not in source
