"""
Module: pipeline.batch_processor
Purpose: Orchestrates batch processing of fill rate analyses with resilient error handling
Dependencies: asyncio, concurrent processing, circuit breakers, retry logic

This module provides a robust pipeline for processing hundreds of company analyses
with built-in fault tolerance, progress tracking, and modular component design.

Classes:
    BatchProcessor: Main orchestrator for batch analysis
    ProcessingResult: Container for individual processing results
    BatchJob: Represents a batch processing job with metadata
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
import time

from src.api.fill_rate_analysis_client import FillRateAnalysisClient, AnalysisResponse
from src.api.claude_client import ClaudeAPIClient
from src.classification.recommendation_classifier import (
    RecommendationClassifier, 
    ClassificationResult,
    RecommendationCategory,
    group_by_category,
    prioritize_actions
)


class ProcessingStatus(Enum):
    """Status of individual company processing"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    CLASSIFYING = "classifying"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ProcessingResult:
    """
    Container for individual company processing result
    
    Attributes:
        company_id: Company identifier
        status: Current processing status
        analysis: Fill rate analysis response
        classifications: Classified recommendations
        error: Error message if failed
        retry_count: Number of retry attempts
        processing_time: Time taken to process
    """
    company_id: str
    status: ProcessingStatus
    analysis: Optional[AnalysisResponse] = None
    classifications: List[ClassificationResult] = field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = 0
    processing_time: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class BatchJob:
    """
    Represents a batch processing job
    
    Attributes:
        job_id: Unique job identifier
        company_ids: List of companies to process
        created_at: Job creation timestamp
        config: Job configuration
        results: Processing results by company
        metadata: Additional job metadata
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    config: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, ProcessingResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_companies(self) -> int:
        """Total number of companies in batch"""
        return len(self.company_ids)
    
    @property
    def completed_count(self) -> int:
        """Number of successfully completed companies"""
        return sum(
            1 for r in self.results.values() 
            if r.status == ProcessingStatus.COMPLETED
        )
    
    @property
    def failed_count(self) -> int:
        """Number of failed companies"""
        return sum(
            1 for r in self.results.values() 
            if r.status == ProcessingStatus.FAILED
        )
    
    @property
    def progress_percentage(self) -> float:
        """Progress percentage (0-100)"""
        if not self.company_ids:
            return 100.0
        processed = len([
            r for r in self.results.values() 
            if r.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
        ])
        return (processed / self.total_companies) * 100


class BatchProcessor:
    """
    Orchestrates batch processing of fill rate analyses
    
    This class provides a resilient pipeline that:
    - Processes companies in parallel with rate limiting
    - Handles failures with exponential backoff retry
    - Tracks progress and provides real-time updates
    - Modular design for easy component swapping
    - Circuit breaker pattern for API protection
    """
    
    def __init__(
        self,
        fill_rate_client: FillRateAnalysisClient,
        claude_client: ClaudeAPIClient,
        max_concurrent: int = 10,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5
    ):
        """
        Initialize batch processor
        
        Args:
            fill_rate_client: Client for fill rate analysis API
            claude_client: Client for Claude API
            max_concurrent: Maximum concurrent API calls
            max_retries: Maximum retry attempts per company
            circuit_breaker_threshold: Consecutive failures before circuit break
        """
        self.fill_rate_client = fill_rate_client
        self.classifier = RecommendationClassifier(claude_client)
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.circuit_breaker_threshold = circuit_breaker_threshold
        
        self.logger = logging.getLogger(__name__)
        
        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open = False
        self._circuit_open_until = None
        
        # Active jobs tracking
        self.active_jobs: Dict[str, BatchJob] = {}
        
        # Thread pool for CPU-bound classification tasks
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    async def process_batch(
        self,
        company_ids: List[str],
        analysis_type: str = "past",
        job_config: Optional[Dict[str, Any]] = None
    ) -> BatchJob:
        """
        Process a batch of companies with full pipeline
        
        Args:
            company_ids: List of company IDs to process
            analysis_type: Type of analysis (past/risk)
            job_config: Optional job configuration
            
        Returns:
            BatchJob with results
        """
        # Create job
        job = BatchJob(
            company_ids=company_ids,
            config=job_config or {
                "analysis_type": analysis_type,
                "max_concurrent": self.max_concurrent,
                "max_retries": self.max_retries
            }
        )
        
        self.active_jobs[job.job_id] = job
        self.logger.info(f"Starting batch job {job.job_id} with {len(company_ids)} companies")
        
        try:
            # Initialize results for all companies
            for company_id in company_ids:
                job.results[company_id] = ProcessingResult(
                    company_id=company_id,
                    status=ProcessingStatus.PENDING
                )
            
            # Process companies in chunks to respect rate limits
            await self._process_companies_chunked(job, analysis_type)
            
            # Generate summary statistics
            job.metadata.update(self._generate_job_summary(job))
            
            self.logger.info(
                f"Batch job {job.job_id} completed: "
                f"{job.completed_count} success, {job.failed_count} failed"
            )
            
            return job
            
        except Exception as e:
            self.logger.error(f"Batch job {job.job_id} failed: {e}")
            job.metadata["error"] = str(e)
            raise
        finally:
            # Clean up active job
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def _process_companies_chunked(
        self,
        job: BatchJob,
        analysis_type: str
    ) -> None:
        """
        Process companies in chunks with concurrency control
        
        Args:
            job: Batch job to process
            analysis_type: Type of analysis
        """
        company_ids = job.company_ids
        chunk_size = self.max_concurrent
        
        # Process in chunks
        for i in range(0, len(company_ids), chunk_size):
            chunk = company_ids[i:i + chunk_size]
            
            # Check circuit breaker before processing chunk
            if self._is_circuit_open():
                wait_time = (self._circuit_open_until - datetime.utcnow()).total_seconds()
                self.logger.warning(f"Circuit breaker open, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self._reset_circuit_breaker()
            
            # Process chunk concurrently
            tasks = [
                self._process_single_company(job, company_id, analysis_type)
                for company_id in chunk
            ]
            
            # Wait for chunk to complete with proper error handling
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and update circuit breaker
            for company_id, result in zip(chunk, results):
                if isinstance(result, Exception):
                    self._record_failure()
                    job.results[company_id].status = ProcessingStatus.FAILED
                    job.results[company_id].error = str(result)
                else:
                    self._record_success()
            
            # Brief delay between chunks to prevent API overload
            if i + chunk_size < len(company_ids):
                await asyncio.sleep(1)
    
    async def _process_single_company(
        self,
        job: BatchJob,
        company_id: str,
        analysis_type: str
    ) -> ProcessingResult:
        """
        Process a single company through the full pipeline
        
        Args:
            job: Parent batch job
            company_id: Company to process
            analysis_type: Type of analysis
            
        Returns:
            Processing result
        """
        result = job.results[company_id]
        result.started_at = datetime.utcnow()
        result.status = ProcessingStatus.ANALYZING
        
        try:
            # Phase 1: Get fill rate analysis with retry logic
            analysis = await self._analyze_with_retry(company_id, analysis_type, result)
            if not analysis:
                raise Exception("Analysis failed after retries")
            
            result.analysis = analysis
            result.status = ProcessingStatus.CLASSIFYING
            
            # Phase 2: Classify recommendations
            # Run CPU-intensive classification in thread pool
            classifications = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._classify_recommendations,
                analysis.recommendations,
                {"company_id": company_id, "analysis_type": analysis_type}
            )
            
            result.classifications = classifications
            result.status = ProcessingStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Failed to process {company_id}: {e}")
            result.status = ProcessingStatus.FAILED
            result.error = str(e)
            raise
        finally:
            result.completed_at = datetime.utcnow()
            result.processing_time = (
                result.completed_at - result.started_at
            ).total_seconds()
        
        return result
    
    async def _analyze_with_retry(
        self,
        company_id: str,
        analysis_type: str,
        result: ProcessingResult
    ) -> Optional[AnalysisResponse]:
        """
        Analyze company with exponential backoff retry
        
        Args:
            company_id: Company to analyze
            analysis_type: Type of analysis
            result: Result object to update
            
        Returns:
            Analysis response or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    result.status = ProcessingStatus.RETRYING
                    result.retry_count = attempt
                    # Exponential backoff: 1s, 2s, 4s, etc.
                    wait_time = 2 ** (attempt - 1)
                    await asyncio.sleep(wait_time)
                
                # Make API call
                analysis = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.fill_rate_client.analyze_company,
                    company_id,
                    analysis_type
                )
                
                return analysis
                
            except Exception as e:
                self.logger.warning(
                    f"Analysis attempt {attempt + 1} failed for {company_id}: {e}"
                )
                if attempt == self.max_retries - 1:
                    # Final attempt failed
                    return None
        
        return None
    
    def _classify_recommendations(
        self,
        recommendations: List[str],
        context: Dict[str, Any]
    ) -> List[ClassificationResult]:
        """
        Classify recommendations (CPU-bound task)
        
        Args:
            recommendations: List of recommendations to classify
            context: Additional context for classification
            
        Returns:
            List of classification results
        """
        try:
            return self.classifier.classify_recommendations(
                recommendations,
                context
            )
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            # Return empty classifications rather than failing entire company
            return []
    
    def _is_circuit_open(self) -> bool:
        """
        Check if circuit breaker is open
        
        Returns:
            True if circuit is open
        """
        if self._circuit_open and self._circuit_open_until:
            if datetime.utcnow() < self._circuit_open_until:
                return True
            else:
                # Circuit timeout expired
                self._reset_circuit_breaker()
        return False
    
    def _record_failure(self) -> None:
        """Record a failure for circuit breaker"""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.circuit_breaker_threshold:
            self._open_circuit()
    
    def _record_success(self) -> None:
        """Record a success for circuit breaker"""
        # Reset consecutive failures on success
        if self._consecutive_failures > 0:
            self._consecutive_failures = 0
    
    def _open_circuit(self) -> None:
        """Open the circuit breaker"""
        self._circuit_open = True
        # Circuit stays open for 30 seconds
        self._circuit_open_until = datetime.utcnow() + timedelta(seconds=30)
        self.logger.warning(
            f"Circuit breaker opened after {self._consecutive_failures} failures"
        )
    
    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker state"""
        self._circuit_open = False
        self._circuit_open_until = None
        self._consecutive_failures = 0
        self.logger.info("Circuit breaker reset")
    
    def _generate_job_summary(self, job: BatchJob) -> Dict[str, Any]:
        """
        Generate comprehensive job summary statistics
        
        Args:
            job: Completed batch job
            
        Returns:
            Summary statistics
        """
        # Collect all classifications
        all_classifications = []
        for result in job.results.values():
            if result.status == ProcessingStatus.COMPLETED:
                all_classifications.extend(result.classifications)
        
        # Group by category
        by_category = group_by_category(all_classifications)
        
        # Count high priority actions
        high_priority_count = sum(
            1 for c in all_classifications 
            if c.action_priority == "HIGH"
        )
        
        # Calculate average processing time
        processing_times = [
            r.processing_time for r in job.results.values()
            if r.processing_time is not None
        ]
        avg_processing_time = (
            sum(processing_times) / len(processing_times) 
            if processing_times else 0
        )
        
        return {
            "total_companies": job.total_companies,
            "completed": job.completed_count,
            "failed": job.failed_count,
            "total_recommendations": len(all_classifications),
            "high_priority_actions": high_priority_count,
            "recommendations_by_category": {
                cat.value: len(items) 
                for cat, items in by_category.items()
            },
            "average_processing_time": avg_processing_time,
            "total_processing_time": sum(processing_times),
            "completion_rate": job.completed_count / job.total_companies * 100
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary or None if not found
        """
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                "job_id": job_id,
                "status": "active",
                "progress": job.progress_percentage,
                "completed": job.completed_count,
                "failed": job.failed_count,
                "total": job.total_companies
            }
        return None
    
    async def get_prioritized_actions(
        self,
        job: BatchJob,
        top_n: Optional[int] = None
    ) -> List[Tuple[str, ClassificationResult]]:
        """
        Get prioritized actions across all companies
        
        Args:
            job: Completed batch job
            top_n: Number of top actions to return
            
        Returns:
            List of (company_id, classification) tuples
        """
        # Collect all classifications with company context
        company_classifications = []
        for company_id, result in job.results.items():
            if result.status == ProcessingStatus.COMPLETED:
                for classification in result.classifications:
                    company_classifications.append((company_id, classification))
        
        # Sort by priority and confidence
        sorted_actions = sorted(
            company_classifications,
            key=lambda x: (
                {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(x[1].action_priority, 0),
                x[1].confidence
            ),
            reverse=True
        )
        
        return sorted_actions[:top_n] if top_n else sorted_actions
    
    def export_job_results(
        self,
        job: BatchJob,
        format: str = "json"
    ) -> str:
        """
        Export job results in specified format
        
        Args:
            job: Batch job to export
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        if format == "json":
            return self._export_json(job)
        elif format == "csv":
            return self._export_csv(job)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, job: BatchJob) -> str:
        """Export job results as JSON"""
        export_data = {
            "job_id": job.job_id,
            "created_at": job.created_at.isoformat(),
            "config": job.config,
            "summary": job.metadata,
            "results": {}
        }
        
        for company_id, result in job.results.items():
            export_data["results"][company_id] = {
                "status": result.status.value,
                "processing_time": result.processing_time,
                "analysis": {
                    "fill_rate": result.analysis.fill_rate if result.analysis else None,
                    "risk_level": result.analysis.risk_level if result.analysis else None,
                    "recommendations_count": len(result.analysis.recommendations) if result.analysis else 0
                },
                "classifications": [
                    {
                        "category": c.category.value,
                        "priority": c.action_priority,
                        "confidence": c.confidence,
                        "action": c.specific_action
                    }
                    for c in result.classifications
                ],
                "error": result.error
            }
        
        return json.dumps(export_data, indent=2)
    
    def _export_csv(self, job: BatchJob) -> str:
        """Export job results as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "company_id",
            "status",
            "fill_rate",
            "risk_level",
            "recommendation_category",
            "priority",
            "confidence",
            "specific_action",
            "processing_time",
            "error"
        ])
        
        # Data rows
        for company_id, result in job.results.items():
            if result.classifications:
                for classification in result.classifications:
                    writer.writerow([
                        company_id,
                        result.status.value,
                        result.analysis.fill_rate if result.analysis else "",
                        result.analysis.risk_level if result.analysis else "",
                        classification.category.value,
                        classification.action_priority,
                        classification.confidence,
                        classification.specific_action,
                        result.processing_time,
                        result.error or ""
                    ])
            else:
                # Company with no classifications
                writer.writerow([
                    company_id,
                    result.status.value,
                    result.analysis.fill_rate if result.analysis else "",
                    result.analysis.risk_level if result.analysis else "",
                    "",
                    "",
                    "",
                    "",
                    result.processing_time,
                    result.error or ""
                ])
        
        return output.getvalue()