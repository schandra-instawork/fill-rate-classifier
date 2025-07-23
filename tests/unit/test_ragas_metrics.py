"""
Module: tests.unit.test_ragas_metrics
Purpose: Unit tests for RAGAS-inspired evaluation metrics
Dependencies: pytest, numpy

This module contains comprehensive tests for the evaluation metrics
inspired by the RAGAS framework.
"""

import pytest
import numpy as np
from datetime import datetime

from src.evaluation.ragas_metrics import (
    EvaluationSample,
    ClassificationFaithfulness,
    ClassificationRelevancy,
    ClassificationPrecision,
    ClassificationRecall,
    RAGASEvaluator
)
from src.models.classification import (
    Classification,
    ClassificationConfidence,
    ResponseType,
    ClassificationType
)


class TestClassificationFaithfulness:
    """Test suite for ClassificationFaithfulness"""
    
    def test_exact_match_faithfulness(self):
        """Test faithfulness with exact text match"""
        evaluator = ClassificationFaithfulness()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type=ClassificationType.EMAIL_X,
            confidence=confidence,
            matched_text="pay rates below market"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="The fill rates are low because pay rates below market average",
            predicted_classifications=[classification]
        )
        
        score = evaluator.calculate(sample)
        assert score == 1.0  # Exact match should get full score
    
    def test_partial_match_faithfulness(self):
        """Test faithfulness with partial text match"""
        evaluator = ClassificationFaithfulness()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type=ClassificationType.EMAIL_X,
            confidence=confidence,
            matched_text="low pay market"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="Pay rates are low and below the market average",
            predicted_classifications=[classification]
        )
        
        score = evaluator.calculate(sample)
        assert score == 0.7  # Partial match should get partial score
    
    def test_no_match_faithfulness(self):
        """Test faithfulness with no text match"""
        evaluator = ClassificationFaithfulness()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type=ClassificationType.EMAIL_X,
            confidence=confidence,
            matched_text="geographic coverage issues"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="The shift times don't align with worker availability",
            predicted_classifications=[classification]
        )
        
        score = evaluator.calculate(sample)
        assert score == 0.0  # No match should get zero score


class TestClassificationRelevancy:
    """Test suite for ClassificationRelevancy"""
    
    def test_high_relevancy_score(self):
        """Test high relevancy when keywords match"""
        evaluator = ClassificationRelevancy()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="low_pay_rate",
            confidence=confidence,
            matched_text="pay rates below market"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="Low fill rates due to pay and wage issues, compensation below market rate",
            predicted_classifications=[classification]
        )
        
        score = evaluator.calculate(sample)
        assert score > 0.8  # Should have high relevancy
    
    def test_medium_relevancy_score(self):
        """Test medium relevancy with some keyword matches"""
        evaluator = ClassificationRelevancy()
        
        confidence = ClassificationConfidence(
            overall_score=0.6,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="geographic_coverage",
            confidence=confidence,
            matched_text="location issues"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="Some locations have limited worker coverage",
            predicted_classifications=[classification]
        )
        
        score = evaluator.calculate(sample)
        assert 0.3 < score < 0.8  # Should have medium relevancy
    
    def test_unknown_classification_relevancy(self):
        """Test relevancy for unknown classification type"""
        evaluator = ClassificationRelevancy()
        
        confidence = ClassificationConfidence(
            overall_score=0.8,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.ACTION,
            classification_type="unknown_issue",
            confidence=confidence,
            matched_text="unknown problem"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="There's an unknown issue affecting fill rates",
            predicted_classifications=[classification]
        )
        
        score = evaluator.calculate(sample)
        assert score == 0.5  # Unknown types get neutral score


class TestClassificationPrecision:
    """Test suite for ClassificationPrecision"""
    
    def test_perfect_precision(self):
        """Test perfect precision calculation"""
        evaluator = ClassificationPrecision()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="low_pay_rate",
            confidence=confidence,
            matched_text="pay below market"
        )
        
        samples = [
            EvaluationSample(
                company_id="comp_1",
                api_response="pay rates are low",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            ),
            EvaluationSample(
                company_id="comp_2",
                api_response="wages below average",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            )
        ]
        
        precision = evaluator.calculate(samples)
        assert precision["low_pay_rate"] == 1.0
    
    def test_partial_precision(self):
        """Test partial precision with false positives"""
        evaluator = ClassificationPrecision()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="low_pay_rate",
            confidence=confidence,
            matched_text="pay below market"
        )
        
        samples = [
            EvaluationSample(
                company_id="comp_1",
                api_response="pay rates are low",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            ),
            EvaluationSample(
                company_id="comp_2",
                api_response="location issues",
                predicted_classifications=[classification],
                ground_truth_classifications=["geographic_coverage"]
            )
        ]
        
        precision = evaluator.calculate(samples)
        assert precision["low_pay_rate"] == 0.5  # 1 TP, 1 FP


class TestClassificationRecall:
    """Test suite for ClassificationRecall"""
    
    def test_perfect_recall(self):
        """Test perfect recall calculation"""
        evaluator = ClassificationRecall()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="low_pay_rate",
            confidence=confidence,
            matched_text="pay below market"
        )
        
        samples = [
            EvaluationSample(
                company_id="comp_1",
                api_response="pay rates are low",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            ),
            EvaluationSample(
                company_id="comp_2",
                api_response="wages below average",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            )
        ]
        
        recall = evaluator.calculate(samples)
        assert recall["low_pay_rate"] == 1.0
    
    def test_partial_recall(self):
        """Test partial recall with false negatives"""
        evaluator = ClassificationRecall()
        
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="low_pay_rate",
            confidence=confidence,
            matched_text="pay below market"
        )
        
        samples = [
            EvaluationSample(
                company_id="comp_1",
                api_response="pay rates are low",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            ),
            EvaluationSample(
                company_id="comp_2",
                api_response="wages below average",
                predicted_classifications=[],  # Missing classification
                ground_truth_classifications=["low_pay_rate"]
            )
        ]
        
        recall = evaluator.calculate(samples)
        assert recall["low_pay_rate"] == 0.5  # 1 TP, 1 FN


class TestRAGASEvaluator:
    """Test suite for RAGASEvaluator"""
    
    def test_single_sample_evaluation(self):
        """Test evaluation of a single sample"""
        evaluator = RAGASEvaluator()
        
        confidence = ClassificationConfidence(
            overall_score=0.85,
            explanation="Test confidence"
        )
        
        classification = Classification(
            id="test_001",
            response_type=ResponseType.EMAIL,
            classification_type="low_pay_rate",
            confidence=confidence,
            matched_text="pay rates below market"
        )
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="Fill rates are low because pay rates below market average",
            predicted_classifications=[classification]
        )
        
        scores = evaluator.evaluate_single(sample)
        
        assert "faithfulness" in scores
        assert "relevancy" in scores
        assert "confidence" in scores
        assert "classification_count" in scores
        
        assert scores["faithfulness"] > 0.8  # Should have high faithfulness
        assert scores["confidence"] == 0.85
        assert scores["classification_count"] == 1
    
    def test_batch_evaluation(self):
        """Test batch evaluation with multiple samples"""
        evaluator = RAGASEvaluator()
        
        # Create test samples
        samples = []
        for i in range(3):
            confidence = ClassificationConfidence(
                overall_score=0.8 + i * 0.05,
                explanation="Test confidence"
            )
            
            classification = Classification(
                id=f"test_{i:03d}",
                response_type=ResponseType.EMAIL,
                classification_type="low_pay_rate",
                confidence=confidence,
                matched_text="pay rates below market"
            )
            
            sample = EvaluationSample(
                company_id=f"comp_{i}",
                api_response=f"Fill rates are low because pay rates below market average {i}",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            )
            samples.append(sample)
        
        metrics = evaluator.evaluate_batch(samples)
        
        assert metrics.total_classifications == 3
        assert metrics.accuracy_score is not None
        assert metrics.precision_by_type is not None
        assert metrics.recall_by_type is not None
        assert metrics.confidence_distribution is not None
        assert metrics.feedback_scores is not None
    
    def test_rule_version_comparison(self):
        """Test comparison between two rule versions"""
        evaluator = RAGASEvaluator()
        
        # Create samples for version 1 (lower performance)
        samples_v1 = []
        for i in range(2):
            confidence = ClassificationConfidence(
                overall_score=0.6,
                explanation="Test confidence"
            )
            
            classification = Classification(
                id=f"v1_{i:03d}",
                response_type=ResponseType.EMAIL,
                classification_type="low_pay_rate",
                confidence=confidence,
                matched_text="pay issues"
            )
            
            sample = EvaluationSample(
                company_id=f"comp_{i}",
                api_response="Pay rates are below market average",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            )
            samples_v1.append(sample)
        
        # Create samples for version 2 (higher performance)
        samples_v2 = []
        for i in range(2):
            confidence = ClassificationConfidence(
                overall_score=0.9,
                explanation="Test confidence"
            )
            
            classification = Classification(
                id=f"v2_{i:03d}",
                response_type=ResponseType.EMAIL,
                classification_type="low_pay_rate",
                confidence=confidence,
                matched_text="pay rates below market"
            )
            
            sample = EvaluationSample(
                company_id=f"comp_{i}",
                api_response="Pay rates are below market average",
                predicted_classifications=[classification],
                ground_truth_classifications=["low_pay_rate"]
            )
            samples_v2.append(sample)
        
        comparison = evaluator.compare_rule_versions(samples_v1, samples_v2)
        
        assert "version_comparison" in comparison
        assert "f1_comparison" in comparison
        assert "feedback_comparison" in comparison
        assert "recommendation" in comparison
        
        # V2 should be better
        assert comparison["version_comparison"]["accuracy_improvement"] >= 0
    
    def test_empty_samples_handling(self):
        """Test handling of empty sample lists"""
        evaluator = RAGASEvaluator()
        
        sample = EvaluationSample(
            company_id="comp_123",
            api_response="Some API response",
            predicted_classifications=[]
        )
        
        scores = evaluator.evaluate_single(sample)
        assert scores["faithfulness"] == 0.0
        assert scores["relevancy"] == 0.0
        assert scores["confidence"] == 0.0
        assert scores["classification_count"] == 0