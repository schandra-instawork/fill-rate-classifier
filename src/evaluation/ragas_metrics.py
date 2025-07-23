"""
Module: evaluation.ragas_metrics
Purpose: RAGAS-inspired metrics for classification evaluation
Dependencies: pydantic, typing, numpy

This module implements RAGAS-inspired evaluation metrics adapted for
classification systems, focusing on faithfulness, relevancy, and precision
of our classification rules.

Classes:
    ClassificationFaithfulness: Measures if classification matches API response
    ClassificationRelevancy: Measures if classification is relevant to issue
    ClassificationPrecision: Measures precision of classification rules
    ClassificationRecall: Measures recall of classification rules
    RAGASEvaluator: Main evaluator combining all metrics
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import defaultdict
import re

from src.models.classification import Classification, ClassificationResult
from src.models.experiments import ExperimentMetrics


@dataclass
class EvaluationSample:
    """Single sample for evaluation"""
    company_id: str
    api_response: str
    predicted_classifications: List[Classification]
    ground_truth_classifications: Optional[List[str]] = None
    human_feedback: Optional[Dict[str, Any]] = None


class ClassificationFaithfulness:
    """
    Measures faithfulness of classifications to API response
    
    This metric evaluates whether the classifications are faithful
    to the actual content in the API response, similar to RAGAS
    faithfulness metric.
    """
    
    def __init__(self, pattern_weights: Optional[Dict[str, float]] = None):
        """
        Initialize faithfulness evaluator
        
        Args:
            pattern_weights: Weights for different pattern types
        """
        self.pattern_weights = pattern_weights or {
            "exact_match": 1.0,
            "partial_match": 0.7,
            "semantic_match": 0.5
        }
    
    def calculate(self, sample: EvaluationSample) -> float:
        """
        Calculate faithfulness score
        
        Returns:
            Score between 0 and 1 indicating faithfulness
        """
        if not sample.predicted_classifications:
            return 0.0
        
        scores = []
        api_text_lower = sample.api_response.lower()
        
        for classification in sample.predicted_classifications:
            matched_text = classification.matched_text.lower()
            
            # Check exact match
            if matched_text in api_text_lower:
                scores.append(self.pattern_weights["exact_match"])
            # Check partial match (all words present)
            elif all(word in api_text_lower for word in matched_text.split()):
                scores.append(self.pattern_weights["partial_match"])
            # Check semantic match (key terms present)
            else:
                key_terms = self._extract_key_terms(matched_text)
                if any(term in api_text_lower for term in key_terms):
                    scores.append(self.pattern_weights["semantic_match"])
                else:
                    scores.append(0.0)
        
        return np.mean(scores) if scores else 0.0
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Simple implementation - in production would use NLP
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been"}
        words = text.lower().split()
        return [w for w in words if w not in stopwords and len(w) > 3]


class ClassificationRelevancy:
    """
    Measures relevancy of classifications to the actual issue
    
    This metric evaluates whether the classifications are relevant
    to solving the fill rate problem, inspired by RAGAS answer
    relevancy metric.
    """
    
    def __init__(self):
        """Initialize relevancy evaluator"""
        self.relevancy_patterns = {
            "low_pay_rate": ["pay", "wage", "salary", "compensation", "rate"],
            "geographic_coverage": ["location", "area", "region", "coverage", "distance"],
            "shift_timing_mismatch": ["time", "shift", "schedule", "timing", "hours"],
            "contract_renegotiation": ["contract", "agreement", "terms", "renewal"],
            "market_analysis": ["market", "competition", "analysis", "trends"],
            "partner_meeting": ["meeting", "discussion", "review", "escalation"]
        }
    
    def calculate(self, sample: EvaluationSample) -> float:
        """
        Calculate relevancy score
        
        Returns:
            Score between 0 and 1 indicating relevancy
        """
        if not sample.predicted_classifications:
            return 0.0
        
        scores = []
        api_text_lower = sample.api_response.lower()
        
        for classification in sample.predicted_classifications:
            class_type = classification.classification_type
            
            if class_type in self.relevancy_patterns:
                # Check if relevant keywords are present
                keywords = self.relevancy_patterns[class_type]
                keyword_matches = sum(1 for kw in keywords if kw in api_text_lower)
                relevancy_score = keyword_matches / len(keywords)
                
                # Boost score if confidence is high
                if classification.confidence.overall_score > 0.8:
                    relevancy_score = min(1.0, relevancy_score * 1.2)
                
                scores.append(relevancy_score)
            else:
                scores.append(0.5)  # Unknown classification types get neutral score
        
        return np.mean(scores) if scores else 0.0


class ClassificationPrecision:
    """
    Measures precision of classification rules
    
    Precision = True Positives / (True Positives + False Positives)
    """
    
    def calculate(self, samples: List[EvaluationSample]) -> Dict[str, float]:
        """
        Calculate precision by classification type
        
        Returns:
            Dictionary mapping classification types to precision scores
        """
        if not any(s.ground_truth_classifications for s in samples):
            return {}
        
        tp_by_type = defaultdict(int)
        fp_by_type = defaultdict(int)
        
        for sample in samples:
            if not sample.ground_truth_classifications:
                continue
            
            predicted_types = {c.classification_type for c in sample.predicted_classifications}
            ground_truth_types = set(sample.ground_truth_classifications)
            
            for pred_type in predicted_types:
                if pred_type in ground_truth_types:
                    tp_by_type[pred_type] += 1
                else:
                    fp_by_type[pred_type] += 1
        
        precision_by_type = {}
        for class_type in set(tp_by_type.keys()) | set(fp_by_type.keys()):
            tp = tp_by_type[class_type]
            fp = fp_by_type[class_type]
            if tp + fp > 0:
                precision_by_type[class_type] = tp / (tp + fp)
            else:
                precision_by_type[class_type] = 0.0
        
        return precision_by_type


class ClassificationRecall:
    """
    Measures recall of classification rules
    
    Recall = True Positives / (True Positives + False Negatives)
    """
    
    def calculate(self, samples: List[EvaluationSample]) -> Dict[str, float]:
        """
        Calculate recall by classification type
        
        Returns:
            Dictionary mapping classification types to recall scores
        """
        if not any(s.ground_truth_classifications for s in samples):
            return {}
        
        tp_by_type = defaultdict(int)
        fn_by_type = defaultdict(int)
        
        for sample in samples:
            if not sample.ground_truth_classifications:
                continue
            
            predicted_types = {c.classification_type for c in sample.predicted_classifications}
            ground_truth_types = set(sample.ground_truth_classifications)
            
            for gt_type in ground_truth_types:
                if gt_type in predicted_types:
                    tp_by_type[gt_type] += 1
                else:
                    fn_by_type[gt_type] += 1
        
        recall_by_type = {}
        for class_type in set(tp_by_type.keys()) | set(fn_by_type.keys()):
            tp = tp_by_type[class_type]
            fn = fn_by_type[class_type]
            if tp + fn > 0:
                recall_by_type[class_type] = tp / (tp + fn)
            else:
                recall_by_type[class_type] = 0.0
        
        return recall_by_type


class RAGASEvaluator:
    """
    Main evaluator combining all RAGAS-inspired metrics
    
    This evaluator provides a comprehensive evaluation of classification
    performance using multiple metrics inspired by the RAGAS framework.
    """
    
    def __init__(self):
        """Initialize RAGAS evaluator"""
        self.faithfulness_evaluator = ClassificationFaithfulness()
        self.relevancy_evaluator = ClassificationRelevancy()
        self.precision_evaluator = ClassificationPrecision()
        self.recall_evaluator = ClassificationRecall()
    
    def evaluate_single(self, sample: EvaluationSample) -> Dict[str, float]:
        """
        Evaluate a single sample
        
        Returns:
            Dictionary of metric scores
        """
        return {
            "faithfulness": self.faithfulness_evaluator.calculate(sample),
            "relevancy": self.relevancy_evaluator.calculate(sample),
            "confidence": self._calculate_avg_confidence(sample),
            "classification_count": len(sample.predicted_classifications)
        }
    
    def evaluate_batch(self, samples: List[EvaluationSample]) -> ExperimentMetrics:
        """
        Evaluate a batch of samples
        
        Returns:
            ExperimentMetrics with comprehensive evaluation results
        """
        # Calculate individual metrics
        individual_scores = [self.evaluate_single(s) for s in samples]
        
        # Calculate precision and recall
        precision_by_type = self.precision_evaluator.calculate(samples)
        recall_by_type = self.recall_evaluator.calculate(samples)
        
        # Calculate confidence distribution
        all_confidences = []
        for sample in samples:
            for classification in sample.predicted_classifications:
                all_confidences.append(classification.confidence.overall_score)
        
        confidence_bins = self._bin_confidences(all_confidences)
        
        # Calculate overall metrics
        avg_faithfulness = np.mean([s["faithfulness"] for s in individual_scores])
        avg_relevancy = np.mean([s["relevancy"] for s in individual_scores])
        
        # Create experiment metrics
        metrics = ExperimentMetrics(
            total_classifications=sum(s["classification_count"] for s in individual_scores),
            accuracy_score=self._calculate_accuracy(samples),
            precision_by_type=precision_by_type,
            recall_by_type=recall_by_type,
            confidence_distribution=confidence_bins,
            feedback_scores={
                "faithfulness": avg_faithfulness,
                "relevancy": avg_relevancy
            }
        )
        
        return metrics
    
    def compare_rule_versions(
        self, 
        samples_v1: List[EvaluationSample],
        samples_v2: List[EvaluationSample]
    ) -> Dict[str, Any]:
        """
        Compare two rule versions
        
        Returns:
            Comparison results with statistical significance
        """
        metrics_v1 = self.evaluate_batch(samples_v1)
        metrics_v2 = self.evaluate_batch(samples_v2)
        
        # Calculate F1 scores
        f1_v1 = metrics_v1.calculate_f1_scores()
        f1_v2 = metrics_v2.calculate_f1_scores()
        
        # Compare key metrics
        comparison = {
            "version_comparison": {
                "v1_accuracy": metrics_v1.accuracy_score,
                "v2_accuracy": metrics_v2.accuracy_score,
                "accuracy_improvement": (metrics_v2.accuracy_score or 0) - (metrics_v1.accuracy_score or 0)
            },
            "f1_comparison": {
                "v1": f1_v1,
                "v2": f1_v2
            },
            "feedback_comparison": {
                "v1": metrics_v1.feedback_scores,
                "v2": metrics_v2.feedback_scores
            },
            "recommendation": self._generate_recommendation(metrics_v1, metrics_v2)
        }
        
        return comparison
    
    def _calculate_avg_confidence(self, sample: EvaluationSample) -> float:
        """Calculate average confidence for a sample"""
        if not sample.predicted_classifications:
            return 0.0
        confidences = [c.confidence.overall_score for c in sample.predicted_classifications]
        return np.mean(confidences)
    
    def _bin_confidences(self, confidences: List[float]) -> Dict[str, int]:
        """Bin confidence scores"""
        bins = {
            "0.0-0.5": 0,
            "0.5-0.7": 0,
            "0.7-0.8": 0,
            "0.8-0.9": 0,
            "0.9-1.0": 0
        }
        
        for conf in confidences:
            if conf <= 0.5:
                bins["0.0-0.5"] += 1
            elif conf <= 0.7:
                bins["0.5-0.7"] += 1
            elif conf <= 0.8:
                bins["0.7-0.8"] += 1
            elif conf <= 0.9:
                bins["0.8-0.9"] += 1
            else:
                bins["0.9-1.0"] += 1
        
        return bins
    
    def _calculate_accuracy(self, samples: List[EvaluationSample]) -> Optional[float]:
        """Calculate overall accuracy if ground truth available"""
        samples_with_truth = [s for s in samples if s.ground_truth_classifications]
        if not samples_with_truth:
            return None
        
        correct = 0
        total = 0
        
        for sample in samples_with_truth:
            predicted_types = {c.classification_type for c in sample.predicted_classifications}
            ground_truth_types = set(sample.ground_truth_classifications)
            
            # Consider it correct if all ground truth classifications are found
            if ground_truth_types.issubset(predicted_types):
                correct += 1
            total += 1
        
        return correct / total if total > 0 else 0.0
    
    def _generate_recommendation(
        self, 
        metrics_v1: ExperimentMetrics, 
        metrics_v2: ExperimentMetrics
    ) -> str:
        """Generate recommendation based on comparison"""
        v1_score = self._calculate_overall_score(metrics_v1)
        v2_score = self._calculate_overall_score(metrics_v2)
        
        if v2_score > v1_score * 1.1:  # 10% improvement threshold
            return "Recommend adopting V2 - significant improvement"
        elif v2_score > v1_score:
            return "V2 shows marginal improvement - consider testing further"
        elif v1_score > v2_score * 1.1:
            return "Recommend keeping V1 - V2 shows regression"
        else:
            return "No significant difference - maintain current version"
    
    def _calculate_overall_score(self, metrics: ExperimentMetrics) -> float:
        """Calculate overall score for metrics"""
        # Weighted combination of metrics
        accuracy_weight = 0.4
        faithfulness_weight = 0.3
        relevancy_weight = 0.3
        
        accuracy = metrics.accuracy_score or 0.5
        faithfulness = metrics.feedback_scores.get("faithfulness", 0.5) if metrics.feedback_scores else 0.5
        relevancy = metrics.feedback_scores.get("relevancy", 0.5) if metrics.feedback_scores else 0.5
        
        return (accuracy * accuracy_weight + 
                faithfulness * faithfulness_weight + 
                relevancy * relevancy_weight)