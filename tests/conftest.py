"""
Module: tests.conftest
Purpose: Pytest configuration and shared fixtures
Dependencies: pytest, faker, datetime

This module provides shared test fixtures and configuration for the
entire test suite, including mock data generators and test utilities.
"""

import pytest
from datetime import datetime, timedelta
from faker import Faker
from typing import List, Dict, Any
import tempfile
import os

from src.models.company import Company, CompanyMetrics, CompanyStatus, MetricPeriod
from src.models.classification import (
    Classification, ClassificationResult, ClassificationConfidence,
    ResponseType, ClassificationType
)
from src.models.experiments import RuleVersion, Experiment, ExperimentStatus
from src.evaluation.ragas_metrics import EvaluationSample


@pytest.fixture
def fake():
    """Faker instance for generating test data"""
    return Faker()


@pytest.fixture
def sample_company(fake) -> Company:
    """Generate a sample company for testing"""
    return Company(
        id=f"comp_{fake.uuid4()}",
        name=fake.company(),
        status=CompanyStatus.ACTIVE,
        location=f"{fake.city()}, {fake.state_abbr()}",
        timezone="America/Los_Angeles",
        metadata={
            "industry": fake.random_element(["hospitality", "retail", "warehouse"]),
            "size": fake.random_element(["small", "medium", "large"])
        }
    )


@pytest.fixture
def sample_company_metrics(sample_company) -> CompanyMetrics:
    """Generate sample company metrics"""
    total_shifts = 100
    filled_shifts = 75
    fill_rate = (filled_shifts / total_shifts) * 100
    
    return CompanyMetrics(
        company_id=sample_company.id,
        period=MetricPeriod.WEEKLY,
        fill_rate=fill_rate,
        total_shifts=total_shifts,
        filled_shifts=filled_shifts,
        avg_time_to_fill=3.5,
        cancellation_rate=8.5,
        worker_ratings=4.2,
        regional_breakdown={
            "north": 82.0,
            "south": 68.0,
            "east": 75.0,
            "west": 77.0
        },
        shift_type_breakdown={
            "morning": 85.0,
            "afternoon": 70.0,
            "evening": 65.0,
            "overnight": 50.0
        }
    )


@pytest.fixture
def sample_classification_confidence() -> ClassificationConfidence:
    """Generate sample classification confidence"""
    return ClassificationConfidence(
        overall_score=0.85,
        pattern_matches=[
            {"pattern": "pay.*below.*market", "score": 0.9},
            {"pattern": "compensation.*insufficient", "score": 0.8}
        ],
        rule_scores={
            "low_pay_rate": 0.85,
            "market_comparison": 0.82
        },
        confidence_factors=["keyword_match", "pattern_strength", "context_relevance"],
        explanation="High confidence due to strong pattern matches in API response"
    )


@pytest.fixture
def sample_classification(sample_classification_confidence) -> Classification:
    """Generate sample classification"""
    return Classification(
        id="class_001",
        response_type=ResponseType.EMAIL,
        classification_type=ClassificationType.EMAIL_X,
        confidence=sample_classification_confidence,
        matched_text="pay rates are below market average for this region",
        recommended_template="low_pay_rate_alert",
        priority="high",
        metadata={
            "rule_version": "v1.2.0",
            "processing_time_ms": 125
        }
    )


@pytest.fixture
def sample_classification_result(sample_company, sample_classification) -> ClassificationResult:
    """Generate sample classification result"""
    return ClassificationResult(
        company_id=sample_company.id,
        api_response="Fill rates have been declining due to pay rates below market average. Workers are choosing higher-paying opportunities.",
        classifications=[sample_classification],
        processing_time_ms=150,
        api_metadata={
            "model_version": "v2.1.0",
            "confidence_threshold": 0.7,
            "response_time_ms": 1200
        }
    )


@pytest.fixture
def sample_rule_version() -> RuleVersion:
    """Generate sample rule version"""
    rules_config = {
        "version": "1.0.0",
        "classification_rules": {
            "email_classifications": {
                "low_pay_rate": {
                    "id": "EMAIL_X",
                    "patterns": [
                        {"regex": "pay.*below.*market", "weight": 0.9},
                        {"keywords": ["low pay", "underpaid"], "weight": 0.7}
                    ],
                    "confidence_boost": [
                        {"if_contains": ["salary", "wage"], "boost": 0.1}
                    ],
                    "email_template": "low_pay_rate_alert"
                }
            }
        }
    }
    
    return RuleVersion(
        version_id="v1.0.0",
        rules_config=rules_config,
        created_by="test_user",
        change_summary=["Initial rule version"],
        is_baseline=True
    )


@pytest.fixture
def sample_experiment(sample_rule_version) -> Experiment:
    """Generate sample experiment"""
    return Experiment(
        experiment_id="exp_001",
        name="Test Classification Rules v1.0",
        description="Testing initial classification rules for low pay rate detection",
        status=ExperimentStatus.ACTIVE,
        rule_version=sample_rule_version,
        start_date=datetime.utcnow() - timedelta(days=7),
        sample_size=250,
        sample_criteria={
            "company_types": ["retail", "hospitality"],
            "min_shifts_per_week": 10,
            "regions": ["west_coast", "east_coast"]
        },
        tags={"baseline", "pay_rate_detection", "v1"}
    )


@pytest.fixture
def sample_evaluation_samples(sample_company, sample_classification) -> List[EvaluationSample]:
    """Generate sample evaluation samples"""
    samples = []
    
    # High confidence, correct classification
    samples.append(EvaluationSample(
        company_id=f"{sample_company.id}_1",
        api_response="Fill rates are low because pay rates are significantly below market average",
        predicted_classifications=[sample_classification],
        ground_truth_classifications=["low_pay_rate"],
        human_feedback={"quality": 5, "relevance": 5}
    ))
    
    # Medium confidence, partially correct
    medium_confidence_classification = Classification(
        id="class_002",
        response_type=ResponseType.EMAIL,
        classification_type=ClassificationType.EMAIL_Y,
        confidence=ClassificationConfidence(
            overall_score=0.65,
            explanation="Medium confidence geographic match"
        ),
        matched_text="limited worker coverage in certain areas"
    )
    
    samples.append(EvaluationSample(
        company_id=f"{sample_company.id}_2",
        api_response="Geographic coverage is limited and some areas have no available workers",
        predicted_classifications=[medium_confidence_classification],
        ground_truth_classifications=["geographic_coverage"],
        human_feedback={"quality": 4, "relevance": 4}
    ))
    
    # Low confidence, incorrect classification
    low_confidence_classification = Classification(
        id="class_003",
        response_type=ResponseType.ACTION,
        classification_type=ClassificationType.ACTION_A,
        confidence=ClassificationConfidence(
            overall_score=0.45,
            explanation="Low confidence contract-related match"
        ),
        matched_text="contract terms need review"
    )
    
    samples.append(EvaluationSample(
        company_id=f"{sample_company.id}_3",
        api_response="Shift timing conflicts with worker availability preferences",
        predicted_classifications=[low_confidence_classification],
        ground_truth_classifications=["shift_timing_mismatch"],
        human_feedback={"quality": 2, "relevance": 2}
    ))
    
    return samples


@pytest.fixture
def temp_db_path():
    """Provide temporary database path for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_api_responses() -> Dict[str, Dict[str, Any]]:
    """Mock API responses for testing"""
    return {
        "low_pay_company": {
            "company_id": "comp_low_pay",
            "predictions": [
                "Fill rates are suffering due to compensation below market rates",
                "Workers are choosing higher-paying alternatives"
            ],
            "metrics": {
                "fill_rate": 45.0,
                "total_shifts": 200,
                "avg_pay_rate": 15.50,
                "market_avg_pay": 18.75
            },
            "confidence": 0.92,
            "generated_at": datetime.utcnow().isoformat(),
            "model_version": "v2.1.0"
        },
        "geographic_issue_company": {
            "company_id": "comp_geo_issue",
            "predictions": [
                "Limited worker coverage in rural locations",
                "Distance from urban centers affecting availability"
            ],
            "metrics": {
                "fill_rate": 55.0,
                "total_shifts": 150,
                "coverage_gaps": ["rural_north", "suburban_east"]
            },
            "confidence": 0.78,
            "generated_at": datetime.utcnow().isoformat(),
            "model_version": "v2.1.0"
        },
        "timing_issue_company": {
            "company_id": "comp_timing",
            "predictions": [
                "Overnight and early morning shifts have low fill rates",
                "Worker availability doesn't match shift timing requirements"
            ],
            "metrics": {
                "fill_rate": 62.0,
                "total_shifts": 180,
                "problematic_times": ["00:00-06:00", "22:00-24:00"]
            },
            "confidence": 0.85,
            "generated_at": datetime.utcnow().isoformat(),
            "model_version": "v2.1.0"
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment with necessary configurations"""
    # Set test-specific environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce noise in tests
    
    yield
    
    # Cleanup
    os.environ.pop("TESTING", None)
    os.environ.pop("LOG_LEVEL", None)


class TestDataGenerator:
    """Utility class for generating test data"""
    
    @staticmethod
    def generate_companies(count: int, fake: Faker) -> List[Company]:
        """Generate multiple test companies"""
        companies = []
        for i in range(count):
            company = Company(
                id=f"test_comp_{i:03d}",
                name=f"{fake.company()} {i}",
                status=fake.random_element(list(CompanyStatus)),
                location=f"{fake.city()}, {fake.state_abbr()}",
                timezone=fake.random_element([
                    "America/Los_Angeles", "America/New_York", 
                    "America/Chicago", "America/Denver"
                ])
            )
            companies.append(company)
        return companies
    
    @staticmethod
    def generate_classification_results(
        companies: List[Company], 
        classification_types: List[str]
    ) -> List[ClassificationResult]:
        """Generate classification results for multiple companies"""
        results = []
        for company in companies:
            # Generate 1-3 classifications per company
            num_classifications = fake.random_int(1, 3)
            classifications = []
            
            for _ in range(num_classifications):
                classification_type = fake.random_element(classification_types)
                confidence = ClassificationConfidence(
                    overall_score=fake.random.uniform(0.5, 0.95),
                    explanation=f"Generated confidence for {classification_type}"
                )
                
                classification = Classification(
                    id=f"class_{fake.uuid4()}",
                    response_type=fake.random_element(list(ResponseType)),
                    classification_type=classification_type,
                    confidence=confidence,
                    matched_text=f"Sample matched text for {classification_type}"
                )
                classifications.append(classification)
            
            result = ClassificationResult(
                company_id=company.id,
                api_response=f"Sample API response for {company.name}",
                classifications=classifications,
                processing_time_ms=fake.random_int(50, 500)
            )
            results.append(result)
        
        return results


# Make TestDataGenerator available as a fixture
@pytest.fixture
def test_data_generator():
    """Provide test data generator"""
    return TestDataGenerator