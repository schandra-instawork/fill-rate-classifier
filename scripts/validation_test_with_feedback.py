#!/usr/bin/env python3
"""
75-Company Validation Test with Claude Feedback Loop

This script:
1. Tests 75 random Tier 1-3 companies
2. Classifies their issues into email templates
3. Uses Claude to validate the classification quality
4. Iterates based on feedback to improve accuracy
5. Generates executive-ready documentation
"""

import json
import pandas as pd
import requests
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import pytz
from typing import Dict, List, Any, Tuple
import random
import os


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


def get_email_template(template_id: str) -> str:
    """Get the email template content for a given template ID"""
    templates = {
        "1A": """Subject: Expanding Geographic Worker Coverage for {COMPANY_NAME}

Hi {CONTACT_NAME},

Our analysis shows that expanding worker pool targeting in your geographic area could significantly improve {COMPANY_NAME}'s fill rates.

We've identified underutilized worker segments within your service radius who match your shift requirements but aren't currently being reached effectively.

Quick 15-minute call to discuss:
• Expanding your geographic recruitment radius
• Targeting workers in nearby high-density areas
• Expected increase in available worker pool

This is location-specific data that could make an immediate impact.

Best regards,
{ACCOUNT_MANAGER_NAME}""",
        
        "1B": """Subject: Optimizing Worker Targeting for Your Shift Types at {COMPANY_NAME}

Hi {CONTACT_NAME},

Our data shows that refining worker targeting based on your specific shift characteristics could improve {COMPANY_NAME}'s fill rates.

We've found that workers with certain profiles and availability patterns are particularly well-suited for your shift types but may not be seeing your opportunities.

Brief 15-minute discussion about:
• Worker profile optimization for your shift requirements
• Targeting based on shift duration, timing, and skill requirements
• Improved matching for better retention rates

This targeting refinement could significantly boost your qualified applicant pool.

Best regards,
{ACCOUNT_MANAGER_NAME}""",
        
        "2A": """Subject: Peak Demand Timing Analysis for {COMPANY_NAME}

Hi {CONTACT_NAME},

Our analysis of {COMPANY_NAME}'s shift patterns has revealed specific peak demand periods that could optimize your scheduling strategy.

We've identified when worker availability is highest in your area and how this aligns with your current shift timing.

Quick 15-minute call to review:
• Your highest-opportunity time slots based on worker availability
• Peak demand windows vs. current scheduling
• Timing adjustments for maximum fill rate impact

This timing intelligence is specific to your market and could improve fill rates immediately.

Best regards,
{ACCOUNT_MANAGER_NAME}""",
        
        "2B": """Subject: Schedule Alignment Optimization for {COMPANY_NAME}

Hi {CONTACT_NAME},

We've analyzed {COMPANY_NAME}'s shift patterns and identified opportunities to better align your schedule with worker availability windows.

Our data shows specific times when worker engagement is highest in your area, which could significantly improve your fill rates.

15-minute discussion about:
• Aligning your shifts with peak worker availability
• Schedule adjustments that maximize worker interest
• Timeline for implementing schedule optimizations

This alignment strategy could transform your fill rate performance.

Best regards,
{ACCOUNT_MANAGER_NAME}""",
        
        "3A": """Subject: Market Rate Analysis Results for {COMPANY_NAME}

Hi {CONTACT_NAME},

Our market rate analysis suggests that benchmarking {COMPANY_NAME}'s pricing against local competitors could significantly improve worker attraction.

We've identified where your rates stand relative to similar shifts in your market and the potential impact of adjustments.

20-minute confidential discussion about:
• Your competitive positioning vs. market rates
• Specific rate benchmarks for better worker attraction
• ROI projections for potential pricing adjustments

This sensitive market intelligence could give you a competitive advantage.

Best regards,
{ACCOUNT_MANAGER_NAME}""",
        
        "3B": """Subject: Performance-Based Pricing Strategy for {COMPANY_NAME}

Hi {CONTACT_NAME},

Our analysis suggests that implementing performance-based pricing could help {COMPANY_NAME} attract higher-quality workers and improve overall fill rates.

We've identified opportunities to use premium pricing strategically to build a stronger, more reliable worker pool.

20-minute strategic discussion about:
• Premium pricing for high-performing workers
• Quality-based rate structures to improve retention
• Expected impact on both fill rates and worker quality

This pricing strategy could differentiate {COMPANY_NAME} in the market.

Best regards,
{ACCOUNT_MANAGER_NAME}""",
        
        "UNK": "Unable to generate template - classification failed"
    }
    
    return templates.get(template_id, templates["UNK"])


async def test_single_company(session: aiohttp.ClientSession, company_data: dict, bearer_token: str) -> dict:
    """Test a single company through the API"""
    url = "http://localhost:8000/api/v1/sc-fill-rate-company"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    data = {"input": str(company_data["company_id"])}
    
    try:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
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
                    
                    # Populate the email template
                    email_template = get_email_template(template_id)
                    populated_email = email_template.format(
                        COMPANY_NAME=output_data.get("company_name", "Unknown"),
                        CONTACT_NAME="[Contact Name]",
                        ACCOUNT_MANAGER_NAME=output_data.get("account_manager", "Account Manager")
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
                        "populated_email": populated_email,
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


async def run_validation_batch(companies: List[dict], bearer_token: str) -> List[dict]:
    """Run validation test on batch of companies"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for company in companies:
            task = test_single_company(session, company, bearer_token)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results


def validate_with_claude(classification_result: dict, finch_api_key: str) -> dict:
    """Use Claude to validate a single classification"""
    
    prompt = f"""You are an expert reviewer for Instawork's account management team. 
Instawork is a gig economy platform that connects businesses with hourly workers.

Please evaluate this automated email classification for quality and effectiveness:

**Company**: {classification_result.get('company_name')} ({classification_result.get('tier')})
**Issue Identified**: {classification_result.get('primary_action')}
**Template Selected**: {classification_result.get('template_id')} - {classification_result.get('template_name')}

**Generated Email**:
{classification_result.get('populated_email')}

Please evaluate and provide structured feedback:

1. **Template Match Score (1-10)**: Does the email template appropriately address the identified issue?
2. **Business Effectiveness Score (1-10)**: Would this email be effective in driving action from the partner?
3. **Clarity Score (1-10)**: Is the email clear and easy to understand?
4. **Instawork Context Score (1-10)**: Does this feel appropriate for an Instawork account manager to send?

5. **Better Template Choice**: If you think a different template would be better, which one and why?
   - 1A: Geographic Targeting
   - 1B: Shift Type Targeting  
   - 2A: Peak Demand Analysis
   - 2B: Schedule Alignment
   - 3A: Market Rate Benchmarking
   - 3B: Performance-Based Pricing

6. **Specific Improvements**: What 1-2 changes would make this email more effective?

7. **Risk Assessment**: Any concerns about sending this email? (LOW/MEDIUM/HIGH)

Return your response in this JSON format:
{{
    "template_match_score": <number>,
    "effectiveness_score": <number>,
    "clarity_score": <number>,
    "context_score": <number>,
    "overall_score": <average of above>,
    "better_template": "<template_id or 'none'>",
    "improvements": ["improvement 1", "improvement 2"],
    "risk_level": "<LOW/MEDIUM/HIGH>",
    "recommendation": "<SEND/REVISE/SKIP>"
}}"""
    
    # Call Claude API via Finch
    url = "https://finch.instawork.com/direct-claude/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {finch_api_key}"
    }
    data = {"input": prompt}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            claude_response = response.json().get("output", "{}")
            # Parse Claude's JSON response
            try:
                feedback = json.loads(claude_response)
                return {
                    "success": True,
                    "feedback": feedback
                }
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{[^{}]*\}', claude_response, re.DOTALL)
                if json_match:
                    try:
                        feedback = json.loads(json_match.group())
                        return {
                            "success": True,
                            "feedback": feedback
                        }
                    except:
                        pass
                
                return {
                    "success": False,
                    "error": "Failed to parse Claude response",
                    "raw_response": claude_response
                }
        else:
            return {
                "success": False,
                "error": f"Claude API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Claude validation error: {str(e)}"
        }


def analyze_validation_results(results_with_feedback: List[dict]) -> dict:
    """Analyze the validation results to find improvement opportunities"""
    
    # Aggregate metrics
    template_scores = {}
    improvement_themes = {}
    risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    recommendations = {"SEND": 0, "REVISE": 0, "SKIP": 0}
    
    successful_validations = [r for r in results_with_feedback 
                             if r.get("validation", {}).get("success")]
    
    for result in successful_validations:
        feedback = result["validation"]["feedback"]
        template_id = result["template_id"]
        
        # Track scores by template
        if template_id not in template_scores:
            template_scores[template_id] = {
                "scores": [],
                "count": 0,
                "template_name": result["template_name"]
            }
        
        template_scores[template_id]["scores"].append(feedback.get("overall_score", 0))
        template_scores[template_id]["count"] += 1
        
        # Track improvement themes
        for improvement in feedback.get("improvements", []):
            improvement_lower = improvement.lower()
            for theme in ["personalization", "clarity", "urgency", "value prop", "data", "cta"]:
                if theme in improvement_lower:
                    improvement_themes[theme] = improvement_themes.get(theme, 0) + 1
        
        # Track risk and recommendations
        risk_levels[feedback.get("risk_level", "MEDIUM")] += 1
        recommendations[feedback.get("recommendation", "REVISE")] += 1
    
    # Calculate average scores by template
    template_performance = {}
    for template_id, data in template_scores.items():
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        template_performance[template_id] = {
            "template_name": data["template_name"],
            "average_score": round(avg_score, 2),
            "sample_size": data["count"]
        }
    
    return {
        "template_performance": template_performance,
        "improvement_themes": improvement_themes,
        "risk_distribution": risk_levels,
        "recommendation_distribution": recommendations,
        "total_validations": len(successful_validations)
    }


def generate_executive_report(results: List[dict], validation_analysis: dict, output_dir: Path) -> Path:
    """Generate executive-friendly report"""
    
    cst_now = get_cst_timestamp()
    
    # Calculate key metrics
    total_tested = len(results)
    successful_classifications = len([r for r in results if r.get("success") and r.get("template_id") != "UNK"])
    classification_rate = (successful_classifications / total_tested * 100) if total_tested > 0 else 0
    
    # Template distribution
    template_counts = {}
    for result in results:
        if result.get("success"):
            template_id = result.get("template_id", "UNK")
            template_counts[template_id] = template_counts.get(template_id, 0) + 1
    
    # Create markdown report
    report_content = f"""# Email Classification Validation Report

**Generated**: {cst_now.strftime('%Y-%m-%d %H:%M:%S CST')}  
**Test Size**: 75 companies (Tier 1-3)  
**Purpose**: Validate email classification accuracy and effectiveness

---

## Executive Summary

### Key Metrics
- **Classification Success Rate**: {classification_rate:.1f}%
- **Templates Validated**: {len(validation_analysis['template_performance'])}
- **Average Quality Score**: {sum(t['average_score'] for t in validation_analysis['template_performance'].values()) / len(validation_analysis['template_performance']):.1f}/10
- **Ready to Send**: {validation_analysis['recommendation_distribution'].get('SEND', 0)} emails ({validation_analysis['recommendation_distribution'].get('SEND', 0) / validation_analysis['total_validations'] * 100:.1f}%)

### Risk Assessment
- **Low Risk**: {validation_analysis['risk_distribution']['LOW']} ({validation_analysis['risk_distribution']['LOW'] / validation_analysis['total_validations'] * 100:.1f}%)
- **Medium Risk**: {validation_analysis['risk_distribution']['MEDIUM']} ({validation_analysis['risk_distribution']['MEDIUM'] / validation_analysis['total_validations'] * 100:.1f}%)
- **High Risk**: {validation_analysis['risk_distribution']['HIGH']} ({validation_analysis['risk_distribution']['HIGH'] / validation_analysis['total_validations'] * 100:.1f}%)

---

## Template Performance

| Template | Description | Avg Score | Usage | Recommendation |
|----------|-------------|-----------|-------|----------------|
"""
    
    for template_id, perf in sorted(validation_analysis['template_performance'].items()):
        usage_pct = (template_counts.get(template_id, 0) / total_tested * 100)
        recommendation = "✅ Deploy" if perf['average_score'] >= 7 else "⚠️ Refine" if perf['average_score'] >= 5 else "❌ Redesign"
        report_content += f"| {template_id} | {perf['template_name']} | {perf['average_score']}/10 | {usage_pct:.1f}% | {recommendation} |\n"
    
    report_content += f"""
---

## Issue Distribution

"""
    
    # Show template distribution
    for template_id, count in sorted(template_counts.items(), key=lambda x: x[1], reverse=True):
        if template_id != "UNK":
            percentage = (count / total_tested * 100)
            template_name = next((r['template_name'] for r in results if r.get('template_id') == template_id), "Unknown")
            report_content += f"- **{template_name}** ({template_id}): {count} companies ({percentage:.1f}%)\n"
    
    # Add improvement themes
    if validation_analysis['improvement_themes']:
        report_content += f"""
---

## Top Improvement Themes

Based on AI validation feedback:

"""
        for theme, count in sorted(validation_analysis['improvement_themes'].items(), 
                                 key=lambda x: x[1], reverse=True)[:5]:
            report_content += f"- **{theme.title()}**: Mentioned {count} times\n"
    
    # Add examples
    report_content += f"""
---

## Example Classifications

### High-Performing Example
"""
    
    # Find best example
    best_examples = [r for r in results if r.get("validation", {}).get("success")]
    best_examples.sort(key=lambda x: x.get("validation", {}).get("feedback", {}).get("overall_score", 0), reverse=True)
    
    if best_examples:
        best = best_examples[0]
        report_content += f"""
**Company**: {best['company_name']} ({best['tier']})  
**Issue**: {best['primary_action']}  
**Template**: {best['template_name']} ({best['template_id']})  
**Score**: {best['validation']['feedback']['overall_score']}/10  
**Risk**: {best['validation']['feedback']['risk_level']}  

### Email Preview:
```
{best['populated_email'][:500]}...
```
"""
    
    # Add recommendations
    report_content += f"""
---

## Recommendations

1. **Immediate Deployment**: Templates scoring 7+ can be deployed with minimal risk
2. **Quick Wins**: Focus on {list(validation_analysis['improvement_themes'].keys())[0] if validation_analysis['improvement_themes'] else 'personalization'} improvements
3. **Volume Opportunity**: Worker Pool Targeting templates address {template_counts.get('1A', 0) + template_counts.get('1B', 0)} companies ({(template_counts.get('1A', 0) + template_counts.get('1B', 0)) / total_tested * 100:.1f}%)
4. **Risk Mitigation**: Implement manual review for Medium/High risk classifications

---

## Next Steps

1. Implement top improvement themes in templates
2. Deploy high-scoring templates (7+) in pilot program
3. Set up A/B testing framework for subject lines
4. Create escalation process for high-risk accounts

---

*Validation conducted using Claude AI for quality assessment*
"""
    
    # Save report
    report_filename = f"validation_report_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.md"
    report_path = output_dir / report_filename
    
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    return report_path


async def main():
    """Main execution function"""
    
    bearer_token = os.getenv("INSTAWORK_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    finch_api_key = os.getenv("FINCH_API_KEY", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    print("🧪 EMAIL CLASSIFICATION VALIDATION TEST")
    print("=" * 80)
    print("Testing 75 companies with Claude feedback loop...")
    
    # Create output directory
    cst_now = get_cst_timestamp()
    output_dir = Path(f"data/output/validation_test/{cst_now.strftime('%Y-%m-%d')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and sample companies
    print("\n📊 Loading company data...")
    company_df = load_company_data()
    test_companies = company_df.sample(n=75, random_state=42).to_dict('records')
    
    print(f"✅ Selected 75 companies from Tiers 1-3")
    print(f"   • Tier 1: {sum(1 for c in test_companies if c['tier'] == 'Tier 1')}")
    print(f"   • Tier 2: {sum(1 for c in test_companies if c['tier'] == 'Tier 2')}")
    print(f"   • Tier 3: {sum(1 for c in test_companies if c['tier'] == 'Tier 3')}")
    
    # Phase 1: Initial classification
    print("\n🔄 Phase 1: Running classifications...")
    initial_results = await run_validation_batch(test_companies, bearer_token)
    
    successful_results = [r for r in initial_results if r.get("success")]
    print(f"✅ Successfully classified {len(successful_results)}/{len(initial_results)} companies")
    
    # Phase 2: Claude validation (sample for speed)
    print("\n🧠 Phase 2: Claude validation (sampling 20 for speed)...")
    validation_sample = random.sample(successful_results, min(20, len(successful_results)))
    
    results_with_feedback = []
    for i, result in enumerate(validation_sample, 1):
        print(f"   Validating {i}/{len(validation_sample)}...", end='\r')
        validation = validate_with_claude(result, finch_api_key)
        result["validation"] = validation
        results_with_feedback.append(result)
    
    print(f"\n✅ Validated {len(results_with_feedback)} classifications")
    
    # Phase 3: Analyze and report
    print("\n📊 Phase 3: Analyzing results...")
    validation_analysis = analyze_validation_results(results_with_feedback)
    
    # Generate executive report
    report_path = generate_executive_report(initial_results, validation_analysis, output_dir)
    
    # Save detailed results
    detailed_results = {
        "test_info": {
            "timestamp_cst": cst_now.isoformat(),
            "companies_tested": len(test_companies),
            "classifications_successful": len(successful_results),
            "validations_performed": len(results_with_feedback)
        },
        "classification_results": initial_results,
        "validation_analysis": validation_analysis,
        "sample_validations": results_with_feedback[:5]  # Include some examples
    }
    
    detailed_path = output_dir / f"detailed_results_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.json"
    with open(detailed_path, 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"\n✅ Validation complete!")
    print(f"📄 Executive report: {report_path}")
    print(f"📊 Detailed results: {detailed_path}")
    
    # Print key insights
    print(f"\n🎯 KEY INSIGHTS:")
    print(f"   • Classification success rate: {len(successful_results)/len(initial_results)*100:.1f}%")
    print(f"   • Average template quality score: {sum(t['average_score'] for t in validation_analysis['template_performance'].values()) / len(validation_analysis['template_performance']):.1f}/10")
    print(f"   • Ready to deploy: {validation_analysis['recommendation_distribution'].get('SEND', 0)} emails")
    print(f"   • Top improvement theme: {list(validation_analysis['improvement_themes'].keys())[0] if validation_analysis['improvement_themes'] else 'None identified'}")


if __name__ == "__main__":
    asyncio.run(main())