#!/usr/bin/env python3
"""
Quick 10-company validation test with real API data
"""

import json
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
import pytz
from typing import Dict, List, Any, Tuple
import random
import os
import time


def get_cst_timestamp() -> datetime:
    """Get current time in CST timezone"""
    cst = pytz.timezone('America/Chicago')
    return datetime.now(cst)


def classify_action_to_template(action_text: str) -> Tuple[str, str, float]:
    """Classify action recommendation to email template"""
    action_lower = action_text.lower()
    
    # Worker Pool Issues
    if "worker pool" in action_lower or "targeting" in action_lower or "recruitment" in action_lower or "pipeline" in action_lower:
        if "location" in action_lower or "geographic" in action_lower or "radius" in action_lower:
            return "1A", "Geographic Targeting", 0.95
        else:
            return "1B", "Shift Type Targeting", 0.90
    
    # Shift Pattern Issues
    elif "shift pattern" in action_lower or "peak demand" in action_lower or "timing" in action_lower or "schedule" in action_lower:
        if "peak demand" in action_lower or "demand period" in action_lower or "timing" in action_lower:
            return "2A", "Peak Demand Analysis", 0.92
        else:
            return "2B", "Schedule Alignment", 0.88
    
    # Pricing Issues
    elif "pricing" in action_lower or "price" in action_lower or "compensation" in action_lower or "pay" in action_lower or "bonus" in action_lower or "premium" in action_lower:
        if "market" in action_lower or "benchmark" in action_lower or "competitive" in action_lower:
            return "3A", "Market Rate Benchmarking", 0.85
        else:
            return "3B", "Performance-Based Pricing", 0.82
    
    # Unclassified
    else:
        return "UNK", "Unclassified", 0.50


def test_single_company(company_data: dict, bearer_token: str) -> dict:
    """Test a single company through the API"""
    url = "http://localhost:8000/api/v1/sc-fill-rate-company"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    data = {"input": str(company_data["company_id"])}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            output_data = json.loads(result["output"])
            
            # Extract action recommendations
            action_recs = [rec for rec in output_data.get("recommendations", []) 
                          if rec.get("type") == "action"]
            
            # Classify the highest priority action
            if action_recs:
                # Sort by priority and confidence
                sorted_actions = sorted(action_recs, 
                                      key=lambda x: (x.get("priority") == "high", 
                                                   x.get("confidence", 0)), 
                                      reverse=True)
                primary_action = sorted_actions[0]
                
                template_id, template_name, confidence = classify_action_to_template(
                    primary_action["action"]
                )
                
                return {
                    "company_id": company_data["company_id"],
                    "company_name": output_data.get("company_name"),
                    "tier": output_data.get("tier"),
                    "account_manager": output_data.get("account_manager"),
                    "primary_action": primary_action["action"],
                    "action_priority": primary_action.get("priority"),
                    "action_confidence": primary_action.get("confidence"),
                    "template_id": template_id,
                    "template_name": template_name,
                    "classification_confidence": confidence,
                    "all_actions": action_recs,
                    "success": True
                }
            else:
                return {
                    "company_id": company_data["company_id"],
                    "error": "No action recommendations found",
                    "success": False
                }
        else:
            return {
                "company_id": company_data["company_id"],
                "error": f"HTTP {response.status}",
                "success": False
            }
    except Exception as e:
        return {
            "company_id": company_data["company_id"],
            "error": str(e),
            "success": False
        }


def main():
    """Main execution function"""
    
    bearer_token = "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6"
    
    print("🧪 QUICK VALIDATION TEST (10 companies)")
    print("=" * 60)
    
    # Load and sample companies
    df = pd.read_csv('data/raw/company_ids_and_other.csv', skiprows=1)
    tier_1_3 = df[df['tier'].isin(['Tier 1', 'Tier 2', 'Tier 3'])]
    test_companies = tier_1_3.sample(n=10, random_state=42).to_dict('records')
    
    print(f"✅ Selected 10 companies from Tiers 1-3")
    
    # Process companies
    results = []
    
    for i, company in enumerate(test_companies, 1):
        print(f"🔄 Testing {i}/10: Company {company['company_id']}...", end=' ')
        
        result = test_single_company(company, bearer_token)
        results.append(result)
        
        if result.get("success"):
            print(f"✅ {result['template_id']} - {result['template_name']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        time.sleep(1)  # Small delay between requests
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    
    print(f"\n📊 RESULTS:")
    print(f"   • Success rate: {len(successful)}/10 ({len(successful)*10}%)")
    
    # Template distribution
    template_counts = {}
    for result in successful:
        template_id = result.get("template_id", "UNK")
        template_counts[template_id] = template_counts.get(template_id, 0) + 1
    
    print(f"\n🎯 TEMPLATE DISTRIBUTION:")
    for template_id, count in sorted(template_counts.items(), key=lambda x: x[1], reverse=True):
        template_name = next((r['template_name'] for r in successful if r.get('template_id') == template_id), "Unknown")
        percentage = (count / len(successful) * 100) if successful else 0
        print(f"   • {template_id}: {template_name} - {count} companies ({percentage:.1f}%)")
    
    # Show examples
    print(f"\n📋 SAMPLE CLASSIFICATIONS:")
    for result in successful[:5]:
        print(f"\n{result['company_name']} ({result['tier']}):")
        print(f"   Action: {result['primary_action'][:100]}...")
        print(f"   Template: {result['template_id']} - {result['template_name']}")
    
    # Save results
    cst_now = get_cst_timestamp()
    output_dir = Path(f"data/output/validation_test/{cst_now.strftime('%Y-%m-%d')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / f"quick_test_{cst_now.strftime('%H-%M-%S')}_CST.json"
    with open(results_file, 'w') as f:
        json.dump({"results": results, "timestamp": cst_now.isoformat()}, f, indent=2)
    
    print(f"\n💾 Results saved: {results_file}")
    
    return successful


if __name__ == "__main__":
    main()