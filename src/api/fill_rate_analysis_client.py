"""
Module: api.fill_rate_analysis_client
Purpose: Client for the Fill Rate Analysis API that returns shift analysis recommendations
Dependencies: requests, tenacity, pydantic

This module provides a client for calling the Fill Rate Analysis API with company IDs
and retrieving detailed shift analysis recommendations.

Classes:
    FillRateAnalysisClient: Client for the Fill Rate Analysis API
    AnalysisResponse: Response model for analysis results
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

import requests
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)
from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    """Response from Fill Rate Analysis API"""
    company_id: str = Field(..., description="Company identifier")
    analysis_type: str = Field(..., description="Type of analysis (past/risk)")
    shift_group_id: Optional[str] = Field(None, description="Shift group analyzed")
    analysis_text: str = Field(..., description="Full analysis text")
    fill_rate: Optional[float] = Field(None, description="Current fill rate")
    risk_level: Optional[str] = Field(None, description="Risk level (CRITICAL/HIGH/MEDIUM/LOW)")
    recommendations: List[str] = Field(default_factory=list, description="Extracted recommendations")
    key_findings: Dict[str, Any] = Field(default_factory=dict, description="Key findings")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FillRateAnalysisError(Exception):
    """Exception for Fill Rate Analysis API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class FillRateAnalysisClient:
    """
    Client for the Fill Rate Analysis API
    
    This client handles communication with the Fill Rate Analysis API
    that processes company shift data and returns recommendations.
    Uses the same API key as Claude API.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://finch.instawork.com"):
        """
        Initialize Fill Rate Analysis client
        
        Args:
            api_key: API key for authentication (same as Claude API key)
            base_url: Base URL for the API (default: finch.instawork.com)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/fill-rate-diagnoser/run"
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
        retry=retry_if_exception_type((requests.RequestException, FillRateAnalysisError)),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING)
    )
    def analyze_company(
        self, 
        company_id: str,
        analysis_type: str = "past",
        shift_group_id: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> AnalysisResponse:
        """
        Analyze a single company's fill rate
        
        Args:
            company_id: Company identifier
            analysis_type: Type of analysis ("past" or "risk")
            shift_group_id: Optional specific shift group to analyze
            additional_params: Additional parameters for the analysis
            
        Returns:
            Analysis response with recommendations
            
        Raises:
            FillRateAnalysisError: If API call fails
        """
        try:
            # Build the input prompt for the API
            input_text = f"Analyze company_id: {company_id}"
            
            if shift_group_id:
                input_text += f", shift_group_id: {shift_group_id}"
            
            if analysis_type == "risk":
                input_text += ", analysis_type: risk_prediction"
            else:
                input_text += ", analysis_type: past_shift_analysis"
            
            if additional_params:
                for key, value in additional_params.items():
                    input_text += f", {key}: {value}"
            
            data = {"input": input_text}
            
            self.logger.debug(f"Analyzing company {company_id} with input: {input_text}")
            start_time = time.time()
            
            response = self.session.post(
                self.endpoint,
                json=data,
                timeout=60  # Longer timeout for analysis
            )
            
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                raise FillRateAnalysisError(
                    f"API request failed with status {response.status_code}: {response.text}",
                    status_code=response.status_code
                )
            
            response_data = response.json()
            
            # The API returns {"output": "analysis text"}
            if "output" not in response_data:
                raise FillRateAnalysisError("Invalid response format: missing 'output' field")
            
            # Parse the analysis text to extract key information
            analysis_response = self._parse_analysis_response({
                "company_id": company_id,
                "analysis_type": analysis_type,
                "shift_group_id": shift_group_id,
                "analysis": response_data["output"]
            })
            
            self.logger.info(
                f"Analysis for {company_id} completed in {response_time:.2f}s, "
                f"found {len(analysis_response.recommendations)} recommendations"
            )
            
            return analysis_response
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise FillRateAnalysisError(f"Request failed: {e}") from e
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise FillRateAnalysisError(f"Unexpected error: {e}") from e
    
    async def analyze_batch(
        self,
        company_ids: List[str],
        analysis_type: str = "past",
        max_concurrent: int = 10
    ) -> Dict[str, AnalysisResponse]:
        """
        Analyze multiple companies in batch
        
        Args:
            company_ids: List of company identifiers
            analysis_type: Type of analysis for all companies
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dictionary mapping company_id to analysis response
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        results = {}
        
        async def process_company(company_id: str) -> tuple[str, AnalysisResponse]:
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.analyze_company,
                    company_id,
                    analysis_type
                )
                return company_id, response
            except Exception as e:
                self.logger.error(f"Failed to analyze {company_id}: {e}")
                return company_id, None
        
        # Process in batches
        for i in range(0, len(company_ids), max_concurrent):
            batch = company_ids[i:i + max_concurrent]
            tasks = [process_company(cid) for cid in batch]
            
            batch_results = await asyncio.gather(*tasks)
            
            for company_id, response in batch_results:
                if response:
                    results[company_id] = response
            
            # Brief delay between batches
            if i + max_concurrent < len(company_ids):
                await asyncio.sleep(1)
        
        self.logger.info(
            f"Batch analysis complete: {len(results)}/{len(company_ids)} successful"
        )
        
        return results
    
    def _parse_analysis_response(self, response_data: Dict[str, Any]) -> AnalysisResponse:
        """
        Parse the raw API response into structured data
        
        Args:
            response_data: Raw response from API
            
        Returns:
            Structured AnalysisResponse
        """
        analysis_text = response_data.get("analysis", "")
        
        # Extract recommendations (looking for common patterns)
        recommendations = []
        key_findings = {}
        
        # Parse recommendations section
        if "Recommendations" in analysis_text:
            rec_section = analysis_text.split("Recommendations")[1]
            # Look for bullet points or numbered items
            lines = rec_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and (
                    line[0] in '•-*' or 
                    (len(line) > 2 and line[0].isdigit() and line[1] in '.)')
                ):
                    # Clean up the recommendation
                    if line[0] in '•-*':
                        rec = line[1:].strip()
                    else:
                        rec = line[2:].strip()
                    if rec:
                        recommendations.append(rec)
        
        # Extract fill rate
        fill_rate = None
        if "Fill Rate:" in analysis_text:
            try:
                fill_text = analysis_text.split("Fill Rate:")[1].split('\n')[0]
                fill_rate = float(fill_text.strip().rstrip('%'))
            except:
                pass
        
        # Extract risk level
        risk_level = None
        if "Risk Level:" in analysis_text:
            risk_text = analysis_text.split("Risk Level:")[1].split('\n')[0]
            risk_level = risk_text.strip().upper()
        
        # Extract key metrics
        if "Wage ratio:" in analysis_text:
            try:
                wage_text = analysis_text.split("Wage ratio:")[1].split('\n')[0]
                key_findings["wage_ratio"] = float(wage_text.strip())
            except:
                pass
        
        if "Lead time:" in analysis_text:
            try:
                lead_text = analysis_text.split("Lead time:")[1].split('\n')[0]
                hours = lead_text.split("hours")[0].strip()
                key_findings["lead_time_hours"] = float(hours)
            except:
                pass
        
        return AnalysisResponse(
            company_id=response_data.get("company_id", ""),
            analysis_type=response_data.get("analysis_type", "past"),
            shift_group_id=response_data.get("shift_group_id"),
            analysis_text=analysis_text,
            fill_rate=fill_rate,
            risk_level=risk_level,
            recommendations=recommendations,
            key_findings=key_findings
        )