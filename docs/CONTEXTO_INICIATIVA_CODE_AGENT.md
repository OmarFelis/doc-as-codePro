# CONTEXTO: Iniciativa Code-Agent V1 — Para el Agente que Continúa

> **Lee este documento primero.** Resume toda la conversación de análisis realizada y define exactamente qué construir y por qué.

---

## 1. Qué es este proyecto y de dónde viene

Este repositorio (`doc-as-codePRO`) es la **versión 3.0 refactorizada** de un piloto anterior (`ci-scripts/`) que generaba documentación técnica automáticamente usando OpenAI + Confluence.

El piloto funcionaba pero era un script monolítico sin arquitectura. Este proyecto lo reescribió con:
- FastAPI como API REST
- Analizadores reales por lenguaje (Python AST, Java con `javalang`, JS con `esprima`, TS con `tree-sitter`)
- Configuración centralizada con Pydantic Settings
- Logging estructurado con structlog
- Tests unitarios con pytest

**La Fase 1 está completa.** La Fase 2 está parcialmente implementada (ver sección 4).

---

## 2. La iniciativa real: Code-Agent V1

El objetivo **no es solo generar documentación en Confluence**. Eso era el piloto. La iniciativa aprobada (INI: Code-Agent V1.0, sponsor: Javier Draxl) define algo más ambicioso:

> Construir una **fuente de verdad técnica estructurada** donde cada función, flujo y regla de negocio de los microservicios sea un activo independiente en una base de datos, vinculado entre sí y consultable en lenguaje natural.

### El problema que resuelve
- Los microservicios críticos (ACS, Orquestador, PSE, OSE, Transaction Key) no tienen visibilidad interna
- Un PO o analista debe leer documentos extensos en Confluence para entender el impacto de un cambio
- El crecimiento de código generado por IA será exponencial — sin mapeo en tiempo real, la arquitectura se vuelve ingobernable

### Lo que debe hacer el sistema (según Acta de Proyecto)
1. **Separar unidades lógicas** dentro de cada microservicio: funciones, flujos, reglas de negocio, entradas/salidas
2. **Diagnosticar calidad** de cada unidad: atomicidad, transparencia, complejidad, dependencias externas
3. **Asignar score de riesgo** (alto/medio/bajo) por unidad y por microservicio
4. **Extraer reglas de negocio** en lenguaje natural con trazabilidad a componente y función
5. **Clasificar capas arquitectónicas**: Adaptador (entrada) / Dominio (lógica) / Infraestructura (salida)
6. **Persistir todo en Postgres** — Confluence es solo una vista opcional, no el destino principal
7. **Mapear dependencias externas** (AWS: S3, SQS, DynamoDB, Lambda, etc.)

### Cronograma crítico
- **14 de marzo**: 100% de mapeo de ACS, Orquestador, PSE, OSE y Transaction Key
- **15 de abril**: Comparación de diferencias arquitectónicas entre QA y DEV

---

## 3. Estado actual del código en este repo

### Lo que funciona ✅
- `src/api/main.py` — FastAPI app con CORS y Prometheus
- `src/api/routes/analysis.py` — POST `/api/v1/analyze` y GET `/api/v1/analysis/{id}` (async background tasks)
- `src/core/analyzers/python_analyzer.py` — AST real, extrae clases, funciones, imports, endpoints, complejidad
- `src/core/analyzers/java_analyzer.py` — `javalang` real, detecta Spring endpoints, JPA entities, complejidad
- `src/core/analyzers/javascript_analyzer.py` — `esprima`, detecta funciones, clases, Express routes
- `src/core/analyzers/typescript_analyzer.py` — `tree-sitter`, detecta tipos, interfaces, decorators
- `src/core/analyzers/factory.py` — Factory pattern, selecciona analizador por extensión
- `src/core/analyzers/project_analyzer.py` — Orquesta análisis paralelo de proyecto completo
- `src/core/llm/bedrock_client.py` — Cliente AWS Bedrock (Claude 3.5 Sonnet)
- `src/core/llm/openai_client.py` — Cliente OpenAI (GPT-4)
- `src/core/generators/readme_generator.py` — Genera README con LLM, fallback a template
- `src/config/settings.py` — Configuración Pydantic Settings con validación
- `src/models/domain.py` — Modelos base: FileAnalysis, ProjectAnalysis, Documentation
- `tests/unit/` — Tests para los 4 analizadores

### Bugs conocidos ⚠️
- `OpenAIClient` referencia `settings.openai` que **no existe** en la clase `Settings` (solo hay `bedrock`)
- `BedrockClient` accede a `settings.bedrock.access_key_id` pero el campo se llama `aws_access_key_id`
- `@app.on_event("startup/shutdown")` está **deprecado** en FastAPI moderno — usar `lifespan` context manager
- `allow_origins=["*"]` en CORS hardcodeado con TODO pendiente
- El route de análisis usa `dict` en memoria (`_analyses: dict`) — se pierde al reiniciar

### Lo que está como stub vacío ❌
- `src/integrations/` — carpeta con solo `__init__.py`, Confluence y Jira Assets no implementados
- `src/cache/` — carpeta con solo `__init__.py`, Redis no implementado
- `repository_url` en el endpoint lanza 501 — solo funciona `local_path`
- No hay modelos SQLAlchemy ni migrations Alembic (las dependencias están en `pyproject.toml` pero sin uso)

### Lo que el piloto tiene y este repo no ❌
El piloto (`ci-scripts/` en el repo `omarpruebas2-doc-as-code-service-pre-prod-f48836a0475b`) tiene lógica funcional que hay que migrar:
- `post_to_confluence.py` — publica páginas hijas con versionado, limpieza de versiones antiguas
- `jira_assets_single.py` — consulta Jira Assets por nombre de repo, extrae Page ID y Space Key

---

## 4. La brecha: lo que ninguno de los dos proyectos tiene

Esto es lo que hay que construir desde cero para cumplir la iniciativa:

### 4.1 Modelo de dominio extendido
El `domain.py` actual modela `FileAnalysis` y `ProjectAnalysis` pero no tiene los tipos que pide el Acta:

```python
# Tipos que faltan en domain.py
class LogicalUnitType(str, Enum):
    FLUJO = "UNIDAD_LOGICA_FLUJO"
    FUNCION = "UNIDAD_LOGICA_FUNCION"
    DETALLE = "UNIDAD_LOGICA_DETALLE"
    REGLA_NEGOCIO = "UNIDAD_LOGICA_REGLA_NEGOCIO"

class ArchitectureLayer(str, Enum):
    ADAPTADOR = "adaptador"    # Entrada — sin lógica de negocio
    DOMINIO = "dominio"        # Lógica pura, agnóstica de infraestructura
    INFRAESTRUCTURA = "infraestructura"  # Llamadas a BD o AWS

class RiskLevel(str, Enum):
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"

class LogicalUnit(BaseModel):
    id: str
    parent_file: str           # Archivo de origen
    name: str                  # Nombre de la función/clase
    type: LogicalUnitType
    layer: ArchitectureLayer
    loc: int                   # Líneas de código
    complexity: int            # Complejidad ciclomática
    atomicity_score: float     # 0-1: ¿hace una sola cosa?
    transparency_score: float  # 0-1: ¿es función pura?
    has_multi_layer_coupling: bool  # Flag de riesgo
    external_dependencies: List[str]  # AWS services, external APIs
    risk_level: RiskLevel
    risk_score: float          # 0-100

class BusinessRule(BaseModel):
    id: str
    description: str           # En lenguaje natural
    linked_application: str
    linked_component: str
    linked_unit_id: str        # FK a LogicalUnit

class QualityDiagnostic(BaseModel):
    unit_id: str
    atomicity: float
    transparency: float
    complexity_score: float
    maintainability: float
    overall_score: float
    risk_level: RiskLevel
    recommendations: List[str]
```

### 4.2 Extractor de unidades lógicas
Nuevo componente `src/core/analyzers/logical_unit_extractor.py` que:
- Recibe el `FileAnalysis` actual (ya tiene funciones, clases, complejidad)
- Clasifica cada función en su capa arquitectónica (detectando patrones de imports y nombres)
- Calcula atomicidad (¿la función hace más de una cosa?) y transparencia (¿tiene side effects?)
- Detecta dependencias AWS (boto3, S3, SQS, DynamoDB, Lambda en imports y llamadas)
- Produce `List[LogicalUnit]` con score de riesgo

### 4.3 Extractor de reglas de negocio
Nuevo componente `src/core/analyzers/business_rule_extractor.py` que:
- Recibe el código fuente de funciones clasificadas como capa DOMINIO
- Envía al LLM un prompt especializado para identificar validaciones y cálculos en lenguaje natural
- Produce `List[BusinessRule]` con trazabilidad completa

### 4.4 Schema de Postgres
Las dependencias ya están (`sqlalchemy`, `alembic`, `psycopg2`). Falta:
- `src/db/models.py` — tablas: `microservicio`, `unidad_logica`, `regla_negocio`, `diagnostico_calidad`
- `src/db/session.py` — configuración de conexión y session factory
- `alembic/` — migrations iniciales

**IMPORTANTE**: El schema debe alinearse con el diseño de Stefano (responsable de BD en el equipo). Confirmar antes de implementar.

### 4.5 Integraciones (migrar del piloto)
- `src/integrations/confluence.py` — portar lógica de `post_to_confluence.py`
- `src/integrations/jira_assets.py` — portar lógica de `jira_assets_single.py`

---

## 5. Arquitectura objetivo

```
POST /api/v1/analyze
        │
        ▼
ProjectAnalyzerService          ← ya existe
        │
        ├── FileAnalysis[]       ← ya existe (Python, Java, JS, TS)
        │
        ▼
LogicalUnitExtractor            ← construir
        │
        ├── LogicalUnit[]        ← con layer, scores, risk
        │
        ▼
BusinessRuleExtractor           ← construir (usa LLM)
        │
        ├── BusinessRule[]       ← en lenguaje natural
        │
        ▼
QualityDiagnosticService        ← construir
        │
        ├── QualityDiagnostic[] ← scores finales
        │
        ▼
┌──────────────────────────────────┐
│  PostgresRepository             │  ← construir (SQLAlchemy)
│  - microservicio                │
│  - unidad_logica                │
│  - regla_negocio                │
│  - diagnostico_calidad          │
└──────────────────────────────────┘
        │
        ▼ (opcional, secundario)
ConfluencePublisher              ← migrar del piloto
```

---

## 6. Orden de implementación recomendado

Dado el deadline del 14 de marzo para mapear ACS, Orquestador, PSE, OSE y Transaction Key:

**Paso 1 — Corregir bugs existentes** (1-2 horas)
- Fix `OpenAIClient`: agregar `openai` a `Settings` o usar variable de entorno directa
- Fix `BedrockClient`: corregir nombre de atributo `aws_access_key_id`
- Migrar `@app.on_event` a `lifespan`

**Paso 2 — Extender domain.py** (2-3 horas)
- Agregar `LogicalUnitType`, `ArchitectureLayer`, `RiskLevel`, `LogicalUnit`, `BusinessRule`, `QualityDiagnostic`

**Paso 3 — LogicalUnitExtractor** (1 día)
- Clasificación de capas por patrones de imports y nombres
- Cálculo de atomicidad y transparencia
- Detección de dependencias AWS
- Score de riesgo

**Paso 4 — BusinessRuleExtractor** (1 día)
- Prompt LLM especializado para dominio
- Extracción de validaciones y cálculos en lenguaje natural

**Paso 5 — Schema Postgres + SQLAlchemy** (1 día)
- Confirmar schema con Stefano primero
- Modelos SQLAlchemy + migration Alembic inicial

**Paso 6 — Migrar integraciones del piloto** (1 día)
- Confluence publisher
- Jira Assets client

**Paso 7 — Conectar todo en el pipeline** (1 día)
- Actualizar `ProjectAnalyzerService` para orquestar los nuevos extractores
- Actualizar response del API para incluir unidades lógicas y diagnóstico

---

## 7. Archivos de referencia importantes

### En este repo (doc-as-codePRO)
- `src/models/domain.py` — modelos base a extender
- `src/core/analyzers/base.py` — interfaz que deben seguir los nuevos extractores
- `src/core/analyzers/project_analyzer.py` — orquestador a actualizar
- `src/config/settings.py` — agregar config de Postgres y corregir OpenAI
- `pyproject.toml` — dependencias ya incluyen sqlalchemy, alembic, psycopg2, javalang

### En el repo del piloto (`omarpruebas2-doc-as-code-service-pre-prod-f48836a0475b`)
- `ci-scripts/post_to_confluence.py` — lógica de publicación a migrar
- `ci-scripts/jira_assets_single.py` — lógica de Assets a migrar
- `docs/Acta de proyecto.md` — definición completa de funcionalidades del agente
- `docs/🏛️ INI_ Code-Agent V1.md` — iniciativa estratégica, NFRs, métricas de calidad

### Métricas de calidad definidas en la INI (NFRs)
- Complejidad ciclomática ideal: 1-10. Si > 15 → marcar para refactorización
- LoC por microservicio: 500-2000
- Cobertura de tests: > 80% obligatorio
- Una Lambda = Una tarea (prohibidos "lambda-litos")

---

## 8. Preguntas abiertas antes de implementar

1. **¿Está disponible el schema de Postgres de Stefano?** — Bloquea el Paso 5
2. **¿El servicio corre como API centralizada o como script en cada pipeline?** — La arquitectura actual (FastAPI) asume centralizado, que es lo correcto según el Acta
3. **¿Se tiene acceso de lectura a los repos de ACS, Orquestador, PSE, OSE, Transaction Key?** — Necesario para el mapeo del 14 de marzo
4. **¿AWS Bedrock está habilitado en la cuenta?** — El `BedrockClient` usa `anthropic.claude-3-5-sonnet-20241022-v2:0`, confirmar disponibilidad en la región configurada

---

*Documento generado el: 2025*
*Basado en: análisis de código de ambos repos + Acta de Proyecto + INI Code-Agent V1*
*Próximo paso: confirmar schema de BD con Stefano y comenzar Paso 1 (fix bugs)*
