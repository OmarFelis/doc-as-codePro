# Plan Maestro de Implementación — Code-Agent V1.0

> **Documento único de referencia técnica** para el desarrollo del agente.
> Consolida: arquitectura de datos, fases de implementación, tests y criterios de aceptación.
> Fuentes: INI Code-Agent V1.0 · Acta de Proyecto · implementation_plan_DEFINITIVO · PLAN_IMPLEMENTACION_TECNICO
> Actualizado: incluye AWS Strands Agents en Fase 2 y Fase 4

---

## Visión del Sistema

El Code-Agent no es solo un parser. Es un **agente de ingeniería inversa** que:

1. Lee repositorios de Bitbucket (solo lectura)
2. Descompone cada microservicio en unidades físicas (archivos) y lógicas (clases/funciones)
3. Diagnostica calidad: atomicidad, transparencia, complejidad, capas arquitectónicas
4. Usa LLM (Claude/Bedrock) para generar resúmenes en lenguaje natural y extraer reglas de negocio
5. Persiste todo en PostgreSQL (schemas `code` y `quality`) vinculado a `infra.activos`
6. Expone los datos vía endpoints del backend genérico de A-ONE para consumo del frontend

**Resultado final:** Cada función de cada microservicio es un registro consultable, con score de riesgo, capa arquitectónica, resumen en lenguaje natural y trazabilidad al activo padre en `infra.activos`.

---

## Stack Tecnológico

| Capa | Tecnología | Uso |
|---|---|---|
| Orquestación agente | **AWS Strands Agents** | Fase 2 (LLM enrichment) y Fase 4 (lote multi-repo) |
| LLM principal | Claude 3.5 Sonnet vía **AWS Bedrock** | Resúmenes, reglas de negocio, OWASP |
| LLM fallback | OpenAI GPT-4 | Si Bedrock no disponible |
| Persistencia | PostgreSQL — schemas `code` + `quality` | Todas las fases |
| ORM | SQLAlchemy | Todas las fases |
| Modelos de dominio | Pydantic v2 | Todas las fases |
| Fuente de código | Bitbucket (solo lectura) | Fase 4 |

**Por qué Strands y no loop manual:**
El pipeline de enriquecimiento LLM es naturalmente un loop agente: el modelo decide qué herramientas llamar, en qué orden, y maneja reintentos. Strands provee esto de forma declarativa con `@tool`, eliminando el loop manual de `if llm_client: ...` en el pipeline.

---

## Estado actual del código (baseline)

| Componente | Estado | Notas |
|---|---|---|
| `python_analyzer.py` | ✅ Funcional | Produce `FileAnalysis` con clases, funciones, imports, complejidad |
| `java_analyzer.py` | ✅ Funcional | Spring endpoints, JPA entities |
| `javascript_analyzer.py` | ✅ Funcional | Express routes |
| `typescript_analyzer.py` | ✅ Funcional | Decorators, interfaces |
| `logical_unit_extractor.py` | ⚠️ Incorrecto | Produce `QualityAudit` plano — no separa físico/lógico |
| `pipeline.py` | ⚠️ Incorrecto | Usa tabla `quality_audits` única |
| `db/models.py` | ⚠️ Incorrecto | Una sola tabla `quality_audits` |
| `db/repository.py` | ⚠️ Incorrecto | Upsert por nombre — no aplica al nuevo modelo |
| `business_rule_extractor.py` | ✅ Lógica correcta | Solo cambiar tipos de entrada |
| `llm/bedrock_client.py` | ✅ Funcional | Claude 3.5 Sonnet |
| `llm/openai_client.py` | ✅ Funcional | GPT-4 fallback |
| `api/routes/` | ✅ Funcional | Adaptar responses al nuevo modelo |

---

## Arquitectura de datos objetivo

```
infra.activos (existente — NO SE TOCA)
    └── code.archivos_fuente          ← 1 registro por archivo del repo
            └── code.unidades_logicas (tipo=CLASE)    ← AREQAdapter
                    └── code.unidades_logicas (tipo=FUNCION) ← adapt
                    └── code.unidades_logicas (tipo=FUNCION) ← _map_currency
quality.escaneos                      ← 1 snapshot por microservicio por ejecución
```

**Flujo de datos por microservicio:**
```
Bitbucket repo
    → ProjectAnalyzerService (FileAnalysis × N archivos)
    → logical_unit_extractor (ArchivoFuente + List[UnidadLogica] por archivo)
    → repository.insert (code.archivos_fuente + code.unidades_logicas)
    → LLM enricher (resumen + reglas de negocio — solo capa DOMINIO)
    → quality.escaneos (1 snapshot con score agregado)
    → grafo.relaciones_globales (REL-INFRA-05: activo CONTIENE archivo)
```

---

## FASE 1 — Migración al schema definitivo (parseo + persistencia)

**Objetivo:** Reemplazar `quality_audits` por `code.*` + `quality.*` con jerarquía correcta.
**Criterio de aceptación:** El output del pipeline muestra archivos físicos separados de clases y funciones, todo persistido en las tablas correctas.

### 1.1 `src/db/models.py` — 3 tablas ORM

Eliminar `QualityAuditORM`. Crear:

- `ArchivoFuenteORM` → schema `code`, tabla `archivos_fuente`
- `UnidadLogicaORM` → schema `code`, tabla `unidades_logicas`
- `EscaneoORM` → schema `quality`, tabla `escaneos`

Columnas clave de `archivos_fuente`:
```
id, activo_id, aplicacion_id, nombre, ruta_archivo, proposito, capa,
lenguaje, total_funciones, total_clases, endpoints, operaciones_bd,
llamadas_externas, complejidad_ciclomatica, lineas_codigo, resumen,
metadata JSONB, build_number, commit_hash, escaneado_en, activo
```

Columnas clave de `unidades_logicas`:
```
id, archivo_id (FK → archivos_fuente), parent_id (autoreferencial),
activo_id (desnormalizado), nombre, tipo (CLASE|FUNCION|INTERFAZ|ENUM),
capa, proposito, complejidad, lineas_codigo, accede_bd BOOLEAN,
llamadas_externas, docstring BOOLEAN, resumen, metadata JSONB,
risk_level, overall_score, compliance JSONB, activo
```

Columnas clave de `escaneos`:
```
id, activo_id, aplicacion_id, build_number, commit_hash, escaneado_en,
generado_por, score_general, nivel_riesgo CHECK(LOW|MEDIUM|HIGH),
archivos_total, funciones_total, clases_total, dominios_negocio TEXT[],
metricas JSONB, arquitectura JSONB, seguridad JSONB,
rendimiento JSONB, negocio JSONB, cumplimiento JSONB
```

### 1.2 `src/models/domain.py` — 3 modelos Pydantic

Eliminar `QualityAudit`, `EntityType`. Agregar `ArchivoFuente`, `UnidadLogica`, `Escaneo`.

Conservar sin cambios: `FileAnalysis`, `ProjectAnalysis`, `BusinessRule`, `LanguageType`, `ArchitectureLayer`, `RiskLevel`.

### 1.3 `src/db/repository.py` — 3 repositorios

```python
# archivos_fuente
def insert_archivo(session, archivo: ArchivoFuente) -> ArchivoFuente
def delete_archivos_by_activo(session, activo_id: str)  # re-escaneos futuros

# unidades_logicas
def insert_unidades(session, unidades: List[UnidadLogica]) -> List[UnidadLogica]

# escaneos (INSERT-only, nunca upsert)
def insert_escaneo(session, escaneo: Escaneo) -> Escaneo
def get_escaneos_by_activo(session, activo_id: str) -> List[Escaneo]
```

### 1.4 `src/core/analyzers/logical_unit_extractor.py` — jerarquía correcta

**Nueva firma:** `extract(file_analysis: FileAnalysis, activo_id: str) -> tuple[ArchivoFuente, List[UnidadLogica]]`

**Lógica de jerarquía:**
```
file_analysis.classes = ["AREQAdapter"]
file_analysis.functions = ["AREQAdapter.adapt", "AREQAdapter._map_currency", "standalone_func"]

→ ArchivoFuente(nombre="areq_adapter.py", ...)
→ UnidadLogica(tipo=CLASE,   nombre="AREQAdapter",   parent_id=None,       fisica_id=uuid-F)
→ UnidadLogica(tipo=FUNCION, nombre="adapt",          parent_id=uuid-clase, fisica_id=uuid-F)
→ UnidadLogica(tipo=FUNCION, nombre="_map_currency",  parent_id=uuid-clase, fisica_id=uuid-F)
→ UnidadLogica(tipo=FUNCION, nombre="standalone_func",parent_id=None,       fisica_id=uuid-F)
```

Scoring (conservar lógica existente): `overall_score` y `risk_level` van en `UnidadLogica`.

### 1.5 `src/core/analyzers/pipeline.py` — nuevo flujo

```python
async def run(project_path, activo_id, microservice_name, session, llm_client=None) -> dict:
    project = ProjectAnalyzerService().analyze_project(project_path, microservice_name)

    all_logicas = []
    for file_analysis in project.files:
        archivo, logicas = logical_unit_extractor.extract(file_analysis, activo_id)
        saved_archivo = repository.insert_archivo(session, archivo)
        for u in logicas:
            u.fisica_id = saved_archivo.id
        saved_logicas = repository.insert_unidades(session, logicas)
        all_logicas.extend(saved_logicas)

        if llm_client:
            # enriquecer resumen + reglas de negocio (capa DOMINIO)
            ...

    session.commit()

    # calcular y persistir escaneo
    escaneo = _build_escaneo(activo_id, project, all_logicas)
    saved = repository.insert_escaneo(session, escaneo)
    session.commit()
    return _build_summary(saved, all_logicas)
```

**Cambio de firma:** `activo_id: str` es ahora parámetro obligatorio. El llamador resuelve el UUID de `infra.activos` antes de invocar.

### 1.6 `src/db/session.py` — crear schemas

```python
def init_db(url=None):
    engine = get_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS code"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS quality"))
        conn.commit()
    Base.metadata.create_all(engine)
```

### 1.7 `src/core/analyzers/business_rule_extractor.py` — adaptar tipos

Cambio mínimo: `List[QualityAudit]` → `List[UnidadLogica]`, y `audit.metrics.get("architecture_layer")` → `unidad.capa`.

### Tests Fase 1

```
tests/unit/test_logical_unit_extractor.py
  - test_produce_archivo_fuente_por_file_analysis
  - test_clase_tiene_parent_id_none
  - test_funcion_tiene_parent_id_de_su_clase
  - test_funcion_standalone_tiene_parent_id_none
  - test_scoring_se_asigna_a_unidad_logica

tests/unit/test_repository.py
  - test_insert_archivo_retorna_id
  - test_insert_unidades_asigna_fisica_id
  - test_insert_escaneo_es_insert_only
  - test_delete_archivos_cascade_elimina_logicas

tests/integration/test_pipeline_fase1.py
  - test_pipeline_produce_jerarquia_correcta (archivo → clase → funcion)
  - test_pipeline_persiste_en_schemas_correctos
  - test_pipeline_retorna_summary_con_conteos_correctos
```

**Output esperado Fase 1:**
```
ESCANEO PERSISTIDO
  escaneo_id     : uuid
  activo_id      : uuid (infra.activos)
  score_general  : 66.4
  nivel_riesgo   : HIGH
  archivos_total : 72
  clases_total   : 28
  funciones_total: 116

code.archivos_fuente: 72 registros
  areq_adapter.py  → uuid-F1  capa=dominio
  pasarela_adapter.py → uuid-F2  capa=dominio

code.unidades_logicas: 200 registros
  [CLASE]   AREQAdapter     fisica_id=uuid-F1  parent_id=null
  [FUNCION] adapt           fisica_id=uuid-F1  parent_id=uuid-clase
  [FUNCION] _map_currency   fisica_id=uuid-F1  parent_id=uuid-clase
```

---

## FASE 2 — Enriquecimiento con LLM (AWS Strands + Claude/Bedrock)

**Objetivo:** Cada unidad lógica de capa DOMINIO tiene `resumen` en lenguaje natural. Cada microservicio tiene `quality.escaneos.negocio` con reglas de negocio extraídas.

**Prerequisito:** Fase 1 completada. Acceso a AWS Bedrock (Claude 3.5 Sonnet). `strands-agents` instalado.

**Dependencia nueva:**
```toml
# pyproject.toml
strands-agents = ">=0.1"
strands-agents-tools = ">=0.1"  # herramientas built-in opcionales
```

### 2.1 Arquitectura del agente Strands

En lugar del loop manual `if llm_client: ...` en el pipeline, se define un agente con herramientas declarativas:

```python
# src/core/enricher/enrichment_agent.py
from strands import Agent, tool
from strands.models import BedrockModel

@tool
def enriquecer_unidades(archivo_id: str, source_code: str) -> dict:
    """Genera resúmenes en español para cada función de capa DOMINIO.
    Retorna JSON: [{nombre, resumen}]"""
    ...

@tool
def extraer_reglas_negocio(source_code: str) -> list:
    """Extrae reglas de negocio: validaciones, cálculos, flujos.
    Retorna JSON: [{descripcion, funcion_origen, tipo}]"""
    ...

@tool
def analizar_owasp(source_code: str) -> list:
    """Detecta patrones OWASP Top 10 en código de capa INFRAESTRUCTURA.
    Retorna JSON: [{categoria, descripcion, linea}]"""
    ...

@tool
def generar_resumen_microservicio(inventario_funciones: str) -> dict:
    """Genera resumen ejecutivo del microservicio.
    Retorna JSON: {summary, purpose, data_sensitivity}"""
    ...

enrichment_agent = Agent(
    model=BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
    ),
    tools=[enriquecer_unidades, extraer_reglas_negocio, analizar_owasp, generar_resumen_microservicio],
    system_prompt="Eres un analista técnico de software de pagos digitales. "
                  "Respondes siempre en español. Produces JSON válido sin markdown.",
)
```

El agente decide el orden de llamadas según el contexto del archivo. El pipeline lo invoca una vez por archivo:

```python
# En pipeline.py — reemplaza el bloque `if llm_client:`
if enrichment_agent:
    result = enrichment_agent(f"Enriquece el archivo {archivo.nombre} con activo {activo_id}")
    repository.apply_enrichment(session, archivo.id, result)
```

### 2.2 Prompts por herramienta

| Herramienta | Trigger | Output → tabla |
|---|---|---|
| `enriquecer_unidades` | Archivo con unidades capa DOMINIO | `code.unidades_logicas.resumen` |
| `extraer_reglas_negocio` | Archivo con capa DOMINIO | `quality.escaneos.negocio.reglas[]` |
| `analizar_owasp` | Archivo con capa INFRAESTRUCTURA | `quality.escaneos.seguridad.owasp[]` |
| `generar_resumen_microservicio` | Al final de todos los archivos | `quality.escaneos.negocio.{summary,purpose,data_sensitivity}` |

### 2.3 Patrones OWASP detectados

- Queries sin sanitización → A03:2021 Injection
- Credenciales hardcodeadas → A02:2021 Cryptographic Failures
- Sin validación de JWT → A07:2021 Auth Failures

### 2.4 Fallback graceful

Si Bedrock no está disponible, el agente no se instancia y el pipeline continúa sin enriquecimiento. Los campos `resumen` quedan `null` — no es error bloqueante.

```python
try:
    enrichment_agent = build_enrichment_agent()  # lanza si no hay credenciales
except Exception:
    enrichment_agent = None  # pipeline continúa sin LLM
```

### Tests Fase 2

```
tests/unit/test_enrichment_agent.py
  - test_tool_enriquecer_unidades_retorna_json_valido
  - test_tool_no_procesa_capa_infraestructura
  - test_tool_extraer_reglas_tiene_trazabilidad_funcion_origen
  - test_tool_owasp_detecta_query_sin_sanitizar
  - test_fallback_graceful_si_bedrock_no_disponible

tests/unit/test_business_rule_extractor.py
  - test_solo_procesa_capa_dominio
  - test_regla_tiene_trazabilidad_a_funcion_origen
  - test_json_invalido_retorna_lista_vacia

tests/integration/test_pipeline_fase2.py
  - test_pipeline_con_agent_mock_enriquece_resumen
  - test_pipeline_sin_agent_completa_sin_error
  - test_escaneo_negocio_tiene_reglas_extraidas
```

---

## FASE 3 — Endpoints al backend de A-ONE

**Objetivo:** Los datos en `code.*` y `quality.*` son consumibles por el frontend de A-ONE vía el backend genérico existente (GET, POST, UPDATE básicos ya provistos).

**Prerequisito:** DBA confirma nombre de BD y configura acceso. Fase 1 y 2 completadas.

### 3.1 Configuración del backend genérico

El backend de A-ONE expone entidades por nombre de tabla. Se deben registrar:

| Entidad | Tabla | Operaciones |
|---|---|---|
| `archivos_fuente` | `code.archivos_fuente` | GET (list, by id, by activo_id) |
| `unidades_logicas` | `code.unidades_logicas` | GET (list, by archivo_id, by activo_id) |
| `escaneos` | `quality.escaneos` | GET (list, by activo_id, último por activo) |

No se necesita POST ni UPDATE desde el frontend — solo el Code-Agent escribe.

### 3.2 Queries que el frontend necesita

```sql
-- Archivos de un microservicio ordenados por complejidad
GET /entities/archivos_fuente?activo_id={uuid}&order=complejidad_ciclomatica:desc

-- Funciones HIGH risk de un microservicio
GET /entities/unidades_logicas?activo_id={uuid}&risk_level=HIGH&tipo=FUNCION

-- Último escaneo de un microservicio
GET /entities/escaneos?activo_id={uuid}&order=escaneado_en:desc&limit=1

-- Evolución de score (todos los escaneos)
GET /entities/escaneos?activo_id={uuid}&order=escaneado_en:asc
```

### 3.3 Relaciones en el grafo (INSERT en A-ONE)

Una vez que los archivos están en `code.archivos_fuente`, crear relaciones:

```sql
-- REL-INFRA-05: Lambda CONTIENE archivo (1 por archivo)
INSERT INTO grafo.relaciones_globales (origen_id, destino_id, tipo_relacion_id, contexto)
VALUES (activo_id, archivo_fuente_id, uuid_REL-INFRA-05, 'Composición código')

-- REL-INFRA-34: Función ACCEDE recurso AWS (detectado por imports)
INSERT INTO grafo.relaciones_globales (origen_id, destino_id, tipo_relacion_id, contexto)
VALUES (unidad_logica_id, activo_aws_id, uuid_REL-INFRA-34, 'boto3.s3')
```

El pipeline debe recibir el `uuid_REL-INFRA-05` como configuración (no hardcodeado).

### 3.4 Nuevo módulo `src/integrations/aone_graph.py`

```python
def insert_contiene_relaciones(session_aone, activo_id, archivos: List[ArchivoFuente], rel_infra_05_id: str)
def insert_acceso_aws_relaciones(session_aone, unidades: List[UnidadLogica], activos_aws: dict, rel_infra_34_id: str)
```

Este módulo usa una sesión separada apuntando a la BD de A-ONE (puede ser la misma BD, schema diferente).

### Tests Fase 3

```
tests/unit/test_aone_graph.py
  - test_insert_contiene_crea_relacion_por_archivo
  - test_insert_acceso_aws_detecta_boto3_en_imports
  - test_no_crea_relacion_si_activo_aws_no_existe

tests/integration/test_pipeline_fase3.py
  - test_pipeline_completo_crea_relaciones_en_grafo
  - test_pipeline_idempotente_no_duplica_relaciones
```

---

## FASE 4 — Cobertura de microservicios críticos (deadline 14 de marzo)

**Objetivo:** 100% de mapeo de ACS, Orquestador, PSE, OSE y Transaction Key.

**Prerequisito:** Fases 1, 2 y 3 completadas. Acceso de lectura a Bitbucket otorgado por TI.

### 4.1 Integración con Bitbucket

```python
# src/integrations/bitbucket.py
def clone_repo(repo_slug: str, workspace: str, branch: str, target_dir: Path) -> Path
def get_commit_hash(repo_path: Path) -> str
def get_build_number(repo_slug: str) -> str  # vía Bitbucket Pipelines API
```

El pipeline recibe `repo_slug` en lugar de `local_path`. Clona en directorio temporal, escanea, limpia.

### 4.2 Agente de lote con Strands (multi-repo paralelo)

En lugar de un loop secuencial, se usa un agente Strands que orquesta el escaneo de los 5 repos. El modelo decide el orden y maneja errores por repo sin detener el lote:

```python
# scan_all.py
from strands import Agent, tool
from strands.models import BedrockModel

MICROSERVICIOS = [
    {"nombre": "ACS",             "repo": "acs-service",          "activo_id": "uuid-acs"},
    {"nombre": "Orquestador",     "repo": "orchestrator-service",  "activo_id": "uuid-orch"},
    {"nombre": "PSE",             "repo": "pse-service",           "activo_id": "uuid-pse"},
    {"nombre": "OSE",             "repo": "ose-service",           "activo_id": "uuid-ose"},
    {"nombre": "Transaction Key", "repo": "transaction-key",       "activo_id": "uuid-tk"},
]

@tool
def escanear_microservicio(nombre: str, repo: str, activo_id: str) -> dict:
    """Clona el repo de Bitbucket, ejecuta el pipeline completo y retorna el resumen del escaneo."""
    repo_path = bitbucket.clone_repo(repo)
    return asyncio.run(pipeline.run(
        project_path=repo_path,
        activo_id=activo_id,
        microservice_name=nombre,
        session=get_session(),
        enrichment_agent=build_enrichment_agent(),
    ))

batch_agent = Agent(
    model=BedrockModel(model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
    tools=[escanear_microservicio],
    system_prompt="Escanea todos los microservicios críticos. Si uno falla, continúa con los demás.",
)

batch_agent(f"Escanea estos microservicios: {[ms['nombre'] for ms in MICROSERVICIOS]}")
```

**Ventaja sobre loop manual:** Si un repo falla (Bitbucket timeout, error de parseo), el agente reporta el error y continúa con los demás sin código de manejo de excepciones por repo.

### 4.3 Validación de resultados

Después de cada escaneo, verificar:
- `code.archivos_fuente` tiene registros para el `activo_id`
- `code.unidades_logicas` tiene clases Y funciones (no solo funciones)
- `quality.escaneos` tiene `score_general` y `nivel_riesgo` poblados
- Al menos 1 unidad de capa DOMINIO tiene `resumen` no nulo (LLM funcionó)

### Tests Fase 4

```
tests/integration/test_bitbucket.py
  - test_clone_repo_retorna_path_valido
  - test_get_commit_hash_retorna_string_40_chars

tests/unit/test_batch_agent.py
  - test_tool_escanear_microservicio_retorna_summary
  - test_batch_continua_si_un_repo_falla

tests/e2e/test_scan_microservicio.py
  - test_scan_produce_archivos_fisicos
  - test_scan_produce_jerarquia_clase_funcion
  - test_scan_produce_escaneo_con_score
  - test_scan_enriquece_con_llm (con mock de Bedrock)
```

---

## Resumen de fases y archivos

| Fase | Qué hace | Archivos modificados | Tests |
|---|---|---|---|
| 1 | Migración schema code+quality, jerarquía física/lógica | `models.py`, `domain.py`, `repository.py`, `logical_unit_extractor.py`, `pipeline.py`, `session.py`, `business_rule_extractor.py` | 3 archivos de test |
| 2 | **Strands Agent** + LLM: resúmenes + reglas de negocio + OWASP | `src/core/enricher/enrichment_agent.py` (nuevo), `business_rule_extractor.py`, `pipeline.py` | 3 archivos de test |
| 3 | Endpoints A-ONE + relaciones en grafo | `src/integrations/aone_graph.py` (nuevo), `pipeline.py` | 2 archivos de test |
| 4 | Bitbucket + **Strands batch agent** + 5 microservicios críticos | `src/integrations/bitbucket.py` (nuevo), `scan_all.py` (nuevo) | 3 archivos de test |

---

## Lo que NO cambia en ninguna fase

| Componente | Razón |
|---|---|
| `python_analyzer.py`, `java_analyzer.py`, `javascript_analyzer.py`, `typescript_analyzer.py` | Producen `FileAnalysis` correcto |
| `project_analyzer.py`, `factory.py`, `base.py` | Orquestación sin cambios |
| `llm/bedrock_client.py`, `llm/openai_client.py` | Clientes LLM sin cambios |
| `api/routes/analysis.py` | Solo actualizar tipos de response |
| `infra.activos`, `grafo.relaciones_globales` (A-ONE) | Sin cambios estructurales |

---

## Criterios de aceptación globales

- [ ] `code.archivos_fuente` tiene 1 registro por archivo `.py`/`.java` del repo
- [ ] `code.unidades_logicas` tiene registros de tipo CLASE con `parent_id=null`
- [ ] `code.unidades_logicas` tiene registros de tipo FUNCION con `parent_id=uuid_clase`
- [ ] `quality.escaneos` tiene `score_general`, `nivel_riesgo`, `archivos_total`, `clases_total`, `funciones_total`
- [ ] Unidades de capa DOMINIO tienen `resumen` generado por LLM
- [ ] `quality.escaneos.negocio` tiene al menos 1 regla de negocio extraída
- [ ] `grafo.relaciones_globales` tiene relaciones REL-INFRA-05 (activo CONTIENE archivo)
- [ ] Los 5 microservicios críticos están escaneados antes del 14 de marzo
- [ ] Cobertura de tests > 80%

---

*Generado: 2025 — doc-as-codePRO — Alignet Ecosistema de Pagos Digitales*
