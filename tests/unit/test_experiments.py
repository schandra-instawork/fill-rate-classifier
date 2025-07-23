"""
Module: tests.unit.test_experiments
Purpose: Unit tests for experiment tracking and version control
Dependencies: pytest, datetime, json

This module contains comprehensive tests for the experiment tracking
and version control system.
"""

import pytest
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, Any

from src.models.experiments import (
    ExperimentStatus,
    RuleVersion,
    ExperimentMetrics,
    Experiment,
    ExperimentComparison,
    ExperimentRepository
)


class TestRuleVersion:
    """Test suite for RuleVersion model"""
    
    def test_rule_version_creation(self):
        """Test creating a valid rule version"""
        rules_config = {
            "classification_rules": {
                "low_pay_rate": {
                    "patterns": ["pay.*below.*market"],
                    "confidence_threshold": 0.8
                }
            }
        }
        
        version = RuleVersion(
            version_id="v1.0.0",
            rules_config=rules_config,
            created_by="test_user",
            change_summary=["Initial version"]
        )
        
        assert version.version_id == "v1.0.0"
        assert version.rules_config == rules_config
        assert version.created_by == "test_user"
        assert len(version.rule_hash) == 64  # SHA256 hash length
        assert not version.is_baseline
    
    def test_rule_hash_computation(self):
        """Test automatic rule hash computation"""
        rules_config = {
            "test": "value",
            "nested": {"key": "value"}
        }
        
        version = RuleVersion(
            version_id="v1.0.0",
            rule_hash="",  # Empty hash should be computed
            rules_config=rules_config,
            created_by="test_user"
        )
        
        # Verify hash was computed
        expected_hash = hashlib.sha256(
            json.dumps(rules_config, sort_keys=True).encode()
        ).hexdigest()
        
        assert version.rule_hash == expected_hash
    
    def test_get_changes_from_parent(self):
        """Test change detection from parent version"""
        parent = RuleVersion(
            version_id="v1.0.0",
            rules_config={"old": "config"},
            created_by="test_user"
        )
        
        child = RuleVersion(
            version_id="v1.1.0",
            rules_config={"new": "config"},
            created_by="test_user",
            parent_version="v1.0.0",
            change_summary=["Updated configuration"]
        )
        
        changes = child.get_changes_from_parent(parent)
        assert "Updated configuration" in changes
        
        # Test with no parent
        changes_no_parent = child.get_changes_from_parent(None)
        assert "Initial version" in changes_no_parent


class TestExperimentMetrics:
    """Test suite for ExperimentMetrics model"""
    
    def test_metrics_creation(self):
        """Test creating experiment metrics"""
        metrics = ExperimentMetrics(
            total_classifications=100,
            accuracy_score=0.85,
            precision_by_type={"low_pay_rate": 0.9, "geographic_coverage": 0.8},
            recall_by_type={"low_pay_rate": 0.85, "geographic_coverage": 0.75},
            error_rate=0.1,
            processing_time_p50=150.0,
            processing_time_p95=500.0
        )
        
        assert metrics.total_classifications == 100
        assert metrics.accuracy_score == 0.85
        assert metrics.error_rate == 0.1
    
    def test_f1_score_calculation(self):
        """Test F1 score calculation"""
        metrics = ExperimentMetrics(
            precision_by_type={"type_a": 0.8, "type_b": 0.9},
            recall_by_type={"type_a": 0.7, "type_b": 0.8}
        )
        
        f1_scores = metrics.calculate_f1_scores()
        
        # F1 = 2 * (precision * recall) / (precision + recall)
        expected_f1_a = 2 * (0.8 * 0.7) / (0.8 + 0.7)
        expected_f1_b = 2 * (0.9 * 0.8) / (0.9 + 0.8)
        
        assert abs(f1_scores["type_a"] - expected_f1_a) < 0.001
        assert abs(f1_scores["type_b"] - expected_f1_b) < 0.001
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        metrics = ExperimentMetrics(
            total_classifications=50,
            accuracy_score=0.92,
            error_rate=0.05,
            precision_by_type={"type_a": 0.9},
            recall_by_type={"type_a": 0.85},
            processing_time_p50=120.0,
            confidence_distribution={"0.8-0.9": 30, "0.9-1.0": 20}
        )
        
        summary = metrics.get_performance_summary()
        
        assert summary["total_classifications"] == 50
        assert summary["accuracy"] == 0.92
        assert summary["error_rate"] == 0.05
        assert "f1_scores" in summary
        assert "confidence_stats" in summary


class TestExperiment:
    """Test suite for Experiment model"""
    
    def test_experiment_creation(self):
        """Test creating a valid experiment"""
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        experiment = Experiment(
            experiment_id="exp_001",
            name="Test Experiment",
            description="Testing new classification rules",
            rule_version=rule_version,
            start_date=datetime.utcnow(),
            sample_size=100
        )
        
        assert experiment.experiment_id == "exp_001"
        assert experiment.name == "Test Experiment"
        assert experiment.status == ExperimentStatus.DRAFT
        assert experiment.sample_size == 100
    
    def test_experiment_validation(self):
        """Test experiment validation rules"""
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)  # Invalid: end before start
        
        with pytest.raises(ValueError) as exc_info:
            Experiment(
                experiment_id="exp_001",
                name="Test Experiment",
                description="Test",
                rule_version=rule_version,
                start_date=start_date,
                end_date=end_date
            )
        
        assert "End date must be after start date" in str(exc_info.value)
    
    def test_add_note(self):
        """Test adding notes to experiment"""
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        experiment = Experiment(
            experiment_id="exp_001",
            name="Test Experiment",
            description="Test",
            rule_version=rule_version
        )
        
        experiment.add_note("This is a test note", "test_user")
        
        assert len(experiment.notes) == 1
        assert experiment.notes[0]["note"] == "This is a test note"
        assert experiment.notes[0]["author"] == "test_user"
        assert "timestamp" in experiment.notes[0]
    
    def test_status_transitions(self):
        """Test valid status transitions"""
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        experiment = Experiment(
            experiment_id="exp_001",
            name="Test Experiment",
            description="Test",
            rule_version=rule_version,
            status=ExperimentStatus.DRAFT
        )
        
        # Valid transitions from DRAFT
        assert experiment.can_transition_to(ExperimentStatus.ACTIVE)
        assert experiment.can_transition_to(ExperimentStatus.ARCHIVED)
        assert not experiment.can_transition_to(ExperimentStatus.COMPLETED)
        
        # Change status and test new transitions
        experiment.status = ExperimentStatus.ACTIVE
        assert experiment.can_transition_to(ExperimentStatus.PAUSED)
        assert experiment.can_transition_to(ExperimentStatus.COMPLETED)
        assert not experiment.can_transition_to(ExperimentStatus.DRAFT)
    
    def test_duration_calculation(self):
        """Test experiment duration calculation"""
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        start_date = datetime(2024, 1, 1, 10, 0, 0)
        end_date = datetime(2024, 1, 8, 10, 0, 0)
        
        experiment = Experiment(
            experiment_id="exp_001",
            name="Test Experiment",
            description="Test",
            rule_version=rule_version,
            start_date=start_date,
            end_date=end_date
        )
        
        duration = experiment.get_duration_days()
        assert duration == 7
        
        # Test active experiment (no end date)
        experiment.end_date = None
        experiment.status = ExperimentStatus.ACTIVE
        duration = experiment.get_duration_days()
        assert duration is not None  # Should calculate from start to now


class TestExperimentComparison:
    """Test suite for ExperimentComparison model"""
    
    def test_comparison_creation(self):
        """Test creating experiment comparison"""
        comparison = ExperimentComparison(
            comparison_id="comp_001",
            experiment_ids=["exp_001", "exp_002"]
        )
        
        assert comparison.comparison_id == "comp_001"
        assert len(comparison.experiment_ids) == 2
        assert comparison.winner is None
    
    def test_add_metric_comparison(self):
        """Test adding metric comparisons"""
        comparison = ExperimentComparison(
            comparison_id="comp_001",
            experiment_ids=["exp_001", "exp_002"]
        )
        
        accuracy_values = {"exp_001": 0.85, "exp_002": 0.92}
        comparison.add_metric_comparison("accuracy", accuracy_values)
        
        assert "accuracy" in comparison.comparison_metrics
        assert comparison.comparison_metrics["accuracy"]["values"] == accuracy_values
        assert comparison.comparison_metrics["accuracy"]["best_value"] == 0.92
        assert comparison.comparison_metrics["accuracy"]["worst_value"] == 0.85
    
    def test_winner_determination(self):
        """Test winner determination"""
        comparison = ExperimentComparison(
            comparison_id="comp_001",
            experiment_ids=["exp_001", "exp_002"],
            statistical_significance=0.96
        )
        
        accuracy_values = {"exp_001": 0.85, "exp_002": 0.92}
        comparison.add_metric_comparison("accuracy_score", accuracy_values)
        
        winner = comparison.determine_winner("accuracy_score", min_significance=0.95)
        assert winner == "exp_002"
        assert comparison.winner == "exp_002"
    
    def test_winner_validation(self):
        """Test winner validation"""
        with pytest.raises(ValueError) as exc_info:
            ExperimentComparison(
                comparison_id="comp_001",
                experiment_ids=["exp_001", "exp_002"],
                winner="exp_003"  # Not in experiment_ids
            )
        
        assert "must be one of the compared experiments" in str(exc_info.value)


class TestExperimentRepository:
    """Test suite for ExperimentRepository model"""
    
    def test_add_experiment(self):
        """Test adding experiment to repository"""
        repo = ExperimentRepository()
        
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        experiment = Experiment(
            experiment_id="exp_001",
            name="Test Experiment",
            description="Test",
            rule_version=rule_version,
            status=ExperimentStatus.ACTIVE
        )
        
        repo.add_experiment(experiment)
        
        assert "exp_001" in repo.experiments
        assert "exp_001" in repo.active_experiments
    
    def test_get_active_experiments(self):
        """Test getting active experiments"""
        repo = ExperimentRepository()
        
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        # Add active experiment
        active_exp = Experiment(
            experiment_id="exp_active",
            name="Active Experiment",
            description="Test",
            rule_version=rule_version,
            status=ExperimentStatus.ACTIVE
        )
        repo.add_experiment(active_exp)
        
        # Add completed experiment
        completed_exp = Experiment(
            experiment_id="exp_completed",
            name="Completed Experiment",
            description="Test",
            rule_version=rule_version,
            status=ExperimentStatus.COMPLETED
        )
        repo.add_experiment(completed_exp)
        
        active_experiments = repo.get_active_experiments()
        assert len(active_experiments) == 1
        assert active_experiments[0].experiment_id == "exp_active"
    
    def test_get_experiments_by_tag(self):
        """Test getting experiments by tag"""
        repo = ExperimentRepository()
        
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        # Add experiment with tag
        exp_with_tag = Experiment(
            experiment_id="exp_tagged",
            name="Tagged Experiment",
            description="Test",
            rule_version=rule_version,
            tags={"machine_learning", "optimization"}
        )
        repo.add_experiment(exp_with_tag)
        
        # Add experiment without tag
        exp_without_tag = Experiment(
            experiment_id="exp_no_tag",
            name="Untagged Experiment",
            description="Test",
            rule_version=rule_version
        )
        repo.add_experiment(exp_without_tag)
        
        tagged_experiments = repo.get_experiments_by_tag("machine_learning")
        assert len(tagged_experiments) == 1
        assert tagged_experiments[0].experiment_id == "exp_tagged"
    
    def test_get_best_performing(self):
        """Test getting best performing experiment"""
        repo = ExperimentRepository()
        
        rule_version = RuleVersion(
            version_id="v1.0.0",
            rules_config={"test": "config"},
            created_by="test_user"
        )
        
        # Add experiments with different performance
        exp1 = Experiment(
            experiment_id="exp_001",
            name="Experiment 1",
            description="Test",
            rule_version=rule_version,
            status=ExperimentStatus.COMPLETED,
            metrics=ExperimentMetrics(accuracy_score=0.85)
        )
        repo.add_experiment(exp1)
        
        exp2 = Experiment(
            experiment_id="exp_002",
            name="Experiment 2",
            description="Test",
            rule_version=rule_version,
            status=ExperimentStatus.COMPLETED,
            metrics=ExperimentMetrics(accuracy_score=0.92)
        )
        repo.add_experiment(exp2)
        
        best = repo.get_best_performing("accuracy_score")
        assert best.experiment_id == "exp_002"
        assert best.metrics.accuracy_score == 0.92