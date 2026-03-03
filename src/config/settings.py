"""Configuración centralizada del servicio usando Pydantic Settings."""
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BedrockSettings(BaseSettings):
    """Configuración de AWS Bedrock."""
    
    region: str = Field(default="us-east-1", description="Región de AWS")
    model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        description="ID del modelo en Bedrock"
    )
    max_tokens: int = Field(default=200000, description="Límite de tokens")
    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Credenciales AWS (opcional, si no usa AWS CLI)
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS Access Key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS Secret Access Key")
    
    model_config = SettingsConfigDict(env_prefix="BEDROCK_")


class ConfluenceSettings(BaseSettings):
    """Configuración de Confluence."""
    
    base_url: Optional[str] = Field(default=None, description="URL base de Confluence")
    email: Optional[str] = Field(default=None, description="Email de usuario")
    api_token: Optional[str] = Field(default=None, description="Token API")
    verify_ssl: bool = Field(default=False, description="Verificar SSL")
    
    model_config = SettingsConfigDict(env_prefix="CONFLUENCE_")


class JiraSettings(BaseSettings):
    """Configuración de Jira Assets."""
    
    base_url: Optional[str] = Field(default=None, description="URL base de Jira")
    email: Optional[str] = Field(default=None, description="Email de usuario")
    api_token: Optional[str] = Field(default=None, description="Token API")
    workspace_id: str = Field(
        default="cb50f8bc-b8e8-4641-8301-f0096cbe8841",
        description="ID del workspace de Assets"
    )
    
    model_config = SettingsConfigDict(env_prefix="JIRA_")


class EraserSettings(BaseSettings):
    """Configuración de EraserAI."""
    
    api_key: Optional[str] = Field(default=None, description="API key de EraserAI")
    enabled: bool = Field(default=True, description="Habilitar generación de diagramas")
    
    model_config = SettingsConfigDict(env_prefix="ERASER_")


class RedisSettings(BaseSettings):
    """Configuración de Redis."""
    
    host: str = Field(default="localhost", description="Host de Redis")
    port: int = Field(default=6379, description="Puerto de Redis")
    db: int = Field(default=0, description="Base de datos")
    password: Optional[str] = Field(default=None, description="Password")
    ttl: int = Field(default=3600, description="TTL por defecto en segundos")
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")


class DatabaseSettings(BaseSettings):
    """Configuración de PostgreSQL."""
    
    host: str = Field(default="localhost", description="Host de PostgreSQL")
    port: int = Field(default=5432, description="Puerto")
    database: str = Field(default="docascode", description="Nombre de la BD")
    username: str = Field(default="postgres", description="Usuario")
    password: Optional[str] = Field(default=None, description="Password")
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    @property
    def url(self) -> str:
        """Genera URL de conexión."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class AnalyzerSettings(BaseSettings):
    """Configuración del analizador de código."""
    
    max_file_size_kb: int = Field(default=500, description="Tamaño máximo de archivo en KB")
    parallel_processing: bool = Field(default=True, description="Procesamiento paralelo")
    max_workers: int = Field(default=4, description="Número de workers")
    
    model_config = SettingsConfigDict(env_prefix="ANALYZER_")


class Settings(BaseSettings):
    """Configuración global del servicio."""
    
    # Información del servicio
    service_name: str = Field(default="doc-as-code-service", description="Nombre del servicio")
    version: str = Field(default="3.0.0", description="Versión")
    environment: str = Field(default="development", description="Entorno")
    debug: bool = Field(default=False, description="Modo debug")
    
    # Configuraciones de componentes
    bedrock: BedrockSettings = Field(default_factory=BedrockSettings)
    confluence: ConfluenceSettings = Field(default_factory=ConfluenceSettings)
    jira: JiraSettings = Field(default_factory=JiraSettings)
    eraser: EraserSettings = Field(default_factory=EraserSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    analyzer: AnalyzerSettings = Field(default_factory=AnalyzerSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_file_override=True,
        case_sensitive=False,
        extra="ignore"
    )


# Singleton de configuración
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Obtiene la instancia singleton de configuración."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
