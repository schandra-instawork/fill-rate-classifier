#!/usr/bin/env python3
"""
Module: src.api.conversational_fill_rate_client
Purpose: Conversational client for Finch fill-rate-diagnoser API
Dependencies: requests, json, logging, typing

This module implements the correct conversational pattern for the Finch API
as discovered in SAMPLE_FINCH_CHAIAN. The API requires a 2-step conversation:
1. Send "hey" to initiate
2. Send company_id to get analysis
"""

import requests
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class AutomationTuple:
    """Represents an automation tuple from the API response"""
    action_type: str  # "email" or "action"
    message: str
    category: str
    priority: int
    confidence: float = 0.9

class ConversationalFillRateError(Exception):
    """Exception raised for conversational API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class ConversationalFillRateClient:
    """
    Client for Finch APIs with correct separation of concerns
    
    - fill-rate-diagnoser: Gets raw analysis data (conversational pattern)
    - direct-claude: Classifies analysis into email vs action (direct input)
    
    Based on analysis of SAMPLE_FINCH_CHAIAN, the diagnoser API requires a specific
    conversational flow, while Claude API uses direct prompts.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://finch.instawork.com"):
        """
        Initialize conversational client
        
        Args:
            api_key: API key for authentication (same as Claude API key)
            base_url: Base URL for the API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.diagnoser_endpoint = f"{self.base_url}/fill-rate-diagnoser/run"
        self.claude_endpoint = f"{self.base_url}/direct-claude/run"
        self.logger = logging.getLogger(__name__)
        
        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        
        self.logger.info(f"ConversationalFillRateClient initialized")
        self.logger.debug(f"Diagnoser endpoint: {self.diagnoser_endpoint}")
        self.logger.debug(f"Claude endpoint: {self.claude_endpoint}")
    
    def _make_diagnoser_call(self, input_text: str, step: str) -> Dict[str, Any]:
        """
        Make a single API call to the fill-rate-diagnoser endpoint (conversational)
        
        Args:
            input_text: Text to send to the API
            step: Description of the step for logging
            
        Returns:
            API response data
            
        Raises:
            ConversationalFillRateError: If API call fails
        """
        self.logger.debug(f"Making diagnoser call - {step}: {input_text}")
        
        try:
            response = self.session.post(
                self.diagnoser_endpoint,
                json={"input": input_text},
                timeout=60
            )
            
            self.logger.debug(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                output = data.get("output", "")
                
                if output and output.strip():
                    self.logger.debug(f"Got response: {len(output)} chars")
                    return data
                else:
                    raise ConversationalFillRateError(
                        f"Empty response in {step}",
                        response.status_code
                    )
            else:
                raise ConversationalFillRateError(
                    f"API call failed in {step}: {response.text}",
                    response.status_code
                )
                
        except requests.RequestException as e:
            raise ConversationalFillRateError(f"Network error in {step}: {e}")
    
    def _make_claude_call(self, prompt: str) -> str:
        """
        Make a call to the direct-claude endpoint for classification
        
        Args:
            prompt: Classification prompt to send
            
        Returns:
            Claude's response text
            
        Raises:
            ConversationalFillRateError: If API call fails
        """
        self.logger.debug("Making claude classification call")
        
        try:
            response = self.session.post(
                self.claude_endpoint,
                json={"input": prompt},
                timeout=60
            )
            
            self.logger.debug(f"Claude response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                output = data.get("output", "")
                
                if output and output.strip():
                    self.logger.debug(f"Got claude response: {len(output)} chars")
                    return output
                else:
                    raise ConversationalFillRateError("Empty response from Claude API")
            else:
                raise ConversationalFillRateError(
                    f"Claude API call failed: {response.text}",
                    response.status_code
                )
                
        except requests.RequestException as e:
            raise ConversationalFillRateError(f"Network error calling Claude: {e}")
    
    def get_raw_analysis(self, company_id: str) -> str:
        """
        Get raw company analysis using the conversational pattern with fill-rate-diagnoser
        
        This implements the 2-step conversation flow:
        1. Send "hey" to initiate conversation
        2. Send company_id to get raw analysis
        
        Args:
            company_id: Company identifier
            
        Returns:
            Raw analysis text from the diagnoser API
            
        Raises:
            ConversationalFillRateError: If conversation fails at any step
        """
        self.logger.info(f"Getting raw analysis for company {company_id}")
        
        # Step 1: Initiate conversation with "hey"
        try:
            step1_response = self._make_diagnoser_call("hey", "Conversation Initiation")
            step1_output = step1_response.get("output", "")
            
            # Validate that system is asking for company_id
            if "company" not in step1_output.lower():
                self.logger.warning(f"Unexpected step 1 response: {step1_output[:100]}")
                # Continue anyway - the pattern might still work
            
            self.logger.debug("Step 1 successful: System ready for company_id")
            
        except ConversationalFillRateError as e:
            self.logger.error(f"Step 1 failed: {e}")
            raise
        
        # Step 2: Provide company ID
        try:
            step2_response = self._make_diagnoser_call(company_id, f"Raw Analysis ({company_id})")
            step2_output = step2_response.get("output", "")
            
            # Validate that we got substantial analysis
            if len(step2_output) < 50:
                raise ConversationalFillRateError(
                    f"Minimal analysis returned for company {company_id}: {step2_output}"
                )
            
            self.logger.info(f"Raw analysis successful: {len(step2_output)} chars returned")
            return step2_output
            
        except ConversationalFillRateError as e:
            self.logger.error(f"Step 2 failed for company {company_id}: {e}")
            raise

    def classify_analysis(self, raw_analysis: str, company_id: str = "") -> List[AutomationTuple]:
        """
        Classify raw analysis into email vs action recommendations using Claude
        
        Args:
            raw_analysis: Raw analysis text from fill-rate-diagnoser
            company_id: Optional company ID for context
            
        Returns:
            List of classified automation tuples
        """
        self.logger.info("Classifying analysis into email vs action recommendations")
        
        # Create classification prompt for Claude
        classification_prompt = f"""
Analyze the following fill rate analysis and extract actionable recommendations.
Classify each recommendation as either "email" (requires outreach/communication) or "action" (requires operational changes).

Analysis to classify:
{raw_analysis}

Return ONLY automation tuples in this exact format:
("email", "specific recommendation message", "category", priority_number)
("action", "specific recommendation message", "category", priority_number)

Where priority_number is 1-100 (1=highest priority).

Focus on actionable, specific recommendations that can be implemented by account managers.
"""
        
        try:
            claude_response = self._make_claude_call(classification_prompt)
            
            # Parse automation tuples from Claude's response
            automation_tuples = self.parse_automation_tuples(claude_response)
            
            self.logger.info(f"Classification successful: {len(automation_tuples)} tuples extracted")
            return automation_tuples
            
        except ConversationalFillRateError as e:
            self.logger.error(f"Classification failed: {e}")
            raise
    
    def parse_automation_tuples(self, analysis_text: str) -> List[AutomationTuple]:
        """
        Parse automation tuples from the analysis response
        
        Based on SAMPLE_FINCH_CHAIAN format:
        ("action", "message", "category", priority)
        ("email", "message", "category", priority)
        
        Args:
            analysis_text: Raw analysis text from API
            
        Returns:
            List of parsed automation tuples
        """
        self.logger.debug("Parsing automation tuples from analysis")
        
        tuples = []
        
        # Pattern to match automation tuples
        # ("action", "message", "category", priority)
        tuple_pattern = r'\("(action|email)",\s*"([^"]+)",\s*"([^"]+)",\s*(\d+)\)'
        
        matches = re.findall(tuple_pattern, analysis_text)
        
        for match in matches:
            action_type, message, category, priority_str = match
            
            try:
                priority = int(priority_str)
                tuple_obj = AutomationTuple(
                    action_type=action_type,
                    message=message,
                    category=category,
                    priority=priority
                )
                tuples.append(tuple_obj)
                
            except ValueError as e:
                self.logger.warning(f"Failed to parse priority '{priority_str}': {e}")
                continue
        
        # If no tuples found, try alternative parsing
        if not tuples:
            tuples = self._parse_alternative_format(analysis_text)
        
        self.logger.info(f"Parsed {len(tuples)} automation tuples")
        return tuples
    
    def _parse_alternative_format(self, analysis_text: str) -> List[AutomationTuple]:
        """
        Parse automation tuples from alternative formats in the response
        
        Sometimes the API might return different formats. This handles
        common variations found in responses.
        """
        tuples = []
        
        # Look for structured recommendations in text
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for lines starting with action types
            if line.lower().startswith(('action:', 'email:')):
                action_type = 'action' if line.lower().startswith('action:') else 'email'
                message = line[7:].strip()  # Remove "action:" or "email:"
                
                # Default values when format is different
                tuple_obj = AutomationTuple(
                    action_type=action_type,
                    message=message,
                    category="general",
                    priority=50
                )
                tuples.append(tuple_obj)
        
        return tuples
    
    def get_recommendations(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Get formatted recommendations for a company
        
        This is the main method that combines analysis and parsing
        to return recommendations in the format expected by our API.
        
        Args:
            company_id: Company identifier
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            # Get raw analysis
            raw_analysis = self.get_raw_analysis(company_id)
            
            # Classify analysis
            automation_tuples = self.classify_analysis(raw_analysis, company_id)
            
            # Convert to API format
            recommendations = []
            for tuple_obj in automation_tuples:
                recommendations.append({
                    "type": tuple_obj.action_type,
                    "message": tuple_obj.message,
                    "category": tuple_obj.category,
                    "priority": tuple_obj.priority,
                    "confidence": tuple_obj.confidence
                })
            
            self.logger.info(f"Generated {len(recommendations)} recommendations for company {company_id}")
            return recommendations
            
        except ConversationalFillRateError as e:
            self.logger.error(f"Failed to get recommendations for company {company_id}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test if the conversational API is working
        
        Returns:
            True if API responds correctly, False otherwise
        """
        try:
            step1_response = self._make_diagnoser_call("hey", "Connection Test")
            return True
        except ConversationalFillRateError:
            return False


# Example usage for testing
if __name__ == "__main__":
    import os
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with the API key
    api_key = os.getenv("CLAUDE_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    client = ConversationalFillRateClient(api_key)
    
    # Test connection
    if client.test_connection():
        print("✅ Connection test passed")
        
        # Test with company from sample
        try:
            recommendations = client.get_recommendations("13100")
            print(f"✅ Got {len(recommendations)} recommendations for company 13100")
            
            for i, rec in enumerate(recommendations):
                print(f"  {i+1}. {rec['type']}: {rec['message'][:100]}...")
                
        except Exception as e:
            print(f"❌ Failed to get recommendations: {e}")
    else:
        print("❌ Connection test failed") 