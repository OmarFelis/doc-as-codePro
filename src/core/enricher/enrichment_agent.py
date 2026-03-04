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
            """OBLIGATORIO llamar para analizar un archivo.
            Analiza el código y retorna SOLO JSON sin texto adicional:
            [{"nombre": "NombreFuncion", "resumen": "descripcion en español"}]
            NO generes código. NO expliques. SOLO el JSON.
            """
            return json.dumps([])

        @tool
        def extraer_reglas_negocio(source_code: str) -> str:
            """Extrae reglas de negocio del código.
            Retorna SOLO JSON sin texto adicional:
            [{"descripcion": str, "funcion_origen": str, "tipo": str}]
            NO generes código. NO expliques. SOLO el JSON.
            """
            return json.dumps([])

        @tool
        def analizar_owasp(source_code: str) -> str:
            """Detecta vulnerabilidades OWASP Top 10.
            Retorna SOLO JSON sin texto adicional:
            [{"categoria": str, "descripcion": str, "linea": int}]
            NO generes código. NO expliques. SOLO el JSON.
            """
            return json.dumps([])

        @tool
        def generar_resumen_microservicio(inventario_funciones: str) -> str:
            """Genera resumen ejecutivo del microservicio.
            Retorna SOLO JSON sin texto adicional:
            {"summary": str, "purpose": str, "data_sensitivity": str}
            NO generes código. NO expliques. SOLO el JSON.
            """
            return json.dumps({"summary": "", "purpose": "", "data_sensitivity": "unknown"})

        model = BedrockModel(
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            boto_session=session,
        )

        return Agent(
            model=model,
            tools=[enriquecer_unidades, extraer_reglas_negocio, analizar_owasp, generar_resumen_microservicio],
            system_prompt=(
                "Eres un analizador estático de código. "
                "REGLAS ESTRICTAS: "
                "1. SIEMPRE usa las tools disponibles — nunca respondas en texto libre. "
                "2. NUNCA generes código fuente, ejemplos ni implementaciones. "
                "3. NUNCA uses bloques markdown ni backticks. "
                "4. Tu única salida válida es invocar una tool. "
                "5. Responde en español dentro de los campos JSON."
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
