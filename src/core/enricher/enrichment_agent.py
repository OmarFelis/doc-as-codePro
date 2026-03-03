"""Agente Strands para enriquecimiento LLM — Fase 2.

Herramientas:
  - enriquecer_unidades: resúmenes por función/clase de capa DOMINIO
  - extraer_reglas_negocio: reglas de negocio con trazabilidad a función origen
  - analizar_owasp: patrones OWASP en capa INFRAESTRUCTURA
  - generar_resumen_microservicio: resumen ejecutivo del microservicio
"""
import json
import os

def build_enrichment_agent():
    """Instancia el agente Strands con BedrockModel via SSO.
    Retorna None si las credenciales no están disponibles (fallback graceful).
    """
    try:
        import boto3
        from strands import Agent, tool
        from strands.models import BedrockModel

        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        if session.get_credentials() is None:
            return None

        @tool
        def enriquecer_unidades(archivo_id: str, source_code: str) -> str:
            """Genera resúmenes en español para cada función/clase de capa DOMINIO.
            Retorna JSON: [{"nombre": str, "resumen": str}]
            """
            ...

        @tool
        def extraer_reglas_negocio(source_code: str) -> str:
            """Extrae reglas de negocio: validaciones, cálculos, flujos de pago.
            Retorna JSON: [{"descripcion": str, "funcion_origen": str, "tipo": str}]
            """
            ...

        @tool
        def analizar_owasp(source_code: str) -> str:
            """Detecta patrones OWASP Top 10 en código de capa INFRAESTRUCTURA.
            Retorna JSON: [{"categoria": str, "descripcion": str, "linea": int}]
            """
            ...

        @tool
        def generar_resumen_microservicio(inventario_funciones: str) -> str:
            """Genera resumen ejecutivo del microservicio completo.
            Retorna JSON: {"summary": str, "purpose": str, "data_sensitivity": str}
            """
            ...

        model = BedrockModel(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            boto_session=session,
        )

        return Agent(
            model=model,
            tools=[enriquecer_unidades, extraer_reglas_negocio, analizar_owasp, generar_resumen_microservicio],
            system_prompt=(
                "Eres un analista técnico de software de pagos digitales. "
                "Respondes siempre en español. Produces JSON válido sin markdown ni bloques de código."
            ),
        )

    except Exception:
        return None


def parse_enrichment_result(result) -> dict:
    """Extrae el JSON del resultado del agente Strands."""
    text = str(result)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}
