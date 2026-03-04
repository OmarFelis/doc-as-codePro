"""Modelos de dominio usando Pydantic."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LanguageType(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    CSHARP = "csharp"
    CPP = "cpp"
    OTHER = "other"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComponentType(str, Enum):
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    UTILITY = "utility"
    INTEGRATION = "integration"


class TipoUnidad(str, Enum):
    CLASE = "CLASE"
    FUNCION = "FUNCION"
    INTERFAZ = "INTERFAZ"
    ENUM = "ENUM"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ArchitectureLayer(str, Enum):
    ADAPTADOR = "adaptador"
    DOMINIO = "dominio"
    INFRAESTRUCTURA = "infraestructura"


class FileAnalysis(BaseModel):
    """Análisis de un archivo individual."""
    file_path: str = Field(..., description="Ruta del archivo")
    language: LanguageType = Field(..., description="Lenguaje del archivo")
    lines: int = Field(default=0, description="Número de líneas")
    classes: List[str] = Field(default_factory=list, description="Clases encontradas")
    functions: List[str] = Field(default_factory=list, description="Funciones encontradas")
    imports: List[str] = Field(default_factory=list, description="Imports")
    endpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Endpoints API")
    database_calls: List[str] = Field(default_factory=list, description="Llamadas a BD")
    complexity: int = Field(default=0, description="Complejidad ciclomática")
    func_complexity: Dict[str, int] = Field(default_factory=dict, description="Complejidad por función")
    error: Optional[str] = Field(default=None, description="Error durante el análisis")

    model_config = ConfigDict(use_enum_values=True)


class ProjectAnalysis(BaseModel):
    """Análisis completo del proyecto."""
    repository_name: str = Field(..., description="Nombre del repositorio")
    repository_owner: str = Field(..., description="Owner del repositorio")
    branch: str = Field(default="main", description="Rama analizada")
    commit_hash: Optional[str] = Field(default=None, description="Hash del commit")
    files: List[FileAnalysis] = Field(default_factory=list, description="Archivos analizados")
    total_files: int = Field(default=0, description="Total de archivos")
    total_lines: int = Field(default=0, description="Total de líneas")
    languages: List[LanguageType] = Field(default_factory=list, description="Lenguajes detectados")
    components: Dict[ComponentType, List[str]] = Field(default_factory=dict)
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(use_enum_values=True)


class ArchivoFuente(BaseModel):
    id: Optional[str] = None
    activo_id: str
    aplicacion_id: Optional[str] = None
    nombre: str
    ruta_archivo: str
    proposito: Optional[str] = None
    capa: Optional[str] = None
    lenguaje: Optional[str] = None
    total_funciones: int = 0
    total_clases: int = 0
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    operaciones_bd: List[str] = Field(default_factory=list)
    llamadas_externas: List[str] = Field(default_factory=list)
    complejidad_ciclomatica: int = 0
    lineas_codigo: int = 0
    resumen: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    build_number: Optional[str] = None
    commit_hash: Optional[str] = None
    escaneado_en: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class UnidadLogica(BaseModel):
    id: Optional[str] = None
    archivo_id: Optional[str] = None
    parent_id: Optional[str] = None
    activo_id: str
    nombre: str
    tipo: TipoUnidad
    capa: Optional[str] = None
    proposito: Optional[str] = None
    complejidad: int = 0
    lineas_codigo: int = 0
    accede_bd: bool = False
    llamadas_externas: List[str] = Field(default_factory=list)
    docstring: bool = False
    resumen: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    overall_score: Optional[float] = None
    compliance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class Escaneo(BaseModel):
    id: Optional[str] = None
    activo_id: str
    aplicacion_id: Optional[str] = None
    build_number: Optional[str] = None
    commit_hash: Optional[str] = None
    escaneado_en: Optional[datetime] = None
    generado_por: str = "code-agent-v1"
    score_general: Optional[float] = None
    nivel_riesgo: Optional[RiskLevel] = None
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

    model_config = ConfigDict(use_enum_values=True)


class BusinessRule(BaseModel):
    description: str
    linked_application: str
    linked_component: str
    linked_unit_name: str
