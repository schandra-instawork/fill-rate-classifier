"""
Module: api.client
Purpose: Handles all communication with the fill rate prediction API
Dependencies: requests, tenacity (for retries), pydantic, logging

This module provides a resilient API client that:
- Handles authentication and rate limiting
- Implements exponential backoff retry logic
- Validates responses against expected schema
- Provides detailed error messages for debugging
- Supports batch processing with concurrency control

Classes:
    APIError: Custom exception for API-related errors
    RateLimitError: Exception for rate limit violations
    FillRateAPIClient: Main API client class
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)
from pydantic import BaseModel, Field, validator

from src.models.schemas import APIResponse, APIResponseSchema
from src.models.company import Company


class APIError(Exception):
    """Base exception for API-related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(APIError):
    """Exception for rate limit violations"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Exception for authentication failures"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class ValidationError(APIError):
    """Exception for request validation failures"""
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None):
        super().__init__(message, status_code=400)
        self.validation_errors = validation_errors or []


class APIClientConfig(BaseModel):
    """Configuration for the API client"""
    base_url: str = Field(..., description="Base URL for the API")
    api_key: str = Field(..., description="API key for authentication")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="Base retry delay in seconds")
    rate_limit_calls: int = Field(default=60, ge=1, description="API calls per minute")
    rate_limit_burst: int = Field(default=10, ge=1, description="Burst size for rate limiting")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    
    @validator("base_url")
    def validate_base_url(cls, v):
        """Ensure base URL ends with slash"""
        return v.rstrip('/') + '/'


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, calls_per_minute: int, burst_size: int):
        """
        Initialize rate limiter
        
        Args:
            calls_per_minute: Maximum calls per minute
            burst_size: Maximum burst size
        """
        self.calls_per_minute = calls_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token, blocking if necessary"""
        async with self._lock:
            now = time.time()
            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            tokens_to_add = elapsed * (self.calls_per_minute / 60.0)
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens < 1:
                # Wait for next token
                wait_time = (1 - self.tokens) / (self.calls_per_minute / 60.0)
                await asyncio.sleep(wait_time)
                self.tokens = 1
            
            self.tokens -= 1


class FillRateAPIClient:
    """
    Client for the fill rate prediction API
    
    This client provides:
    - Automatic retry with exponential backoff
    - Rate limiting to respect API quotas
    - Request/response validation
    - Comprehensive error handling
    - Batch processing capabilities
    """
    
    def __init__(self, config: APIClientConfig):
        """
        Initialize API client
        
        Args:
            config: Client configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(config.rate_limit_calls, config.rate_limit_burst)
        
        # Setup HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=0,  # We handle retries with tenacity
            backoff_factor=0,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FillRateClassifier/1.0.0",
            "Accept": "application/json"
        })
        
        # Metrics tracking
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "retry_attempts": 0,
            "total_response_time": 0.0
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((requests.RequestException, APIError)),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING)
    )
    async def get_fill_rate_prediction(
        self, 
        company_id: str,
        include_metrics: bool = True,
        force_refresh: bool = False
    ) -> APIResponseSchema:
        """
        Get fill rate prediction for a single company
        
        Args:
            company_id: Company identifier
            include_metrics: Whether to include current metrics
            force_refresh: Bypass cache and get fresh prediction
            
        Returns:
            Validated API response
            
        Raises:
            APIError: For API-related errors
            ValidationError: For invalid responses
        """
        await self.rate_limiter.acquire()
        
        params = {
            "company_id": company_id,
            "include_metrics": include_metrics,
            "force_refresh": force_refresh
        }
        
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            response = self.session.get(
                urljoin(self.config.base_url, "predict"),
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            response_time = time.time() - start_time
            self.metrics["total_response_time"] += response_time
            
            self._handle_response_errors(response)
            
            # Parse and validate response
            response_data = response.json()
            api_response = APIResponse(**response_data)
            
            # Create validated schema
            schema = APIResponseSchema(raw_response=api_response)
            schema.enrich_with_context({
                "request_timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": response_time * 1000,
                "company_id": company_id
            })
            
            self.metrics["successful_requests"] += 1
            self.logger.info(
                f"Successfully retrieved prediction for company {company_id} "
                f"in {response_time:.2f}s"
            )
            
            return schema
            
        except requests.RequestException as e:
            self.metrics["failed_requests"] += 1
            self.logger.error(f"Request failed for company {company_id}: {e}")
            raise APIError(f"Request failed: {e}") from e
        
        except Exception as e:
            self.metrics["failed_requests"] += 1
            self.logger.error(f"Unexpected error for company {company_id}: {e}")
            raise APIError(f"Unexpected error: {e}") from e
    
    async def get_batch_predictions(
        self,
        company_ids: List[str],
        batch_size: int = 10,
        max_concurrent: int = 5
    ) -> Dict[str, Union[APIResponseSchema, Exception]]:
        """
        Get predictions for multiple companies in batches
        
        Args:
            company_ids: List of company identifiers
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dictionary mapping company IDs to responses or exceptions
        """
        if not company_ids:
            return {}
        
        self.logger.info(f"Starting batch prediction for {len(company_ids)} companies")
        
        # Split into batches
        batches = [
            company_ids[i:i + batch_size] 
            for i in range(0, len(company_ids), batch_size)
        ]
        
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_company(company_id: str) -> tuple[str, Union[APIResponseSchema, Exception]]:
            """Process a single company with semaphore control"""
            async with semaphore:
                try:
                    response = await self.get_fill_rate_prediction(company_id)
                    return company_id, response
                except Exception as e:
                    self.logger.warning(f"Failed to get prediction for {company_id}: {e}")
                    return company_id, e
        
        # Process all companies
        tasks = [process_company(company_id) for company_id in company_ids]
        
        for completed_task in asyncio.as_completed(tasks):
            company_id, result = await completed_task
            results[company_id] = result
        
        success_count = sum(1 for r in results.values() if not isinstance(r, Exception))
        self.logger.info(
            f"Batch prediction completed: {success_count}/{len(company_ids)} successful"
        )
        
        return results
    
    def _handle_response_errors(self, response: requests.Response) -> None:
        """Handle HTTP response errors"""
        if response.status_code == 200:
            return
        
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"message": response.text}
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key or authentication failed")
        
        elif response.status_code == 400:
            validation_errors = error_data.get("validation_errors", [])
            raise ValidationError(
                error_data.get("message", "Request validation failed"),
                validation_errors
            )
        
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after = int(retry_after) if retry_after else None
            self.metrics["rate_limited_requests"] += 1
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=retry_after
            )
        
        elif response.status_code >= 500:
            raise APIError(
                f"Server error: {error_data.get('message', 'Internal server error')}",
                status_code=response.status_code,
                response_data=error_data
            )
        
        else:
            raise APIError(
                f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}",
                status_code=response.status_code,
                response_data=error_data
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform API health check
        
        Returns:
            Health status information
        """
        try:
            start_time = time.time()
            response = self.session.get(
                urljoin(self.config.base_url, "health"),
                timeout=10,
                verify=self.config.verify_ssl
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "healthy",
                    "response_time_ms": response_time * 1000,
                    "api_version": health_data.get("version"),
                    "uptime": health_data.get("uptime"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": response_time * 1000,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics
        
        Returns:
            Dictionary of performance metrics
        """
        total_requests = self.metrics["total_requests"]
        avg_response_time = (
            self.metrics["total_response_time"] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "rate_limited_requests": self.metrics["rate_limited_requests"],
            "success_rate": (
                self.metrics["successful_requests"] / total_requests 
                if total_requests > 0 else 0
            ),
            "average_response_time_ms": avg_response_time * 1000,
            "error_rate": (
                self.metrics["failed_requests"] / total_requests 
                if total_requests > 0 else 0
            )
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics to zero"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "retry_attempts": 0,
            "total_response_time": 0.0
        }
    
    def close(self) -> None:
        """Close the HTTP session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()