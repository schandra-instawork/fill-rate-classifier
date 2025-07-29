#!/usr/bin/env python3
"""
Test fill rate API with more context
"""

import requests
import json
import pandas as pd
import os

def test_with_company_context(company_id: str):
    """Test with full company context"""
    
    api_key = os.getenv("FINCH_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    # Load company info
    df = pd.read_csv('data/raw/company_ids_and_other.csv', skiprows=1)
    company_row = df[df['company_id'] == int(company_id)]
    
    if company_row.empty:
        print(f"❌ Company {company_id} not found in CSV")
        return None
        
    company_info = company_row.iloc[0].to_dict()
    company_name = company_info.get('company_name', 'Unknown')
    tier = company_info.get('tier', 'Unknown')
    
    print(f"\n🏢 Testing company: {company_name} (ID: {company_id}, {tier})")
    
    # Try different prompts
    prompts = [
        # 1. Simple company analysis
        f"Generate fill rate analysis and recommendations for company_id: {company_id}, company_name: {company_name}, tier: {tier}",
        
        # 2. Direct request for recommendations
        f"What are the top 3 fill rate improvement recommendations for {company_name} (company_id: {company_id})?",
        
        # 3. Specific issue analysis
        f"Analyze fill rate issues for {company_name} and provide specific action items for: 1) email outreach, 2) shift pattern optimization, 3) worker pool targeting"
    ]
    
    url = "https://finch.instawork.com/direct-claude/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n🔍 Attempt {i}/3: {prompt[:80]}...")
        
        data = {"input": prompt}
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                output = result.get("output", "No output")
                
                if output and len(output) > 10:
                    print("✅ Got response!")
                    print("-" * 50)
                    print(output[:300] + "..." if len(output) > 300 else output)
                    
                    # Look for specific patterns
                    if "recommendation" in output.lower() or "action" in output.lower():
                        print("\n🎯 Contains recommendations!")
                        return output
                else:
                    print("❌ Empty/short response")
            else:
                print(f"❌ Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    return None


def main():
    print("🧪 TESTING FILL RATE API WITH CONTEXT")
    print("=" * 80)
    
    # Test a few companies
    test_companies = ["1112", "2905", "971"]
    
    successful_responses = []
    
    for company_id in test_companies:
        result = test_with_company_context(company_id)
        if result:
            successful_responses.append({
                "company_id": company_id,
                "response": result
            })
    
    if successful_responses:
        print(f"\n\n✅ Got {len(successful_responses)} successful responses!")
        print("\n📊 SAMPLE RESPONSE:")
        print("-" * 80)
        print(successful_responses[0]['response'][:500])
    else:
        print("\n\n❌ No successful responses. The API might need different input format.")


if __name__ == "__main__":
    main()