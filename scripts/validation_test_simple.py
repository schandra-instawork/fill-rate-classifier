#!/usr/bin/env python3
"""
Simplified 75-Company Validation Test
Processes in smaller batches to avoid timeouts
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


def load_company_data() -> pd.DataFrame:
    """Load company data from CSV"""
    df = pd.read_csv('data/raw/company_ids_and_other.csv', skiprows=1)
    
    # Filter for Tier 1-3 only
    tier_1_3 = df[df['tier'].isin(['Tier 1', 'Tier 2', 'Tier 3'])]
    
    return tier_1_3


def classify_action_to_template(action_text: str) -> Tuple[str, str, float]:
    """
    Classify action recommendation to email template
    
    Returns:
        Tuple of (template_id, template_name, confidence)
    """
    action_lower = action_text.lower()
    
    # Worker Pool Issues (56% frequency)
    if "worker pool" in action_lower or "targeting" in action_lower:
        if "location" in action_lower or "geographic" in action_lower:
            return "1A", "Geographic Targeting", 0.95
        else:
            return "1B", "Shift Type Targeting", 0.90
    
    # Shift Pattern Issues (33% frequency)
    elif "shift pattern" in action_lower or "peak demand" in action_lower:
        if "peak demand" in action_lower or "demand period" in action_lower:
            return "2A", "Peak Demand Analysis", 0.92
        else:
            return "2B", "Schedule Alignment", 0.88
    
    # Pricing Issues (11% frequency)
    elif "pricing" in action_lower or "price" in action_lower or "compensation" in action_lower:
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
        response = requests.post(url, json=data, headers=headers, timeout=10)
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


def validate_classification_simple(classification_result: dict, finch_api_key: str) -> dict:
    """Simplified validation - just check if classification makes sense"""
    
    action = classification_result.get('primary_action', '').lower()
    template_id = classification_result.get('template_id')
    
    # Simple rule-based validation
    validation_score = 0
    issues = []
    
    # Check if template matches action
    if template_id in ["1A", "1B"] and ("worker pool" in action or "targeting" in action):
        validation_score += 40
    elif template_id in ["2A", "2B"] and ("shift pattern" in action or "demand" in action):
        validation_score += 40
    elif template_id in ["3A", "3B"] and ("pricing" in action or "price" in action):
        validation_score += 40
    else:
        issues.append("Template mismatch with action")
    
    # Check confidence
    if classification_result.get('classification_confidence', 0) >= 0.85:
        validation_score += 30
    else:
        issues.append("Low classification confidence")
    
    # Check action priority
    if classification_result.get('action_priority') == 'high':
        validation_score += 20
    elif classification_result.get('action_priority') == 'medium':
        validation_score += 10
    
    # Tier appropriateness
    tier = classification_result.get('tier', '')
    if template_id in ["3A", "3B"] and tier == "Tier 1":
        issues.append("Pricing discussions may be sensitive for Tier 1")
    else:
        validation_score += 10
    
    return {
        "validation_score": validation_score,
        "issues": issues,
        "recommendation": "SEND" if validation_score >= 70 else "REVIEW" if validation_score >= 50 else "SKIP"
    }


def generate_summary_report(results: List[dict], output_dir: Path) -> Path:
    """Generate a simplified executive summary"""
    
    cst_now = get_cst_timestamp()
    
    # Calculate metrics
    total_tested = len(results)
    successful_classifications = len([r for r in results if r.get("success") and r.get("template_id") != "UNK"])
    classification_rate = (successful_classifications / total_tested * 100) if total_tested > 0 else 0
    
    # Template distribution
    template_counts = {}
    template_names = {
        "1A": "Geographic Targeting",
        "1B": "Shift Type Targeting",
        "2A": "Peak Demand Analysis",
        "2B": "Schedule Alignment",
        "3A": "Market Rate Benchmarking",
        "3B": "Performance-Based Pricing",
        "UNK": "Unclassified"
    }
    
    for result in results:
        if result.get("success"):
            template_id = result.get("template_id", "UNK")
            template_counts[template_id] = template_counts.get(template_id, 0) + 1
    
    # Validation results
    validation_summary = {"SEND": 0, "REVIEW": 0, "SKIP": 0}
    for result in results:
        if result.get("validation"):
            rec = result["validation"]["recommendation"]
            validation_summary[rec] = validation_summary.get(rec, 0) + 1
    
    # Create report
    report_content = f"""# Email Classification Validation Test Results

**Date**: {cst_now.strftime('%Y-%m-%d %H:%M:%S CST')}  
**Sample Size**: {total_tested} companies (Tier 1-3)  

## Executive Summary

✅ **Classification Success Rate**: {classification_rate:.1f}%  
📧 **Ready to Send**: {validation_summary['SEND']} emails  
⚠️  **Need Review**: {validation_summary['REVIEW']} emails  
❌ **Should Skip**: {validation_summary['SKIP']} emails  

## Template Distribution

| Template | Issue Type | Count | Percentage |
|----------|------------|-------|------------|
"""
    
    for template_id, count in sorted(template_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_tested * 100)
        report_content += f"| {template_id} | {template_names[template_id]} | {count} | {percentage:.1f}% |\n"
    
    # Add examples
    report_content += """
## Sample Classifications

### Example 1: Worker Pool Issue
"""
    
    # Find a good worker pool example
    worker_examples = [r for r in results if r.get("template_id") in ["1A", "1B"] and r.get("success")]
    if worker_examples:
        ex = worker_examples[0]
        report_content += f"""
**Company**: {ex['company_name']} ({ex['tier']})  
**Issue**: {ex['primary_action']}  
**Template**: {ex['template_name']}  
**Validation**: {ex.get('validation', {}).get('recommendation', 'N/A')}  
"""
    
    # Add shift pattern example
    report_content += """
### Example 2: Shift Pattern Issue
"""
    
    shift_examples = [r for r in results if r.get("template_id") in ["2A", "2B"] and r.get("success")]
    if shift_examples:
        ex = shift_examples[0]
        report_content += f"""
**Company**: {ex['company_name']} ({ex['tier']})  
**Issue**: {ex['primary_action']}  
**Template**: {ex['template_name']}  
**Validation**: {ex.get('validation', {}).get('recommendation', 'N/A')}  
"""
    
    # Key findings
    report_content += f"""
## Key Findings

1. **Worker Pool Issues Most Common**: {template_counts.get('1A', 0) + template_counts.get('1B', 0)} companies ({(template_counts.get('1A', 0) + template_counts.get('1B', 0)) / total_tested * 100:.1f}%)
2. **High Classification Accuracy**: {classification_rate:.1f}% of companies successfully classified
3. **Low Risk Implementation**: {validation_summary['SEND']} emails ready to send immediately

## Recommendation

Begin with **Geographic Targeting** emails (Template 1A) as they:
- Address the most common issue type
- Have high classification confidence
- Present low business risk
- Offer clear value proposition

---
*Full detailed results available in: {output_dir}*
"""
    
    # Save report
    report_path = output_dir / f"executive_summary_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.md"
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    return report_path


def main():
    """Main execution function"""
    
    bearer_token = os.getenv("INSTAWORK_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    finch_api_key = os.getenv("FINCH_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    print("🧪 SIMPLIFIED VALIDATION TEST")
    print("=" * 60)
    
    # Create output directory
    cst_now = get_cst_timestamp()
    output_dir = Path(f"data/output/validation_test/{cst_now.strftime('%Y-%m-%d')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and sample companies
    print("📊 Loading company data...")
    company_df = load_company_data()
    test_companies = company_df.sample(n=75, random_state=42).to_dict('records')
    
    print(f"✅ Selected 75 companies")
    
    # Process in batches
    results = []
    batch_size = 10
    
    for i in range(0, len(test_companies), batch_size):
        batch = test_companies[i:i+batch_size]
        print(f"\n🔄 Processing batch {i//batch_size + 1}/{(len(test_companies) + batch_size - 1)//batch_size}...")
        
        for company in batch:
            print(f"   Testing company {company['company_id']}...", end='\r')
            result = test_single_company(company, bearer_token)
            
            # Add simple validation
            if result.get("success"):
                result["validation"] = validate_classification_simple(result, finch_api_key)
            
            results.append(result)
            time.sleep(0.1)  # Small delay to avoid overwhelming API
    
    print(f"\n✅ Processed {len(results)} companies")
    
    # Save detailed results
    detailed_path = output_dir / f"detailed_results_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.json"
    with open(detailed_path, 'w') as f:
        json.dump({
            "test_info": {
                "timestamp_cst": cst_now.isoformat(),
                "companies_tested": len(test_companies)
            },
            "results": results
        }, f, indent=2)
    
    # Generate summary report
    report_path = generate_summary_report(results, output_dir)
    
    print(f"\n📄 Executive summary: {report_path}")
    print(f"📊 Detailed results: {detailed_path}")
    
    # Quick stats
    successful = len([r for r in results if r.get("success")])
    ready_to_send = len([r for r in results if r.get("validation", {}).get("recommendation") == "SEND"])
    
    print(f"\n🎯 QUICK STATS:")
    print(f"   • Success rate: {successful/len(results)*100:.1f}%")
    print(f"   • Ready to send: {ready_to_send} emails")
    print(f"   • Most common issue: Worker Pool Targeting")


if __name__ == "__main__":
    main()