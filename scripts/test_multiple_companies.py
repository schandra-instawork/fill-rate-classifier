#!/usr/bin/env python3
"""
Test script to show API output for multiple companies and save outputs with CST timestamps
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

def save_raw_output(company_id: str, raw_response: dict, parsed_data: dict, output_dir: Path):
    """Save raw API response and parsed data to files"""
    cst_now = get_cst_timestamp()
    timestamp_str = cst_now.strftime("%H-%M-%S")
    
    # Save raw API response
    raw_filename = f"company_{company_id}_raw_{timestamp_str}.json"
    raw_filepath = output_dir / raw_filename
    
    with open(raw_filepath, 'w') as f:
        json.dump({
            "timestamp_cst": cst_now.isoformat(),
            "company_id": company_id,
            "raw_api_response": raw_response,
            "request_info": {
                "endpoint": "/api/v1/sc-fill-rate-company",
                "method": "POST",
                "input": company_id
            }
        }, f, indent=2)
    
    # Save parsed data
    parsed_filename = f"company_{company_id}_parsed_{timestamp_str}.json"
    parsed_filepath = output_dir / parsed_filename
    
    with open(parsed_filepath, 'w') as f:
        json.dump({
            "timestamp_cst": cst_now.isoformat(),
            "company_id": company_id,
            "parsed_data": parsed_data
        }, f, indent=2)
    
    return raw_filepath, parsed_filepath

def test_company(company_id: str, output_dir: Path, base_url: str = "http://localhost:8000", bearer_token: str = None):
    """Test a single company and return parsed results, saving raw outputs"""
    url = f"{base_url}/api/v1/sc-fill-rate-company"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    request_body = {"input": company_id}
    
    try:
        response = requests.post(url, json=request_body, headers=headers, timeout=10)
        
        # Always save the raw response
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
                
                # Save both raw and parsed data
                raw_file, parsed_file = save_raw_output(company_id, raw_response, parsed_data, output_dir)
                
                # Add file paths to the returned data
                parsed_data["_saved_files"] = {
                    "raw_output": str(raw_file),
                    "parsed_output": str(parsed_file)
                }
                
                return parsed_data
            else:
                error_data = {"error": "Missing 'output' field in response"}
                save_raw_output(company_id, raw_response, error_data, output_dir)
                return error_data
        else:
            error_data = {"error": f"HTTP {response.status_code}: {response.text}"}
            save_raw_output(company_id, raw_response, error_data, output_dir)
            return error_data
            
    except Exception as e:
        error_data = {"error": str(e)}
        # Save error info too
        error_response = {
            "status_code": "ERROR",
            "error": str(e),
            "request_body": request_body
        }
        save_raw_output(company_id, error_response, error_data, output_dir)
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
    print(f"🔑 Using Bearer Token: {bearer_token[:20]}...")
    print(f"🎯 Testing {len(company_ids)} companies")
    
    successful_tests = 0
    
    for i, company_id in enumerate(company_ids, 1):
        print(f"\n⏳ Testing Company ID: {company_id}...")
        
        result = test_company(company_id, bearer_token=bearer_token)
        
        if "error" in result:
            print(f"❌ Error for Company {company_id}: {result['error']}")
        else:
            print_company_analysis(result, i)
            successful_tests += 1
    
    print(f"\n{'='*80}")
    print(f"✅ SUMMARY: {successful_tests}/{len(company_ids)} companies tested successfully")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()