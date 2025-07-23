"""
Module: models.schemas
Purpose: API request/response schemas and validation
Dependencies: pydantic, typing, datetime

This module defines the schemas for API interactions, including
request validation and response formatting. All schemas include
comprehensive validation and serialization logic.

Classes:
    APIResponse: Raw API response model
    APIResponseSchema: Validated API response
    ClassificationRequest: Request to classify companies
    ClassificationResponse: Response with classification results
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from .company import Company, CompanyMetrics
from .classification import ClassificationResult


class APIResponse(BaseModel):
    """
    Raw response from the fill rate prediction API
    
    Attributes:
        company_id: Company identifier
        predictions: List of prediction texts
        metrics: Current metrics that influenced predictions
        confidence: API's confidence in predictions
        generated_at: When predictions were generated
        model_version: Version of the prediction model used
    """
    model_config = ConfigDict(validate_assignment=True)
    
    company_id: str = Field(..., description="Company identifier")
    predictions: List[str] = Field(..., min_items=1, description="Prediction texts")
    metrics: Dict[str, Any] = Field(..., description="Metrics used for predictions")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    generated_at: datetime = Field(..., description="Generation timestamp")
    model_version: str = Field(..., description="Model version used")
    
    @validator("predictions")
    def validate_predictions(cls, v):
        """Ensure predictions are non-empty strings"""
        for pred in v:
            if not pred or not pred.strip():
                raise ValueError("Empty prediction text found")
        return v
    
    @validator("metrics")
    def validate_metrics(cls, v):
        """Ensure required metrics are present"""
        required_metrics = {"fill_rate", "total_shifts"}
        if not all(metric in v for metric in required_metrics):
            raise ValueError(f"Missing required metrics: {required_metrics}")
        return v


class APIResponseSchema(BaseModel):
    """
    Validated and enriched API response
    
    Includes additional validation and business logic checks
    beyond the raw API response.
    """
    model_config = ConfigDict(validate_assignment=True)
    
    raw_response: APIResponse = Field(..., description="Original API response")
    is_valid: bool = Field(default=True, description="Validation status")
    validation_errors: List[str] = Field(default_factory=list)
    enriched_data: Dict[str, Any] = Field(default_factory=dict)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_validation_error(self, error: str) -> None:
        """Add a validation error and mark as invalid"""
        self.validation_errors.append(error)
        self.is_valid = False
    
    def enrich_with_context(self, context: Dict[str, Any]) -> None:
        """Add contextual data to the response"""
        self.enriched_data.update(context)
        self.processing_metadata["enriched_at"] = datetime.utcnow().isoformat()
    
    def get_combined_prediction_text(self) -> str:
        """Combine all predictions into a single text for classification"""
        return " ".join(self.raw_response.predictions)


class ClassificationRequest(BaseModel):
    """
    Request to classify one or more companies
    
    Attributes:
        company_ids: List of company IDs to classify
        include_metrics: Whether to fetch current metrics
        force_refresh: Bypass cache and fetch fresh data
        classification_config: Override default classification settings
        batch_size: Number of companies to process in parallel
    """
    model_config = ConfigDict(validate_assignment=True)
    
    company_ids: List[str] = Field(..., min_items=1, max_items=1000)
    include_metrics: bool = Field(default=True, description="Include current metrics")
    force_refresh: bool = Field(default=False, description="Bypass cache")
    classification_config: Optional[Dict[str, Any]] = Field(None)
    batch_size: int = Field(default=100, ge=1, le=500)
    
    @validator("company_ids")
    def validate_company_ids(cls, v):
        """Ensure company IDs are unique and valid"""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate company IDs found")
        for company_id in v:
            if not company_id or not company_id.strip():
                raise ValueError("Empty company ID found")
        return v
    
    @validator("classification_config")
    def validate_config(cls, v):
        """Validate classification configuration if provided"""
        if v:
            allowed_keys = {
                "confidence_threshold", 
                "max_classifications", 
                "enable_multi_label",
                "custom_rules"
            }
            invalid_keys = set(v.keys()) - allowed_keys
            if invalid_keys:
                raise ValueError(f"Invalid configuration keys: {invalid_keys}")
        return v


class BatchClassificationStatus(BaseModel):
    """
    Status of a batch classification job
    
    Attributes:
        total_companies: Total number of companies to process
        processed: Number of companies processed
        successful: Number of successful classifications
        failed: Number of failed classifications
        in_progress: Currently processing
        estimated_completion: Estimated completion time
    """
    total_companies: int = Field(..., ge=0)
    processed: int = Field(default=0, ge=0)
    successful: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    in_progress: bool = Field(default=True)
    estimated_completion: Optional[datetime] = Field(None)
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_companies == 0:
            return 100.0
        return round((self.processed / self.total_companies) * 100, 2)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed == 0:
            return 0.0
        return round((self.successful / self.processed) * 100, 2)


class ClassificationResponse(BaseModel):
    """
    Response containing classification results
    
    Attributes:
        request_id: Unique request identifier
        results: List of classification results
        status: Batch processing status
        summary: High-level summary of results
        errors: Any errors encountered
        metadata: Additional response metadata
    """
    model_config = ConfigDict(validate_assignment=True)
    
    request_id: str = Field(..., description="Unique request ID")
    results: List[ClassificationResult] = Field(default_factory=list)
    status: BatchClassificationStatus = Field(...)
    summary: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_result(self, result: ClassificationResult) -> None:
        """Add a classification result"""
        self.results.append(result)
        self.status.processed += 1
        self.status.successful += 1
        
    def add_error(self, company_id: str, error: str) -> None:
        """Add an error for a specific company"""
        self.errors.append({
            "company_id": company_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.status.processed += 1
        self.status.failed += 1
    
    def generate_summary(self) -> None:
        """Generate summary statistics"""
        if not self.results:
            self.summary = {"message": "No results to summarize"}
            return
            
        email_count = sum(len(r.get_email_classifications()) for r in self.results)
        action_count = sum(len(r.get_action_classifications()) for r in self.results)
        
        self.summary = {
            "total_companies": len(self.results),
            "total_classifications": sum(len(r.classifications) for r in self.results),
            "email_classifications": email_count,
            "action_classifications": action_count,
            "high_confidence_results": sum(1 for r in self.results if r.has_high_confidence_results()),
            "processing_time_ms": sum(r.processing_time_ms for r in self.results),
            "average_confidence": self._calculate_average_confidence(),
            "classification_distribution": self._get_classification_distribution()
        }
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence across all classifications"""
        all_confidences = []
        for result in self.results:
            all_confidences.extend([c.confidence.overall_score for c in result.classifications])
        
        if not all_confidences:
            return 0.0
        return round(sum(all_confidences) / len(all_confidences), 3)
    
    def _get_classification_distribution(self) -> Dict[str, int]:
        """Get distribution of classification types"""
        distribution = {}
        for result in self.results:
            for classification in result.classifications:
                key = f"{classification.response_type}_{classification.classification_type}"
                distribution[key] = distribution.get(key, 0) + 1
        return distribution
    
    def to_export_format(self, format: str = "json") -> Union[Dict, str]:
        """Export results in specified format"""
        if format == "json":
            return self.model_dump()
        elif format == "summary":
            return self.summary
        else:
            raise ValueError(f"Unsupported export format: {format}")