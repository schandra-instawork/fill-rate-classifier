"""
Module: api.claude_client
Purpose: Client for Instawork's internal Claude API for fill rate predictions
Dependencies: requests, tenacity, pydantic, logging

This module provides a client for generating fill rate predictions using
Instawork's internal Claude API. It creates realistic fill rate analysis
based on company metrics and generates actionable insights.

Classes:
    ClaudeAPIClient: Client for the internal Claude API
    FillRatePredictionGenerator: Generates fill rate predictions using Claude
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import json

import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)
from pydantic import BaseModel, Field

from src.models.schemas import APIResponse
from src.models.company import Company, CompanyMetrics


class ClaudeAPIError(Exception):
    """Exception for Claude API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ClaudeAPIClient:
    """
    Client for Instawork's internal Claude API
    
    This client handles communication with the Claude API through
    Instawork's internal finch.instawork.com endpoint.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://finch.instawork.com"):
        """
        Initialize Claude API client
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API (default: finch.instawork.com)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/direct-claude/run"
        self.logger = logging.getLogger(__name__)
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.RequestException, ClaudeAPIError)),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING)
    )
    def call_claude(self, input_text: str, timeout: int = 30) -> str:
        """
        Call Claude API with input text
        
        Args:
            input_text: Text input for Claude
            timeout: Request timeout in seconds
            
        Returns:
            Claude's response text
            
        Raises:
            ClaudeAPIError: If API call fails
        """
        try:
            data = {"input": input_text}
            
            self.logger.debug(f"Calling Claude API with input length: {len(input_text)}")
            start_time = time.time()
            
            response = self.session.post(
                self.endpoint,
                json=data,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                raise ClaudeAPIError(
                    f"API request failed with status {response.status_code}: {response.text}",
                    status_code=response.status_code
                )
            
            response_data = response.json()
            
            if "output" not in response_data:
                raise ClaudeAPIError("Invalid response format: missing 'output' field")
            
            output = response_data["output"]
            
            self.logger.info(
                f"Claude API call successful in {response_time:.2f}s, "
                f"output length: {len(output)}"
            )
            
            return output
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise ClaudeAPIError(f"Request failed: {e}") from e
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise ClaudeAPIError(f"Unexpected error: {e}") from e


class FillRatePredictionGenerator:
    """
    Generate fill rate predictions using Claude API
    
    This class creates prompts for Claude to analyze company metrics
    and generate realistic fill rate predictions with actionable insights.
    """
    
    def __init__(self, claude_client: ClaudeAPIClient):
        """
        Initialize prediction generator
        
        Args:
            claude_client: Claude API client instance
        """
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
    
    async def generate_prediction(
        self, 
        company: Company, 
        metrics: CompanyMetrics,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        Generate fill rate prediction for a company
        
        Args:
            company: Company information
            metrics: Company's fill rate metrics
            additional_context: Additional context for prediction
            
        Returns:
            APIResponse with predictions
        """
        start_time = time.time()
        
        # Build the prompt for Claude
        prompt = self._build_prediction_prompt(company, metrics, additional_context)
        
        try:
            # Call Claude API
            claude_response = self.claude_client.call_claude(prompt)
            
            # Parse Claude's response into structured predictions
            predictions = self._parse_claude_response(claude_response)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create API response
            api_response = APIResponse(
                company_id=company.id,
                predictions=predictions,
                metrics={
                    "fill_rate": metrics.fill_rate,
                    "total_shifts": metrics.total_shifts,
                    "filled_shifts": metrics.filled_shifts,
                    "cancellation_rate": metrics.cancellation_rate,
                    "avg_time_to_fill": metrics.avg_time_to_fill,
                    "worker_ratings": metrics.worker_ratings,
                    "regional_breakdown": metrics.regional_breakdown,
                    "shift_type_breakdown": metrics.shift_type_breakdown
                },
                confidence=self._calculate_confidence(metrics, claude_response),
                generated_at=datetime.utcnow(),
                model_version="claude-3.5-sonnet-via-finch-v1.0"
            )
            
            self.logger.info(
                f"Generated prediction for {company.id} in {processing_time:.2f}s, "
                f"{len(predictions)} insights generated"
            )
            
            return api_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate prediction for {company.id}: {e}")
            raise
    
    def _build_prediction_prompt(
        self, 
        company: Company, 
        metrics: CompanyMetrics,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a comprehensive prompt for Claude to analyze fill rates
        
        Args:
            company: Company information
            metrics: Company metrics
            additional_context: Additional context
            
        Returns:
            Formatted prompt for Claude
        """
        concerns = metrics._identify_concerns()
        performance_rating = metrics._calculate_performance_rating()
        
        prompt = f"""You are an expert analyst for Instawork, a platform connecting companies to gig workers. Analyze the following company's fill rate performance and provide actionable insights.

Company Information:
- Company: {company.name} (ID: {company.id})
- Location: {company.location}
- Status: {company.status}
- Industry: {company.metadata.get('industry', 'Unknown')}
- Company Size: {company.metadata.get('size', 'Unknown')}

Fill Rate Metrics:
- Current Fill Rate: {metrics.fill_rate}%
- Total Shifts Requested: {metrics.total_shifts}
- Successfully Filled: {metrics.filled_shifts}
- Average Time to Fill: {metrics.avg_time_to_fill or 'N/A'} hours
- Cancellation Rate: {metrics.cancellation_rate}%
- Worker Ratings: {metrics.worker_ratings or 'N/A'}/5.0
- Performance Rating: {performance_rating}

Regional Breakdown:
{self._format_breakdown(metrics.regional_breakdown)}

Shift Type Performance:
{self._format_breakdown(metrics.shift_type_breakdown)}

Identified Concerns: {', '.join(concerns) if concerns else 'None'}

Additional Context:
{json.dumps(additional_context, indent=2) if additional_context else 'None provided'}

Please provide 2-4 specific, actionable insights about why this company might have fill rate issues and what can be done to improve them. Focus on:

1. Root cause analysis based on the metrics
2. Specific recommendations for improvement
3. Market context and competitive factors
4. Operational improvements

Format your response as clear, concise bullet points or short paragraphs. Each insight should be specific to this company's situation and actionable."""

        return prompt
    
    def _format_breakdown(self, breakdown: Dict[str, float]) -> str:
        """Format breakdown data for prompt"""
        if not breakdown:
            return "No breakdown data available"
        
        formatted = []
        for key, value in breakdown.items():
            formatted.append(f"  - {key.replace('_', ' ').title()}: {value}%")
        
        return "\n".join(formatted)
    
    def _parse_claude_response(self, claude_response: str) -> List[str]:
        """
        Parse Claude's response into structured predictions
        
        Args:
            claude_response: Raw response from Claude
            
        Returns:
            List of prediction strings
        """
        # Split response into individual insights
        # Handle various bullet point formats and paragraph breaks
        lines = claude_response.strip().split('\n')
        predictions = []
        current_prediction = ""
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                if current_prediction:
                    predictions.append(current_prediction.strip())
                    current_prediction = ""
                continue
            
            # Check if this is a new bullet point or numbered item
            if (line.startswith(('•', '-', '*')) or 
                (len(line) > 2 and line[0].isdigit() and line[1] in '.)')):
                
                # Save previous prediction
                if current_prediction:
                    predictions.append(current_prediction.strip())
                
                # Start new prediction (remove bullet/number)
                if line.startswith(('•', '-', '*')):
                    current_prediction = line[1:].strip()
                else:
                    # Remove number prefix
                    current_prediction = line[2:].strip()
            else:
                # Continue current prediction
                if current_prediction:
                    current_prediction += " " + line
                else:
                    current_prediction = line
        
        # Add final prediction
        if current_prediction:
            predictions.append(current_prediction.strip())
        
        # If no structured format found, split by sentences
        if not predictions and claude_response:
            sentences = claude_response.split('. ')
            predictions = [s.strip() + '.' for s in sentences if len(s.strip()) > 20]
        
        # Ensure we have at least one prediction
        if not predictions:
            predictions = [claude_response[:500] + "..." if len(claude_response) > 500 else claude_response]
        
        # Limit to reasonable number of predictions
        return predictions[:5]
    
    def _calculate_confidence(self, metrics: CompanyMetrics, claude_response: str) -> float:
        """
        Calculate confidence score based on data quality and response
        
        Args:
            metrics: Company metrics
            claude_response: Claude's response
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on data completeness
        if metrics.total_shifts > 50:
            confidence += 0.1
        if metrics.avg_time_to_fill is not None:
            confidence += 0.1
        if metrics.worker_ratings is not None:
            confidence += 0.1
        if metrics.regional_breakdown:
            confidence += 0.1
        if metrics.shift_type_breakdown:
            confidence += 0.1
        
        # Boost confidence based on response quality
        if len(claude_response) > 200:
            confidence += 0.1
        if len(claude_response.split()) > 50:
            confidence += 0.1
        
        # Reduce confidence for very low fill rates (less reliable data)
        if metrics.fill_rate < 30:
            confidence -= 0.1
        
        return max(0.3, min(0.95, confidence))


class MockFillRateAPI:
    """
    Mock API that simulates the fill rate prediction service
    using Claude for realistic predictions
    """
    
    def __init__(self, claude_api_key: str):
        """
        Initialize mock API
        
        Args:
            claude_api_key: API key for Claude
        """
        self.claude_client = ClaudeAPIClient(claude_api_key)
        self.prediction_generator = FillRatePredictionGenerator(self.claude_client)
        self.logger = logging.getLogger(__name__)
    
    async def get_prediction(
        self, 
        company_id: str,
        company_data: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        Get fill rate prediction for a company
        
        Args:
            company_id: Company identifier
            company_data: Optional company data, will generate mock data if not provided
            
        Returns:
            APIResponse with prediction
        """
        # Generate or use provided company data
        if company_data:
            company = Company(**company_data['company'])
            metrics = CompanyMetrics(**company_data['metrics'])
        else:
            company, metrics = self._generate_mock_company_data(company_id)
        
        # Generate prediction using Claude
        return await self.prediction_generator.generate_prediction(
            company, metrics, company_data.get('additional_context')
        )
    
    def _generate_mock_company_data(self, company_id: str) -> tuple[Company, CompanyMetrics]:
        """Generate realistic mock company data for testing"""
        import random
        
        company = Company(
            id=company_id,
            name=f"Test Company {company_id[-3:]}",
            location="San Francisco, CA",
            metadata={
                "industry": random.choice(["hospitality", "retail", "warehouse", "events"]),
                "size": random.choice(["small", "medium", "large"])
            }
        )
        
        # Generate realistic metrics with some correlation
        total_shifts = random.randint(50, 500)
        base_fill_rate = random.uniform(40, 90)
        filled_shifts = int(total_shifts * (base_fill_rate / 100))
        
        metrics = CompanyMetrics(
            company_id=company_id,
            fill_rate=base_fill_rate,
            total_shifts=total_shifts,
            filled_shifts=filled_shifts,
            avg_time_to_fill=random.uniform(1, 48),
            cancellation_rate=random.uniform(5, 25),
            worker_ratings=random.uniform(3.0, 4.8),
            regional_breakdown={
                "north": base_fill_rate + random.uniform(-15, 15),
                "south": base_fill_rate + random.uniform(-15, 15),
                "east": base_fill_rate + random.uniform(-15, 15),
                "west": base_fill_rate + random.uniform(-15, 15)
            },
            shift_type_breakdown={
                "morning": base_fill_rate + random.uniform(-10, 10),
                "afternoon": base_fill_rate + random.uniform(-10, 10),
                "evening": base_fill_rate + random.uniform(-10, 10),
                "overnight": base_fill_rate + random.uniform(-20, 5)
            }
        )
        
        return company, metrics