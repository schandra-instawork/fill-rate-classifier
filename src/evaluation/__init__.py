"""
Evaluation Package

Purpose: Evaluation metrics and tools for classification performance
Dependencies: numpy, typing

This package provides comprehensive evaluation tools inspired by
the RAGAS framework for measuring classification quality.
"""

from .ragas_metrics import (
    EvaluationSample,
    ClassificationFaithfulness,
    ClassificationRelevancy,
    ClassificationPrecision,
    ClassificationRecall,
    RAGASEvaluator
)

__all__ = [
    "EvaluationSample",
    "ClassificationFaithfulness",
    "ClassificationRelevancy",
    "ClassificationPrecision",
    "ClassificationRecall",
    "RAGASEvaluator",
]