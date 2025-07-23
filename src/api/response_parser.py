"""
Module: api.response_parser
Purpose: Transforms API responses into structured, validated data
Dependencies: pydantic, typing, re, datetime

This module provides utilities for parsing and transforming raw API
responses into structured data suitable for classification. It includes:
- Text preprocessing and normalization
- Extraction of key information from response text
- Validation of response structure
- Enrichment with additional context

Classes:
    TextProcessor: Utility for text preprocessing
    APIResponseParser: Main parser for API responses
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass

from src.models.schemas import APIResponse, APIResponseSchema


@dataclass
class ParsedContent:
    """Structured content extracted from API response"""
    original_text: str
    normalized_text: str
    key_phrases: List[str]
    sentiment_indicators: Dict[str, List[str]]
    confidence_signals: List[str]
    entities: Dict[str, List[str]]
    metadata: Dict[str, Any]


class TextProcessor:
    """
    Utility class for text preprocessing and normalization
    
    This class provides methods for:
    - Text cleaning and normalization
    - Key phrase extraction
    - Sentiment analysis
    - Entity recognition (simplified)
    """
    
    def __init__(self):
        """Initialize text processor"""
        self.logger = logging.getLogger(__name__)
        
        # Common stopwords for filtering
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Patterns for extracting specific information
        self.patterns = {
            'percentage': re.compile(r'\b(\d+(?:\.\d+)?)\s*%', re.IGNORECASE),
            'currency': re.compile(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'time_period': re.compile(r'\b(daily|weekly|monthly|quarterly|annual|hourly)\b', re.IGNORECASE),
            'location': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)\b'),
            'urgency': re.compile(r'\b(urgent|immediate|asap|critical|high priority)\b', re.IGNORECASE),
            'negative_sentiment': re.compile(r'\b(low|poor|bad|terrible|awful|decline|decrease|drop|fall)\b', re.IGNORECASE),
            'positive_sentiment': re.compile(r'\b(high|good|great|excellent|improve|increase|rise|growth)\b', re.IGNORECASE)
        }
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent processing
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove special characters but keep basic punctuation
        normalized = re.sub(r'[^\w\s.,!?;:\-()$%]', '', normalized)
        
        return normalized
    
    def extract_key_phrases(self, text: str, min_length: int = 3, max_phrases: int = 20) -> List[str]:
        """
        Extract key phrases from text
        
        Args:
            text: Text to analyze
            min_length: Minimum phrase length in characters
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of key phrases
        """
        if not text:
            return []
        
        # Normalize text
        normalized = self.normalize_text(text)
        
        # Split into sentences
        sentences = re.split(r'[.!?;]', normalized)
        
        phrases = []
        for sentence in sentences:
            # Split into potential phrases (noun phrases, etc.)
            words = sentence.split()
            
            # Extract multi-word phrases
            for i in range(len(words)):
                for j in range(i + 2, min(i + 6, len(words) + 1)):  # 2-5 word phrases
                    phrase = ' '.join(words[i:j])
                    
                    # Filter out phrases with only stopwords
                    phrase_words = phrase.split()
                    if not all(word in self.stopwords for word in phrase_words):
                        if len(phrase) >= min_length:
                            phrases.append(phrase)
        
        # Remove duplicates and sort by length (longer phrases first)
        unique_phrases = list(set(phrases))
        unique_phrases.sort(key=len, reverse=True)
        
        return unique_phrases[:max_phrases]
    
    def analyze_sentiment_indicators(self, text: str) -> Dict[str, List[str]]:
        """
        Analyze sentiment indicators in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of sentiment indicators
        """
        indicators = {
            'negative': [],
            'positive': [],
            'neutral': []
        }
        
        if not text:
            return indicators
        
        # Find negative sentiment words
        negative_matches = self.patterns['negative_sentiment'].findall(text)
        indicators['negative'] = list(set(negative_matches))
        
        # Find positive sentiment words
        positive_matches = self.patterns['positive_sentiment'].findall(text)
        indicators['positive'] = list(set(positive_matches))
        
        # Calculate overall sentiment
        negative_count = len(indicators['negative'])
        positive_count = len(indicators['positive'])
        
        if negative_count > positive_count * 1.5:
            indicators['overall'] = 'negative'
        elif positive_count > negative_count * 1.5:
            indicators['overall'] = 'positive'
        else:
            indicators['overall'] = 'neutral'
        
        return indicators
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text (simplified implementation)
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {
            'percentages': [],
            'currencies': [],
            'time_periods': [],
            'locations': [],
            'urgency_markers': []
        }
        
        if not text:
            return entities
        
        # Extract percentages
        percentages = self.patterns['percentage'].findall(text)
        entities['percentages'] = [f"{p}%" for p in percentages]
        
        # Extract currency amounts
        currencies = self.patterns['currency'].findall(text)
        entities['currencies'] = [f"${c}" for c in currencies]
        
        # Extract time periods
        time_periods = self.patterns['time_period'].findall(text)
        entities['time_periods'] = list(set(time_periods))
        
        # Extract potential locations
        locations = self.patterns['location'].findall(text)
        entities['locations'] = list(set(locations))
        
        # Extract urgency markers
        urgency_markers = self.patterns['urgency'].findall(text)
        entities['urgency_markers'] = list(set(urgency_markers))
        
        return entities
    
    def identify_confidence_signals(self, text: str) -> List[str]:
        """
        Identify signals that indicate confidence level
        
        Args:
            text: Text to analyze
            
        Returns:
            List of confidence signals
        """
        signals = []
        
        if not text:
            return signals
        
        # High confidence signals
        high_confidence_patterns = [
            r'\b(definitely|certainly|clearly|obviously|undoubtedly)\b',
            r'\b(strong|significant|major|substantial)\b',
            r'\b(data shows|analysis indicates|research confirms)\b'
        ]
        
        # Low confidence signals
        low_confidence_patterns = [
            r'\b(possibly|maybe|might|could|appears|seems)\b',
            r'\b(uncertain|unclear|ambiguous)\b',
            r'\b(limited data|insufficient information)\b'
        ]
        
        text_lower = text.lower()
        
        for pattern in high_confidence_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                signals.extend([f"high_confidence: {match}" for match in matches])
        
        for pattern in low_confidence_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                signals.extend([f"low_confidence: {match}" for match in matches])
        
        return signals


class APIResponseParser:
    """
    Main parser for API responses
    
    This class transforms raw API responses into structured, validated
    data ready for classification processing.
    """
    
    def __init__(self):
        """Initialize response parser"""
        self.logger = logging.getLogger(__name__)
        self.text_processor = TextProcessor()
    
    def parse_response(self, api_response: APIResponse) -> ParsedContent:
        """
        Parse API response into structured content
        
        Args:
            api_response: Raw API response to parse
            
        Returns:
            Structured parsed content
        """
        self.logger.debug(f"Parsing response for company {api_response.company_id}")
        
        # Combine all prediction texts
        combined_text = ' '.join(api_response.predictions)
        
        # Process the text
        normalized_text = self.text_processor.normalize_text(combined_text)
        key_phrases = self.text_processor.extract_key_phrases(combined_text)
        sentiment_indicators = self.text_processor.analyze_sentiment_indicators(combined_text)
        confidence_signals = self.text_processor.identify_confidence_signals(combined_text)
        entities = self.text_processor.extract_entities(combined_text)
        
        # Extract metadata from API response
        metadata = {
            'company_id': api_response.company_id,
            'api_confidence': api_response.confidence,
            'prediction_count': len(api_response.predictions),
            'model_version': api_response.model_version,
            'generated_at': api_response.generated_at.isoformat(),
            'metrics_summary': self._summarize_metrics(api_response.metrics)
        }
        
        parsed_content = ParsedContent(
            original_text=combined_text,
            normalized_text=normalized_text,
            key_phrases=key_phrases,
            sentiment_indicators=sentiment_indicators,
            confidence_signals=confidence_signals,
            entities=entities,
            metadata=metadata
        )
        
        self.logger.debug(
            f"Parsed response: {len(key_phrases)} phrases, "
            f"{len(entities['percentages'])} percentages, "
            f"sentiment: {sentiment_indicators.get('overall', 'unknown')}"
        )
        
        return parsed_content
    
    def validate_and_enrich_response(
        self, 
        raw_response: APIResponse,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> APIResponseSchema:
        """
        Validate and enrich API response
        
        Args:
            raw_response: Raw API response
            additional_context: Additional context to include
            
        Returns:
            Validated and enriched response schema
        """
        schema = APIResponseSchema(raw_response=raw_response)
        
        # Parse content
        parsed_content = self.parse_response(raw_response)
        
        # Validate response quality
        validation_errors = []
        
        # Check for empty predictions
        if not raw_response.predictions or all(not p.strip() for p in raw_response.predictions):
            validation_errors.append("Empty or whitespace-only predictions")
            schema.add_validation_error("Empty predictions received")
        
        # Check prediction length
        combined_length = sum(len(p) for p in raw_response.predictions)
        if combined_length < 10:
            validation_errors.append("Predictions too short")
            schema.add_validation_error("Predictions are too short to be meaningful")
        elif combined_length > 10000:
            validation_errors.append("Predictions too long")
            schema.add_validation_error("Predictions are unusually long")
        
        # Check confidence level
        if raw_response.confidence < 0.1:
            validation_errors.append("Very low API confidence")
            schema.add_validation_error("API confidence is very low")
        
        # Check for required metrics
        required_metrics = {'fill_rate', 'total_shifts'}
        missing_metrics = required_metrics - set(raw_response.metrics.keys())
        if missing_metrics:
            error_msg = f"Missing required metrics: {missing_metrics}"
            validation_errors.append(error_msg)
            schema.add_validation_error(error_msg)
        
        # Enrich with parsed content
        enrichment_data = {
            'parsed_content': {
                'key_phrases': parsed_content.key_phrases[:10],  # Limit for storage
                'sentiment': parsed_content.sentiment_indicators.get('overall'),
                'entity_count': {k: len(v) for k, v in parsed_content.entities.items()},
                'confidence_signals_count': len(parsed_content.confidence_signals),
                'text_length': len(parsed_content.original_text),
                'normalized_text_length': len(parsed_content.normalized_text)
            },
            'validation_summary': {
                'error_count': len(validation_errors),
                'errors': validation_errors,
                'quality_score': self._calculate_quality_score(parsed_content, raw_response)
            }
        }
        
        # Add additional context if provided
        if additional_context:
            enrichment_data.update(additional_context)
        
        schema.enrich_with_context(enrichment_data)
        
        return schema
    
    def extract_classification_hints(self, parsed_content: ParsedContent) -> Dict[str, float]:
        """
        Extract hints for classification from parsed content
        
        Args:
            parsed_content: Parsed content to analyze
            
        Returns:
            Dictionary mapping classification types to hint scores
        """
        hints = {}
        
        # Analyze key phrases for classification hints
        text_lower = parsed_content.normalized_text
        
        # Pay rate related hints
        pay_indicators = ['pay', 'wage', 'salary', 'compensation', 'rate', 'below market', 'underpaid']
        pay_score = sum(1 for indicator in pay_indicators if indicator in text_lower)
        if pay_score > 0:
            hints['low_pay_rate'] = min(1.0, pay_score / len(pay_indicators))
        
        # Geographic coverage hints
        geo_indicators = ['location', 'area', 'region', 'coverage', 'distance', 'nearby', 'far']
        geo_score = sum(1 for indicator in geo_indicators if indicator in text_lower)
        if geo_score > 0:
            hints['geographic_coverage'] = min(1.0, geo_score / len(geo_indicators))
        
        # Timing related hints
        timing_indicators = ['time', 'shift', 'schedule', 'timing', 'hours', 'overnight', 'morning']
        timing_score = sum(1 for indicator in timing_indicators if indicator in text_lower)
        if timing_score > 0:
            hints['shift_timing_mismatch'] = min(1.0, timing_score / len(timing_indicators))
        
        # Contract related hints
        contract_indicators = ['contract', 'agreement', 'terms', 'renewal', 'expired', 'renegotiate']
        contract_score = sum(1 for indicator in contract_indicators if indicator in text_lower)
        if contract_score > 0:
            hints['contract_renegotiation'] = min(1.0, contract_score / len(contract_indicators))
        
        # Boost scores based on sentiment and confidence signals
        if parsed_content.sentiment_indicators.get('overall') == 'negative':
            # Negative sentiment boosts problem-related classifications
            for key in ['low_pay_rate', 'geographic_coverage', 'shift_timing_mismatch']:
                if key in hints:
                    hints[key] = min(1.0, hints[key] * 1.2)
        
        # High confidence API response boosts all hints
        api_confidence = parsed_content.metadata.get('api_confidence', 0.5)
        if api_confidence > 0.8:
            for key in hints:
                hints[key] = min(1.0, hints[key] * 1.1)
        
        return hints
    
    def _summarize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize metrics for metadata"""
        summary = {}
        
        # Extract key metrics
        if 'fill_rate' in metrics:
            fill_rate = metrics['fill_rate']
            if isinstance(fill_rate, (int, float)):
                if fill_rate < 50:
                    summary['fill_rate_category'] = 'very_low'
                elif fill_rate < 70:
                    summary['fill_rate_category'] = 'low'
                elif fill_rate < 85:
                    summary['fill_rate_category'] = 'medium'
                else:
                    summary['fill_rate_category'] = 'high'
        
        # Count available metrics
        summary['metrics_count'] = len(metrics)
        summary['has_financial_data'] = any(
            key in metrics for key in ['pay_rate', 'cost', 'revenue', 'margin']
        )
        summary['has_geographic_data'] = any(
            key in metrics for key in ['location', 'region', 'coverage', 'distance']
        )
        
        return summary
    
    def _calculate_quality_score(
        self, 
        parsed_content: ParsedContent, 
        raw_response: APIResponse
    ) -> float:
        """
        Calculate overall quality score for the response
        
        Args:
            parsed_content: Parsed content
            raw_response: Raw API response
            
        Returns:
            Quality score between 0 and 1
        """
        score = 0.0
        
        # API confidence contributes 30%
        score += raw_response.confidence * 0.3
        
        # Text content quality contributes 25%
        text_length = len(parsed_content.original_text)
        if 50 <= text_length <= 1000:  # Ideal range
            score += 0.25
        elif text_length > 10:  # Minimum acceptable
            score += 0.15
        
        # Key phrase extraction contributes 20%
        phrase_count = len(parsed_content.key_phrases)
        if phrase_count >= 5:
            score += 0.20
        elif phrase_count >= 2:
            score += 0.10
        
        # Entity extraction contributes 15%
        entity_count = sum(len(entities) for entities in parsed_content.entities.values())
        if entity_count >= 3:
            score += 0.15
        elif entity_count >= 1:
            score += 0.10
        
        # Confidence signals contribute 10%
        if parsed_content.confidence_signals:
            score += 0.10
        
        return min(1.0, score)