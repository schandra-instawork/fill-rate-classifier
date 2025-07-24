"""
Module: api.server
Purpose: FastAPI server with webhook endpoints and bearer authentication
Dependencies: fastapi, uvicorn, pydantic

This module provides a FastAPI server that:
- Accepts webhook requests with fill rate data
- Validates bearer authentication
- Processes fill rate classifications
- Returns structured responses

Endpoints:
    POST /webhook/fill-rate: Process fill rate data webhook
    GET /health: Health check endpoint
    POST /predict: Direct prediction endpoint
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from src.api.claude_client import ClaudeAPIClient, FillRatePredictionGenerator
from src.api.fill_rate_analysis_client import FillRateAnalysisClient
from src.models.company import Company, CompanyMetrics
from src.models.schemas import APIResponse
from src.pipeline.batch_processor import BatchProcessor, BatchJob, ProcessingStatus


# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# FastAPI app
app = FastAPI(
    title="Fill Rate Classifier API",
    description="API for processing fill rate data and generating predictions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebhookPayload(BaseModel):
    """Webhook payload structure"""
    company: Dict[str, Any] = Field(..., description="Company information")
    metrics: Dict[str, Any] = Field(..., description="Company metrics")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    webhook_id: Optional[str] = Field(None, description="Unique webhook identifier")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class PredictionRequest(BaseModel):
    """Direct prediction request"""
    company_id: str = Field(..., description="Company identifier")
    company_data: Optional[Dict[str, Any]] = Field(None, description="Company data")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    company_ids: List[str] = Field(..., description="List of company IDs to analyze")
    analysis_type: str = Field(default="past", description="Type of analysis (past/risk)")
    job_config: Optional[Dict[str, Any]] = Field(None, description="Optional job configuration")


class BatchJobResponse(BaseModel):
    """Response for batch job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    total_companies: int = Field(..., description="Total companies to process")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_completion_time: Optional[str] = Field(None, description="Estimated completion time")


class BatchJobStatusResponse(BaseModel):
    """Response for batch job status"""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status (active/completed)")
    progress_percentage: float = Field(..., description="Progress percentage")
    completed: int = Field(..., description="Completed companies")
    failed: int = Field(..., description="Failed companies")
    total: int = Field(..., description="Total companies")
    summary: Optional[Dict[str, Any]] = Field(None, description="Job summary if completed")


class BatchResultsResponse(BaseModel):
    """Response for batch results"""
    job_id: str = Field(..., description="Job identifier")
    results: Dict[str, Any] = Field(..., description="Processing results")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    export_formats: List[str] = Field(default=["json", "csv"], description="Available export formats")


class PrioritizedActionsResponse(BaseModel):
    """Response for prioritized actions"""
    job_id: str = Field(..., description="Job identifier")
    total_actions: int = Field(..., description="Total number of actions")
    high_priority_count: int = Field(..., description="Number of high priority actions")
    actions: List[Dict[str, Any]] = Field(..., description="Prioritized action list")


# Global variables for API clients and processors
claude_client: Optional[ClaudeAPIClient] = None
prediction_generator: Optional[FillRatePredictionGenerator] = None
fill_rate_client: Optional[FillRateAnalysisClient] = None
batch_processor: Optional[BatchProcessor] = None

# In-memory job storage (use Redis/DB in production)
job_storage: Dict[str, BatchJob] = {}


def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify bearer token authentication
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        Token if valid
        
    Raises:
        HTTPException: If token is invalid
    """
    expected_token = os.getenv("API_BEARER_TOKEN")
    
    if not expected_token:
        logger.error("API_BEARER_TOKEN environment variable not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    if credentials.credentials != expected_token:
        logger.warning(f"Invalid bearer token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global claude_client, prediction_generator, fill_rate_client, batch_processor
    
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    claude_base_url = os.getenv("CLAUDE_BASE_URL", "https://finch.instawork.com")
    
    if not claude_api_key:
        logger.error("CLAUDE_API_KEY environment variable not set")
        raise RuntimeError("CLAUDE_API_KEY is required")
    
    # Initialize all clients
    claude_client = ClaudeAPIClient(claude_api_key, claude_base_url)
    prediction_generator = FillRatePredictionGenerator(claude_client)
    fill_rate_client = FillRateAnalysisClient(claude_api_key, claude_base_url)
    
    # Initialize batch processor with configurable settings
    max_concurrent = int(os.getenv("BATCH_MAX_CONCURRENT", 10))
    max_retries = int(os.getenv("BATCH_MAX_RETRIES", 3))
    
    batch_processor = BatchProcessor(
        fill_rate_client=fill_rate_client,
        claude_client=claude_client,
        max_concurrent=max_concurrent,
        max_retries=max_retries
    )
    
    logger.info("Fill Rate Classifier API started successfully")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.post("/webhook/fill-rate", response_model=APIResponse)
async def process_fill_rate_webhook(
    payload: WebhookPayload,
    token: str = Depends(verify_bearer_token)
) -> APIResponse:
    """
    Process fill rate data webhook
    
    Args:
        payload: Webhook payload with company and metrics data
        token: Verified bearer token
        
    Returns:
        API response with predictions
        
    Raises:
        HTTPException: If processing fails
    """
    if not prediction_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction service not initialized"
        )
    
    try:
        logger.info(f"Processing webhook for company: {payload.company.get('id', 'unknown')}")
        
        # Parse company and metrics from payload
        company = Company(**payload.company)
        metrics = CompanyMetrics(**payload.metrics)
        
        # Generate prediction
        response = await prediction_generator.generate_prediction(
            company=company,
            metrics=metrics,
            additional_context=payload.additional_context
        )
        
        logger.info(f"Successfully processed webhook for company {company.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@app.post("/predict", response_model=APIResponse)
async def predict_fill_rate(
    request: PredictionRequest,
    token: str = Depends(verify_bearer_token)
) -> APIResponse:
    """
    Direct prediction endpoint
    
    Args:
        request: Prediction request
        token: Verified bearer token
        
    Returns:
        API response with predictions
        
    Raises:
        HTTPException: If prediction fails
    """
    if not prediction_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction service not initialized"
        )
    
    try:
        logger.info(f"Processing direct prediction for company: {request.company_id}")
        
        if request.company_data:
            # Use provided company data
            company = Company(**request.company_data['company'])
            metrics = CompanyMetrics(**request.company_data['metrics'])
        else:
            # Generate mock data for testing
            from src.api.claude_client import MockFillRateAPI
            mock_api = MockFillRateAPI(os.getenv("CLAUDE_API_KEY"))
            return await mock_api.get_prediction(request.company_id)
        
        # Generate prediction
        response = await prediction_generator.generate_prediction(
            company=company,
            metrics=metrics,
            additional_context=request.company_data.get('additional_context')
        )
        
        logger.info(f"Successfully generated prediction for company {request.company_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction: {str(e)}"
        )


@app.post("/analyze/batch", response_model=BatchJobResponse)
async def start_batch_analysis(
    request: BatchAnalysisRequest,
    token: str = Depends(verify_bearer_token)
) -> BatchJobResponse:
    """
    Start batch analysis for multiple companies
    
    Args:
        request: Batch analysis request with company IDs
        token: Verified bearer token
        
    Returns:
        Batch job response with job ID
        
    Raises:
        HTTPException: If batch processing fails to start
    """
    if not batch_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Batch processor not initialized"
        )
    
    try:
        logger.info(f"Starting batch analysis for {len(request.company_ids)} companies")
        
        # Validate company IDs
        if not request.company_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No company IDs provided"
            )
        
        if len(request.company_ids) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 1000 companies per batch"
            )
        
        # Start batch processing asynchronously
        job = await batch_processor.process_batch(
            company_ids=request.company_ids,
            analysis_type=request.analysis_type,
            job_config=request.job_config
        )
        
        # Store job for later retrieval
        job_storage[job.job_id] = job
        
        # Estimate completion time based on company count
        # Assumes ~3 seconds per company with parallelization
        estimated_seconds = (len(request.company_ids) / batch_processor.max_concurrent) * 3
        estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
        
        return BatchJobResponse(
            job_id=job.job_id,
            status="processing",
            total_companies=job.total_companies,
            created_at=job.created_at,
            estimated_completion_time=estimated_completion.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error starting batch analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch analysis: {str(e)}"
        )


@app.get("/analyze/batch/{job_id}/status", response_model=BatchJobStatusResponse)
async def get_batch_job_status(
    job_id: str,
    token: str = Depends(verify_bearer_token)
) -> BatchJobStatusResponse:
    """
    Get status of a batch analysis job
    
    Args:
        job_id: Unique job identifier
        token: Verified bearer token
        
    Returns:
        Current job status
        
    Raises:
        HTTPException: If job not found
    """
    # Check active jobs first
    active_status = batch_processor.get_job_status(job_id) if batch_processor else None
    if active_status:
        return BatchJobStatusResponse(**active_status)
    
    # Check completed jobs in storage
    if job_id in job_storage:
        job = job_storage[job_id]
        return BatchJobStatusResponse(
            job_id=job_id,
            status="completed",
            progress_percentage=100.0,
            completed=job.completed_count,
            failed=job.failed_count,
            total=job.total_companies,
            summary=job.metadata
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Job {job_id} not found"
    )


@app.get("/analyze/batch/{job_id}/results", response_model=BatchResultsResponse)
async def get_batch_results(
    job_id: str,
    token: str = Depends(verify_bearer_token)
) -> BatchResultsResponse:
    """
    Get detailed results of a completed batch job
    
    Args:
        job_id: Job identifier
        token: Verified bearer token
        
    Returns:
        Detailed job results
        
    Raises:
        HTTPException: If job not found or not completed
    """
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = job_storage[job_id]
    
    # Build detailed results
    results = {}
    for company_id, result in job.results.items():
        results[company_id] = {
            "status": result.status.value,
            "processing_time": result.processing_time,
            "recommendations_count": len(result.classifications),
            "high_priority_actions": sum(
                1 for c in result.classifications 
                if c.action_priority == "HIGH"
            ),
            "classifications": [
                {
                    "category": c.category.value,
                    "priority": c.action_priority,
                    "confidence": c.confidence,
                    "action": c.specific_action,
                    "extracted_values": c.extracted_values
                }
                for c in result.classifications
            ],
            "error": result.error
        }
    
    return BatchResultsResponse(
        job_id=job_id,
        results=results,
        summary=job.metadata or {}
    )


@app.get("/analyze/batch/{job_id}/actions", response_model=PrioritizedActionsResponse)
async def get_prioritized_actions(
    job_id: str,
    top_n: Optional[int] = 50,
    token: str = Depends(verify_bearer_token)
) -> PrioritizedActionsResponse:
    """
    Get prioritized actions across all companies in batch
    
    Args:
        job_id: Job identifier
        top_n: Number of top actions to return
        token: Verified bearer token
        
    Returns:
        Prioritized list of actions
        
    Raises:
        HTTPException: If job not found
    """
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = job_storage[job_id]
    
    # Get prioritized actions
    prioritized = await batch_processor.get_prioritized_actions(job, top_n)
    
    # Format for response
    actions = []
    for company_id, classification in prioritized:
        actions.append({
            "company_id": company_id,
            "category": classification.category.value,
            "priority": classification.action_priority,
            "confidence": classification.confidence,
            "specific_action": classification.specific_action,
            "extracted_values": classification.extracted_values,
            "original_recommendation": classification.original_recommendation
        })
    
    high_priority_count = sum(
        1 for _, c in prioritized 
        if c.action_priority == "HIGH"
    )
    
    return PrioritizedActionsResponse(
        job_id=job_id,
        total_actions=len(prioritized),
        high_priority_count=high_priority_count,
        actions=actions
    )


@app.get("/analyze/batch/{job_id}/export")
async def export_batch_results(
    job_id: str,
    format: str = "json",
    token: str = Depends(verify_bearer_token)
) -> Any:
    """
    Export batch results in specified format
    
    Args:
        job_id: Job identifier
        format: Export format (json/csv)
        token: Verified bearer token
        
    Returns:
        Exported data in requested format
        
    Raises:
        HTTPException: If job not found or format unsupported
    """
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = job_storage[job_id]
    
    try:
        exported = batch_processor.export_job_results(job, format)
        
        if format == "csv":
            from fastapi.responses import Response
            return Response(
                content=exported,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=batch_{job_id}.csv"
                }
            )
        else:
            return Response(
                content=exported,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=batch_{job_id}.json"
                }
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )


def main():
    """Run the FastAPI server"""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        log_level="info"
    )


if __name__ == "__main__":
    main()