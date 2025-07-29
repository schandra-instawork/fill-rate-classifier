"""
Module: classification.recommendation_classifier
Purpose: Classifies fill rate recommendations into actionable categories
Dependencies: src/api/claude_client.py, src/models/classification.py

This module uses Claude to intelligently classify recommendations from
the Fill Rate Analysis API into specific action categories.

Classes:
    RecommendationClassifier: Main classifier for recommendations
    ClassificationResult: Result of classification with confidence
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re

from src.api.claude_client import ClaudeAPIClient
from src.models.classification import Classification


class RecommendationCategory(Enum):
    """Categories for fill rate recommendations"""
    WAGE_ADJUSTMENT = "wage_adjustment"
    LEAD_TIME = "lead_time"
    GEOGRAPHIC_EXPANSION = "geographic_expansion"
    WORKER_QUALITY = "worker_quality"
    REQUIREMENT_BARRIERS = "requirement_barriers"
    SHIFT_TIMING = "shift_timing"
    SUPPLY_DEMAND = "supply_demand"
    URGENT_ACTION = "urgent_action"
    OTHER = "other"


@dataclass
class ClassificationResult:
    """Result of recommendation classification"""
    category: RecommendationCategory
    confidence: float
    extracted_values: Dict[str, Any]
    action_priority: str  # HIGH, MEDIUM, LOW
    specific_action: str
    original_recommendation: str


class RecommendationClassifier:
    """
    Classifies fill rate recommendations into actionable categories
    
    Uses Claude to understand context and extract specific values
    from recommendations for targeted actions.
    """
    
    def __init__(self, claude_client: ClaudeAPIClient):
        """
        Initialize classifier
        
        Args:
            claude_client: Claude API client for classification
        """
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
        
        # Pattern matchers for quick classification
        self.patterns = {
            RecommendationCategory.WAGE_ADJUSTMENT: [
                r"increase.*wage|raise.*pay|pay.*below|wage.*competitive|increase.*rate.*\$",
                r"offer.*\$\d+|recommended.*\$\d+|adjust.*pricing"
            ],
            RecommendationCategory.LEAD_TIME: [
                r"post.*earlier|lead.*time|advance.*notice|booking.*lead",
                r"\d+.*hours.*advance|schedule.*sooner"
            ],
            RecommendationCategory.GEOGRAPHIC_EXPANSION: [
                r"expand.*radius|geographic|distance|miles.*away|access.*tier",
                r"worker.*pool.*location|broaden.*reach"
            ],
            RecommendationCategory.WORKER_QUALITY: [
                r"call.*worker|high.*risk|reliability|worker.*ID|contact.*immediately",
                r"monitor.*specific|check.*status"
            ],
            RecommendationCategory.REQUIREMENT_BARRIERS: [
                r"remove.*requirement|background.*check|drug.*screen|W2.*only",
                r"relax.*criteria|reduce.*barrier"
            ],
            RecommendationCategory.SHIFT_TIMING: [
                r"shift.*timing|time.*of.*day|morning.*shift|evening.*hours",
                r"avoid.*early|weekend.*pattern"
            ],
            RecommendationCategory.SUPPLY_DEMAND: [
                r"supply.*demand|worker.*shortage|eligible.*pool|increase.*slots",
                r"not.*enough.*workers|limited.*availability"
            ],
            RecommendationCategory.URGENT_ACTION: [
                r"immediate|urgent|critical|NOW|ASAP|today",
                r"within.*\d+.*hour|before.*shift.*start"
            ]
        }
    
    def classify_recommendations(
        self,
        recommendations: List[str],
        analysis_context: Optional[Dict[str, Any]] = None
    ) -> List[ClassificationResult]:
        """
        Classify a list of recommendations
        
        Args:
            recommendations: List of recommendation texts
            analysis_context: Additional context from the analysis
            
        Returns:
            List of classification results
        """
        results = []
        
        for recommendation in recommendations:
            result = self._classify_single_recommendation(recommendation, analysis_context)
            results.append(result)
        
        return results
    
    def _classify_single_recommendation(
        self,
        recommendation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classify a single recommendation
        
        Args:
            recommendation: Recommendation text
            context: Additional context
            
        Returns:
            Classification result
        """
        # First try pattern matching for quick classification
        category, confidence = self._pattern_match_category(recommendation)
        
        # Extract values from recommendation
        extracted_values = self._extract_values(recommendation)
        
        # Use Claude for more nuanced classification if needed
        if confidence < 0.7:
            category, confidence, extracted_values = self._claude_classify(
                recommendation, context
            )
        
        # Determine action priority
        priority = self._determine_priority(recommendation, category, extracted_values)
        
        # Generate specific action
        specific_action = self._generate_specific_action(
            category, extracted_values, recommendation
        )
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            extracted_values=extracted_values,
            action_priority=priority,
            specific_action=specific_action,
            original_recommendation=recommendation
        )
    
    def _pattern_match_category(self, text: str) -> Tuple[RecommendationCategory, float]:
        """
        Use regex patterns to quickly categorize
        
        Args:
            text: Recommendation text
            
        Returns:
            Category and confidence score
        """
        text_lower = text.lower()
        best_category = RecommendationCategory.OTHER
        best_confidence = 0.3
        
        for category, patterns in self.patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text_lower))
            if matches > 0:
                confidence = min(0.9, 0.5 + (matches * 0.2))
                if confidence > best_confidence:
                    best_category = category
                    best_confidence = confidence
        
        return best_category, best_confidence
    
    def _extract_values(self, text: str) -> Dict[str, Any]:
        """
        Extract specific values from recommendation text
        
        Args:
            text: Recommendation text
            
        Returns:
            Dictionary of extracted values
        """
        values = {}
        
        # Extract dollar amounts
        dollar_matches = re.findall(r'\$(\d+(?:\.\d{2})?)', text)
        if dollar_matches:
            values['wage_amounts'] = [float(amt) for amt in dollar_matches]
        
        # Extract percentages
        percent_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        if percent_matches:
            values['percentages'] = [float(pct) for pct in percent_matches]
        
        # Extract hours
        hour_matches = re.findall(r'(\d+)\s*hours?', text)
        if hour_matches:
            values['hours'] = [int(hrs) for hrs in hour_matches]
        
        # Extract distances
        mile_matches = re.findall(r'(\d+)\s*miles?', text)
        if mile_matches:
            values['miles'] = [int(dist) for dist in mile_matches]
        
        # Extract worker IDs (assuming format like W12345)
        worker_id_matches = re.findall(r'[Ww]orker.*?([A-Z]?\d{4,})', text)
        if worker_id_matches:
            values['worker_ids'] = worker_id_matches
        
        return values
    
    def _claude_classify(
        self,
        recommendation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[RecommendationCategory, float, Dict[str, Any]]:
        """
        Use Claude for more sophisticated classification
        
        Args:
            recommendation: Recommendation text
            context: Additional context
            
        Returns:
            Category, confidence, and extracted values
        """
        prompt = f"""Classify this fill rate recommendation into one of these categories:
- WAGE_ADJUSTMENT: Pay rate changes, pricing adjustments
- LEAD_TIME: Posting shifts earlier, advance notice
- GEOGRAPHIC_EXPANSION: Expanding worker radius, location issues
- WORKER_QUALITY: Specific worker actions, reliability issues
- REQUIREMENT_BARRIERS: Background checks, certifications, employment type
- SHIFT_TIMING: Time of day, day of week patterns
- SUPPLY_DEMAND: Worker pool size, availability issues
- URGENT_ACTION: Immediate actions needed
- OTHER: Doesn't fit other categories

Recommendation: "{recommendation}"

{f"Context: {context}" if context else ""}

Respond with:
1. Category name (from list above)
2. Confidence (0-1)
3. Any specific values mentioned (wages, hours, distances, worker IDs)

Format: CATEGORY|CONFIDENCE|VALUE1:X,VALUE2:Y"""
        
        try:
            response = self.claude_client.call_claude(prompt)
            
            # Parse Claude's response
            parts = response.strip().split('|')
            if len(parts) >= 2:
                category_str = parts[0].strip().upper()
                confidence = float(parts[1].strip())
                
                # Map string to enum
                try:
                    category = RecommendationCategory[category_str]
                except KeyError:
                    category = RecommendationCategory.OTHER
                
                # Extract values if provided
                values = {}
                if len(parts) > 2:
                    value_pairs = parts[2].split(',')
                    for pair in value_pairs:
                        if ':' in pair:
                            key, val = pair.split(':', 1)
                            values[key.strip().lower()] = val.strip()
                
                return category, confidence, values
                
        except Exception as e:
            self.logger.error(f"Claude classification failed: {e}")
            
        # Fallback to pattern matching
        return self._pattern_match_category(recommendation)[0], 0.5, {}
    
    def _determine_priority(
        self,
        text: str,
        category: RecommendationCategory,
        values: Dict[str, Any]
    ) -> str:
        """
        Determine action priority
        
        Args:
            text: Recommendation text
            category: Classified category
            values: Extracted values
            
        Returns:
            Priority level (HIGH, MEDIUM, LOW)
        """
        text_lower = text.lower()
        
        # Check for urgent keywords
        if any(word in text_lower for word in ['immediate', 'urgent', 'critical', 'now', 'asap']):
            return "HIGH"
        
        # Category-specific priority rules
        if category == RecommendationCategory.URGENT_ACTION:
            return "HIGH"
        
        if category == RecommendationCategory.WAGE_ADJUSTMENT:
            if 'percentages' in values and any(pct > 20 for pct in values['percentages']):
                return "HIGH"
            return "MEDIUM"
        
        if category == RecommendationCategory.WORKER_QUALITY:
            if 'worker_ids' in values:
                return "HIGH"
            return "MEDIUM"
        
        if category == RecommendationCategory.LEAD_TIME:
            if 'hours' in values and any(hrs < 24 for hrs in values['hours']):
                return "HIGH"
            return "MEDIUM"
        
        return "MEDIUM"
    
    def _generate_specific_action(
        self,
        category: RecommendationCategory,
        values: Dict[str, Any],
        original_text: str
    ) -> str:
        """
        Generate specific actionable instruction
        
        Args:
            category: Recommendation category
            values: Extracted values
            original_text: Original recommendation
            
        Returns:
            Specific action text
        """
        if category == RecommendationCategory.WAGE_ADJUSTMENT:
            if 'wage_amounts' in values and len(values['wage_amounts']) >= 2:
                return f"Update wage from ${values['wage_amounts'][0]} to ${values['wage_amounts'][1]}"
            return "Review and adjust wage to market rate"
        
        elif category == RecommendationCategory.LEAD_TIME:
            if 'hours' in values:
                return f"Post shifts at least {max(values['hours'])} hours in advance"
            return "Increase shift posting lead time"
        
        elif category == RecommendationCategory.GEOGRAPHIC_EXPANSION:
            if 'miles' in values:
                return f"Expand worker search radius to {max(values['miles'])} miles"
            return "Expand geographic search radius"
        
        elif category == RecommendationCategory.WORKER_QUALITY:
            if 'worker_ids' in values:
                return f"Contact workers immediately: {', '.join(values['worker_ids'])}"
            return "Review and contact high-risk workers"
        
        elif category == RecommendationCategory.REQUIREMENT_BARRIERS:
            return "Review and potentially relax job requirements"
        
        elif category == RecommendationCategory.SHIFT_TIMING:
            return "Adjust shift timing to match worker availability"
        
        elif category == RecommendationCategory.SUPPLY_DEMAND:
            return "Increase worker pool or adjust demand"
        
        elif category == RecommendationCategory.URGENT_ACTION:
            return original_text  # Keep original for urgent actions
        
        else:
            return "Review recommendation for custom action"


def group_by_category(
    classifications: List[ClassificationResult]
) -> Dict[RecommendationCategory, List[ClassificationResult]]:
    """
    Group classification results by category
    
    Args:
        classifications: List of classification results
        
    Returns:
        Dictionary mapping categories to results
    """
    grouped = {}
    for result in classifications:
        if result.category not in grouped:
            grouped[result.category] = []
        grouped[result.category].append(result)
    
    return grouped


def prioritize_actions(
    classifications: List[ClassificationResult]
) -> List[ClassificationResult]:
    """
    Sort classifications by priority and confidence
    
    Args:
        classifications: List of classification results
        
    Returns:
        Sorted list with highest priority first
    """
    priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    
    return sorted(
        classifications,
        key=lambda x: (priority_map.get(x.action_priority, 0), x.confidence),
        reverse=True
    )