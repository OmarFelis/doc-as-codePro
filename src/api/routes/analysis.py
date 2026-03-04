"""Analysis routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
from datetime import datetime
import uuid

from src.api.schemas.requests import AnalysisRequest
from src.api.schemas.responses import AnalysisResponse, AnalysisStatus
from src.core.analyzers import pipeline
from src.core.llm.bedrock_client import BedrockClient
from src.db.session import get_session
from src.utils.logging import get_logger

# Instancia compartida del cliente LLM
_llm_client = BedrockClient()

router = APIRouter()
logger = get_logger(__name__)

# In-memory storage for demo (will use Redis/DB in future phases)
_analyses: dict[str, AnalysisResponse] = {}


@router.post("/analyze", response_model=AnalysisResponse, status_code=202, tags=["Analysis"])
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start code analysis for a repository or local path.
    
    Returns immediately with analysis_id and status "pending".
    The actual analysis runs in the background.
    """
    # Validate request
    if not request.repository_url and not request.local_path:
        raise HTTPException(
            status_code=400,
            detail="Either repository_url or local_path must be provided"
        )
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Create initial response
    analysis = AnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    # Store in memory
    _analyses[analysis_id] = analysis
    
    # Schedule background task
    if request.local_path:
        background_tasks.add_task(
            _run_analysis,
            analysis_id,
            Path(request.local_path),
            request
        )
    
    else:
        raise HTTPException(status_code=501, detail="Use local_path. repository_url not implemented yet.")


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse, tags=["Analysis"])
async def get_analysis(analysis_id: str):
    """
    Get analysis result by ID.
    
    Returns current status and results (if completed).
    """
    analysis = _analyses.get(analysis_id)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )
    
    return analysis


async def _run_analysis(analysis_id: str, project_path: Path, request: AnalysisRequest):
    """Ejecuta el pipeline completo en background."""
    try:
        _analyses[analysis_id].status = AnalysisStatus.PROCESSING
        _analyses[analysis_id].progress = 10

        session = get_session()
        try:
            summary = await pipeline.run(
                project_path=project_path,
                microservice_name=project_path.name,
                session=session,
                llm_client=_llm_client if _llm_client.is_available() else None,
            )
        finally:
            session.close()

        _analyses[analysis_id].status = AnalysisStatus.COMPLETED
        _analyses[analysis_id].repository_name = summary["microservice_name"]
        _analyses[analysis_id].progress = 100
        _analyses[analysis_id].completed_at = datetime.utcnow()
        _analyses[analysis_id].quality_summary = summary

        logger.info("analysis_completed", analysis_id=analysis_id, summary=summary)

    except Exception as e:
        logger.error("analysis_failed", analysis_id=analysis_id, error=str(e))
        _analyses[analysis_id].status = AnalysisStatus.FAILED
        _analyses[analysis_id].error = str(e)
        _analyses[analysis_id].completed_at = datetime.utcnow()
