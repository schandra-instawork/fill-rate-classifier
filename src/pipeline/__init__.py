"""
Pipeline Package
Purpose: Batch processing and orchestration

This package provides batch processing capabilities for
analyzing multiple companies at scale.

Modules:
    batch_processor: Main batch processing pipeline
"""

from .batch_processor import BatchProcessor, BatchJob, ProcessingStatus

__all__ = [
    "BatchProcessor",
    "BatchJob", 
    "ProcessingStatus"
]