#!/usr/bin/env python3
"""
Simple test script to validate our core models
"""

import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from models.company import Company, CompanyMetrics, CompanyStatus
from models.classification import (
    Classification, ClassificationConfidence, 
    ResponseType, ClassificationType
)

def test_company_creation():
    """Test basic company creation"""
    try:
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
    """Test company metrics with validation"""
    try:
        metrics = CompanyMetrics(
            company_id="test_123",
            fill_rate=75.0,
            total_shifts=100,
            filled_shifts=75
        )
        print(f"✅ Company metrics created: {metrics.fill_rate}% fill rate")
        
        # Test performance summary
        summary = metrics.get_performance_summary()
        print(f"✅ Performance rating: {summary['performance_rating']}")
        return True
    except Exception as e:
        print(f"❌ Company metrics failed: {e}")
        return False

def test_classification():
    """Test classification creation"""
    try:
        confidence = ClassificationConfidence(
            overall_score=0.85,
            explanation="High confidence match"
        )
        
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
    """Test YAML configuration loading"""
    try:
        import yaml
        with open('config/classification_rules.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ YAML config loaded: {config['version']}")
        print(f"✅ Found {len(config['classification_rules']['email_classifications'])} email rules")
        return True
    except Exception as e:
        print(f"❌ YAML config loading failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Fill Rate Classifier Core Components")
    print("=" * 50)
    
    tests = [
        ("Company Creation", test_company_creation),
        ("Company Metrics", test_company_metrics), 
        ("Classification", test_classification),
        ("YAML Config", test_yaml_config_loading)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"💥 {test_name} test failed!")
    
    print(f"\n{'='*50}")
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Core components are working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())