"""Modelos de dominio usando Pydantic."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class LanguageType(str, Enum):
    """Tipos de lenguajes soportados."""
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
    """Estados del análisis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComponentType(str, Enum):
    """Tipos de componentes."""
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    UTILITY = "utility"
    INTEGRATION = "integration"


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
    
    components: Dict[ComponentType, List[str]] = Field(
        default_factory=dict,
        description="Componentes clasificados"
    )
    
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, description="Estado")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    model_config = ConfigDict(use_enum_values=True)


class DocumentationSection(BaseModel):
    """Sección de documentación."""
    
    title: str = Field(..., description="Título de la sección")
    content: str = Field(..., description="Contenido")
    order: int = Field(..., description="Orden de la sección")


class Documentation(BaseModel):
    """Documentación generada."""
    
    analysis_id: str = Field(..., description="ID del análisis")
    repository_name: str = Field(..., description="Nombre del repositorio")
    
    sections: List[DocumentationSection] = Field(
        default_factory=list,
        description="Secciones de documentación"
    )
    
    diagrams: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Diagramas generados"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata adicional"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(use_enum_values=True)


class PublishRequest(BaseModel):
    """Request para publicar documentación."""
    
    documentation_id: str = Field(..., description="ID de la documentación")
    confluence_page_id: str = Field(..., description="ID de página de Confluence")
    confluence_space_key: str = Field(..., description="Space key de Confluence")
    create_version: bool = Field(default=True, description="Crear versión nueva")


class PublishResponse(BaseModel):
    """Response de publicación."""
    
    success: bool = Field(..., description="Éxito de la operación")
    page_id: str = Field(..., description="ID de la página creada/actualizada")
    page_url: str = Field(..., description="URL de la página")
    message: str = Field(..., description="Mensaje")
