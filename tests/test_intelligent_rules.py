#!/usr/bin/env python3
"""
Module: tests.test_intelligent_rules
Purpose: Test intelligent application of Cursor rules
Dependencies: tests.cursor_rules_validator, .cursor/rules/ directory

This script tests the intelligent features of Cursor rules including
context awareness, conditional actions, and smart pattern matching.
"""

import json
import unittest
from pathlib import Path
from typing import Dict, List, Any

# Import the validator
from cursor_rules_validator import validate_all_rules, validate_cursor_rules_location


class TestIntelligentRules(unittest.TestCase):
    """Test suite for intelligent Cursor rule features"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(".")
        self.cursor_rules_dir = self.project_root / ".cursor" / "rules"
    
    def test_rule_location_intelligence(self):
        """Test that rules are in the correct location"""
        validation = validate_cursor_rules_location(str(self.project_root))
        
        self.assertTrue(validation["valid"], 
                       "All Cursor rules should be in .cursor/rules directory")
        
        if validation["warnings"]:
            print(f"⚠️  Warnings found: {validation['warnings']}")
        
        if validation["suggestions"]:
            print(f"💡 Suggestions: {validation['suggestions']}")
    
    def test_rule_structure_intelligence(self):
        """Test that rules have proper intelligent structure"""
        validation = validate_all_rules(str(self.project_root))
        
        self.assertTrue(validation["valid"], 
                       "All Cursor rules should have proper structure")
        
        # Check for intelligent features
        for file_name, details in validation["file_details"].items():
            with self.subTest(file_name=file_name):
                self.assertTrue(details["valid"], 
                              f"Rule {file_name} should be valid")
                
                # Check for intelligent features
                if details["warnings"]:
                    print(f"⚠️  {file_name} warnings: {details['warnings']}")
                
                if details["suggestions"]:
                    print(f"💡 {file_name} suggestions: {details['suggestions']}")
    
    def test_context_awareness(self):
        """Test that rules are context-aware"""
        # This would test specific context-aware features
        # For now, just ensure rules exist and are valid
        mdc_files = list(self.cursor_rules_dir.glob("*.mdc"))
        
        self.assertGreater(len(mdc_files), 0, 
                          "Should have at least one Cursor rule file")
        
        for mdc_file in mdc_files:
            with self.subTest(rule_file=mdc_file.name):
                content = mdc_file.read_text()
                
                # Check for context-aware features
                self.assertIn("filters:", content, 
                             "Rules should have filters for context awareness")
                
                self.assertIn("actions:", content, 
                             "Rules should have actions for intelligent responses")
    
    def test_conditional_logic(self):
        """Test that rules have conditional logic"""
        mdc_files = list(self.cursor_rules_dir.glob("*.mdc"))
        
        for mdc_file in mdc_files:
            with self.subTest(rule_file=mdc_file.name):
                content = mdc_file.read_text()
                
                # Check for conditional features
                has_when_clause = "when:" in content
                has_if_conditions = "if" in content.lower()
                
                # At least one conditional feature should be present
                self.assertTrue(has_when_clause or has_if_conditions,
                              f"Rule {mdc_file.name} should have conditional logic")
    
    def test_pattern_matching(self):
        """Test that rules have intelligent pattern matching"""
        mdc_files = list(self.cursor_rules_dir.glob("*.mdc"))
        
        for mdc_file in mdc_files:
            with self.subTest(rule_file=mdc_file.name):
                content = mdc_file.read_text()
                
                # Check for pattern matching features
                has_pattern = "pattern:" in content
                has_regex = "regex" in content.lower()
                has_keywords = "keyword" in content.lower()
                
                # At least one pattern matching feature should be present
                self.assertTrue(has_pattern or has_regex or has_keywords,
                              f"Rule {mdc_file.name} should have pattern matching")
    
    def test_examples_and_metadata(self):
        """Test that rules have examples and metadata"""
        mdc_files = list(self.cursor_rules_dir.glob("*.mdc"))
        
        for mdc_file in mdc_files:
            with self.subTest(rule_file=mdc_file.name):
                content = mdc_file.read_text()
                
                # Check for examples
                has_examples = "examples:" in content
                if not has_examples:
                    print(f"💡 {mdc_file.name}: Consider adding examples")
                
                # Check for metadata
                has_description = "description:" in content
                self.assertTrue(has_description,
                              f"Rule {mdc_file.name} should have a description")
    
    def test_rule_completeness(self):
        """Test that rules are complete and comprehensive"""
        validation = validate_all_rules(str(self.project_root))
        
        for file_name, details in validation["file_details"].items():
            with self.subTest(rule_file=file_name):
                # Check for completeness indicators
                content = (self.cursor_rules_dir / file_name).read_text()
                
                # Should have all major sections
                required_sections = ["name:", "description:", "filters:", "actions:"]
                for section in required_sections:
                    self.assertIn(section, content,
                                f"Rule {file_name} should have {section} section")
                
                # Should not have critical errors
                self.assertEqual(len(details["errors"]), 0,
                               f"Rule {file_name} should not have errors")
    
    def test_rule_consistency(self):
        """Test that rules are consistent across the project"""
        mdc_files = list(self.cursor_rules_dir.glob("*.mdc"))
        
        # Check for consistent naming
        rule_names = []
        for mdc_file in mdc_files:
            content = mdc_file.read_text()
            import re
            name_match = re.search(r'name:\s*(\w+)', content)
            if name_match:
                rule_names.append(name_match.group(1))
        
        # Rule names should be unique
        self.assertEqual(len(rule_names), len(set(rule_names)),
                       "Rule names should be unique")
        
        # Rule names should follow consistent pattern
        for name in rule_names:
            self.assertTrue(name.islower() or name.startswith('_'),
                          f"Rule name '{name}' should be lowercase or start with underscore")
    
    def test_intelligent_suggestions(self):
        """Test that rules provide intelligent suggestions"""
        mdc_files = list(self.cursor_rules_dir.glob("*.mdc"))
        
        for mdc_file in mdc_files:
            with self.subTest(rule_file=mdc_file.name):
                content = mdc_file.read_text()
                
                # Check for suggestion patterns
                has_suggestions = "suggest:" in content or "message:" in content
                self.assertTrue(has_suggestions,
                              f"Rule {mdc_file.name} should provide suggestions")
                
                # Check for helpful content
                has_helpful_content = any(keyword in content.lower() 
                                        for keyword in ["example", "guideline", "best practice"])
                if not has_helpful_content:
                    print(f"💡 {mdc_file.name}: Consider adding helpful examples or guidelines")


def run_intelligent_tests():
    """Run all intelligent rule tests"""
    print("🧠 Testing Intelligent Cursor Rules...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntelligentRules)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Intelligent Rules Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All intelligent rule tests passed!")
        return True
    else:
        print("\n⚠️  Some intelligent rule tests failed.")
        return False


if __name__ == "__main__":
    success = run_intelligent_tests()
    exit(0 if success else 1) 