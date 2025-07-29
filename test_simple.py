#!/usr/bin/env python3
"""
Module: test_simple.py
Purpose: Simple validation tests for core Fill Rate Classifier models
Dependencies: src/models/company.py, src/models/classification.py, config/classification_rules.yaml

This script provides basic validation tests for the core data models
used in the Fill Rate Classifier system. It tests company creation,
metrics validation, classification logic, and configuration loading.

Usage:
    python test_simple.py
"""

import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, 'src')

from models.company import Company, CompanyMetrics, CompanyStatus
from models.classification import (
    Classification, ClassificationConfidence, 
    ResponseType, ClassificationType
)


def test_company_creation():
    """
    Test basic company creation with minimal required fields
    
    Validates that Company model can be instantiated with
    required fields and handles validation correctly.
    
    Dependencies: src/models/company.py
    
    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        # Create company with minimal required fields
        company = Company(
            id="test_123",
            name="Test Company"
        )
        print(f"✅ Company created: {company.name} (ID: {company.id})")
        return True
    except Exception as e:
        print(f"❌ Company creation failed: {e}")
        return False


def test_company_metrics():
    """
    Test company metrics creation and validation
    
    Validates CompanyMetrics model with fill rate calculations
    and performance summary generation.
    
    Dependencies: src/models/company.py
    
    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        # Create metrics with validation
        metrics = CompanyMetrics(
            company_id="test_123",
            fill_rate=75.0,  # 75% fill rate
            total_shifts=100,
            filled_shifts=75
        )
        print(f"✅ Company metrics created: {metrics.fill_rate}% fill rate")
        
        # Test performance summary generation
        summary = metrics.get_performance_summary()
        print(f"✅ Performance rating: {summary['performance_rating']}")
        return True
    except Exception as e:
        print(f"❌ Company metrics failed: {e}")
        return False


def test_classification():
    """
    Test classification creation with confidence scoring
    
    Validates Classification model with confidence scoring
    and proper type assignment.
    
    Dependencies: src/models/classification.py
    
    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        # Create confidence scoring
        confidence = ClassificationConfidence(
            overall_score=0.85,  # 85% confidence
            explanation="High confidence match"
        )
        
        # Create classification with email type
        classification = Classification(
            id="class_001",
            response_type=ResponseType.EMAIL,
            classification_type=ClassificationType.EMAIL_X,
            confidence=confidence,
            matched_text="pay rates below market"
        )
        
        print(f"✅ Classification created: {classification.classification_type}")
        print(f"✅ Confidence: {classification.confidence.overall_score}")
        return True
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        return False


def test_yaml_config_loading():
    """
    Test YAML configuration file loading
    
    Validates that classification rules can be loaded
    from YAML configuration files.
    
    Dependencies: config/classification_rules.yaml
    
    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        import yaml
        # Load classification rules from YAML
        with open('config/classification_rules.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ YAML config loaded: {config['version']}")
        print(f"✅ Found {len(config['classification_rules']['email_classifications'])} email rules")
        return True
    except Exception as e:
        print(f"❌ YAML config loading failed: {e}")
        return False


def main():
    """
    Main test runner for core components
    
    Executes all validation tests and provides
    a summary of results.
    
    Dependencies: All test functions above
    """
    print("🚀 Testing Fill Rate Classifier Core Components")
    print("=" * 50)
    
    # Define test suite with descriptive names
    tests = [
        ("Company Creation", test_company_creation),
        ("Company Metrics", test_company_metrics), 
        ("Classification", test_classification),
        ("YAML Config", test_yaml_config_loading)
    ]
    
    passed = 0
    total = len(tests)
    
    # Execute each test and track results
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    # Print final summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)