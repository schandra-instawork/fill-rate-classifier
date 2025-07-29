#!/usr/bin/env python3
"""
Test script for SC Fill Rate Company API endpoint

This script tests the /api/v1/sc-fill-rate-company endpoint
to ensure it's working correctly.
"""

import requests
import json
import os
from typing import Dict, Any


def test_sc_fill_rate_company_api(
    base_url: str = "http://localhost:8000",
    bearer_token: str = None,
    company_id: str = "test_company_123"
) -> Dict[str, Any]:
    """
    Test the SC Fill Rate Company API endpoint
    
    Args:
        base_url: Base URL of the API server
        bearer_token: Bearer token for authentication
        company_id: Company ID to test with
        
    Returns:
        Dictionary containing test results
    """
    # Construct the full URL
    url = f"{base_url}/api/v1/sc-fill-rate-company"
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json"
    }
    
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    
    # Prepare request body matching the React hook structure
    request_body = {
        "input": company_id
    }
    
    print(f"Testing SC Fill Rate Company API...")
    print(f"URL: {url}")
    print(f"Company ID: {company_id}")
    print(f"Request Body: {json.dumps(request_body, indent=2)}")
    print("-" * 50)
    
    try:
        # Make the API call
        response = requests.post(
            url,
            json=request_body,
            headers=headers
        )
        
        # Check response status
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse response
            response_data = response.json()
            print("Response received successfully!")
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
            
            # Parse the output field (which contains JSON string)
            if "output" in response_data:
                output_data = json.loads(response_data["output"])
                print("\nParsed Output Data:")
                print(json.dumps(output_data, indent=2))
                
                # Verify expected fields
                expected_fields = ["company_id", "analysis", "recommendations", "timestamp"]
                for field in expected_fields:
                    if field in output_data:
                        print(f"✓ Found expected field: {field}")
                    else:
                        print(f"✗ Missing expected field: {field}")
            
            return {"success": True, "data": response_data}
            
        elif response.status_code == 401:
            print("Authentication failed! Please check your bearer token.")
            return {"success": False, "error": "Authentication failed", "status": 401}
            
        elif response.status_code == 503:
            print("Service unavailable! The fill rate analysis service may not be initialized.")
            return {"success": False, "error": "Service unavailable", "status": 503}
            
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return {"success": False, "error": response.text, "status": response.status_code}
            
    except requests.exceptions.ConnectionError:
        print("Connection error! Is the server running?")
        print(f"Try starting the server with: python -m src.api.server")
        return {"success": False, "error": "Connection refused"}
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Get bearer token from environment variable
    bearer_token = os.getenv("API_BEARER_TOKEN")
    
    if not bearer_token:
        print("WARNING: API_BEARER_TOKEN not set in environment variables")
        print("The API call will likely fail with 401 Unauthorized")
        print("Set it with: export API_BEARER_TOKEN='your-token-here'")
        print("-" * 50)
    
    # Test with a sample company ID
    result = test_sc_fill_rate_company_api(
        bearer_token=bearer_token,
        company_id="company_12345"
    )
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    if result["success"]:
        print("✅ API test passed!")
    else:
        print("❌ API test failed!")
        if "error" in result:
            print(f"Error: {result['error']}")