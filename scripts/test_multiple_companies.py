#!/usr/bin/env python3
"""
Test script to show API output for multiple companies and save outputs with CST timestamps

Dependencies: data/raw/company_ids_and_other.csv, data/output/ directory structure

This script processes multiple companies through the API and saves
detailed results with timestamps for analysis.
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path
import pytz
from typing import List, Dict, Any

def get_cst_timestamp() -> datetime:
    """Get current time in CST timezone"""
    cst = pytz.timezone('America/Chicago')
    return datetime.now(cst)

def create_output_directory() -> Path:
    """Create date-wise output directory structure"""
    cst_now = get_cst_timestamp()
    date_str = cst_now.strftime("%Y-%m-%d")
    
    # Create directory structure: data/output/test_results/YYYY-MM-DD/
    output_dir = Path("data/output/test_results") / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir

class TestBatchCollector:
    """Collects all test results for a single batch file"""
    
    def __init__(self):
        self.batch_start_time = get_cst_timestamp()
        self.test_results = []
        self.batch_info = {
            "batch_start_time_cst": self.batch_start_time.isoformat(),
            "date": self.batch_start_time.strftime("%Y-%m-%d"),
            "time": self.batch_start_time.strftime("%H:%M:%S CST"),
            "endpoint": "/api/v1/sc-fill-rate-company",
            "method": "POST"
        }
    
    def add_test_result(self, company_id: str, raw_response: dict, parsed_data: dict):
        """Add a single test result to the batch"""
        test_timestamp = get_cst_timestamp()
        
        # Format the raw response for better readability
        formatted_raw_response = raw_response.copy()
        
        # If the response body contains an 'output' field with JSON string, parse it
        if (isinstance(raw_response.get('response_body'), dict) and 
            'output' in raw_response['response_body']):
            
            try:
                # Parse the JSON string in the output field
                output_json = json.loads(raw_response['response_body']['output'])
                
                # Replace the escaped JSON string with parsed JSON for readability
                formatted_raw_response['response_body'] = {
                    **raw_response['response_body'],
                    'output_parsed': output_json,  # Add parsed version
                    'output_raw': raw_response['response_body']['output']  # Keep original
                }
                
            except json.JSONDecodeError:
                # If parsing fails, keep original
                formatted_raw_response = raw_response
        
        result = {
            "company_id": company_id,
            "test_timestamp_cst": test_timestamp.isoformat(),
            "raw_api_response": formatted_raw_response,
            "parsed_data": parsed_data,
            "success": "error" not in parsed_data
        }
        
        self.test_results.append(result)
    
    def save_batch_file(self, output_dir: Path, company_ids: List[str]) -> Path:
        """Save all results to a single batch file"""
        batch_end_time = get_cst_timestamp()
        
        # Create comprehensive batch data
        batch_data = {
            "batch_info": {
                **self.batch_info,
                "batch_end_time_cst": batch_end_time.isoformat(),
                "duration_seconds": (batch_end_time - self.batch_start_time).total_seconds(),
                "total_companies_tested": len(company_ids),
                "successful_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                "companies_tested": company_ids
            },
            "test_results": self.test_results
        }
        
        # Create filename with batch timestamp
        filename = f"api_test_batch_{self.batch_start_time.strftime('%Y-%m-%d_%H-%M-%S')}_CST.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        return filepath

def test_company(company_id: str, batch_collector: TestBatchCollector, base_url: str = "http://localhost:8000", bearer_token: str = None):
    """Test a single company and return parsed results, adding to batch collector"""
    url = f"{base_url}/api/v1/sc-fill-rate-company"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    request_body = {"input": company_id}
    
    try:
        response = requests.post(url, json=request_body, headers=headers, timeout=10)
        
        # Always collect the raw response
        raw_response = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response_body": response.json() if response.status_code == 200 else response.text,
            "request_body": request_body
        }
        
        if response.status_code == 200:
            response_data = response.json()
            if "output" in response_data:
                parsed_data = json.loads(response_data["output"])
                
                # Add to batch collector
                batch_collector.add_test_result(company_id, raw_response, parsed_data)
                
                return parsed_data
            else:
                error_data = {"error": "Missing 'output' field in response"}
                batch_collector.add_test_result(company_id, raw_response, error_data)
                return error_data
        else:
            error_data = {"error": f"HTTP {response.status_code}: {response.text}"}
            batch_collector.add_test_result(company_id, raw_response, error_data)
            return error_data
            
    except Exception as e:
        error_data = {"error": str(e)}
        # Add error info to batch
        error_response = {
            "status_code": "ERROR",
            "error": str(e),
            "request_body": request_body
        }
        batch_collector.add_test_result(company_id, error_response, error_data)
        return error_data

def print_company_analysis(data: dict, index: int):
    """Pretty print a single company's analysis"""
    print(f"\n{'='*80}")
    print(f"🏢 COMPANY #{index} - {data.get('company_name', 'Unknown')}")
    print(f"{'='*80}")
    print(f"📊 Company ID: {data.get('company_id', 'N/A')}")
    print(f"🎯 Tier: {data.get('tier', 'N/A')}")
    print(f"👤 Account Manager: {data.get('account_manager', 'N/A')}")
    print(f"📈 Status: {data.get('fill_rate_status', 'N/A')}")
    print(f"🕐 Generated: {data.get('generated_at', 'N/A')}")
    
    print(f"\n📋 RECOMMENDATIONS:")
    print("-" * 50)
    
    recommendations = data.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        rec_type = rec.get('type', 'unknown').upper()
        priority = rec.get('priority', 'unknown').upper()
        confidence = rec.get('confidence', 0)
        action = rec.get('action', 'No action specified')
        
        # Format type with emoji
        type_emoji = "📧" if rec_type == "EMAIL" else "⚡" if rec_type == "ACTION" else "❓"
        
        # Format priority with color coding
        priority_color = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
        
        print(f"{i}. {type_emoji} [{rec_type}] {priority_color} {priority}")
        print(f"   📝 {action}")
        if confidence:
            print(f"   🎯 Confidence: {confidence:.0%}")
        print()

def main():
    # Create output directory with CST date
    output_dir = create_output_directory()
    
    # Initialize batch collector
    batch_collector = TestBatchCollector()
    
    # Test company IDs from the CSV
    company_ids = [
        "1112",  # Sharon Heights Golf & Country Club (Tier 3)
        "2905",  # Starfire Golf Club (Tier 4)
        "971",   # Jane (no tier)
        "1047",  # Tapex (no tier)
        "4695",  # D Squared (Tier 3)
        "4813",  # Beachside Bakery (Tier 3)
        "2848",  # Thistle (Tier 2)
        "11611", # Haute Chefs Los Angeles (Tier 4)
        "11644", # Oakland Marriott City Center (Tier 3)
        "11735"  # Filson (Tier 3)
    ]
    
    bearer_token = os.getenv("API_BEARER_TOKEN", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    print("🚀 TESTING SC FILL RATE COMPANY API")
    print("=" * 80)
    print(f"📅 Test Date: {batch_collector.batch_info['date']} ({batch_collector.batch_info['time']})")
    print(f"📁 Output Directory: {output_dir}")
    print(f"🔑 Using Bearer Token: {bearer_token[:20]}...")
    print(f"🎯 Testing {len(company_ids)} companies")
    
    successful_tests = 0
    
    for i, company_id in enumerate(company_ids, 1):
        print(f"\n⏳ Testing Company ID: {company_id}...")
        
        result = test_company(company_id, batch_collector, bearer_token=bearer_token)
        
        if "error" in result:
            print(f"❌ Error for Company {company_id}: {result['error']}")
        else:
            print_company_analysis(result, i)
            successful_tests += 1
    
    # Save single batch file with all results
    batch_file = batch_collector.save_batch_file(output_dir, company_ids)
    
    print(f"\n{'='*80}")
    print(f"✅ SUMMARY: {successful_tests}/{len(company_ids)} companies tested successfully")
    print(f"📁 Output Directory: {output_dir}")
    print(f"📄 Single Batch File: {batch_file.name}")
    print(f"💾 Full Path: {batch_file}")
    print(f"⏱️  Batch Duration: {batch_collector.test_results[-1]['test_timestamp_cst'] if batch_collector.test_results else 'N/A'}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()