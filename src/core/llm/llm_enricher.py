"""Enriquece UnidadLogica (capa DOMINIO) con Bedrock: resumen."""
import json
import re
from typing import List, Optional

from src.core.llm.base import LLMClient
from src.models.domain import UnidadLogica
from src.utils.logging import get_logger

logger = get_logger(__name__)

_SYSTEM = (
    "Eres un arquitecto de software senior. Analizas código fuente y respondes SOLO con JSON válido, "
    "sin markdown, sin explicaciones adicionales."
)

_PROMPT = """Analiza esta unidad lógica de código y responde SOLO con un JSON con esta estructura exacta:
{{
  "description": {{
    "summary": "Una oración: qué hace esta función/clase.",
    "purpose": "Por qué existe: qué problema resuelve.",
    "business_value": "Impacto en el negocio si falla o se modifica."
  }},
  "external_relations": {{
    "inbound": [],
    "outbound": [],
    "data_storage": [],
    "events_published": []
  }}
}}

Para external_relations, infiere las dependencias del código:
- outbound: llamadas HTTP, APIs externas, otros servicios
- data_storage: bases de datos, caché, archivos
- inbound: déjalo vacío (no se puede inferir del código)
- events_published: eventos publicados (Kafka, SQS, EventBridge, etc.)

Unidad: {unit_name}
Capa: {layer}
Lenguaje: {language}
Microservicio: {microservice}

Código:
```
{code_snippet}
```"""


def _extract_json(text: str) -> dict:
    """Extrae el primer JSON válido del texto de respuesta."""
    # Intentar parsear directo
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Buscar bloque JSON entre llaves
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


async def enrich(
    unidades: List[UnidadLogica],
    source_code: str,
    microservice_name: str,
    llm_client: LLMClient,
    max_units: Optional[int] = None,
) -> List[UnidadLogica]:
    """Enriquece unidades DOMINIO con resumen via Bedrock."""
    domain_units = [u for u in unidades if u.capa == "dominio"]
    if not domain_units:
        return unidades
    if max_units:
        domain_units = domain_units[:max_units]

    lines = source_code.splitlines()
    enriched_ids = set()

    for unidad in domain_units:
        snippet = _extract_snippet(source_code, lines, unidad.nombre)
        prompt = _PROMPT.format(
            unit_name=unidad.nombre,
            layer=unidad.capa or "dominio",
            language="python",
            microservice=microservice_name,
            code_snippet=snippet[:3000],
        )
        try:
            raw = await llm_client.generate_text(
                prompt=prompt, max_tokens=800, temperature=0.3, system_prompt=_SYSTEM,
            )
            data = _extract_json(raw)
            if data.get("description"):
                unidad.resumen = data["description"].get("summary", unidad.resumen)
            enriched_ids.add(unidad.nombre)
            logger.info("unit_enriched", unit=unidad.nombre, microservice=microservice_name)
        except Exception as e:
            logger.warning("enrich_failed", unit=unidad.nombre, error=str(e))

    logger.info("enrichment_complete", microservice=microservice_name,
                enriched=len(enriched_ids), total_domain=len(domain_units))
    return unidades


def _extract_snippet(source: str, lines: list, unit_name: str, context: int = 40) -> str:
    """Extrae líneas relevantes alrededor de la definición de la unidad."""
    for i, line in enumerate(lines):
        if unit_name in line and ("def " in line or "class " in line or "function " in line or "public " in line):
            start = max(0, i)
            end = min(len(lines), i + context)
            return "\n".join(lines[start:end])
    # Si no encuentra, devuelve los primeros N caracteres del archivo
    return source[:2000]
