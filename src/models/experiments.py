"""
Module: models.experiments
Purpose: Track classification rule experiments and version control
Dependencies: pydantic, datetime, typing, enum

This module provides models for tracking experiments with classification
rules, enabling A/B testing, performance tracking, and rollback capabilities.

Classes:
    ExperimentStatus: Status of an experiment
    RuleVersion: Version control for classification rules
    ExperimentMetrics: Performance metrics for an experiment
    Experiment: Complete experiment tracking
    ExperimentComparison: Compare multiple experiments
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict
import hashlib
import json


class ExperimentStatus(str, Enum):
    """Status of a classification experiment"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class RuleVersion(BaseModel):
    """
    Version control for classification rules
    
    Attributes:
        version_id: Unique version identifier
        rule_hash: Hash of the rule configuration
        rules_config: Complete rule configuration
        created_at: When this version was created
        created_by: Who created this version
        parent_version: Previous version ID for tracking lineage
        change_summary: Summary of changes from parent
        is_baseline: Whether this is a baseline version
    """
    model_config = ConfigDict(validate_assignment=True)
    
    version_id: str = Field(..., description="Unique version identifier")
    rule_hash: str = Field(..., description="SHA256 hash of rules")
    rules_config: Dict[str, Any] = Field(..., description="Complete rule configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Creator identifier")
    parent_version: Optional[str] = Field(None, description="Parent version ID")
    change_summary: List[str] = Field(default_factory=list)
    is_baseline: bool = Field(default=False, description="Baseline version flag")
    
    @validator("rule_hash", always=True)
    def compute_rule_hash(cls, v, values):
        """Compute hash if not provided"""
        if not v and "rules_config" in values:
            config_str = json.dumps(values["rules_config"], sort_keys=True)
            return hashlib.sha256(config_str.encode()).hexdigest()
        return v
    
    def get_changes_from_parent(self, parent: Optional['RuleVersion']) -> List[str]:
        """Compare with parent version to identify changes"""
        if not parent:
            return ["Initial version"]
        
        changes = []
        # Deep comparison logic would go here
        # For now, return the stored change summary
        return self.change_summary or ["Configuration updated"]


class ExperimentMetrics(BaseModel):
    """
    Performance metrics for an experiment
    
    Attributes:
        total_classifications: Total number of classifications made
        accuracy_score: Overall accuracy (if ground truth available)
        precision_by_type: Precision scores by classification type
        recall_by_type: Recall scores by classification type
        confidence_distribution: Distribution of confidence scores
        processing_time_p50: Median processing time
        processing_time_p95: 95th percentile processing time
        error_rate: Classification error rate
        feedback_scores: Human feedback scores if available
    """
    model_config = ConfigDict(validate_assignment=True)
    
    total_classifications: int = Field(default=0, ge=0)
    accuracy_score: Optional[float] = Field(None, ge=0, le=1)
    precision_by_type: Dict[str, float] = Field(default_factory=dict)
    recall_by_type: Dict[str, float] = Field(default_factory=dict)
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    processing_time_p50: float = Field(default=0.0, ge=0)
    processing_time_p95: float = Field(default=0.0, ge=0)
    error_rate: float = Field(default=0.0, ge=0, le=1)
    feedback_scores: Optional[Dict[str, float]] = Field(None)
    
    def calculate_f1_scores(self) -> Dict[str, float]:
        """Calculate F1 scores for each classification type"""
        f1_scores = {}
        for class_type in self.precision_by_type:
            if class_type in self.recall_by_type:
                precision = self.precision_by_type[class_type]
                recall = self.recall_by_type[class_type]
                if precision + recall > 0:
                    f1 = 2 * (precision * recall) / (precision + recall)
                    f1_scores[class_type] = round(f1, 3)
        return f1_scores
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate a performance summary"""
        return {
            "total_classifications": self.total_classifications,
            "accuracy": self.accuracy_score,
            "error_rate": self.error_rate,
            "f1_scores": self.calculate_f1_scores(),
            "avg_processing_time_ms": self.processing_time_p50,
            "confidence_stats": self._calculate_confidence_stats()
        }
    
    def _calculate_confidence_stats(self) -> Dict[str, float]:
        """Calculate statistics from confidence distribution"""
        if not self.confidence_distribution:
            return {}
        
        total = sum(self.confidence_distribution.values())
        if total == 0:
            return {}
        
        # Calculate weighted average confidence
        weighted_sum = sum(
            float(conf) * count 
            for conf, count in self.confidence_distribution.items()
        )
        avg_confidence = weighted_sum / total
        
        # Calculate high confidence percentage (>0.8)
        high_conf_count = sum(
            count for conf, count in self.confidence_distribution.items()
            if float(conf) > 0.8
        )
        high_conf_pct = (high_conf_count / total) * 100
        
        return {
            "average_confidence": round(avg_confidence, 3),
            "high_confidence_pct": round(high_conf_pct, 2)
        }


class Experiment(BaseModel):
    """
    Complete experiment tracking for classification rules
    
    Attributes:
        experiment_id: Unique experiment identifier
        name: Human-readable experiment name
        description: Detailed description of the experiment
        status: Current experiment status
        rule_version: Version of rules being tested
        baseline_version: Baseline version for comparison
        start_date: When experiment started
        end_date: When experiment ended
        sample_size: Number of companies in experiment
        sample_criteria: Criteria for selecting sample
        metrics: Performance metrics
        tags: Tags for categorization
        notes: Additional notes and observations
    """
    model_config = ConfigDict(use_enum_values=True)
    
    experiment_id: str = Field(..., description="Unique experiment ID")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., description="Experiment description")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    rule_version: RuleVersion = Field(..., description="Rules being tested")
    baseline_version: Optional[RuleVersion] = Field(None, description="Baseline for comparison")
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    sample_size: int = Field(default=0, ge=0)
    sample_criteria: Dict[str, Any] = Field(default_factory=dict)
    metrics: ExperimentMetrics = Field(default_factory=ExperimentMetrics)
    tags: Set[str] = Field(default_factory=set)
    notes: List[Dict[str, Any]] = Field(default_factory=list)
    
    @validator("end_date")
    def validate_end_date(cls, v, values):
        """Ensure end date is after start date"""
        if v and "start_date" in values and values["start_date"]:
            if v < values["start_date"]:
                raise ValueError("End date must be after start date")
        return v
    
    def add_note(self, note: str, author: str) -> None:
        """Add a timestamped note to the experiment"""
        self.notes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "author": author,
            "note": note
        })
    
    def can_transition_to(self, new_status: ExperimentStatus) -> bool:
        """Check if status transition is valid"""
        valid_transitions = {
            ExperimentStatus.DRAFT: [ExperimentStatus.ACTIVE, ExperimentStatus.ARCHIVED],
            ExperimentStatus.ACTIVE: [ExperimentStatus.PAUSED, ExperimentStatus.COMPLETED, ExperimentStatus.FAILED],
            ExperimentStatus.PAUSED: [ExperimentStatus.ACTIVE, ExperimentStatus.COMPLETED, ExperimentStatus.FAILED],
            ExperimentStatus.COMPLETED: [ExperimentStatus.ARCHIVED],
            ExperimentStatus.FAILED: [ExperimentStatus.ARCHIVED],
            ExperimentStatus.ARCHIVED: []
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def get_duration_days(self) -> Optional[int]:
        """Calculate experiment duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        elif self.start_date and self.status == ExperimentStatus.ACTIVE:
            return (datetime.utcnow() - self.start_date).days
        return None


class ExperimentComparison(BaseModel):
    """
    Compare multiple experiments
    
    Attributes:
        comparison_id: Unique comparison identifier
        experiment_ids: List of experiment IDs being compared
        comparison_metrics: Metrics comparing experiments
        winner: Winning experiment ID if determined
        statistical_significance: Statistical significance of results
        created_at: When comparison was created
        analysis_notes: Notes about the comparison
    """
    model_config = ConfigDict(validate_assignment=True)
    
    comparison_id: str = Field(..., description="Unique comparison ID")
    experiment_ids: List[str] = Field(..., min_items=2)
    comparison_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    winner: Optional[str] = Field(None, description="Winning experiment ID")
    statistical_significance: Optional[float] = Field(None, ge=0, le=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_notes: str = Field(default="", description="Analysis notes")
    
    @validator("winner")
    def validate_winner(cls, v, values):
        """Ensure winner is one of the compared experiments"""
        if v and "experiment_ids" in values:
            if v not in values["experiment_ids"]:
                raise ValueError("Winner must be one of the compared experiments")
        return v
    
    def add_metric_comparison(self, metric_name: str, experiment_values: Dict[str, float]) -> None:
        """Add a metric comparison across experiments"""
        self.comparison_metrics[metric_name] = {
            "values": experiment_values,
            "best_value": max(experiment_values.values()),
            "worst_value": min(experiment_values.values()),
            "variance": self._calculate_variance(list(experiment_values.values()))
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance, 4)
    
    def determine_winner(self, key_metric: str = "accuracy_score", min_significance: float = 0.95) -> Optional[str]:
        """Determine winner based on key metric and significance"""
        if key_metric not in self.comparison_metrics:
            return None
        
        metric_values = self.comparison_metrics[key_metric]["values"]
        if not metric_values:
            return None
        
        # Find experiment with best value
        best_experiment = max(metric_values.items(), key=lambda x: x[1])
        
        # Check if statistically significant (simplified check)
        if self.statistical_significance and self.statistical_significance >= min_significance:
            self.winner = best_experiment[0]
            return self.winner
        
        return None


class ExperimentRepository(BaseModel):
    """
    Repository for managing experiments
    
    Attributes:
        experiments: All experiments indexed by ID
        active_experiments: Currently active experiment IDs
        default_baseline: Default baseline version ID
    """
    experiments: Dict[str, Experiment] = Field(default_factory=dict)
    active_experiments: Set[str] = Field(default_factory=set)
    default_baseline: Optional[str] = Field(None)
    
    def add_experiment(self, experiment: Experiment) -> None:
        """Add an experiment to the repository"""
        self.experiments[experiment.experiment_id] = experiment
        if experiment.status == ExperimentStatus.ACTIVE:
            self.active_experiments.add(experiment.experiment_id)
    
    def get_active_experiments(self) -> List[Experiment]:
        """Get all active experiments"""
        return [
            self.experiments[exp_id] 
            for exp_id in self.active_experiments 
            if exp_id in self.experiments
        ]
    
    def get_experiments_by_tag(self, tag: str) -> List[Experiment]:
        """Get experiments with a specific tag"""
        return [
            exp for exp in self.experiments.values()
            if tag in exp.tags
        ]
    
    def get_best_performing(self, metric: str = "accuracy_score") -> Optional[Experiment]:
        """Get the best performing completed experiment"""
        completed = [
            exp for exp in self.experiments.values()
            if exp.status == ExperimentStatus.COMPLETED
        ]
        
        if not completed:
            return None
        
        # Sort by the specified metric
        def get_metric_value(exp: Experiment) -> float:
            if metric == "accuracy_score":
                return exp.metrics.accuracy_score or 0.0
            elif metric == "error_rate":
                return 1 - exp.metrics.error_rate  # Invert for sorting
            else:
                return 0.0
        
        return max(completed, key=get_metric_value)