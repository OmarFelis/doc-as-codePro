"""Enriquecimiento LLM via llamada directa a Bedrock — Fase 2.

Una llamada por archivo. Retorna JSON estructurado con:
  - resúmenes por unidad lógica
  - reglas de negocio
  - hallazgos OWASP
  - resumen del archivo
"""
import json
import os
import re

MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

SYSTEM_PROMPT = (
    "Eres un analizador estático de código de software de pagos digitales. "
    "Respondes ÚNICAMENTE con JSON válido, sin texto adicional, sin markdown, sin explicaciones."
)

PROMPT_TEMPLATE = """\
Analiza el siguiente archivo de código y responde SOLO con el JSON indicado, sin texto adicional.

Archivo: {archivo}
Capa: {capa}
Unidades detectadas: {unidades}

Código fuente:
{codigo}

Responde con este JSON exacto (sin markdown):
{{
  "unidades": [
    {{
      "nombre": "<nombre de la unidad>",
      "resumen": "<qué hace en 1-2 oraciones en español>",
      "reglas_negocio": ["<regla 1>", "<regla 2>"],
      "owasp": ["<categoria: descripcion>"]
    }}
  ],
  "resumen_archivo": "<propósito del archivo en 1 oración>"
}}
"""

RESUMEN_TEMPLATE = """\
Genera un resumen ejecutivo del microservicio '{nombre}' basado en estos resúmenes de archivos.
Responde SOLO con este JSON (sin markdown):
{{
  "summary": "<resumen ejecutivo en 2-3 oraciones>",
  "purpose": "<propósito principal>",
  "data_sensitivity": "<LOW|MEDIUM|HIGH según datos que maneja>"
}}

Resúmenes de archivos:
{resumenes}
"""


def build_llm_client():
    """Retorna cliente boto3 bedrock-runtime o None si no hay credenciales."""
    try:
        import boto3
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        if session.get_credentials() is None:
            return None
        return session.client("bedrock-runtime", region_name="us-east-1")
    except Exception:
        return None


def _invoke(client, user_message: str) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    raw = json.loads(response["body"].read())
    return raw["content"][0]["text"]


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


def enrich_archivo(client, archivo_nombre: str, capa: str, unidades: list, source_code: str) -> dict:
    """Una llamada a Bedrock por archivo. Retorna dict con unidades enriquecidas y resumen_archivo."""
    nombres = [u.get("nombre", "") for u in unidades]
    prompt = PROMPT_TEMPLATE.format(
        archivo=archivo_nombre,
        capa=capa,
        unidades=nombres,
        codigo=source_code[:4000],
    )
    text = _invoke(client, prompt)
    return _parse_json(text)


def enrich_microservicio(client, nombre: str, resumenes_archivos: list[str]) -> dict:
    """Genera resumen ejecutivo del microservicio a partir de los resúmenes por archivo."""
    prompt = RESUMEN_TEMPLATE.format(
        nombre=nombre,
        resumenes="\n".join(f"- {r}" for r in resumenes_archivos if r),
    )
    text = _invoke(client, prompt)
    return _parse_json(text)
