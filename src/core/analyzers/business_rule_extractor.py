"""Extrae reglas de negocio en lenguaje natural usando LLM, solo para capa DOMINIO."""
import json
from typing import List
from src.models.domain import BusinessRule, QualityAudit, ArchitectureLayer
from src.utils.logging import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """Eres un analista de negocio técnico. Analiza el siguiente código y extrae ÚNICAMENTE las reglas de negocio: validaciones, cálculos, condiciones de negocio. NO incluyas lógica de infraestructura ni de entrada/salida.

Para cada regla encontrada describe en lenguaje natural:
- Qué valida o calcula
- Bajo qué condición se aplica
- Qué resultado produce

Código ({language}):
{source_code}

Responde SOLO con JSON válido, sin texto adicional:
[{{"description": "...", "condition": "...", "result": "..."}}]"""


def _is_dominio(audit: QualityAudit) -> bool:
    return audit.metrics.get("architecture_layer") == ArchitectureLayer.DOMINIO.value


async def extract(
    audits: List[QualityAudit],
    source_code: str,
    linked_application: str,
    linked_component: str,
    llm_client,
) -> List[BusinessRule]:
    """Procesa solo unidades de capa DOMINIO y retorna reglas de negocio."""
    dominio_units = [a for a in audits if _is_dominio(a)]
    if not dominio_units:
        return []

    language = dominio_units[0].language or "python"
    prompt = _PROMPT_TEMPLATE.format(source_code=source_code, language=language)

    try:
        raw = await llm_client.generate_text(prompt=prompt, max_tokens=2000, temperature=0.3)
        rules_data = json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("business_rule_extraction_failed", error=str(e))
        return []

    rules = []
    for unit in dominio_units:
        for item in rules_data:
            if not isinstance(item, dict) or "description" not in item:
                continue
            rules.append(BusinessRule(
                description=item["description"],
                linked_application=linked_application,
                linked_component=linked_component,
                linked_unit_name=unit.entity_name,
            ))

    return rules
