#!/usr/bin/env python3
"""
Test the real fill rate diagnoser API
"""

import requests
import json
import os

def test_fill_rate_diagnoser(company_id: str):
    """Test the real fill rate diagnoser API"""
    
    api_key = os.getenv("FINCH_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    # Call the fill rate diagnoser
    url = "https://finch.instawork.com/fill-rate-diagnoser/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Input format for fill rate diagnoser
    input_text = f"Analyze company_id: {company_id}, analysis_type: past_shift_analysis"
    
    data = {"input": input_text}
    
    print(f"🔍 Testing fill rate diagnoser for company {company_id}")
    print(f"   URL: {url}")
    print(f"   Input: {input_text}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            output = result.get("output", "No output")
            
            print(f"\n✅ SUCCESS! Got analysis:")
            print("-" * 80)
            print(output[:500] + "..." if len(output) > 500 else output)
            print("-" * 80)
            
            # Try to extract recommendations
            if "recommendation" in output.lower():
                print("\n🎯 Found recommendations in output!")
            
            return output
        else:
            print(f"\n❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return None


def main():
    # Test with a few company IDs
    test_companies = ["1112", "2905", "971"]
    
    print("🧪 TESTING REAL FILL RATE DIAGNOSER API")
    print("=" * 80)
    
    for company_id in test_companies:
        print(f"\n\nTest {test_companies.index(company_id) + 1}/{len(test_companies)}")
        result = test_fill_rate_diagnoser(company_id)
        
        if result:
            # Save the output for analysis
            filename = f"fill_rate_analysis_{company_id}.txt"
            with open(filename, 'w') as f:
                f.write(result)
            print(f"💾 Saved full output to: {filename}")


if __name__ == "__main__":
    main()