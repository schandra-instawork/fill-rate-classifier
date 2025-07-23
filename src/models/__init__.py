"""
Models Package

Purpose: Data models and schemas for the fill rate classifier
Dependencies: pydantic for validation, datetime for timestamps

This package provides strongly-typed data models with built-in validation
for all entities in the fill rate classification system.
"""

from .company import Company, CompanyMetrics
from .classification import (
    Classification,
    ClassificationResult,
    ClassificationConfidence,
    ClassificationType,
    ResponseType
)
from .schemas import (
    APIResponse,
    APIResponseSchema,
    ClassificationRequest,
    ClassificationResponse
)
from .experiments import (
    Experiment,
    ExperimentStatus,
    RuleVersion,
    ExperimentMetrics,
    ExperimentComparison,
    ExperimentRepository
)

__all__ = [
    "Company",
    "CompanyMetrics",
    "Classification",
    "ClassificationResult",
    "ClassificationConfidence",
    "ClassificationType",
    "ResponseType",
    "APIResponse",
    "APIResponseSchema",
    "ClassificationRequest",
    "ClassificationResponse",
    "Experiment",
    "ExperimentStatus",
    "RuleVersion",
    "ExperimentMetrics",
    "ExperimentComparison",
    "ExperimentRepository",
]