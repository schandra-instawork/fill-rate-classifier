"""
Module: tests.unit.test_models
Purpose: Comprehensive unit tests for data models
Dependencies: pytest, pydantic, datetime, hypothesis

This module contains extensive tests for all data models, including
validation, edge cases, and property-based testing using Hypothesis.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from hypothesis import given, strategies as st
from pydantic import ValidationError

from src.models.company import Company, CompanyStatus, CompanyMetrics, MetricPeriod
from src.models.classification import (
    ResponseType, ClassificationType, ClassificationConfidence,
    Classification, ClassificationResult
)
from src.models.schemas import (
    APIResponse, APIResponseSchema, ClassificationRequest,
    ClassificationResponse, BatchClassificationStatus
)


class TestCompanyModel:
    """Test suite for Company model"""
    
    def test_valid_company_creation(self):
        """Test creating a valid company"""
        company = Company(
            id="comp_123",
            name="Test Company",
            location="San Francisco, CA",
            timezone="America/Los_Angeles"
        )
        assert company.id == "comp_123"
        assert company.name == "Test Company"
        assert company.status == CompanyStatus.ACTIVE
        assert company.location == "San Francisco, CA"
        assert company.timezone == "America/Los_Angeles"
        assert isinstance(company.created_at, datetime)
        assert isinstance(company.updated_at, datetime)
    
    def test_company_validation_errors(self):
        """Test company validation rules"""
        # Test empty ID
        with pytest.raises(ValidationError) as exc_info:
            Company(id="", name="Test")
        assert "at least 1 character" in str(exc_info.value)
        
        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            Company(id="123", name="")
        assert "at least 1 character" in str(exc_info.value)
        
        # Test invalid status
        with pytest.raises(ValidationError) as exc_info:
            Company(id="123", name="Test", status="invalid")
        
    def test_company_metadata_validation(self):
        """Test metadata validation for sensitive keys"""
        with pytest.raises(ValidationError) as exc_info:
            Company(
                id="123",
                name="Test",
                metadata={"password": "secret123"}
            )
        assert "sensitive information" in str(exc_info.value)
    
    @given(
        company_id=st.text(min_size=1, max_size=50),
        company_name=st.text(min_size=1, max_size=255)
    )
    def test_company_property_based(self, company_id, company_name):
        """Property-based testing for company model"""
        company = Company(id=company_id, name=company_name)
        assert company.id == company_id
        assert company.name == company_name.strip()  # Pydantic strips whitespace


class TestCompanyMetrics:
    """Test suite for CompanyMetrics model"""
    
    def test_valid_metrics_creation(self):
        """Test creating valid company metrics"""
        metrics = CompanyMetrics(
            company_id="comp_123",
            fill_rate=85.5,
            total_shifts=100,
            filled_shifts=85,
            avg_time_to_fill=3.5,
            cancellation_rate=5.0,
            worker_ratings=4.2
        )
        assert metrics.company_id == "comp_123"
        assert metrics.fill_rate == 85.5
        assert metrics.total_shifts == 100
        assert metrics.filled_shifts == 85
        assert metrics.period == MetricPeriod.WEEKLY
    
    def test_metrics_validation_errors(self):
        """Test metrics validation rules"""
        # Test filled > total shifts
        with pytest.raises(ValidationError) as exc_info:
            CompanyMetrics(
                company_id="123",
                fill_rate=85.0,
                total_shifts=100,
                filled_shifts=101
            )
        assert "cannot exceed total shifts" in str(exc_info.value)
        
        # Test invalid fill rate
        with pytest.raises(ValidationError) as exc_info:
            CompanyMetrics(
                company_id="123",
                fill_rate=101.0,
                total_shifts=100,
                filled_shifts=85
            )
        assert "less than or equal to 100" in str(exc_info.value)
        
        # Test mismatched fill rate
        with pytest.raises(ValidationError) as exc_info:
            CompanyMetrics(
                company_id="123",
                fill_rate=50.0,  # Should be 85.0
                total_shifts=100,
                filled_shifts=85
            )
        assert "doesn't match calculated rate" in str(exc_info.value)
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        metrics = CompanyMetrics(
            company_id="123",
            fill_rate=65.0,
            total_shifts=100,
            filled_shifts=65,
            cancellation_rate=20.0,
            avg_time_to_fill=30.0,
            worker_ratings=3.2
        )
        
        summary = metrics.get_performance_summary()
        assert summary["performance_rating"] == "fair"
        assert "low_fill_rate" in summary["areas_of_concern"]
        assert "high_cancellation_rate" in summary["areas_of_concern"]
        assert "slow_fill_time" in summary["areas_of_concern"]
        assert "low_worker_satisfaction" in summary["areas_of_concern"]


class TestClassificationModels:
    """Test suite for classification models"""
    
    def test_classification_confidence(self):
        """Test ClassificationConfidence model"""
        confidence = ClassificationConfidence(
            overall_score=0.856789,
            pattern_matches=[{"pattern": "pay.*below", "score": 0.9}],
            rule_scores={"low_pay_rate": 0.85, "general": 0.7},
            confidence_factors=["keyword_match", "context_match"],
            explanation="High confidence due to exact pattern match"
        )
        
        assert confidence.overall_score == 0.857  # Rounded to 3 decimals
        assert confidence.is_high_confidence(0.8)
        assert not confidence.is_high_confidence(0.9)
        
        factors = confidence.get_contributing_factors()
        assert factors[0][0] == "low_pay_rate"
        assert factors[0][1] == 0.85
    
    def test_classification_creation(self):
        """Test Classification model"""
        confidence = ClassificationConfidence(
            overall_score=0.85,
            explanation="Pattern match found"
        )
        
        classification = Classification(
            id="class_001",
            response_type=ResponseType.EMAIL,
            classification_type=ClassificationType.EMAIL_X,
            confidence=confidence,
            matched_text="pay rates are below market average",
            recommended_template="low_pay_rate_alert",
            priority="high"
        )
        
        assert classification.response_type == ResponseType.EMAIL
        assert classification.classification_type == ClassificationType.EMAIL_X
        assert classification.priority == "high"
        
        action_item = classification.to_action_item()
        assert action_item["action"] == "send_email"
        assert action_item["email_template"] == "low_pay_rate_alert"
        assert action_item["confidence"] == 0.85
    
    def test_classification_validation(self):
        """Test classification validation rules"""
        confidence = ClassificationConfidence(
            overall_score=0.85,
            explanation="Test"
        )
        
        # Test template on action classification
        with pytest.raises(ValidationError) as exc_info:
            Classification(
                id="001",
                response_type=ResponseType.ACTION,
                classification_type=ClassificationType.ACTION_A,
                confidence=confidence,
                matched_text="test",
                recommended_template="template_id"
            )
        assert "only be set for email" in str(exc_info.value)
        
        # Test invalid priority
        with pytest.raises(ValidationError) as exc_info:
            Classification(
                id="001",
                response_type=ResponseType.EMAIL,
                classification_type=ClassificationType.EMAIL_X,
                confidence=confidence,
                matched_text="test",
                priority="urgent"  # Invalid
            )
    
    def test_classification_result(self):
        """Test ClassificationResult model"""
        confidence = ClassificationConfidence(
            overall_score=0.9,
            explanation="High confidence match"
        )
        
        classification1 = Classification(
            id="001",
            response_type=ResponseType.EMAIL,
            classification_type=ClassificationType.EMAIL_X,
            confidence=confidence,
            matched_text="low pay rates"
        )
        
        classification2 = Classification(
            id="002",
            response_type=ResponseType.ACTION,
            classification_type=ClassificationType.ACTION_A,
            confidence=ClassificationConfidence(
                overall_score=0.7,
                explanation="Medium confidence"
            ),
            matched_text="contract expired"
        )
        
        result = ClassificationResult(
            company_id="comp_123",
            api_response="Full API response text here",
            classifications=[classification1, classification2],
            processing_time_ms=150
        )
        
        assert result.primary_classification.id == "001"  # Highest confidence
        assert len(result.get_email_classifications()) == 1
        assert len(result.get_action_classifications()) == 1
        assert result.has_high_confidence_results(0.8)
        
        summary = result.to_summary()
        assert summary["total_classifications"] == 2
        assert summary["primary_confidence"] == 0.9
        assert ClassificationType.EMAIL_X in summary["email_classifications"]


class TestAPISchemas:
    """Test suite for API schemas"""
    
    def test_api_response(self):
        """Test APIResponse model"""
        response = APIResponse(
            company_id="comp_123",
            predictions=["Low fill rate due to pay below market"],
            metrics={"fill_rate": 65.0, "total_shifts": 100},
            confidence=0.85,
            generated_at=datetime.utcnow(),
            model_version="v1.2.0"
        )
        
        assert response.company_id == "comp_123"
        assert len(response.predictions) == 1
        assert response.metrics["fill_rate"] == 65.0
    
    def test_api_response_validation(self):
        """Test API response validation"""
        # Test empty predictions
        with pytest.raises(ValidationError) as exc_info:
            APIResponse(
                company_id="123",
                predictions=[],
                metrics={"fill_rate": 65.0, "total_shifts": 100},
                confidence=0.85,
                generated_at=datetime.utcnow(),
                model_version="v1.0"
            )
        assert "at least 1 item" in str(exc_info.value)
        
        # Test missing required metrics
        with pytest.raises(ValidationError) as exc_info:
            APIResponse(
                company_id="123",
                predictions=["test"],
                metrics={"other": 123},
                confidence=0.85,
                generated_at=datetime.utcnow(),
                model_version="v1.0"
            )
        assert "Missing required metrics" in str(exc_info.value)
    
    def test_classification_request(self):
        """Test ClassificationRequest model"""
        request = ClassificationRequest(
            company_ids=["comp_1", "comp_2", "comp_3"],
            include_metrics=True,
            batch_size=50,
            classification_config={
                "confidence_threshold": 0.75,
                "enable_multi_label": True
            }
        )
        
        assert len(request.company_ids) == 3
        assert request.batch_size == 50
        assert request.classification_config["confidence_threshold"] == 0.75
    
    def test_classification_request_validation(self):
        """Test classification request validation"""
        # Test duplicate company IDs
        with pytest.raises(ValidationError) as exc_info:
            ClassificationRequest(
                company_ids=["comp_1", "comp_2", "comp_1"]
            )
        assert "Duplicate company IDs" in str(exc_info.value)
        
        # Test invalid config keys
        with pytest.raises(ValidationError) as exc_info:
            ClassificationRequest(
                company_ids=["comp_1"],
                classification_config={"invalid_key": "value"}
            )
        assert "Invalid configuration keys" in str(exc_info.value)
    
    def test_batch_status(self):
        """Test BatchClassificationStatus model"""
        status = BatchClassificationStatus(
            total_companies=100,
            processed=75,
            successful=70,
            failed=5
        )
        
        assert status.completion_percentage == 75.0
        assert status.success_rate == 93.33
        assert status.in_progress
    
    @given(
        total=st.integers(min_value=0, max_value=1000),
        processed=st.integers(min_value=0, max_value=1000)
    )
    def test_batch_status_property_based(self, total, processed):
        """Property-based testing for batch status calculations"""
        # Ensure processed doesn't exceed total
        processed = min(processed, total)
        successful = min(processed, processed)  # All successful for this test
        
        status = BatchClassificationStatus(
            total_companies=total,
            processed=processed,
            successful=successful,
            failed=0
        )
        
        if total == 0:
            assert status.completion_percentage == 100.0
        else:
            expected_pct = round((processed / total) * 100, 2)
            assert status.completion_percentage == expected_pct
        
        if processed == 0:
            assert status.success_rate == 0.0
        else:
            assert status.success_rate == 100.0  # All successful in this test


class TestIntegrationScenarios:
    """Integration tests for model interactions"""
    
    def test_full_classification_flow(self):
        """Test complete classification flow with all models"""
        # Create company
        company = Company(id="comp_123", name="Test Corp")
        
        # Create metrics
        metrics = CompanyMetrics(
            company_id=company.id,
            fill_rate=55.0,
            total_shifts=200,
            filled_shifts=110,
            cancellation_rate=25.0
        )
        
        # Create API response
        api_response = APIResponse(
            company_id=company.id,
            predictions=[
                "Fill rates are low due to pay rates below market average",
                "High cancellation rate indicates worker dissatisfaction"
            ],
            metrics={
                "fill_rate": metrics.fill_rate,
                "total_shifts": metrics.total_shifts,
                "cancellation_rate": metrics.cancellation_rate
            },
            confidence=0.88,
            generated_at=datetime.utcnow(),
            model_version="v1.2.0"
        )
        
        # Create classification result
        classifications = [
            Classification(
                id="001",
                response_type=ResponseType.EMAIL,
                classification_type=ClassificationType.EMAIL_X,
                confidence=ClassificationConfidence(
                    overall_score=0.92,
                    explanation="Strong pattern match for low pay"
                ),
                matched_text="pay rates below market average",
                recommended_template="low_pay_rate_alert"
            ),
            Classification(
                id="002",
                response_type=ResponseType.ACTION,
                classification_type=ClassificationType.ACTION_C,
                confidence=ClassificationConfidence(
                    overall_score=0.78,
                    explanation="High cancellation requires meeting"
                ),
                matched_text="High cancellation rate",
                recommended_action="schedule_partner_meeting"
            )
        ]
        
        result = ClassificationResult(
            company_id=company.id,
            api_response=" ".join(api_response.predictions),
            classifications=classifications,
            processing_time_ms=125
        )
        
        # Verify the complete flow
        assert result.company_id == company.id
        assert len(result.classifications) == 2
        assert result.primary_classification.classification_type == ClassificationType.EMAIL_X
        assert result.has_high_confidence_results()
        
        # Verify summary
        summary = result.to_summary()
        assert summary["total_classifications"] == 2
        assert summary["has_high_confidence"] == True
        assert len(summary["email_classifications"]) == 1
        assert len(summary["action_classifications"]) == 1