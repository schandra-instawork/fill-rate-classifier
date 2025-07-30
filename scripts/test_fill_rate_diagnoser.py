#!/usr/bin/env python3
"""
Test script for Fill Rate Diagnoser API

This script directly tests the /fill-rate-diagnoser/run endpoint
to see what real analysis data it returns.

Usage:
    python scripts/test_fill_rate_diagnoser.py
"""

import requests
import json
import os
from src.api.fill_rate_analysis_client import FillRateAnalysisClient


def test_fill_rate_diagnoser_direct():
    """Test the fill-rate-diagnoser API directly"""
    
    api_key = os.getenv("CLAUDE_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    base_url = "https://finch.instawork.com"
    endpoint = f"{base_url}/fill-rate-diagnoser/run"
    
    # Test with Stanford Dining (real Tier 2 company)
    company_id = "7259"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Build input according to the client pattern
    input_text = f"Analyze company_id: {company_id}, analysis_type: past_shift_analysis"
    data = {"input": input_text}
    
    print(f"Testing Fill Rate Diagnoser API...")
    print(f"URL: {endpoint}")
    print(f"Company ID: {company_id}")
    print(f"Input: {input_text}")
    print("-" * 50)
    
    try:
        response = requests.post(endpoint, json=data, headers=headers, timeout=60)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ SUCCESS - Raw API Response:")
            print(json.dumps(response_data, indent=2))
            
            if "output" in response_data:
                print("\n" + "="*50)
                print("ANALYSIS OUTPUT:")
                print("="*50)
                print(response_data["output"])
                
                return response_data["output"]
            else:
                print("❌ No 'output' field in response")
                return None
                
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def test_with_client():
    """Test using the FillRateAnalysisClient"""
    
    api_key = os.getenv("CLAUDE_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    print("\n" + "="*50)
    print("TESTING WITH FillRateAnalysisClient")
    print("="*50)
    
    try:
        client = FillRateAnalysisClient(api_key)
        
        # Test with Stanford Dining
        response = client.analyze_company("7259", analysis_type="past")
        
        print("✅ SUCCESS - Parsed Response:")
        print(f"Company ID: {response.company_id}")
        print(f"Analysis Type: {response.analysis_type}")
        print(f"Fill Rate: {response.fill_rate}")
        print(f"Risk Level: {response.risk_level}")
        print(f"Recommendations: {len(response.recommendations)}")
        
        for i, rec in enumerate(response.recommendations, 1):
            print(f"  {i}. {rec}")
            
        print(f"Key Findings: {response.key_findings}")
        
        print("\n" + "-"*30)
        print("FULL ANALYSIS TEXT:")
        print("-"*30)
        print(response.analysis_text)
        
        return response
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    print("🔍 Testing Fill Rate Diagnoser API")
    
    # Test 1: Direct API call
    raw_output = test_fill_rate_diagnoser_direct()
    
    # Test 2: Using the client
    parsed_response = test_with_client()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    if raw_output and parsed_response:
        print("✅ Both direct API and client worked!")
        print(f"✅ Got {len(parsed_response.recommendations)} recommendations")
        print("✅ Data is ready for classification")
    elif raw_output:
        print("✅ Direct API worked, but client parsing failed")
        print("⚠️  Need to fix client parsing logic")
    elif parsed_response:
        print("⚠️  Client worked but direct API test failed (unexpected)")
    else:
        print("❌ Both tests failed - API may be down or auth issue")