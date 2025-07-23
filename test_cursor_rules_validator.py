import unittest
import tempfile
import shutil
from pathlib import Path
from cursor_rules_validator import (
    validate_cursor_rules_location,
    create_cursor_rules_directory,
    move_cursor_rule_file,
    get_cursor_rules_summary,
    _is_cursor_rule_file
)

# Comprehensive tests for Cursor rules validator functionality


class TestCursorRulesValidator(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory for testing"""
        # Create isolated test environment
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)
        
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def test_validate_cursor_rules_location_no_files(self):
        """Test validation when no .mdc files exist"""
        # Test empty project validation
        result = validate_cursor_rules_location(self.test_dir)
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("No .mdc files found", result["warnings"][0])
    
    def test_validate_cursor_rules_location_correct_placement(self):
        """Test validation with correctly placed .mdc files"""
        # Test validation of correctly placed rule files
        cursor_rules_dir = self.project_path / ".cursor" / "rules"
        cursor_rules_dir.mkdir(parents=True)
        
        # Create a valid Cursor rule file
        rule_content = """
        <rule>
        name: test_rule
        description: Test rule
        </rule>
        """
        rule_file = cursor_rules_dir / "test-rule.mdc"
        rule_file.write_text(rule_content)
        
        result = validate_cursor_rules_location(self.test_dir)
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIn(".cursor/rules/test-rule.mdc", result["valid_files"])
    
    def test_validate_cursor_rules_location_incorrect_placement(self):
        """Test validation with incorrectly placed .mdc files"""
        # Test detection of incorrectly placed rule files
        wrong_file = self.project_path / "wrong-location.mdc"
        wrong_file.write_text("test content")
        
        result = validate_cursor_rules_location(self.test_dir)
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("must be placed in .cursor/rules/", result["errors"][0])
        self.assertIn("wrong-location.mdc", result["invalid_files"])
    
    def test_validate_cursor_rules_location_mixed_placement(self):
        """Test validation with both correct and incorrect .mdc files"""
        # Create .cursor/rules directory
        cursor_rules_dir = self.project_path / ".cursor" / "rules"
        cursor_rules_dir.mkdir(parents=True)
        
        # Create correct file
        correct_file = cursor_rules_dir / "correct-rule.mdc"
        correct_file.write_text("<rule>test</rule>")
        
        # Create incorrect file
        wrong_file = self.project_path / "wrong-rule.mdc"
        wrong_file.write_text("test content")
        
        result = validate_cursor_rules_location(self.test_dir)
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["valid_files"]), 1)
        self.assertEqual(len(result["invalid_files"]), 1)
        self.assertIn(".cursor/rules/correct-rule.mdc", result["valid_files"])
        self.assertIn("wrong-rule.mdc", result["invalid_files"])
    
    def test_is_cursor_rule_file_valid(self):
        """Test _is_cursor_rule_file with valid content"""
        # Test detection of valid Cursor rule syntax
        temp_file = self.project_path / "test.mdc"
        temp_file.write_text("<rule>test content</rule>")
        
        self.assertTrue(_is_cursor_rule_file(temp_file))
    
    def test_is_cursor_rule_file_invalid(self):
        """Test _is_cursor_rule_file with invalid content"""
        temp_file = self.project_path / "test.mdc"
        temp_file.write_text("Just some random content")
        
        self.assertFalse(_is_cursor_rule_file(temp_file))
    
    def test_create_cursor_rules_directory(self):
        """Test creating .cursor/rules directory"""
        success = create_cursor_rules_directory(self.test_dir)
        
        self.assertTrue(success)
        cursor_rules_dir = self.project_path / ".cursor" / "rules"
        self.assertTrue(cursor_rules_dir.exists())
        self.assertTrue(cursor_rules_dir.is_dir())
    
    def test_move_cursor_rule_file_success(self):
        """Test moving a .mdc file to correct location"""
        # Test successful file movement to correct location
        source_file = self.project_path / "source-rule.mdc"
        source_file.write_text("<rule>test</rule>")
        
        success, message = move_cursor_rule_file(str(source_file), self.test_dir)
        
        self.assertTrue(success)
        self.assertIn("Successfully moved", message)
        
        # Check if file was moved to correct location
        target_file = self.project_path / ".cursor" / "rules" / "source-rule.mdc"
        self.assertTrue(target_file.exists())
        self.assertFalse(source_file.exists())
    
    def test_move_cursor_rule_file_nonexistent(self):
        """Test moving a non-existent file"""
        success, message = move_cursor_rule_file("nonexistent.mdc", self.test_dir)
        
        self.assertFalse(success)
        self.assertIn("does not exist", message)
    
    def test_move_cursor_rule_file_wrong_extension(self):
        """Test moving a file with wrong extension"""
        # Create file with wrong extension
        wrong_file = self.project_path / "test.txt"
        wrong_file.write_text("test content")
        
        success, message = move_cursor_rule_file(str(wrong_file), self.test_dir)
        
        self.assertFalse(success)
        self.assertIn("not a .mdc file", message)
    
    def test_get_cursor_rules_summary(self):
        """Test getting formatted summary"""
        # Create mixed scenario
        cursor_rules_dir = self.project_path / ".cursor" / "rules"
        cursor_rules_dir.mkdir(parents=True)
        
        correct_file = cursor_rules_dir / "correct.mdc"
        correct_file.write_text("<rule>test</rule>")
        
        wrong_file = self.project_path / "wrong.mdc"
        wrong_file.write_text("test content")
        
        summary = get_cursor_rules_summary(self.test_dir)
        
        self.assertIn("Cursor Rules Location Validation Summary", summary)
        self.assertIn("❌ Found Cursor rule files in incorrect locations", summary)
        self.assertIn("wrong.mdc must be placed in .cursor/rules/", summary)
        self.assertIn(".cursor/rules/correct.mdc", summary)
    
    def test_kebab_case_conversion(self):
        """Test that filenames are converted to kebab-case when moving"""
        # Test filename conversion to kebab-case format
        source_file = self.project_path / "My Rule File!.mdc"
        source_file.write_text("<rule>test</rule>")
        
        success, message = move_cursor_rule_file(str(source_file), self.test_dir)
        
        self.assertTrue(success)
        
        # Check if file was renamed to kebab-case
        target_file = self.project_path / ".cursor" / "rules" / "my-rule-file.mdc"
        self.assertTrue(target_file.exists())
    
    def test_multiple_rule_files(self):
        """Test handling multiple rule files"""
        # Create .cursor/rules directory
        cursor_rules_dir = self.project_path / ".cursor" / "rules"
        cursor_rules_dir.mkdir(parents=True)
        
        # Create multiple correct files
        files = ["rule1.mdc", "rule2.mdc", "rule3.mdc"]
        for filename in files:
            rule_file = cursor_rules_dir / filename
            rule_file.write_text("<rule>test</rule>")
        
        # Create multiple incorrect files
        wrong_files = ["wrong1.mdc", "wrong2.mdc"]
        for filename in wrong_files:
            wrong_file = self.project_path / filename
            wrong_file.write_text("test content")
        
        result = validate_cursor_rules_location(self.test_dir)
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["valid_files"]), 3)
        self.assertEqual(len(result["invalid_files"]), 2)
        self.assertEqual(len(result["errors"]), 2)


if __name__ == "__main__":
    unittest.main() 