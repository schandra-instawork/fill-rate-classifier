"""
Module: classification.rules_loader
Purpose: Loads and manages classification rules from configuration
Dependencies: yaml, pathlib, typing, pydantic

This module handles loading classification rules from YAML configuration
files and provides utilities for rule validation and management.

Classes:
    RulePattern: Individual pattern for matching text
    ClassificationRule: Complete rule with patterns and metadata
    RulesLoader: Main loader for classification rules
"""

import yaml
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field, validator
from src.models.experiments import RuleVersion


@dataclass
class RulePattern:
    """Individual pattern for text matching"""
    pattern: str
    weight: float
    pattern_type: str = "regex"  # regex, keywords, exact
    
    def __post_init__(self):
        """Validate pattern after initialization"""
        if self.weight < 0 or self.weight > 1:
            raise ValueError(f"Pattern weight must be between 0 and 1, got {self.weight}")


class ClassificationRule(BaseModel):
    """
    Complete classification rule with patterns and metadata
    
    Attributes:
        rule_id: Unique rule identifier
        name: Human readable rule name
        description: Rule description
        patterns: List of patterns to match
        confidence_boosts: Conditions that boost confidence
        response_type: Email or Action
        classification_type: Specific classification type
        template_id: Email template ID (for email rules)
        action_type: Action type (for action rules)
        priority: Rule priority
        enabled: Whether rule is active
    """
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human readable name")
    description: str = Field(..., description="Rule description")
    patterns: List[RulePattern] = Field(..., description="Matching patterns")
    confidence_boosts: List[Dict[str, Any]] = Field(default_factory=list)
    response_type: str = Field(..., pattern="^(email|action)$")
    classification_type: str = Field(..., description="Specific classification type")
    template_id: Optional[str] = Field(None, description="Email template ID")
    action_type: Optional[str] = Field(None, description="Action type")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    enabled: bool = Field(default=True, description="Whether rule is active")
    
    @validator("patterns", pre=True)
    def parse_patterns(cls, v):
        """Parse patterns from various formats"""
        if not v:
            raise ValueError("At least one pattern is required")
        
        patterns = []
        for pattern_data in v:
            if isinstance(pattern_data, dict):
                if "regex" in pattern_data:
                    patterns.append(RulePattern(
                        pattern=pattern_data["regex"],
                        weight=pattern_data.get("weight", 1.0),
                        pattern_type="regex"
                    ))
                elif "keywords" in pattern_data:
                    # Convert keywords list to regex pattern
                    keywords = pattern_data["keywords"]
                    if isinstance(keywords, list):
                        regex_pattern = r'\b(' + '|'.join(keywords) + r')\b'
                    else:
                        regex_pattern = keywords
                    patterns.append(RulePattern(
                        pattern=regex_pattern,
                        weight=pattern_data.get("weight", 1.0),
                        pattern_type="keywords"
                    ))
                elif "exact" in pattern_data:
                    patterns.append(RulePattern(
                        pattern=pattern_data["exact"],
                        weight=pattern_data.get("weight", 1.0),
                        pattern_type="exact"
                    ))
            else:
                # Assume it's a regex string
                patterns.append(RulePattern(
                    pattern=str(pattern_data),
                    weight=1.0,
                    pattern_type="regex"
                ))
        
        return patterns


class RulesConfiguration(BaseModel):
    """Complete rules configuration"""
    version: str = Field(..., description="Configuration version")
    settings: Dict[str, Any] = Field(default_factory=dict)
    email_classifications: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    action_classifications: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    fallback_rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class RulesLoader:
    """
    Loads and manages classification rules
    
    This class handles:
    - Loading rules from YAML configuration files
    - Validating rule syntax and structure
    - Converting rules to internal format
    - Caching loaded rules
    - Tracking rule versions for experiments
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize rules loader
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path or "config/classification_rules.yaml")
        self.logger = logging.getLogger(__name__)
        self._cached_rules: Optional[Dict[str, ClassificationRule]] = None
        self._cached_config: Optional[RulesConfiguration] = None
        self._cached_version: Optional[RuleVersion] = None
        self._config_mtime: Optional[float] = None
    
    def load_rules(self, force_reload: bool = False) -> Dict[str, ClassificationRule]:
        """
        Load classification rules from configuration
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            Dictionary of rule_id -> ClassificationRule
        """
        # Check if we need to reload
        if not force_reload and self._cached_rules is not None:
            if self.config_path.exists():
                current_mtime = self.config_path.stat().st_mtime
                if current_mtime == self._config_mtime:
                    return self._cached_rules
        
        self.logger.info(f"Loading classification rules from {self.config_path}")
        
        try:
            # Load YAML configuration
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Validate configuration structure
            config = RulesConfiguration(**config_data)
            
            # Convert to classification rules
            rules = {}
            
            # Load email classification rules
            for rule_name, rule_data in config.email_classifications.items():
                rule = self._create_classification_rule(
                    rule_name, rule_data, "email"
                )
                rules[rule.rule_id] = rule
            
            # Load action classification rules
            for rule_name, rule_data in config.action_classifications.items():
                rule = self._create_classification_rule(
                    rule_name, rule_data, "action"
                )
                rules[rule.rule_id] = rule
            
            # Load fallback rules
            for rule_name, rule_data in config.fallback_rules.items():
                # Determine response type from rule_id
                response_type = "email" if "email" in rule_data.get("id", "").lower() else "action"
                rule = self._create_classification_rule(
                    rule_name, rule_data, response_type
                )
                rules[rule.rule_id] = rule
            
            # Cache results
            self._cached_rules = rules
            self._cached_config = config
            self._config_mtime = self.config_path.stat().st_mtime if self.config_path.exists() else None
            
            self.logger.info(f"Loaded {len(rules)} classification rules")
            return rules
            
        except Exception as e:
            self.logger.error(f"Failed to load rules from {self.config_path}: {e}")
            raise ValueError(f"Failed to load classification rules: {e}") from e
    
    def _create_classification_rule(
        self, 
        rule_name: str, 
        rule_data: Dict[str, Any], 
        response_type: str
    ) -> ClassificationRule:
        """
        Create a ClassificationRule from configuration data
        
        Args:
            rule_name: Name of the rule
            rule_data: Rule configuration data
            response_type: Response type (email or action)
            
        Returns:
            ClassificationRule instance
        """
        # Extract patterns
        patterns_data = rule_data.get("patterns", [])
        if not patterns_data:
            raise ValueError(f"Rule {rule_name} has no patterns defined")
        
        # Build rule data
        rule_dict = {
            "rule_id": rule_data.get("id", f"{response_type}_{rule_name}"),
            "name": rule_data.get("name", rule_name.replace("_", " ").title()),
            "description": rule_data.get("description", f"Classification rule for {rule_name}"),
            "patterns": patterns_data,
            "confidence_boosts": rule_data.get("confidence_boost", []),
            "response_type": response_type,
            "classification_type": rule_name,
            "template_id": rule_data.get("email_template"),
            "action_type": rule_data.get("action_type"),
            "priority": rule_data.get("priority", "medium"),
            "enabled": rule_data.get("enabled", True)
        }
        
        return ClassificationRule(**rule_dict)
    
    def get_rules_by_type(self, response_type: str) -> Dict[str, ClassificationRule]:
        """
        Get rules filtered by response type
        
        Args:
            response_type: Email or action
            
        Returns:
            Filtered rules dictionary
        """
        all_rules = self.load_rules()
        return {
            rule_id: rule 
            for rule_id, rule in all_rules.items() 
            if rule.response_type == response_type and rule.enabled
        }
    
    def get_enabled_rules(self) -> Dict[str, ClassificationRule]:
        """Get only enabled rules"""
        all_rules = self.load_rules()
        return {
            rule_id: rule 
            for rule_id, rule in all_rules.items() 
            if rule.enabled
        }
    
    def get_rule_version(self) -> RuleVersion:
        """
        Get current rule version for experiment tracking
        
        Returns:
            RuleVersion instance
        """
        if self._cached_version is None or self._config_mtime != getattr(self._cached_version, '_mtime', None):
            config = self._cached_config or self._load_config()
            
            # Create rule version
            rules_config = {
                "version": config.version,
                "settings": config.settings,
                "email_classifications": config.email_classifications,
                "action_classifications": config.action_classifications,
                "fallback_rules": config.fallback_rules
            }
            
            # Calculate hash
            config_str = json.dumps(rules_config, sort_keys=True)
            rule_hash = hashlib.sha256(config_str.encode()).hexdigest()
            
            version = RuleVersion(
                version_id=config.version,
                rules_config=rules_config,
                rule_hash=rule_hash,
                created_by="system",
                created_at=datetime.utcnow(),
                is_baseline=True
            )
            
            # Cache with mtime
            version._mtime = self._config_mtime
            self._cached_version = version
        
        return self._cached_version
    
    def _load_config(self) -> RulesConfiguration:
        """Load configuration without caching rules"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return RulesConfiguration(**config_data)
    
    def validate_rules(self) -> List[str]:
        """
        Validate all rules and return any errors
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            rules = self.load_rules()
            
            # Check for duplicate rule IDs
            rule_ids = [rule.rule_id for rule in rules.values()]
            if len(rule_ids) != len(set(rule_ids)):
                duplicates = [rid for rid in rule_ids if rule_ids.count(rid) > 1]
                errors.append(f"Duplicate rule IDs found: {set(duplicates)}")
            
            # Validate individual rules
            for rule_id, rule in rules.items():
                # Check patterns
                if not rule.patterns:
                    errors.append(f"Rule {rule_id} has no patterns")
                
                # Check response type specific requirements
                if rule.response_type == "email" and not rule.template_id:
                    errors.append(f"Email rule {rule_id} missing template_id")
                
                if rule.response_type == "action" and not rule.action_type:
                    errors.append(f"Action rule {rule_id} missing action_type")
                
                # Validate pattern syntax (basic check)
                for pattern in rule.patterns:
                    if pattern.pattern_type == "regex":
                        try:
                            import re
                            re.compile(pattern.pattern)
                        except re.error as e:
                            errors.append(f"Invalid regex in rule {rule_id}: {e}")
            
        except Exception as e:
            errors.append(f"Failed to load or validate rules: {e}")
        
        return errors
    
    def reload_rules(self) -> Dict[str, ClassificationRule]:
        """Force reload rules from file"""
        return self.load_rules(force_reload=True)