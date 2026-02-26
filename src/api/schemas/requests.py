"""Pydantic schemas for API requests."""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class AnalysisOptions(BaseModel):
    """Options for code analysis."""
    
    generate_docs: bool = Field(
        default=True,
        description="Generate documentation with AI"
    )
    publish_confluence: bool = Field(
        default=False,
        description="Publish results to Confluence"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Use cache for results"
    )
    max_file_size_kb: int = Field(
        default=500,
        description="Maximum file size to analyze in KB"
    )


class AnalysisRequest(BaseModel):
    """Request to analyze a code repository."""
    
    repository_url: Optional[HttpUrl] = Field(
        default=None,
        description="Git repository URL to analyze"
    )
    local_path: Optional[str] = Field(
        default=None,
        description="Local path to project directory"
    )
    branch: str = Field(
        default="main",
        description="Branch to analyze"
    )
    languages: Optional[List[str]] = Field(
        default=None,
        description="Languages to analyze (auto-detect if None)"
    )
    options: AnalysisOptions = Field(
        default_factory=AnalysisOptions,
        description="Analysis options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "local_path": "./my-project",
                "branch": "main",
                "languages": ["python", "java"],
                "options": {
                    "generate_docs": True,
                    "cache_enabled": True
                }
            }
        }
