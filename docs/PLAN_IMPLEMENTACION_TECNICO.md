# Plan de Implementación Técnico — Migración a Schema `code` + `quality`

> **Estado:** Pendiente de ejecución  
> **Objetivo:** Reemplazar la tabla única `quality_audits` por el modelo de datos definitivo con separación físico/lógico.  
> **Prerequisito:** El DBA debe crear los schemas `code` y `quality` en la BD de A-ONE (o confirmar nombre de BD).

---

## Contexto: Qué tenemos vs qué necesitamos

### Estado actual del código

El pipeline actual produce esta jerarquía en una sola tabla `quality_audits`:

```
quality_audits (entity_type=MICROSERVICE)  ← mvpRBAMOTORBACK
    └── quality_audits (entity_type=LOGIC_UNIT)  ← AREQAdapter.adapt
    └── quality_audits (entity_type=LOGIC_UNIT)  ← AREQAdapter._map_currency
    └── ...144 funciones al mismo nivel
```

**Problemas:**
- Los archivos físicos no existen como entidades (no hay registro para `areq_adapter.py`)
- Las clases no existen como entidades (no hay registro para `AREQAdapter`)
- No hay jerarquía: archivo → clase → función
- Una sola tabla mezcla microservicio, archivos y funciones

### Estado objetivo

```
infra.activos (Lambda/ECS — existente, no se toca)
    └── code.unidades_fisicas  ← areq_adapter.py
            └── code.unidades_logicas (tipo=CLASE)    ← AREQAdapter
                    └── code.unidades_logicas (tipo=FUNCION) ← adapt
                    └── code.unidades_logicas (tipo=FUNCION) ← _map_currency
    └── code.unidades_fisicas  ← pasarela_adapter.py
            └── ...
quality.escaneos  ← 1 snapshot por microservicio por ejecución
```

---

## Archivos a modificar (ninguno nuevo)

| Archivo | Acción |
|---|---|
| `src/db/models.py` | Reemplazar `QualityAuditORM` por 3 tablas ORM |
| `src/models/domain.py` | Reemplazar `QualityAudit`/`EntityType` por 3 modelos Pydantic |
| `src/db/repository.py` | Reemplazar por 3 repositorios (uno por tabla) |
| `src/core/analyzers/logical_unit_extractor.py` | Producir `UnidadFisica` + `List[UnidadLogica]` |
| `src/core/analyzers/pipeline.py` | Orquestar nuevo flujo |
| `src/core/analyzers/business_rule_extractor.py` | Adaptar firma para recibir `List[UnidadLogica]` |
| `src/db/session.py` | Agregar creación de schemas `code` y `quality` |

---

## Paso 1 — `src/db/models.py`

Eliminar `QualityAuditORM`. Crear 3 tablas ORM.

```python
# Tabla: code.unidades_fisicas
class UnidadFisicaORM(Base):
    __tablename__ = "unidades_fisicas"
    __table_args__ = {"schema": "code"}

    id               = Column(UUID, primary_key=True, default=uuid.uuid4)
    activo_id        = Column(UUID, nullable=False)          # FK lógica → infra.activos
    aplicacion_id    = Column(UUID, nullable=True)
    nombre_archivo   = Column(String(255), nullable=False)   # "areq_adapter.py"
    ruta_relativa    = Column(Text, nullable=False)           # "./app/adapters/areq_adapter.py"
    extension        = Column(String(10))                    # ".py"
    lineas_codigo_total = Column(Integer)
    imports_totales  = Column(Integer, default=0)
    metadata_archivo = Column(JSONB, default=dict)
    build_number     = Column(String(20))
    commit_hash      = Column(String(40))
    escaneado_en     = Column(DateTime(timezone=True), default=now_utc)
    activo           = Column(Boolean, default=True)

# Tabla: code.unidades_logicas
class UnidadLogicaORM(Base):
    __tablename__ = "unidades_logicas"
    __table_args__ = {"schema": "code"}

    id                      = Column(UUID, primary_key=True, default=uuid.uuid4)
    activo_id               = Column(UUID, nullable=False)   # desnormalizado para queries rápidas
    fisica_id               = Column(UUID, ForeignKey("code.unidades_fisicas.id", ondelete="CASCADE"), nullable=False)
    parent_id               = Column(UUID, ForeignKey("code.unidades_logicas.id"), nullable=True)  # clase padre
    nombre                  = Column(String(255), nullable=False)  # "adapt" (sin prefijo de clase)
    tipo_unidad             = Column(String(20), nullable=False)   # CLASE | FUNCION | METODO
    capa                    = Column(String(20))                   # adaptador | dominio | infraestructura
    proposito               = Column(String(30))                   # Controller | Data Access | Utility...
    complejidad_ciclomatica = Column(Integer)
    lineas_codigo_utiles    = Column(Integer)
    endpoints_detectados    = Column(Integer, default=0)
    operaciones_bd          = Column(Integer, default=0)
    llamadas_externas       = Column(Integer, default=0)
    risk_level              = Column(String(10), nullable=False, default="LOW")
    overall_score           = Column(Float)
    resumen_llm             = Column(Text)
    metadata                = Column(JSONB, default=dict)
    compliance              = Column(JSONB, default=dict)
    escaneado_en            = Column(DateTime(timezone=True), default=now_utc)

# Tabla: quality.escaneos
class EscaneoORM(Base):
    __tablename__ = "escaneos"
    __table_args__ = {"schema": "quality"}

    id               = Column(UUID, primary_key=True, default=uuid.uuid4)
    activo_id        = Column(UUID, nullable=False)
    aplicacion_id    = Column(UUID, nullable=True)
    build_number     = Column(String(20))
    commit_hash      = Column(String(40))
    escaneado_en     = Column(DateTime(timezone=True), default=now_utc)
    generado_por     = Column(String(100))
    score_general    = Column(Float)
    nivel_riesgo     = Column(String(10), nullable=False)    # LOW | MEDIUM | HIGH
    archivos_total   = Column(Integer, default=0)
    funciones_total  = Column(Integer, default=0)
    clases_total     = Column(Integer, default=0)
    dominios_negocio = Column(ARRAY(Text))
    metricas         = Column(JSONB, default=dict)
    arquitectura     = Column(JSONB, default=dict)
    seguridad        = Column(JSONB, default=dict)
    rendimiento      = Column(JSONB, default=dict)
    negocio          = Column(JSONB, default=dict)
    cumplimiento     = Column(JSONB, default=dict)
```

---

## Paso 2 — `src/models/domain.py`

Eliminar `QualityAudit`, `EntityType`. Agregar 3 modelos Pydantic.

```python
class UnidadFisica(BaseModel):
    id: Optional[str] = None
    activo_id: str
    aplicacion_id: Optional[str] = None
    nombre_archivo: str
    ruta_relativa: str
    extension: Optional[str] = None
    lineas_codigo_total: Optional[int] = None
    imports_totales: int = 0
    metadata_archivo: Dict[str, Any] = Field(default_factory=dict)
    build_number: Optional[str] = None
    commit_hash: Optional[str] = None
    activo: bool = True

class UnidadLogica(BaseModel):
    id: Optional[str] = None
    activo_id: str
    fisica_id: str
    parent_id: Optional[str] = None          # UUID de la clase padre (None si es raíz)
    nombre: str                               # "adapt" (sin prefijo de clase)
    tipo_unidad: str                          # CLASE | FUNCION | METODO
    capa: Optional[str] = None               # adaptador | dominio | infraestructura
    proposito: Optional[str] = None
    complejidad_ciclomatica: Optional[int] = None
    lineas_codigo_utiles: Optional[int] = None
    endpoints_detectados: int = 0
    operaciones_bd: int = 0
    llamadas_externas: int = 0
    risk_level: str = "LOW"
    overall_score: Optional[float] = None
    resumen_llm: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    compliance: Dict[str, Any] = Field(default_factory=dict)

class Escaneo(BaseModel):
    id: Optional[str] = None
    activo_id: str
    aplicacion_id: Optional[str] = None
    build_number: Optional[str] = None
    commit_hash: Optional[str] = None
    generado_por: Optional[str] = "code-agent-v1"
    score_general: Optional[float] = None
    nivel_riesgo: str                         # LOW | MEDIUM | HIGH
    archivos_total: int = 0
    funciones_total: int = 0
    clases_total: int = 0
    dominios_negocio: List[str] = Field(default_factory=list)
    metricas: Dict[str, Any] = Field(default_factory=dict)
    arquitectura: Dict[str, Any] = Field(default_factory=dict)
    seguridad: Dict[str, Any] = Field(default_factory=dict)
    rendimiento: Dict[str, Any] = Field(default_factory=dict)
    negocio: Dict[str, Any] = Field(default_factory=dict)
    cumplimiento: Dict[str, Any] = Field(default_factory=dict)
```

**Modelos que se conservan sin cambios:** `FileAnalysis`, `ProjectAnalysis`, `BusinessRule`, `LanguageType`, `ArchitectureLayer`, `RiskLevel`.

---

## Paso 3 — `src/db/repository.py`

Reemplazar el repositorio único por 3 funciones por tabla. Interfaz mínima:

```python
# Unidades físicas
def insert_fisica(session, unidad: UnidadFisica) -> UnidadFisica
def delete_fisicas_by_activo(session, activo_id: str)   # para re-escaneos futuros

# Unidades lógicas
def insert_logica(session, unidad: UnidadLogica) -> UnidadLogica
def insert_logicas(session, unidades: List[UnidadLogica]) -> List[UnidadLogica]

# Escaneos
def insert_escaneo(session, escaneo: Escaneo) -> Escaneo
def get_escaneos_by_activo(session, activo_id: str) -> List[Escaneo]
```

> No hay upsert por nombre en el nuevo modelo. Cada escaneo es un INSERT limpio. Los re-escaneos hacen DELETE de `unidades_fisicas` (cascade elimina lógicas) + INSERT masivo.

---

## Paso 4 — `src/core/analyzers/logical_unit_extractor.py`

**Cambio de firma:** de `extract(file_analysis, parent_id) → List[QualityAudit]`  
a `extract(file_analysis, activo_id) → tuple[UnidadFisica, List[UnidadLogica]]`

**Lógica de jerarquía que debe producir:**

```
FileAnalysis (areq_adapter.py)
    → UnidadFisica
        → UnidadLogica(tipo=CLASE,   nombre="AREQAdapter",    parent_id=None)
        → UnidadLogica(tipo=FUNCION, nombre="adapt",          parent_id=uuid_clase)
        → UnidadLogica(tipo=FUNCION, nombre="_map_currency",  parent_id=uuid_clase)
```

**Cómo detectar clases vs funciones:**  
El `python_analyzer.py` ya produce `file_analysis.classes = ["AREQAdapter"]` y `file_analysis.functions = ["AREQAdapter.adapt", "AREQAdapter._map_currency", "standalone_func"]`.

El extractor debe:
1. Crear `UnidadLogica(tipo=CLASE)` por cada elemento en `file_analysis.classes`
2. Para cada función en `file_analysis.functions`:
   - Si tiene formato `Clase.metodo` → `tipo=FUNCION`, `parent_id=uuid_de_esa_clase`
   - Si no tiene prefijo → `tipo=FUNCION`, `parent_id=None` (función standalone)

**Scoring:** la lógica de `_calc_atomicity`, `_calc_transparency`, `_calc_overall`, `_calc_risk` se conserva igual, se mueve a `UnidadLogica.overall_score` y `UnidadLogica.risk_level`.

---

## Paso 5 — `src/core/analyzers/pipeline.py`

Nuevo flujo:

```python
async def run(project_path, activo_id, microservice_name, session, llm_client=None) -> dict:

    # 1. Analizar archivos
    project = ProjectAnalyzerService().analyze_project(project_path, microservice_name)

    # 2. Por cada archivo → insertar UnidadFisica + UnidadLogicas
    all_logicas = []
    for file_analysis in project.files:
        fisica, logicas = logical_unit_extractor.extract(file_analysis, activo_id)
        saved_fisica = repository.insert_fisica(session, fisica)
        # asignar fisica_id real a las logicas
        for u in logicas:
            u.fisica_id = saved_fisica.id
        saved_logicas = repository.insert_logicas(session, logicas)
        all_logicas.extend(saved_logicas)

        # 3. LLM: reglas de negocio + enriquecimiento (solo capa dominio)
        if llm_client:
            ...  # igual que antes, adaptado a UnidadLogica

    session.commit()

    # 4. Calcular métricas y persistir Escaneo
    scores = [u.overall_score for u in all_logicas if u.overall_score]
    high_count = sum(1 for u in all_logicas if u.risk_level == "HIGH")
    clases = [u for u in all_logicas if u.tipo_unidad == "CLASE"]
    funciones = [u for u in all_logicas if u.tipo_unidad == "FUNCION"]

    escaneo = Escaneo(
        activo_id=activo_id,
        score_general=round(sum(scores)/len(scores), 2) if scores else None,
        nivel_riesgo="HIGH" if high_count > 0 else ("MEDIUM" if any(u.risk_level=="MEDIUM" for u in all_logicas) else "LOW"),
        archivos_total=project.total_files,
        funciones_total=len(funciones),
        clases_total=len(clases),
        metricas={"total_lines": project.total_lines, "languages": project.languages},
    )
    saved_escaneo = repository.insert_escaneo(session, escaneo)
    session.commit()

    return {
        "escaneo_id": saved_escaneo.id,
        "activo_id": activo_id,
        "score_general": escaneo.score_general,
        "nivel_riesgo": escaneo.nivel_riesgo,
        "archivos_total": escaneo.archivos_total,
        "clases_total": escaneo.clases_total,
        "funciones_total": escaneo.funciones_total,
        "high_risk_units": high_count,
    }
```

**Cambio en la firma de `run`:** se agrega `activo_id: str` como parámetro obligatorio. El llamador (CLI o API) debe resolver el UUID del activo en `infra.activos` antes de llamar al pipeline.

---

## Paso 6 — `src/db/session.py`

Agregar creación de schemas antes de `create_all`:

```python
from sqlalchemy import text

def init_db(url: str | None = None):
    engine = get_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS code"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS quality"))
        conn.commit()
    Base.metadata.create_all(engine)
```

---

## Paso 7 — `src/core/analyzers/business_rule_extractor.py`

Cambio mínimo: reemplazar `List[QualityAudit]` por `List[UnidadLogica]` en la firma.

```python
# Antes
def _is_dominio(audit: QualityAudit) -> bool:
    return audit.metrics.get("architecture_layer") == ArchitectureLayer.DOMINIO.value

# Después
def _is_dominio(unidad: UnidadLogica) -> bool:
    return unidad.capa == ArchitectureLayer.DOMINIO.value
```

---

## Output esperado después de la migración

```
ESCANEO PERSISTIDO
  escaneo_id     : uuid
  activo_id      : uuid (de infra.activos)
  score_general  : 66.4
  nivel_riesgo   : HIGH
  archivos_total : 72
  clases_total   : 28
  funciones_total: 116

UNIDADES FISICAS (72 registros en code.unidades_fisicas)
  areq_adapter.py          → uuid-F1
  pasarela_adapter.py      → uuid-F2
  ...

UNIDADES LOGICAS (144+ registros en code.unidades_logicas)
  [CLASE]   AREQAdapter              fisica_id=uuid-F1  parent_id=null
  [FUNCION] adapt                    fisica_id=uuid-F1  parent_id=uuid-clase
  [FUNCION] _map_currency            fisica_id=uuid-F1  parent_id=uuid-clase
  ...
```

---

## Orden de ejecución

1. DBA crea schemas `code` y `quality` en la BD (o `init_db()` los crea automáticamente)
2. **Paso 1** — `models.py`
3. **Paso 2** — `domain.py`
4. **Paso 3** — `repository.py`
5. **Paso 4** — `logical_unit_extractor.py`
6. **Paso 5** — `pipeline.py`
7. **Paso 6** — `session.py`
8. **Paso 7** — `business_rule_extractor.py`

> Los pasos 1-3 son prerequisito de los demás. Los pasos 4-7 son independientes entre sí una vez que 1-3 están listos.

---

## Lo que NO cambia

| Componente | Razón |
|---|---|
| `python_analyzer.py` | Ya produce `classes` y `functions` separados correctamente |
| `java_analyzer.py`, `javascript_analyzer.py`, `typescript_analyzer.py` | Misma interfaz `FileAnalysis` |
| `project_analyzer.py`, `factory.py`, `base.py` | Sin cambios |
| `llm/bedrock_client.py`, `llm/openai_client.py` | Sin cambios |
| `api/routes/`, `api/schemas/` | Se actualizan los tipos de respuesta pero la estructura de endpoints no cambia |
| `infra.activos` (BD A-ONE) | Sin cambios — FK lógica, no enforced |

---

*Generado: 2025 — doc-as-codePRO — Alignet Ecosistema de Pagos Digitales*
