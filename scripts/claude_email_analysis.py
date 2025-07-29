#!/usr/bin/env python3
"""
Claude Email Pattern Analysis Script

This script analyzes the 250-company batch results using Claude API to:
1. Identify email patterns and categories
2. Assess risk levels for each pattern type
3. Recommend the best MVP email template
4. Generate stakeholder documentation

Dependencies: 
- Finch API key for Claude analysis
- Previous batch results from email_classification_batch.py
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import pytz
from typing import Dict, List, Any


def get_cst_timestamp() -> datetime:
    """Get current time in CST timezone"""
    cst = pytz.timezone('America/Chicago')
    return datetime.now(cst)


def load_batch_results(batch_file_path: str) -> Dict[str, Any]:
    """
    Load the batch analysis results
    
    Args:
        batch_file_path: Path to the batch results JSON file
        
    Returns:
        Dictionary containing batch results
    """
    with open(batch_file_path, 'r') as f:
        return json.load(f)


def call_claude_for_analysis(email_recommendations: List[Dict[str, Any]], 
                           finch_api_key: str) -> str:
    """
    Use Claude API to analyze email patterns
    
    Args:
        email_recommendations: List of email recommendation data
        finch_api_key: Finch API key for Claude
        
    Returns:
        Claude's analysis response
    """
    # Prepare email texts for analysis
    sample_emails = []
    for i, rec in enumerate(email_recommendations[:50]):  # Analyze first 50 for patterns
        sample_emails.append({
            "id": i + 1,
            "company_name": rec['company_name'],
            "tier": rec['tier'],
            "email_action": rec['email_action'],
            "priority": rec['priority'],
            "confidence": rec['confidence']
        })
    
    # Create comprehensive analysis prompt
    prompt = f"""
    You are an expert business analyst helping design an automated email system for Instawork (a gig worker platform). 
    
    I have collected 232 email recommendations from our AI system across 250 Tier 1-3 partner companies. I need you to analyze these patterns to design a low-risk MVP email automation system.
    
    Here are the first 50 email recommendations to analyze:
    
    {json.dumps(sample_emails, indent=2)}
    
    Please provide a comprehensive analysis with the following sections:
    
    ## 1. EMAIL PATTERN IDENTIFICATION
    - What are the distinct email categories/patterns you see?
    - How standardized is the language within each pattern?
    - What variables would need personalization?
    
    ## 2. RISK ASSESSMENT MATRIX
    For each pattern, assess:
    - Business Risk Level (LOW/MEDIUM/HIGH)
    - Standardization Score (1-10, where 10 = highly standardized)
    - Volume Estimate (how often this pattern appears)
    - Stakeholder Risk (what happens if we get it slightly wrong?)
    
    ## 3. MVP RECOMMENDATION  
    - Which ONE email pattern is safest for MVP automation?
    - Why is this the lowest risk option?
    - What personalization variables are needed?
    - What would the template look like?
    
    ## 4. IMPLEMENTATION ROADMAP
    - Recommended order for implementing additional email types
    - Key success metrics to track
    - Potential failure modes and mitigations
    
    ## 5. STAKEHOLDER SUMMARY
    - Executive summary for leadership approval
    - Key benefits and risk mitigations
    - Resource requirements
    
    Focus on practical, data-driven recommendations that prioritize safety and gradual rollout over aggressive automation.
    """
    
    # Call Claude API via Finch
    url = "https://finch.instawork.com/direct-claude/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {finch_api_key}"
    }
    
    data = {"input": prompt}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get("output", "No output received")
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error calling Claude: {str(e)}"


def create_analysis_report(claude_analysis: str, batch_data: Dict[str, Any], 
                         output_dir: Path) -> Path:
    """
    Create comprehensive analysis report
    
    Args:
        claude_analysis: Claude's analysis response
        batch_data: Original batch data
        output_dir: Output directory
        
    Returns:
        Path to saved report
    """
    cst_now = get_cst_timestamp()
    
    # Create comprehensive report
    report_data = {
        "report_info": {
            "timestamp_cst": cst_now.isoformat(),
            "date": cst_now.strftime("%Y-%m-%d"),
            "time": cst_now.strftime("%H:%M:%S CST"),
            "purpose": "Claude analysis of email patterns for MVP automation",
            "analyst": "Claude via Finch API"
        },
        "data_source": {
            "total_companies_analyzed": batch_data["analysis_summary"]["batch_summary"]["total_companies_tested"],
            "email_recommendations_count": batch_data["analysis_summary"]["batch_summary"]["email_recommendations_found"],
            "tier_distribution": batch_data["analysis_summary"]["batch_summary"]["tier_breakdown"]
        },
        "claude_analysis": claude_analysis,
        "raw_email_samples": batch_data["analysis_summary"]["email_recommendations"][:10]  # Include 10 samples
    }
    
    # Save JSON report
    json_filename = f"claude_email_analysis_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.json"
    json_filepath = output_dir / json_filename
    
    with open(json_filepath, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Create markdown report for stakeholders
    markdown_content = f"""# Email Automation Analysis Report

**Generated**: {cst_now.strftime('%Y-%m-%d %H:%M:%S CST')}
**Purpose**: Email pattern analysis for MVP automation system
**Data Source**: 250 Tier 1-3 companies, 232 email recommendations

## Executive Summary

{claude_analysis}

## Data Overview

- **Total Companies Analyzed**: {batch_data["analysis_summary"]["batch_summary"]["total_companies_tested"]}
- **Companies with Email Recommendations**: {batch_data["analysis_summary"]["batch_summary"]["companies_with_email_recs"]}
- **Total Email Recommendations**: {batch_data["analysis_summary"]["batch_summary"]["email_recommendations_found"]}

### Tier Distribution
"""
    
    for tier, count in batch_data["analysis_summary"]["batch_summary"]["tier_breakdown"].items():
        percentage = (count / batch_data["analysis_summary"]["batch_summary"]["successful_tests"] * 100)
        markdown_content += f"- **{tier}**: {count} companies ({percentage:.1f}%)\n"
    
    markdown_content += f"""
## Sample Email Recommendations

"""
    
    for i, rec in enumerate(batch_data["analysis_summary"]["email_recommendations"][:5]):
        markdown_content += f"""
### {i+1}. {rec['company_name']} ({rec['tier']})
- **Action**: {rec['email_action']}
- **Priority**: {rec['priority']}
- **Confidence**: {rec['confidence']}
- **Account Manager**: {rec['account_manager']}
"""
    
    markdown_content += f"""
---
*Report generated by Claude AI analysis system*
*JSON data available at: {json_filename}*
"""
    
    # Save Markdown report
    md_filename = f"email_analysis_report_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.md"
    md_filepath = output_dir / md_filename
    
    with open(md_filepath, 'w') as f:
        f.write(markdown_content)
    
    return json_filepath, md_filepath


def main():
    """Main execution function"""
    import os
    
    finch_api_key = os.getenv("FINCH_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    print("🧠 CLAUDE EMAIL PATTERN ANALYSIS")
    print("=" * 80)
    
    # Find the most recent batch results file
    analysis_dir = Path("data/output/email_classification_analysis")
    today = get_cst_timestamp().strftime("%Y-%m-%d")
    today_dir = analysis_dir / today
    
    if not today_dir.exists():
        print(f"❌ No analysis directory found: {today_dir}")
        return
    
    # Find the most recent batch file
    batch_files = list(today_dir.glob("email_classification_batch_*.json"))
    if not batch_files:
        print(f"❌ No batch files found in: {today_dir}")
        return
    
    latest_batch_file = max(batch_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Loading batch results: {latest_batch_file.name}")
    
    # Load batch data
    batch_data = load_batch_results(str(latest_batch_file))
    email_recommendations = batch_data["analysis_summary"]["email_recommendations"]
    
    print(f"📊 Analyzing {len(email_recommendations)} email recommendations...")
    
    # Call Claude for analysis
    print("🧠 Calling Claude API for pattern analysis...")
    claude_analysis = call_claude_for_analysis(email_recommendations, finch_api_key)
    
    if claude_analysis.startswith("Error"):
        print(f"❌ Claude analysis failed: {claude_analysis}")
        return
    
    print("✅ Claude analysis completed successfully!")
    
    # Create reports
    json_path, md_path = create_analysis_report(claude_analysis, batch_data, today_dir)
    
    print(f"\n📄 Reports generated:")
    print(f"   JSON: {json_path}")
    print(f"   Markdown: {md_path}")
    
    # Print key insights
    print(f"\n🎯 KEY INSIGHTS:")
    print(claude_analysis[:500] + "..." if len(claude_analysis) > 500 else claude_analysis[:200])
    
    print(f"\n{'='*80}")
    print("✅ Claude email pattern analysis complete!")
    print(f"📁 Full reports saved in: {today_dir}")


if __name__ == "__main__":
    main()