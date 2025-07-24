"""
Module: classification.confidence
Purpose: Calculate confidence scores for classifications
Dependencies: typing, re, math

This module provides sophisticated confidence scoring for classification
results based on pattern matches, context, and various signal strength
indicators.

Classes:
    MatchResult: Result of pattern matching
    ConfidenceCalculator: Main confidence calculation engine
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from src.models.classification import ClassificationConfidence
from src.classification.rules_loader import ClassificationRule, RulePattern


@dataclass
class MatchResult:
    """Result of pattern matching against text"""
    pattern: RulePattern
    matched: bool
    match_text: str = ""
    match_positions: List[Tuple[int, int]] = None
    normalized_score: float = 0.0
    
    def __post_init__(self):
        if self.match_positions is None:
            self.match_positions = []


class ConfidenceCalculator:
    """
    Calculate confidence scores for classifications
    
    This class provides sophisticated confidence scoring that considers:
    - Pattern match strength and count
    - Context surrounding matches
    - Text quality and length
    - Signal consistency across multiple patterns
    - Boost conditions from rules
    """
    
    def __init__(self):
        """Initialize confidence calculator"""
        self.logger = logging.getLogger(__name__)
        
        # Confidence calculation parameters
        self.base_confidence = 0.3
        self.max_confidence = 0.95
        self.pattern_weight = 0.4
        self.context_weight = 0.25
        self.consistency_weight = 0.2
        self.boost_weight = 0.15
    
    def calculate_confidence(
        self, 
        rule: ClassificationRule,
        text: str,
        api_confidence: float = 0.5,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ClassificationConfidence:
        """
        Calculate comprehensive confidence score for a classification
        
        Args:
            rule: Classification rule being evaluated
            text: Text being classified
            api_confidence: Confidence from the API response
            additional_context: Additional context for confidence calculation
            
        Returns:
            ClassificationConfidence with detailed scoring
        """
        # Match patterns against text
        match_results = self._match_patterns(rule.patterns, text)
        
        # Calculate individual confidence components
        pattern_score = self._calculate_pattern_score(match_results)
        context_score = self._calculate_context_score(match_results, text)
        consistency_score = self._calculate_consistency_score(match_results)
        boost_score = self._calculate_boost_score(rule.confidence_boosts, text)
        
        # Combine scores with weights
        weighted_score = (
            pattern_score * self.pattern_weight +
            context_score * self.context_weight +
            consistency_score * self.consistency_weight +
            boost_score * self.boost_weight
        )
        
        # Apply API confidence factor
        api_factor = 0.8 + (api_confidence * 0.4)  # Scale API confidence to 0.8-1.2
        final_score = weighted_score * api_factor
        
        # Ensure score is within bounds
        final_score = max(0.0, min(self.max_confidence, final_score))
        
        # Build detailed confidence explanation
        explanation = self._build_explanation(
            pattern_score, context_score, consistency_score, 
            boost_score, api_confidence, final_score
        )
        
        # Extract pattern match details
        pattern_matches = [
            {
                "pattern": result.pattern.pattern,
                "type": result.pattern.pattern_type,
                "weight": result.pattern.weight,
                "matched": result.matched,
                "score": result.normalized_score,
                "match_text": result.match_text
            }
            for result in match_results
        ]
        
        # Build rule scores
        rule_scores = {
            "pattern_matching": pattern_score,
            "context_analysis": context_score,
            "signal_consistency": consistency_score,
            "boost_conditions": boost_score,
            "api_confidence_factor": api_factor
        }
        
        # Identify confidence factors
        confidence_factors = self._identify_confidence_factors(
            match_results, pattern_score, context_score, consistency_score, boost_score
        )
        
        return ClassificationConfidence(
            overall_score=final_score,
            pattern_matches=pattern_matches,
            rule_scores=rule_scores,
            confidence_factors=confidence_factors,
            explanation=explanation
        )
    
    def _match_patterns(self, patterns: List[RulePattern], text: str) -> List[MatchResult]:
        """
        Match all patterns against text and return results
        
        Args:
            patterns: List of patterns to match
            text: Text to match against
            
        Returns:
            List of match results
        """
        results = []
        text_lower = text.lower()
        
        for pattern in patterns:
            result = MatchResult(pattern=pattern, matched=False)
            
            try:
                if pattern.pattern_type == "regex":
                    matches = list(re.finditer(pattern.pattern, text_lower, re.IGNORECASE))
                    if matches:
                        result.matched = True
                        result.match_text = matches[0].group()
                        result.match_positions = [(m.start(), m.end()) for m in matches]
                        # Score based on number and quality of matches
                        result.normalized_score = min(1.0, len(matches) * 0.3 + 0.4)
                
                elif pattern.pattern_type == "keywords":
                    # Extract keywords from regex pattern
                    keyword_pattern = pattern.pattern
                    if r'\b(' in keyword_pattern and r')\b' in keyword_pattern:
                        # Extract keywords from regex
                        keywords_part = keyword_pattern.split(r'\b(')[1].split(r')\b')[0]
                        keywords = keywords_part.split('|')
                    else:
                        keywords = [keyword_pattern]
                    
                    matched_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in text_lower:
                            matched_keywords.append(keyword)
                    
                    if matched_keywords:
                        result.matched = True
                        result.match_text = ", ".join(matched_keywords)
                        result.normalized_score = min(1.0, len(matched_keywords) / len(keywords))
                
                elif pattern.pattern_type == "exact":
                    if pattern.pattern.lower() in text_lower:
                        result.matched = True
                        result.match_text = pattern.pattern
                        result.normalized_score = 1.0
                
            except Exception as e:
                self.logger.warning(f"Error matching pattern '{pattern.pattern}': {e}")
                result.matched = False
                result.normalized_score = 0.0
            
            results.append(result)
        
        return results
    
    def _calculate_pattern_score(self, match_results: List[MatchResult]) -> float:
        """Calculate score based on pattern matching success"""
        if not match_results:
            return 0.0
        
        total_weight = sum(result.pattern.weight for result in match_results)
        if total_weight == 0:
            return 0.0
        
        weighted_score = sum(
            result.normalized_score * result.pattern.weight 
            for result in match_results 
            if result.matched
        )
        
        # Normalize by total possible weight
        base_score = weighted_score / total_weight
        
        # Boost for multiple matches
        match_count = sum(1 for result in match_results if result.matched)
        if match_count > 1:
            base_score *= (1 + (match_count - 1) * 0.1)  # 10% boost per additional match
        
        return min(1.0, base_score)
    
    def _calculate_context_score(self, match_results: List[MatchResult], text: str) -> float:
        """Calculate score based on context quality around matches"""
        if not any(result.matched for result in match_results):
            return 0.0
        
        context_score = 0.5  # Base context score
        
        # Check text length (sweet spot is 50-500 characters)
        text_length = len(text)
        if 50 <= text_length <= 500:
            context_score += 0.2
        elif 20 <= text_length < 50 or 500 < text_length <= 1000:
            context_score += 0.1
        elif text_length < 20:
            context_score -= 0.2
        
        # Check for supporting words around matches
        supporting_words = {
            'low_pay_rate': ['salary', 'wage', 'compensation', 'pay', 'rate', 'below', 'market'],
            'geographic_coverage': ['location', 'area', 'region', 'distance', 'coverage', 'nearby'],
            'shift_timing_mismatch': ['time', 'shift', 'schedule', 'hours', 'timing', 'availability'],
            'contract_renegotiation': ['contract', 'agreement', 'terms', 'renewal', 'expired'],
            'market_analysis': ['market', 'competition', 'analysis', 'trends', 'research'],
            'partner_meeting': ['meeting', 'discussion', 'review', 'escalation', 'urgent']
        }
        
        # Check for supporting context
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        for category, words in supporting_words.items():
            overlap = len(text_words.intersection(set(words)))
            if overlap > 0:
                context_score += min(0.2, overlap * 0.05)
        
        return min(1.0, context_score)
    
    def _calculate_consistency_score(self, match_results: List[MatchResult]) -> float:
        """Calculate score based on consistency of signals"""
        matched_results = [result for result in match_results if result.matched]
        
        if not matched_results:
            return 0.0
        
        if len(matched_results) == 1:
            return 0.7  # Single match gets moderate consistency
        
        # Multiple matches - check score variance
        scores = [result.normalized_score for result in matched_results]
        avg_score = sum(scores) / len(scores)
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        
        # Lower variance = higher consistency
        consistency = 1.0 - min(1.0, variance * 2)
        
        # Boost for multiple consistent matches
        if len(matched_results) >= 2 and consistency > 0.7:
            consistency += 0.1
        
        return min(1.0, consistency)
    
    def _calculate_boost_score(
        self, 
        boost_conditions: List[Dict[str, Any]], 
        text: str
    ) -> float:
        """Calculate confidence boost based on special conditions"""
        if not boost_conditions:
            return 0.0
        
        total_boost = 0.0
        text_lower = text.lower()
        
        for condition in boost_conditions:
            if "if_contains" in condition:
                terms = condition["if_contains"]
                if isinstance(terms, str):
                    terms = [terms]
                
                if any(term.lower() in text_lower for term in terms):
                    boost_amount = condition.get("boost", 0.1)
                    total_boost += boost_amount
        
        return min(0.3, total_boost)  # Cap boost at 30%
    
    def _build_explanation(
        self, 
        pattern_score: float,
        context_score: float, 
        consistency_score: float,
        boost_score: float,
        api_confidence: float,
        final_score: float
    ) -> str:
        """Build human-readable explanation of confidence calculation"""
        parts = []
        
        # Pattern matching
        if pattern_score > 0.8:
            parts.append("Strong pattern matches found")
        elif pattern_score > 0.5:
            parts.append("Moderate pattern matches found")
        else:
            parts.append("Weak pattern matches")
        
        # Context
        if context_score > 0.7:
            parts.append("good supporting context")
        elif context_score > 0.5:
            parts.append("some supporting context")
        else:
            parts.append("limited context")
        
        # Consistency
        if consistency_score > 0.7:
            parts.append("consistent signals")
        elif consistency_score > 0.5:
            parts.append("moderately consistent signals")
        
        # Boosts
        if boost_score > 0.1:
            parts.append("confidence boost conditions met")
        
        # API confidence
        if api_confidence > 0.8:
            parts.append("high API confidence")
        elif api_confidence < 0.5:
            parts.append("low API confidence")
        
        explanation = f"Classification confidence of {final_score:.3f} based on: {', '.join(parts)}."
        
        return explanation
    
    def _identify_confidence_factors(
        self,
        match_results: List[MatchResult],
        pattern_score: float,
        context_score: float,
        consistency_score: float,
        boost_score: float
    ) -> List[str]:
        """Identify key factors that influenced confidence"""
        factors = []
        
        # Strong factors
        if pattern_score > 0.8:
            factors.append("strong_pattern_match")
        if context_score > 0.7:
            factors.append("rich_context")
        if consistency_score > 0.8:
            factors.append("signal_consistency")
        if boost_score > 0.1:
            factors.append("boost_conditions")
        
        # Multiple matches
        match_count = sum(1 for result in match_results if result.matched)
        if match_count > 2:
            factors.append("multiple_pattern_matches")
        
        # Weak factors
        if pattern_score < 0.4:
            factors.append("weak_pattern_match")
        if context_score < 0.4:
            factors.append("limited_context")
        
        return factors