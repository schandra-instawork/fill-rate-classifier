"""
Module: models.classification
Purpose: Defines classification results and confidence scoring
Dependencies: pydantic, datetime, typing, enum

This module contains models for classification results, including
the two-tier classification system (Email vs Action) and confidence
scoring mechanisms.

Classes:
    ResponseType: Level 1 classification (Email/Action)
    ClassificationType: Level 2 specific classification types
    ClassificationConfidence: Confidence scoring details
    Classification: Individual classification with metadata
    ClassificationResult: Complete classification result for a company
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict


class ResponseType(str, Enum):
    """Level 1 classification: Response type required"""
    EMAIL = "email"
    ACTION = "action"
    UNKNOWN = "unknown"


class ClassificationType(str, Enum):
    """Level 2 classification: Specific issue types"""
    # Email types
    EMAIL_X = "low_pay_rate"
    EMAIL_Y = "geographic_coverage"
    EMAIL_Z = "shift_timing_mismatch"
    EMAIL_UNKNOWN = "general_email"
    
    # Action types
    ACTION_A = "contract_renegotiation"
    ACTION_B = "market_analysis"
    ACTION_C = "partner_meeting"
    ACTION_UNKNOWN = "manual_review"


class ClassificationConfidence(BaseModel):
    """
    Detailed confidence scoring for a classification
    
    Attributes:
        overall_score: Combined confidence score (0-1)
        pattern_matches: Individual pattern match scores
        rule_scores: Scores from each matching rule
        confidence_factors: Factors that influenced the score
        explanation: Human-readable explanation of the score
    """
    model_config = ConfigDict(validate_assignment=True)
    
    overall_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    pattern_matches: List[Dict[str, float]] = Field(default_factory=list)
    rule_scores: Dict[str, float] = Field(default_factory=dict)
    confidence_factors: List[str] = Field(default_factory=list)
    explanation: str = Field(..., description="Explanation of confidence calculation")
    
    @validator("overall_score")
    def round_score(cls, v):
        """Round score to 3 decimal places"""
        return round(v, 3)
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if this is a high-confidence classification"""
        return self.overall_score >= threshold
    
    def get_contributing_factors(self) -> List[Tuple[str, float]]:
        """Get factors that contributed most to the confidence score"""
        factors = []
        for rule, score in self.rule_scores.items():
            factors.append((rule, score))
        return sorted(factors, key=lambda x: x[1], reverse=True)


class Classification(BaseModel):
    """
    Individual classification for an issue
    
    Attributes:
        id: Unique classification ID
        response_type: Level 1 classification (Email/Action)
        classification_type: Level 2 specific classification
        confidence: Confidence scoring details
        matched_text: Text that triggered this classification
        recommended_template: Template ID for emails
        recommended_action: Specific action for manual interventions
        priority: Priority level for this classification
        metadata: Additional classification metadata
    """
    model_config = ConfigDict(use_enum_values=True)
    
    id: str = Field(..., description="Unique classification ID")
    response_type: ResponseType = Field(..., description="Level 1 classification")
    classification_type: ClassificationType = Field(..., description="Level 2 classification")
    confidence: ClassificationConfidence = Field(..., description="Confidence details")
    matched_text: str = Field(..., description="Text that matched the pattern")
    recommended_template: Optional[str] = Field(None, description="Email template ID")
    recommended_action: Optional[str] = Field(None, description="Recommended action")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("recommended_template")
    def validate_template(cls, v, values):
        """Ensure template is only set for email classifications"""
        if v and values.get("response_type") != ResponseType.EMAIL:
            raise ValueError("Template can only be set for email classifications")
        return v
    
    @validator("recommended_action")
    def validate_action(cls, v, values):
        """Ensure action is only set for action classifications"""
        if v and values.get("response_type") != ResponseType.ACTION:
            raise ValueError("Action can only be set for action classifications")
        return v
    
    def to_action_item(self) -> Dict[str, Any]:
        """Convert classification to an actionable item"""
        base_item = {
            "classification_id": self.id,
            "type": self.response_type,
            "specific_type": self.classification_type,
            "priority": self.priority,
            "confidence": self.confidence.overall_score,
        }
        
        if self.response_type == ResponseType.EMAIL:
            base_item["email_template"] = self.recommended_template
            base_item["action"] = "send_email"
        else:
            base_item["action"] = self.recommended_action
            base_item["requires_human"] = True
            
        return base_item


class ClassificationResult(BaseModel):
    """
    Complete classification result for a company
    
    Attributes:
        company_id: Company being classified
        api_response: Raw API response text
        classifications: List of all classifications found
        primary_classification: The highest confidence classification
        processing_time_ms: Time taken to classify in milliseconds
        timestamp: When classification was performed
        api_metadata: Metadata from the API response
        warnings: Any warnings during classification
    """
    model_config = ConfigDict(validate_assignment=True)
    
    company_id: str = Field(..., description="Company identifier")
    api_response: str = Field(..., description="Raw API response text")
    classifications: List[Classification] = Field(default_factory=list)
    primary_classification: Optional[Classification] = Field(None)
    processing_time_ms: int = Field(..., ge=0, description="Processing time in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    api_metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    
    @validator("classifications")
    def validate_classifications(cls, v):
        """Ensure at least one classification exists"""
        if not v:
            raise ValueError("At least one classification is required")
        return v
    
    @validator("primary_classification", always=True)
    def set_primary_classification(cls, v, values):
        """Automatically set primary classification if not provided"""
        if not v and "classifications" in values and values["classifications"]:
            # Select highest confidence classification
            return max(values["classifications"], 
                      key=lambda c: c.confidence.overall_score)
        return v
    
    def get_actionable_items(self) -> List[Dict[str, Any]]:
        """Get all actionable items from classifications"""
        return [c.to_action_item() for c in self.classifications]
    
    def get_email_classifications(self) -> List[Classification]:
        """Get only email-type classifications"""
        return [c for c in self.classifications 
                if c.response_type == ResponseType.EMAIL]
    
    def get_action_classifications(self) -> List[Classification]:
        """Get only action-type classifications"""
        return [c for c in self.classifications 
                if c.response_type == ResponseType.ACTION]
    
    def has_high_confidence_results(self, threshold: float = 0.8) -> bool:
        """Check if any classifications meet the confidence threshold"""
        return any(c.confidence.is_high_confidence(threshold) 
                  for c in self.classifications)
    
    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of the classification result"""
        email_types = [c.classification_type for c in self.get_email_classifications()]
        action_types = [c.classification_type for c in self.get_action_classifications()]
        
        return {
            "company_id": self.company_id,
            "timestamp": self.timestamp.isoformat(),
            "total_classifications": len(self.classifications),
            "primary_type": self.primary_classification.classification_type if self.primary_classification else None,
            "primary_confidence": self.primary_classification.confidence.overall_score if self.primary_classification else 0,
            "email_classifications": email_types,
            "action_classifications": action_types,
            "has_high_confidence": self.has_high_confidence_results(),
            "processing_time_ms": self.processing_time_ms,
            "warnings": self.warnings
        }