#!/usr/bin/env python3
"""
Action Issue Analysis Script

This script extracts and categorizes the 'action' type recommendations 
to identify specific issue categories that can drive email template topics.

Instead of generic "let's discuss optimization" emails, we want issue-specific
emails based on the actual problems flagged by the fill rate bot.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import pytz
from collections import Counter, defaultdict
import re


def get_cst_timestamp() -> datetime:
    """Get current time in CST timezone"""
    cst = pytz.timezone('America/Chicago')
    return datetime.now(cst)


def load_batch_results(batch_file_path: str) -> dict:
    """Load the batch analysis results"""
    with open(batch_file_path, 'r') as f:
        return json.load(f)


def extract_action_recommendations(batch_data: dict) -> list:
    """
    Extract all 'action' type recommendations from batch results
    
    Args:
        batch_data: The loaded batch results
        
    Returns:
        List of action recommendations with company context
    """
    action_recommendations = []
    
    # Look through the detailed results section
    if "detailed_results" in batch_data:
        for company_result in batch_data["detailed_results"]:
            if company_result.get("success") and "parsed_data" in company_result:
                parsed_data = company_result["parsed_data"]
                company_info = {
                    "company_id": parsed_data.get("company_id"),
                    "company_name": parsed_data.get("company_name"),
                    "tier": parsed_data.get("tier"),
                    "account_manager": parsed_data.get("account_manager"),
                    "fill_rate_status": parsed_data.get("fill_rate_status")
                }
                
                # Extract action recommendations
                for rec in parsed_data.get("recommendations", []):
                    if rec.get("type") == "action":
                        action_rec = {
                            **company_info,
                            "action": rec.get("action"),
                            "priority": rec.get("priority"),
                            "confidence": rec.get("confidence", 0)
                        }
                        action_recommendations.append(action_rec)
    
    return action_recommendations


def categorize_actions(action_recommendations: list) -> dict:
    """
    Categorize actions by issue type using keyword analysis
    
    Args:
        action_recommendations: List of action recommendations
        
    Returns:
        Dictionary with categorized actions
    """
    categories = {
        "shift_patterns": {
            "keywords": ["shift pattern", "peak demand", "demand period", "scheduling", "shift time"],
            "actions": [],
            "description": "Issues related to shift timing and demand patterns"
        },
        "worker_pool_targeting": {
            "keywords": ["worker pool", "targeting", "location", "shift types", "demographic"],
            "actions": [],
            "description": "Issues with worker recruitment and targeting"
        },
        "pricing_structure": {
            "keywords": ["pricing", "price", "pay rate", "compensation", "wage", "salary"],
            "actions": [],
            "description": "Issues related to pricing and compensation"
        },
        "geographic_coverage": {
            "keywords": ["geographic", "location", "coverage", "area", "region", "distance"],
            "actions": [],
            "description": "Issues with geographic coverage and location-based problems"
        },
        "capacity_management": {
            "keywords": ["capacity", "volume", "staffing level", "headcount", "resource allocation"],
            "actions": [],
            "description": "Issues with staffing capacity and resource management"
        },
        "communication": {
            "keywords": ["communication", "outreach", "contact", "follow up", "relationship"],
            "actions": [],
            "description": "Issues with partner communication and relationship management"
        },
        "performance_tracking": {
            "keywords": ["track", "monitor", "analyze", "review", "metrics", "performance", "data"],
            "actions": [],
            "description": "Issues requiring performance analysis and tracking"
        },
        "operational_efficiency": {
            "keywords": ["efficiency", "process", "workflow", "operation", "optimization"],
            "actions": [],
            "description": "Issues with operational processes and efficiency"
        }
    }
    
    # Categorize each action
    for action_rec in action_recommendations:
        action_text = action_rec["action"].lower()
        categorized = False
        
        for category_name, category_info in categories.items():
            for keyword in category_info["keywords"]:
                if keyword in action_text:
                    category_info["actions"].append(action_rec)
                    categorized = True
                    break
            if categorized:
                break
        
        # If not categorized, add to a misc category
        if not categorized:
            if "miscellaneous" not in categories:
                categories["miscellaneous"] = {
                    "keywords": [],
                    "actions": [],
                    "description": "Uncategorized actions requiring review"
                }
            categories["miscellaneous"]["actions"].append(action_rec)
    
    return categories


def analyze_email_template_opportunities(categorized_actions: dict) -> dict:
    """
    Analyze which categories are best suited for email templates
    
    Args:
        categorized_actions: Categorized action recommendations
        
    Returns:
        Analysis results with email template recommendations
    """
    template_analysis = {}
    
    for category_name, category_data in categorized_actions.items():
        actions = category_data["actions"]
        if not actions:
            continue
            
        # Calculate metrics
        total_actions = len(actions)
        priority_distribution = Counter([a["priority"] for a in actions])
        tier_distribution = Counter([a["tier"] for a in actions])
        confidence_avg = sum([a["confidence"] for a in actions]) / total_actions if total_actions > 0 else 0
        
        # Assess email template suitability
        # High priority actions are more suitable for immediate email outreach
        high_priority_pct = priority_distribution.get("high", 0) / total_actions * 100
        
        # Actions that require partner involvement are more suitable for emails
        partner_involvement_keywords = ["discuss", "review", "coordinate", "schedule", "communicate"]
        partner_involvement_count = sum(1 for action in actions 
                                      if any(keyword in action["action"].lower() 
                                            for keyword in partner_involvement_keywords))
        partner_involvement_pct = partner_involvement_count / total_actions * 100
        
        # Email template suitability score (0-100)
        email_suitability = (high_priority_pct * 0.4 + 
                           partner_involvement_pct * 0.4 + 
                           confidence_avg * 100 * 0.2)
        
        template_analysis[category_name] = {
            "category_name": category_name,
            "description": category_data["description"],
            "total_actions": total_actions,
            "priority_distribution": dict(priority_distribution),
            "tier_distribution": dict(tier_distribution),
            "avg_confidence": round(confidence_avg, 3),
            "high_priority_percentage": round(high_priority_pct, 1),
            "partner_involvement_percentage": round(partner_involvement_pct, 1),
            "email_suitability_score": round(email_suitability, 1),
            "sample_actions": [a["action"] for a in actions[:3]],  # Top 3 examples
            "sample_companies": [{"name": a["company_name"], "tier": a["tier"]} 
                               for a in actions[:3]]
        }
    
    return template_analysis


def generate_email_template_recommendations(template_analysis: dict) -> list:
    """
    Generate specific email template recommendations based on analysis
    
    Args:
        template_analysis: Analysis results from analyze_email_template_opportunities
        
    Returns:
        List of email template recommendations ranked by suitability
    """
    # Sort categories by email suitability score
    sorted_categories = sorted(template_analysis.items(), 
                             key=lambda x: x[1]["email_suitability_score"], 
                             reverse=True)
    
    recommendations = []
    
    for category_name, analysis in sorted_categories:
        if analysis["total_actions"] < 5:  # Skip categories with too few examples
            continue
            
        recommendation = {
            "category": category_name,
            "description": analysis["description"],
            "email_suitability_score": analysis["email_suitability_score"],
            "total_companies_affected": analysis["total_actions"],
            "business_justification": f"Addresses {analysis['total_actions']} specific issues across multiple partners",
            "email_template_concept": generate_template_concept(category_name, analysis),
            "risk_level": assess_risk_level(category_name, analysis),
            "implementation_priority": get_implementation_priority(analysis["email_suitability_score"])
        }
        recommendations.append(recommendation)
    
    return recommendations


def generate_template_concept(category_name: str, analysis: dict) -> str:
    """Generate email template concept for a category"""
    concepts = {
        "shift_patterns": "Email about optimizing shift schedules based on demand analysis",
        "worker_pool_targeting": "Email about improving worker recruitment and targeting strategies",
        "pricing_structure": "Email about reviewing compensation to improve worker attraction",
        "geographic_coverage": "Email about expanding or optimizing geographic service areas", 
        "capacity_management": "Email about scaling staffing capacity for peak periods",
        "communication": "Email about improving communication and partnership touchpoints",
        "performance_tracking": "Email about implementing better performance monitoring",
        "operational_efficiency": "Email about streamlining operational processes"
    }
    return concepts.get(category_name, f"Email addressing {category_name} issues")


def assess_risk_level(category_name: str, analysis: dict) -> str:
    """Assess risk level for email automation"""
    # High-confidence, high-priority issues are lower risk
    if analysis["avg_confidence"] > 0.85 and analysis["high_priority_percentage"] > 60:
        return "LOW"
    elif analysis["avg_confidence"] > 0.75 and analysis["high_priority_percentage"] > 40:
        return "MEDIUM"
    else:
        return "HIGH"


def get_implementation_priority(suitability_score: float) -> str:
    """Determine implementation priority based on suitability score"""
    if suitability_score >= 70:
        return "Phase 1 (MVP)"
    elif suitability_score >= 50:
        return "Phase 2 (Early)"
    else:
        return "Phase 3 (Later)"


def main():
    """Main execution function"""
    print("🔍 ACTION ISSUE ANALYSIS")
    print("=" * 80)
    
    # Find the latest batch results file
    analysis_dir = Path("data/output/email_classification_analysis")
    today = get_cst_timestamp().strftime("%Y-%m-%d")
    today_dir = analysis_dir / today
    
    # Find the most recent batch file
    batch_files = list(today_dir.glob("email_classification_batch_*.json"))
    if not batch_files:
        print(f"❌ No batch files found in: {today_dir}")
        return
    
    latest_batch_file = max(batch_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Loading batch results: {latest_batch_file.name}")
    
    # Load and process data
    batch_data = load_batch_results(str(latest_batch_file))
    action_recommendations = extract_action_recommendations(batch_data)
    
    if not action_recommendations:
        print("❌ No action recommendations found in batch data")
        return
    
    print(f"📊 Found {len(action_recommendations)} action recommendations")
    
    # Categorize actions
    categorized_actions = categorize_actions(action_recommendations)
    
    # Analyze email template opportunities
    template_analysis = analyze_email_template_opportunities(categorized_actions)
    
    # Generate recommendations
    email_recommendations = generate_email_template_recommendations(template_analysis)
    
    # Create output report
    cst_now = get_cst_timestamp()
    output_data = {
        "analysis_info": {
            "timestamp_cst": cst_now.isoformat(),
            "date": cst_now.strftime("%Y-%m-%d"),
            "time": cst_now.strftime("%H:%M:%S CST"),
            "purpose": "Action recommendation analysis for issue-specific email templates"
        },
        "summary": {
            "total_action_recommendations": len(action_recommendations),
            "categories_identified": len([c for c in categorized_actions.values() if c["actions"]]),
            "top_category": max(categorized_actions.items(), 
                              key=lambda x: len(x[1]["actions"]))[0] if categorized_actions else None
        },
        "categorized_actions": categorized_actions,
        "template_analysis": template_analysis,
        "email_template_recommendations": email_recommendations
    }
    
    # Save results
    filename = f"action_issue_analysis_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.json"
    output_path = today_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 Results saved: {output_path}")
    
    # Print key insights
    print(f"\n🎯 KEY INSIGHTS:")
    print(f"   • {len(action_recommendations)} specific issues identified")
    print(f"   • {len([c for c in categorized_actions.values() if c['actions']])} issue categories")
    
    if email_recommendations:
        top_rec = email_recommendations[0]
        print(f"   • Top email template opportunity: {top_rec['category']} (Score: {top_rec['email_suitability_score']})")
        print(f"   • {top_rec['total_companies_affected']} companies affected")
    
    print(f"\n📧 EMAIL TEMPLATE CATEGORIES RANKED BY SUITABILITY:")
    for i, rec in enumerate(email_recommendations[:5], 1):
        print(f"   {i}. {rec['category'].title().replace('_', ' ')} - Score: {rec['email_suitability_score']} ({rec['risk_level']} risk)")


if __name__ == "__main__":
    main()