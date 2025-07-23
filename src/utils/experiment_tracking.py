"""
Module: utils.experiment_tracking
Purpose: Utilities for experiment tracking and evaluation
Dependencies: pandas, sqlite3, json, datetime

This module provides utilities for tracking classification experiments,
storing results, and evaluating performance over time.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from contextlib import contextmanager

from src.models.experiments import (
    Experiment, ExperimentStatus, RuleVersion, 
    ExperimentMetrics, ExperimentComparison
)


class ExperimentTracker:
    """
    Tracks and persists classification experiments
    
    This class provides methods for:
    - Storing experiment configurations and results
    - Tracking performance metrics over time
    - Comparing different rule versions
    - Generating reports and visualizations
    """
    
    def __init__(self, db_path: str = "data/experiments.db"):
        """
        Initialize experiment tracker
        
        Args:
            db_path: Path to SQLite database for persistence
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        with self._get_db() as conn:
            conn.executescript("""
                -- Rule versions table
                CREATE TABLE IF NOT EXISTS rule_versions (
                    version_id TEXT PRIMARY KEY,
                    rule_hash TEXT NOT NULL,
                    rules_config TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    created_by TEXT NOT NULL,
                    parent_version TEXT,
                    change_summary TEXT,
                    is_baseline BOOLEAN DEFAULT 0,
                    FOREIGN KEY (parent_version) REFERENCES rule_versions(version_id)
                );
                
                -- Experiments table
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    rule_version_id TEXT NOT NULL,
                    baseline_version_id TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    sample_size INTEGER DEFAULT 0,
                    sample_criteria TEXT,
                    tags TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rule_version_id) REFERENCES rule_versions(version_id),
                    FOREIGN KEY (baseline_version_id) REFERENCES rule_versions(version_id)
                );
                
                -- Experiment metrics table
                CREATE TABLE IF NOT EXISTS experiment_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    total_classifications INTEGER DEFAULT 0,
                    accuracy_score REAL,
                    error_rate REAL DEFAULT 0,
                    processing_time_p50 REAL DEFAULT 0,
                    processing_time_p95 REAL DEFAULT 0,
                    metrics_json TEXT,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
                );
                
                -- Classification results table (for detailed tracking)
                CREATE TABLE IF NOT EXISTS classification_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    classification_type TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    is_correct BOOLEAN,
                    processing_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
                );
                
                -- Experiment comparisons table
                CREATE TABLE IF NOT EXISTS experiment_comparisons (
                    comparison_id TEXT PRIMARY KEY,
                    experiment_ids TEXT NOT NULL,
                    comparison_metrics TEXT NOT NULL,
                    winner TEXT,
                    statistical_significance REAL,
                    analysis_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indices for performance
                CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
                CREATE INDEX IF NOT EXISTS idx_experiments_dates ON experiments(start_date, end_date);
                CREATE INDEX IF NOT EXISTS idx_metrics_experiment ON experiment_metrics(experiment_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_results_experiment ON classification_results(experiment_id);
                CREATE INDEX IF NOT EXISTS idx_results_company ON classification_results(company_id);
            """)
            conn.commit()
    
    @contextmanager
    def _get_db(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_rule_version(self, rule_version: RuleVersion) -> None:
        """Save a rule version to the database"""
        with self._get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO rule_versions 
                (version_id, rule_hash, rules_config, created_at, created_by, 
                 parent_version, change_summary, is_baseline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_version.version_id,
                rule_version.rule_hash,
                json.dumps(rule_version.rules_config),
                rule_version.created_at,
                rule_version.created_by,
                rule_version.parent_version,
                json.dumps(rule_version.change_summary),
                rule_version.is_baseline
            ))
    
    def save_experiment(self, experiment: Experiment) -> None:
        """Save an experiment to the database"""
        with self._get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiments
                (experiment_id, name, description, status, rule_version_id,
                 baseline_version_id, start_date, end_date, sample_size,
                 sample_criteria, tags, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id,
                experiment.name,
                experiment.description,
                experiment.status,
                experiment.rule_version.version_id,
                experiment.baseline_version.version_id if experiment.baseline_version else None,
                experiment.start_date,
                experiment.end_date,
                experiment.sample_size,
                json.dumps(experiment.sample_criteria),
                json.dumps(list(experiment.tags)),
                json.dumps(experiment.notes),
                datetime.utcnow()
            ))
            
            # Save the rule version too
            self.save_rule_version(experiment.rule_version)
    
    def update_experiment_metrics(self, experiment_id: str, metrics: ExperimentMetrics) -> None:
        """Update metrics for an experiment"""
        with self._get_db() as conn:
            metrics_dict = {
                "precision_by_type": metrics.precision_by_type,
                "recall_by_type": metrics.recall_by_type,
                "confidence_distribution": metrics.confidence_distribution,
                "feedback_scores": metrics.feedback_scores
            }
            
            conn.execute("""
                INSERT INTO experiment_metrics
                (experiment_id, timestamp, total_classifications, accuracy_score,
                 error_rate, processing_time_p50, processing_time_p95, metrics_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id,
                datetime.utcnow(),
                metrics.total_classifications,
                metrics.accuracy_score,
                metrics.error_rate,
                metrics.processing_time_p50,
                metrics.processing_time_p95,
                json.dumps(metrics_dict)
            ))
    
    def log_classification_result(
        self, 
        experiment_id: str,
        company_id: str,
        classification_type: str,
        confidence_score: float,
        processing_time_ms: int,
        is_correct: Optional[bool] = None
    ) -> None:
        """Log individual classification result"""
        with self._get_db() as conn:
            conn.execute("""
                INSERT INTO classification_results
                (experiment_id, company_id, classification_type, 
                 confidence_score, is_correct, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                experiment_id, company_id, classification_type,
                confidence_score, is_correct, processing_time_ms
            ))
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an experiment by ID"""
        with self._get_db() as conn:
            row = conn.execute("""
                SELECT e.*, rv.rules_config, rv.rule_hash
                FROM experiments e
                JOIN rule_versions rv ON e.rule_version_id = rv.version_id
                WHERE e.experiment_id = ?
            """, (experiment_id,)).fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all active experiments"""
        with self._get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM experiments 
                WHERE status = ? 
                ORDER BY start_date DESC
            """, (ExperimentStatus.ACTIVE,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def calculate_experiment_metrics(self, experiment_id: str) -> ExperimentMetrics:
        """Calculate current metrics for an experiment"""
        with self._get_db() as conn:
            # Get classification results
            results_df = pd.read_sql_query("""
                SELECT classification_type, confidence_score, is_correct, processing_time_ms
                FROM classification_results
                WHERE experiment_id = ?
            """, conn, params=(experiment_id,))
            
            if results_df.empty:
                return ExperimentMetrics()
            
            # Calculate metrics
            metrics = ExperimentMetrics(
                total_classifications=len(results_df)
            )
            
            # Accuracy (if ground truth available)
            if results_df['is_correct'].notna().any():
                metrics.accuracy_score = results_df['is_correct'].mean()
            
            # Precision/Recall by type (if ground truth available)
            if results_df['is_correct'].notna().any():
                for class_type in results_df['classification_type'].unique():
                    type_results = results_df[results_df['classification_type'] == class_type]
                    if len(type_results) > 0:
                        precision = type_results['is_correct'].mean()
                        metrics.precision_by_type[class_type] = precision
                        # Recall would require knowing false negatives
            
            # Confidence distribution
            confidence_bins = pd.cut(results_df['confidence_score'], 
                                   bins=[0, 0.5, 0.7, 0.8, 0.9, 1.0],
                                   labels=['<0.5', '0.5-0.7', '0.7-0.8', '0.8-0.9', '>0.9'])
            metrics.confidence_distribution = confidence_bins.value_counts().to_dict()
            
            # Processing times
            metrics.processing_time_p50 = results_df['processing_time_ms'].quantile(0.5)
            metrics.processing_time_p95 = results_df['processing_time_ms'].quantile(0.95)
            
            # Error rate (classifications with confidence < threshold)
            low_confidence_threshold = 0.5
            metrics.error_rate = (results_df['confidence_score'] < low_confidence_threshold).mean()
            
            return metrics
    
    def compare_experiments(
        self, 
        experiment_ids: List[str],
        save_comparison: bool = True
    ) -> ExperimentComparison:
        """Compare multiple experiments"""
        comparison = ExperimentComparison(
            comparison_id=f"comp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            experiment_ids=experiment_ids
        )
        
        # Calculate metrics for each experiment
        experiment_metrics = {}
        for exp_id in experiment_ids:
            metrics = self.calculate_experiment_metrics(exp_id)
            experiment_metrics[exp_id] = metrics
        
        # Compare key metrics
        if all(m.accuracy_score is not None for m in experiment_metrics.values()):
            accuracy_values = {
                exp_id: metrics.accuracy_score 
                for exp_id, metrics in experiment_metrics.items()
            }
            comparison.add_metric_comparison("accuracy", accuracy_values)
        
        # Compare error rates
        error_values = {
            exp_id: metrics.error_rate 
            for exp_id, metrics in experiment_metrics.items()
        }
        comparison.add_metric_comparison("error_rate", error_values)
        
        # Compare processing times
        p50_values = {
            exp_id: metrics.processing_time_p50 
            for exp_id, metrics in experiment_metrics.items()
        }
        comparison.add_metric_comparison("processing_time_p50", p50_values)
        
        # Determine winner (simplified - would use statistical tests in production)
        comparison.determine_winner("accuracy")
        
        if save_comparison:
            self._save_comparison(comparison)
        
        return comparison
    
    def _save_comparison(self, comparison: ExperimentComparison) -> None:
        """Save comparison to database"""
        with self._get_db() as conn:
            conn.execute("""
                INSERT INTO experiment_comparisons
                (comparison_id, experiment_ids, comparison_metrics, 
                 winner, statistical_significance, analysis_notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                comparison.comparison_id,
                json.dumps(comparison.experiment_ids),
                json.dumps(comparison.comparison_metrics),
                comparison.winner,
                comparison.statistical_significance,
                comparison.analysis_notes
            ))
    
    def generate_experiment_report(self, experiment_id: str) -> Dict[str, Any]:
        """Generate comprehensive report for an experiment"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        metrics = self.calculate_experiment_metrics(experiment_id)
        
        with self._get_db() as conn:
            # Get time series metrics
            metrics_over_time = pd.read_sql_query("""
                SELECT timestamp, total_classifications, accuracy_score, error_rate
                FROM experiment_metrics
                WHERE experiment_id = ?
                ORDER BY timestamp
            """, conn, params=(experiment_id,))
            
            # Get classification distribution
            classification_dist = pd.read_sql_query("""
                SELECT classification_type, COUNT(*) as count, 
                       AVG(confidence_score) as avg_confidence
                FROM classification_results
                WHERE experiment_id = ?
                GROUP BY classification_type
            """, conn, params=(experiment_id,))
        
        return {
            "experiment": experiment,
            "current_metrics": metrics.get_performance_summary(),
            "metrics_over_time": metrics_over_time.to_dict('records'),
            "classification_distribution": classification_dist.to_dict('records'),
            "duration_days": self._calculate_duration(experiment),
            "status": experiment['status']
        }
    
    def _calculate_duration(self, experiment: Dict[str, Any]) -> Optional[int]:
        """Calculate experiment duration"""
        if experiment['start_date'] and experiment['end_date']:
            start = datetime.fromisoformat(experiment['start_date'])
            end = datetime.fromisoformat(experiment['end_date'])
            return (end - start).days
        return None