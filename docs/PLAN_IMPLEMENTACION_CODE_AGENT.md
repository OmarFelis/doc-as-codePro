# Plan de Implementación — Code-Agent V1.0

**Sponsor:** Javier Draxl  
**Deadline crítico:** 14 de marzo — 100% mapeo de ACS, Orquestador, PSE, OSE, Transaction Key  
**Deadline secundario:** 15 de abril — Comparación arquitectónica QA vs DEV  
**Última actualización:** 2025

---

## Objetivo

Construir una **fuente de verdad técnica estructurada** donde cada función, flujo y regla de negocio de los microservicios críticos sea un activo independiente en PostgreSQL, vinculado entre sí, consultable en lenguaje natural y con diagnóstico de calidad automatizado.

Confluence pasa a ser una **vista opcional secundaria**. El destino principal es la base de datos `quality_audits`.

---

## Lo que ya existe y se reutiliza

| Componente | Estado | Rol en el nuevo sistema |
|---|---|---|
| `src/core/analyzers/python_analyzer.py` | ✅ Funcional | Extrae funciones, clases, imports, complejidad — input del `LogicalUnitExtractor` |
| `src/core/analyzers/java_analyzer.py` | ✅ Funcional | Detecta Spring endpoints, JPA entities, complejidad — cubre microservicios Java |
| `src/core/analyzers/project_analyzer.py` | ✅ Funcional | Orquesta análisis paralelo de proyecto completo — se reutiliza sin cambios |
| `src/core/analyzers/base.py` | ✅ Funcional | Interfaz base para nuevos extractores |
| `src/core/llm/bedrock_client.py` | ⚠️ Bug menor | Cliente Claude 3.5 Sonnet — base del `BusinessRuleExtractor` |
| `src/config/settings.py` | ✅ Funcional | `DatabaseSettings` y `BedrockSettings` ya configurados |
| `src/utils/logging.py` | ✅ Funcional | structlog JSON listo para producción |
| `src/api/main.py` + routes | ⚠️ Bug menor | FastAPI funcional — expone el pipeline como API REST |

**No se reutiliza:** `readme_generator.py`, `generators/base.py`, modelos `Documentation`/`PublishRequest` — orientados a Confluence, fuera del nuevo alcance.

---

## Arquitectura objetivo

```
POST /api/v1/analyze
        │
        ▼
ProjectAnalyzerService          ← ya existe
        │
        ├── FileAnalysis[]       ← ya existe (Python, Java, JS, TS)
        │
        ▼
LogicalUnitExtractor            ← Fase 1 ✔ COMPLETADO
        │
        ├── QualityAudit[]       ← con layer, scores, risk_level
        │
        ▼
BusinessRuleExtractor           ← Fase 1 ✔ COMPLETADO — solo capa DOMINIO
        │
        ├── BusinessRule[]       ← en lenguaje natural, trazabilidad completa
        │
        ▼
QualityAuditRepository          ← Fase 1 ✔ COMPLETADO
        │
        └── PostgreSQL: tabla quality_audits
                │
                ▼
        LLMEnricher                 ← Fase 2 — Paso 8
                │
                └── Enriquece description + external_relations con Bedrock
                        │
                        ▼
                DiffAnalyzer            ← Fase 2 — Paso 9
                        └── POST /api/v1/compare (QA vs DEV)
```

> **Nota:** Paso 7 (fix JS/TS) es prerequisito de Paso 8 — debe completarse primero para garantizar
> cobertura completa de lenguajes antes de ejecutar el enriquecimiento LLM.

---

## Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        doc-as-codePRO v3.0                          │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  FastAPI     │    │   Analyzers  │    │   LLM Layer          │  │
│  │              │    │              │    │                      │  │
│  │ POST         │    │ PythonAnalyz │    │ BedrockClient        │  │
│  │ /analyze     │───▶│ JavaAnalyzer │    │ (Claude 3.5 Sonnet)  │  │
│  │              │    │ JSAnalyzer   │    │                      │  │
│  │ POST         │    │ TSAnalyzer   │    │ BusinessRuleExtract  │  │
│  │ /compare     │    │              │    │ LLMEnricher          │  │
│  └──────────────┘    └──────┬───────┘    └──────────┬───────────┘  │
│                             │                       │              │
│                    ┌────────▼────────┐              │              │
│                    │ Pipeline Core   │              │              │
│                    │                 │              │              │
│                    │ ProjectAnalyzer │              │              │
│                    │ LogicalUnitExtr │◀─────────────┘              │
│                    │ QualityAuditRep │                             │
│                    └────────┬────────┘                             │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   PostgreSQL                  │
              │                               │
              │   quality_audits              │
              │   ├── MICROSERVICE (padre)    │
              │   └── LOGIC_UNIT (hijos)      │
              │       ├── description  JSONB  │
              │       ├── external_rel JSONB  │
              │       ├── metrics      JSONB  │
              │       └── compliance   JSONB  │
              └───────────────────────────────┘
```

---

## Diagrama de Flujo — Pipeline de Análisis

```
  ENTRADA: ruta del microservicio
         │
         ▼
  ┌─────────────────────┐
  │  ProjectAnalyzer    │  Recorre directorios, ignora deps
  │  _walk_dir()        │  (.venv, node_modules, target...)
  └──────────┬──────────┘
             │  List[Path]
             ▼
  ┌─────────────────────┐
  │  AnalyzerFactory    │  Selecciona analizador por extensión
  │  .get_analyzer()    │  .py → Python | .java → Java
  └──────────┬──────────┘  .js → JS    | .ts → TS
             │  FileAnalysis[]
             │  { functions, imports, complexity,
             │    endpoints, database_calls, lines }
             ▼
  ┌─────────────────────┐
  │ LogicalUnitExtract  │  Por cada función detectada:
  │ .extract()          │  - Clasifica capa (DOM/INF/ADP)
  └──────────┬──────────┘  - Calcula atomicity + transparency
             │              - Calcula overall_score (0-100)
             │  QualityAudit[]  - Detecta MULTICAPA
             │  entity_type=LOGIC_UNIT
             ▼
  ┌─────────────────────┐
  │ BusinessRuleExtract │  Solo unidades capa DOMINIO
  │ .extract()          │  Llama Bedrock si llm_client != None
  └──────────┬──────────┘  Retorna List[BusinessRule]
             │
             ▼
  ┌─────────────────────┐
  │ QualityAuditRepo    │  upsert por entity_name + entity_type
  │ .upsert_all()       │  Padre (MICROSERVICE) + hijos (LOGIC_UNIT)
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐   ← Fase 2 — Paso 8
  │ LLMEnricher         │  Lee QualityAudit de Postgres
  │ .enrich()           │  Llama Bedrock por unidad DOMINIO
  └──────────┬──────────┘  Actualiza description + external_relations
             │
             ▼
  ┌─────────────────────┐   ← Fase 2 — Paso 9
  │ DiffAnalyzer        │  Compara snapshots QA vs DEV
  │ .compare()          │  Detecta funciones nuevas/eliminadas
  └──────────┬──────────┘  Cambios en risk_level, score, dependencias
             │
             ▼
  SALIDA: quality_summary + quality_audits en PostgreSQL
```

---

## Diagrama de Datos — Tabla `quality_audits`

```
 quality_audits
 ┌─────────────────────────────────────────────────────────┐
 │ id          UUID PK                                     │
 │ parent_id   UUID FK → quality_audits(id)  (nullable)   │
 │ entity_name VARCHAR(255)                                │
 │ entity_type MICROSERVICE | LOGIC_UNIT                   │
 │ runtime_env LAMBDA | ECS_FARGATE | K8S | ON_PREMISE     │
 │ language    python | java | javascript | typescript     │
 │ risk_level  LOW | MEDIUM | HIGH                         │
 │ overall_score DECIMAL(5,2)  0-100                       │
 │                                                         │
 │ description JSONB ──────────────────────────────────┐  │
 │  {                                                  │  │
 │    "summary": "Valida BIN del emisor...",           │  │
 │    "purpose": "Aislar reglas de autorización",      │  │
 │    "business_value": "Crítico para aprobación"      │  │
 │  }                                          ← LLM  │  │
 │                                                     │  │
 │ external_relations JSONB ───────────────────────────┘  │
 │  {                                                      │
 │    "outbound": [{"target": "visa-api"}],                │
 │    "data_storage": [{"resource": "bins-db"}]            │
 │  }                                          ← LLM      │
 │                                                         │
 │ metrics JSONB ← análisis estático                       │
 │  { "lines_of_code": 45, "cyclomatic_complexity": 8 }   │
 │                                                         │
 │ compliance JSONB ← análisis estático                    │
 │  { "has_multi_layer_coupling": false, "loc_ok": true }  │
 │                                                         │
 │ created_at TIMESTAMP WITH TIME ZONE                     │
 └─────────────────────────────────────────────────────────┘

 Relación padre-hijo:

 MICROSERVICE (parent_id = NULL)
 └── LOGIC_UNIT (parent_id = microservice.id)
 └── LOGIC_UNIT
 └── LOGIC_UNIT
     ...
```

---

## Fase 1 — Núcleo del sistema (deadline: 14 de marzo)

**Objetivo:** Pipeline completo que analiza un microservicio y persiste el resultado en `quality_audits`.

### Paso 1 — Fix bugs bloqueantes (1-2 horas)

**Archivos a modificar:**

- `src/core/llm/bedrock_client.py`
  - `settings.bedrock.access_key_id` → `settings.bedrock.aws_access_key_id`
  - `settings.bedrock.secret_access_key` → `settings.bedrock.aws_secret_access_key`

- `src/api/main.py`
  - Migrar `@app.on_event("startup/shutdown")` → `lifespan` context manager (deprecado en FastAPI moderno)

- `src/core/llm/openai_client.py`
  - Reemplazar referencia a `settings.openai` (no existe) por variable de entorno directa `OPENAI_API_KEY`

**Criterio de éxito:** `poetry run python -c "from src.api.main import app"` sin errores.

---

### Paso 2 — Extender `domain.py` con modelos del schema de Stefano (2-3 horas)

**Archivo:** `src/models/domain.py`

Agregar los siguientes modelos alineados al DDL de `quality_audits`:

```python
class EntityType(str, Enum):
    MICROSERVICE = "MICROSERVICE"
    LOGIC_UNIT = "LOGIC_UNIT"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ArchitectureLayer(str, Enum):
    ADAPTADOR = "adaptador"       # Entrada — sin lógica de negocio
    DOMINIO = "dominio"           # Lógica pura, agnóstica de infraestructura
    INFRAESTRUCTURA = "infraestructura"  # Llamadas a BD o AWS

class LogicalUnitType(str, Enum):
    FLUJO = "UNIDAD_LOGICA_FLUJO"
    FUNCION = "UNIDAD_LOGICA_FUNCION"
    DETALLE = "UNIDAD_LOGICA_DETALLE"
    REGLA_NEGOCIO = "UNIDAD_LOGICA_REGLA_NEGOCIO"

class QualityAudit(BaseModel):
    """Mapea directamente a la tabla quality_audits de Stefano."""
    id: Optional[str] = None
    parent_id: Optional[str] = None          # FK al microservicio padre
    entity_name: str                          # Nombre del componente
    entity_type: EntityType
    runtime_env: Optional[str] = None        # LAMBDA, ECS_FARGATE, K8S
    language: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    overall_score: Optional[float] = None    # 0-100
    description: Dict[str, Any] = {}         # JSONB: summary, purpose, business_value
    external_relations: Dict[str, Any] = {}  # JSONB: inbound, outbound, data_storage
    metrics: Dict[str, Any] = {}             # JSONB: loc, complexity, endpoints, coverage
    compliance: Dict[str, Any] = {}          # JSONB: checklist naming, layers, tests
    created_at: Optional[datetime] = None

class BusinessRule(BaseModel):
    description: str           # En lenguaje natural
    linked_application: str
    linked_component: str
    linked_unit_name: str      # Nombre de la función/clase origen
```

**Criterio de éxito:** Los modelos se importan sin error y mapean 1:1 con el DDL.

---

### Paso 3 — `LogicalUnitExtractor` (1 día)

**Archivo nuevo:** `src/core/analyzers/logical_unit_extractor.py`

Recibe un `FileAnalysis` (ya existe) y produce `List[QualityAudit]` con `entity_type=LOGIC_UNIT`.

**Lógica de clasificación de capa:**

| Patrón detectado | Capa asignada |
|---|---|
| Imports: `fastapi`, `flask`, `handler`, `router`, `controller` | ADAPTADOR |
| Imports: `boto3`, `dynamodb`, `s3`, `sqs`, `psycopg2`, `sqlalchemy` | INFRAESTRUCTURA |
| Sin imports de infra ni entrada | DOMINIO |

**Cálculo de scores (basado en `Diagnóstico de Calidad` doc):**

- `atomicity_score`: penalizar si LOC > 30 o complejidad > 10
- `transparency_score`: penalizar si tiene `database_calls` o imports AWS
- `risk_level`: HIGH si complejidad > 15, MEDIUM si 10-15, LOW si < 10
- `overall_score`: promedio ponderado de atomicidad + transparencia + (1/complejidad)

**Flag de riesgo multicapa:** si una función tiene imports de ADAPTADOR e INFRAESTRUCTURA simultáneamente → marcar en `compliance.has_multi_layer_coupling = true`

**Métricas a poblar en `metrics` JSONB:**
```json
{
  "lines_of_code": 45,
  "cyclomatic_complexity": 12,
  "indentation_levels": 3,
  "external_dependencies_count": 2,
  "aws_services": ["S3", "DynamoDB"]
}
```

**Criterio de éxito:** Dado un `FileAnalysis` de Python con 5 funciones, produce 5 `QualityAudit` con `entity_type=LOGIC_UNIT`, `risk_level` y `overall_score` calculados.

---

### Paso 4 — `BusinessRuleExtractor` (1 día)

**Archivo nuevo:** `src/core/analyzers/business_rule_extractor.py`

Solo procesa unidades clasificadas como capa **DOMINIO**.

Usa `BedrockClient` (ya existe, corregido en Paso 1) con un prompt especializado:

```
Eres un analista de negocio técnico. Analiza el siguiente código Python/Java
y extrae ÚNICAMENTE las reglas de negocio: validaciones, cálculos, condiciones
de negocio. NO incluyas lógica de infraestructura ni de entrada/salida.

Para cada regla encontrada, describe en lenguaje natural:
- Qué valida o calcula
- Bajo qué condición se aplica
- Qué resultado produce

Código:
{source_code}

Responde en JSON: [{"description": "...", "condition": "...", "result": "..."}]
```

Output: `List[BusinessRule]` con trazabilidad a `linked_component` y `linked_unit_name`.

**Criterio de éxito:** Dado el código de una función de dominio, retorna al menos 1 regla de negocio en lenguaje natural con trazabilidad completa.

---

### Paso 5 — `QualityAuditRepository` con SQLAlchemy (1 día)

**Archivos nuevos:**
- `src/db/models.py` — modelo SQLAlchemy de `quality_audits`
- `src/db/session.py` — session factory con connection pooling
- `src/db/repository.py` — CRUD: `upsert`, `get_by_name`, `get_by_parent`
- `alembic/` — migration inicial con el DDL de Stefano

**DDL de referencia** (del documento `Estructura de Base de Datos`):
```sql
CREATE TABLE quality_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES quality_audits(id) ON DELETE CASCADE,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) CHECK (entity_type IN ('MICROSERVICE', 'LOGIC_UNIT')),
    runtime_env VARCHAR(50),
    language VARCHAR(50),
    risk_level risk_level_enum DEFAULT 'MEDIUM',
    overall_score DECIMAL(5,2),
    description JSONB NOT NULL DEFAULT '{}',
    external_relations JSONB NOT NULL DEFAULT '{}',
    metrics JSONB NOT NULL DEFAULT '{}',
    compliance JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**IMPORTANTE:** Confirmar con Stefano si el schema está en producción antes de ejecutar migrations.

**Criterio de éxito:** `upsert(quality_audit)` persiste correctamente y `get_by_name("ACS")` retorna el microservicio con sus unidades lógicas hijas.

---

### Paso 6 — Conectar el pipeline completo (1 día)

**Archivo a modificar:** `src/core/analyzers/project_analyzer.py`

Actualizar `analyze_project()` para orquestar el pipeline completo:

```
FileAnalysis[] 
  → LogicalUnitExtractor → List[QualityAudit] (LOGIC_UNIT)
  → BusinessRuleExtractor → List[BusinessRule] (solo DOMINIO)
  → QualityAuditRepository.upsert_all()
```

**Archivo a modificar:** `src/api/routes/analysis.py`

- Reemplazar `dict` en memoria por `QualityAuditRepository`
- Agregar campo `quality_summary` en el response: `overall_score`, `risk_level`, `units_count`, `business_rules_count`

**Criterio de éxito:** `POST /api/v1/analyze` con `local_path` de un microservicio real persiste en Postgres y retorna el resumen de calidad.

---

## Fase 2 — Enriquecimiento LLM y comparación (deadline: 15 de abril)

> **Decisión de arquitectura:** Confluence y Jira quedan fuera del alcance.
> El destino único y fuente de verdad es `quality_audits` en PostgreSQL.
> Cualquier vista externa (dashboards, reportes) se construye consultando esta tabla.

### Paso 7 — Fix analizadores JS/TS (1 día)

**Archivos a corregir:**
- `src/core/analyzers/javascript_analyzer.py` — bug `argument of type 'Module' is not iterable` detectado en prueba con FLOTAS-ADQUIRENTE
- `src/core/analyzers/typescript_analyzer.py` — mismo patrón, verificar

**Relación con pasos anteriores:**
- Habilita Paso 3 (`LogicalUnitExtractor`) para archivos JS/TS — sin este fix, no se generan `QualityAudit` para esos archivos
- Prerequisito del Paso 8 — el enriquecimiento LLM debe tener cobertura completa antes de ejecutarse

**Criterio de éxito:** Correr el pipeline contra FLOTAS-ADQUIRENTE sin `javascript_analysis_error` y con unidades lógicas JS detectadas en `quality_audits`.

---

### Paso 8 — Enriquecimiento LLM de `quality_audits` (1-2 días)

**Objetivo:** Usar Bedrock (Claude 3.5 Sonnet) para rellenar los campos JSONB que el análisis estático no puede inferir.

**Archivo nuevo:** `src/core/analyzers/llm_enricher.py`

Procesa los `QualityAudit` ya persistidos en Postgres y enriquece:

| Campo JSONB | Qué aporta el LLM |
|-------------|-------------------|
| `description.summary` | Qué hace la función/microservicio en lenguaje natural |
| `description.purpose` | Por qué existe, qué problema resuelve |
| `description.business_value` | Impacto de negocio si falla o se modifica |
| `external_relations.outbound` | Dependencias detectadas en el código (APIs, servicios, BDs llamadas) |
| `external_relations.data_storage` | Recursos de datos accedidos (tablas, caches, buckets) |

**Flujo:**
```
QualityAuditRepository.get_by_parent(microservice_id)
    → filtrar entity_type=LOGIC_UNIT y architecture_layer=dominio
    → leer source_code del archivo original
    → BedrockClient.generate() con prompt especializado
    → parsear JSON response
    → QualityAuditRepository.upsert() con campos enriquecidos
```

**Relación con pasos anteriores:**
- Depende de Paso 5 (`QualityAuditRepository`) — lee y escribe en `quality_audits`
- Depende de Paso 4 (`BusinessRuleExtractor`) — comparte el `BedrockClient` y el patrón de prompt
- Extiende Paso 6 (pipeline) — puede ejecutarse como paso opcional post-pipeline o como job independiente

**Criterio de éxito:** Dado un microservicio ya analizado, `description` y `external_relations` de sus unidades de dominio quedan poblados con texto en lenguaje natural consultable.

---

### Paso 9 — Comparación QA vs DEV (1 día)

**Archivo nuevo:** `src/core/analyzers/diff_analyzer.py`

Compara dos snapshots de `quality_audits` del mismo microservicio (uno de QA, uno de DEV):
- Funciones nuevas / eliminadas
- Cambios en `risk_level` o `overall_score`
- Cambios en dependencias (`external_relations`)
- Cambios en `description` generado por LLM (detecta cambios de comportamiento)

Nuevo endpoint: `POST /api/v1/compare` con `{ "base_env": "QA", "target_env": "DEV", "microservice": "ACS" }`

**Relación con pasos anteriores:**
- Depende de Paso 7 — el diff es más rico si `description` y `external_relations` están enriquecidos
- Depende de Paso 5 — consulta `quality_audits` directamente

---



---

## Fase 3 — Observabilidad y escala (post-abril)

- Análisis incremental: solo re-analizar archivos modificados desde último commit
- Métricas Prometheus: tiempo de análisis por microservicio, unidades HIGH risk detectadas
- Endpoint de consulta en lenguaje natural: `GET /api/v1/query?q="¿qué valida ACS antes de procesar un pago?"`
- Versionamiento de auditorías: comparar estado del código entre sprints
- **Scoring por función individual:** actualmente LOC y complejidad se calculan a nivel de archivo
  y se distribuyen equitativamente entre todas las funciones. Mejorar los analizadores para
  calcular métricas por función individual producirá scores más precisos.

---

## Criterio de Overall Score

El `overall_score` (0-100) se calcula en `logical_unit_extractor.py` con tres componentes:

| Componente | Peso | Cómo se calcula |
|------------|------|------------------|
| **Atomicity** | 40% | Base 1.0 — penaliza si LOC > 30 (-0.3) o complexity > 10 (-0.3) |
| **Transparency** | 40% | Base 1.0 — penaliza si tiene database_calls (-0.4) o imports de infra (-0.3) |
| **Complexity inverse** | 20% | `1.0 / max(complexity, 1)` — a mayor complejidad, menor aporte |

```
overall_score = (atomicity × 0.4 + transparency × 0.4 + (1/complexity) × 0.2) × 100
```

**Ejemplos reales:**

| Función | LOC | Complexity | DB calls | Score | Razón |
|---------|-----|-----------|----------|-------|-------|
| `get_settings` | ~5 | 1 | No | 100.0 | Todo perfecto |
| `FraudPredictor.predict` | ~20 | 5 | No | 84.0 | Buena atomicidad, sin infra |
| `StageContextManager` | ~40 | 12 | Sí | 41.7 | LOC alto + DB + complexity |
| `TransactionEnricher` | ~60 | 18 | Sí | 29.2 | Todo penalizado |

**Risk level** se deriva de la complejidad ciclomática (independiente del score):
- `complexity > 15` → HIGH
- `complexity 10–15` → MEDIUM
- `complexity < 10` → LOW

> **Limitación conocida (Fase 1):** LOC y complejidad se calculan a nivel de archivo y se
> distribuyen equitativamente entre todas las funciones del archivo. Si un archivo tiene 10
> funciones, todas reciben el mismo score aunque algunas sean simples y otras complejas.
> La mejora a scoring por función individual está planificada para Fase 3.

---

## NFRs del sistema (según INI Code-Agent V1)

| Métrica | Umbral | Acción si se supera |
|---|---|---|
| Complejidad ciclomática | Ideal 1-10, máximo 15 | Marcar `risk_level=HIGH` |
| LOC por función | Máximo 30 líneas | Flag en `compliance` |
| LOC por microservicio | 500-2000 líneas | Alerta en `description.business_value` |
| Niveles de indentación | Máximo 2 | Flag en `compliance` |
| Dependencias inyectadas | Máximo 3 | Flag multicapa |
| Cobertura de tests | > 80% obligatorio | `risk_level=HIGH` si < 80% |

---

## Preguntas abiertas (bloquean implementación)

| # | Pregunta | Bloquea |
|---|---|---|
| 1 | ¿El schema de Stefano está en producción o es el DDL del documento? | Paso 5 |
| 2 | ¿Acceso de lectura a Bitbucket de ACS, Orquestador, PSE, OSE, Transaction Key? | Deadline 14/3 |
| 3 | ¿AWS Bedrock habilitado con `anthropic.claude-3-5-sonnet-20241022-v2:0` en la cuenta? | Paso 4 |
| 4 | ¿El servicio corre como API centralizada o como script en cada pipeline? | Arquitectura general |

---

## Orden de ejecución recomendado

```
Semana 1:  Paso 1 (bugs) → Paso 2 (modelos) → Paso 3 (LogicalUnitExtractor)     ✔ COMPLETADO
Semana 2:  Paso 4 (BusinessRuleExtractor) → Paso 5 (Postgres)                    ✔ COMPLETADO
Semana 3:  Paso 6 (pipeline completo) → validar con microservicio real            ✔ COMPLETADO
Semana 4:  Paso 7 (fix JS/TS) → Paso 8 (LLM enricher)
           Razón: cobertura completa de lenguajes antes de gastar tokens de Bedrock
Semana 5:  Paso 9 (diff QA vs DEV)
```

---

*Documento generado: 2025*  
*Basado en: INI Code-Agent V1, Acta de Proyecto, Diagnóstico de Calidad, Estructura BD (Stefano), análisis de código doc-as-codePRO v3.0*
