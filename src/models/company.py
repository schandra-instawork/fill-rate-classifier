"""
Module: models.company
Purpose: Defines the Company entity and related metrics
Dependencies: pydantic, datetime, typing, enum

This module contains the data models for companies and their associated
fill rate metrics. All models use Pydantic for automatic validation
and serialization.

Classes:
    Company: Core company entity with identification and metadata
    CompanyMetrics: Fill rate and performance metrics for a company
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict


class CompanyStatus(str, Enum):
    """Enumeration of possible company statuses"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Company(BaseModel):
    """
    Company entity model
    
    Attributes:
        id: Unique identifier for the company
        name: Company display name
        status: Current company status
        location: Primary location/region
        timezone: Company's operating timezone
        metadata: Additional flexible metadata
        created_at: Timestamp of company creation
        updated_at: Last update timestamp
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    id: str = Field(..., description="Unique company identifier", min_length=1)
    name: str = Field(..., description="Company name", min_length=1, max_length=255)
    status: CompanyStatus = Field(default=CompanyStatus.ACTIVE)
    location: Optional[str] = Field(None, description="Primary location/region")
    timezone: str = Field(default="UTC", description="Company timezone")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator("timezone")
    def validate_timezone(cls, v):
        """Validate timezone format"""
        # In production, would validate against pytz timezones
        if not v:
            raise ValueError("Timezone cannot be empty")
        return v
    
    @validator("metadata")
    def validate_metadata(cls, v):
        """Ensure metadata doesn't contain sensitive keys"""
        sensitive_keys = {"password", "secret", "token", "key"}
        if any(key.lower() in sensitive_keys for key in v.keys()):
            raise ValueError("Metadata contains sensitive information")
        return v


class MetricPeriod(str, Enum):
    """Time periods for metrics aggregation"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class CompanyMetrics(BaseModel):
    """
    Fill rate metrics for a company
    
    Attributes:
        company_id: Reference to the company
        period: Time period for these metrics
        fill_rate: Overall fill rate percentage (0-100)
        total_shifts: Total number of shifts requested
        filled_shifts: Number of successfully filled shifts
        avg_time_to_fill: Average time to fill a shift in hours
        cancellation_rate: Percentage of cancelled shifts
        worker_ratings: Average rating from workers
        metrics_date: Date these metrics represent
        regional_breakdown: Fill rates by region
        shift_type_breakdown: Fill rates by shift type
    """
    model_config = ConfigDict(validate_assignment=True)
    
    company_id: str = Field(..., description="Company identifier")
    period: MetricPeriod = Field(default=MetricPeriod.WEEKLY)
    fill_rate: float = Field(..., ge=0, le=100, description="Fill rate percentage")
    total_shifts: int = Field(..., ge=0, description="Total shifts requested")
    filled_shifts: int = Field(..., ge=0, description="Successfully filled shifts")
    avg_time_to_fill: Optional[float] = Field(None, ge=0, description="Avg fill time in hours")
    cancellation_rate: float = Field(default=0.0, ge=0, le=100)
    worker_ratings: Optional[float] = Field(None, ge=1, le=5, description="Average rating")
    metrics_date: datetime = Field(default_factory=datetime.utcnow)
    regional_breakdown: Dict[str, float] = Field(default_factory=dict)
    shift_type_breakdown: Dict[str, float] = Field(default_factory=dict)
    
    @validator("filled_shifts")
    def validate_filled_shifts(cls, v, values):
        """Ensure filled shifts doesn't exceed total shifts"""
        if "total_shifts" in values and v > values["total_shifts"]:
            raise ValueError("Filled shifts cannot exceed total shifts")
        return v
    
    @validator("fill_rate")
    def validate_fill_rate(cls, v, values):
        """Ensure fill rate matches the calculated value"""
        if "total_shifts" in values and "filled_shifts" in values:
            if values["total_shifts"] > 0:
                calculated_rate = (values["filled_shifts"] / values["total_shifts"]) * 100
                if abs(v - calculated_rate) > 0.01:  # Allow small floating point differences
                    raise ValueError(f"Fill rate {v} doesn't match calculated rate {calculated_rate}")
        return v
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Generate a performance summary for the company
        
        Returns:
            Dictionary containing key performance indicators
        """
        return {
            "company_id": self.company_id,
            "period": self.period,
            "fill_rate": self.fill_rate,
            "performance_rating": self._calculate_performance_rating(),
            "areas_of_concern": self._identify_concerns(),
            "metrics_date": self.metrics_date.isoformat()
        }
    
    def _calculate_performance_rating(self) -> str:
        """Calculate overall performance rating based on metrics"""
        if self.fill_rate >= 90:
            return "excellent"
        elif self.fill_rate >= 75:
            return "good"
        elif self.fill_rate >= 60:
            return "fair"
        else:
            return "needs_improvement"
    
    def _identify_concerns(self) -> List[str]:
        """Identify areas of concern based on metrics"""
        concerns = []
        
        if self.fill_rate < 70:
            concerns.append("low_fill_rate")
        
        if self.cancellation_rate > 15:
            concerns.append("high_cancellation_rate")
        
        if self.avg_time_to_fill and self.avg_time_to_fill > 24:
            concerns.append("slow_fill_time")
        
        if self.worker_ratings and self.worker_ratings < 3.5:
            concerns.append("low_worker_satisfaction")
        
        # Check regional disparities
        if self.regional_breakdown:
            rates = list(self.regional_breakdown.values())
            if rates and (max(rates) - min(rates)) > 30:
                concerns.append("regional_disparities")
        
        return concerns