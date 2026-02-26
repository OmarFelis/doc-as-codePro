"""Pydantic schemas for API responses."""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional


class AnalysisStatus(str, Enum):
    """Status of analysis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedDocs(BaseModel):
    """Generated documentation URLs."""
    
    readme: Optional[str] = Field(default=None, description="Generated README URL")
    api_docs: Optional[str] = Field(default=None, description="API documentation URL")
    confluence_url: Optional[str] = Field(default=None, description="Confluence page URL")


class AnalysisResponse(BaseModel):
    """Response for analysis request."""
    
    analysis_id: str = Field(..., description="Unique analysis identifier")
    status: AnalysisStatus = Field(..., description="Current status")
    repository_name: Optional[str] = Field(default=None, description="Repository name")
    total_files: Optional[int] = Field(default=None, description="Total files analyzed")
    total_lines: Optional[int] = Field(default=None, description="Total lines of code")
    languages: Optional[List[str]] = Field(default=None, description="Detected languages")
    components: Optional[Dict[str, int]] = Field(
        default=None,
        description="Components by type"
    )
    generated_docs: Optional[GeneratedDocs] = Field(
        default=None,
        description="Generated documentation"
    )
    progress: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Progress percentage (0-100)"
    )
    current_step: Optional[str] = Field(default=None, description="Current processing step")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    quality_summary: Optional[Dict] = Field(default=None, description="Quality summary from pipeline")
    created_at: datetime = Field(..., description="Analysis creation time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "repository_name": "my-awesome-project",
                "total_files": 150,
                "total_lines": 50000,
                "languages": ["python", "java"],
                "components": {
                    "api": 15,
                    "database": 10,
                    "utility": 125
                },
                "created_at": "2025-02-05T10:00:00Z",
                "completed_at": "2025-02-05T10:04:30Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Dependencies status"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "3.0.0",
                "dependencies": {
                    "redis": "connected",
                    "llm": "available"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Analysis failed",
               "detail": "Unable to parse Java file: syntax error at line 42",
                "request_id": "req_123456"
            }
        }
