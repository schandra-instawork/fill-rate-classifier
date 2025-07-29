#!/usr/bin/env python3
"""
Email Classification Batch Analysis Script

This script:
1. Extracts 250 Tier 1-3 companies from CSV data
2. Runs batch API tests with high concurrency
3. Filters for email-type recommendations 
4. Saves results for Claude analysis

Dependencies: data/raw/company_ids_and_other.csv
Output: data/output/email_classification_analysis/
"""

import requests
import json
import os
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import pytz
import pandas as pd
from typing import List, Dict, Any
import random


def get_cst_timestamp() -> datetime:
    """Get current time in CST timezone"""
    cst = pytz.timezone('America/Chicago')
    return datetime.now(cst)


def create_output_directory() -> Path:
    """Create date-wise output directory structure for email analysis"""
    cst_now = get_cst_timestamp()
    date_str = cst_now.strftime("%Y-%m-%d")
    
    # Create directory structure: data/output/email_classification_analysis/YYYY-MM-DD/
    output_dir = Path("data/output/email_classification_analysis") / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def get_tier_1_to_3_companies(target_count: int = 250) -> List[Dict[str, Any]]:
    """
    Extract companies from Tier 1, 2, and 3 (exclude Tier 4)
    
    Args:
        target_count: Number of companies to return
        
    Returns:
        List of company dictionaries with id, name, tier, account_manager
    """
    csv_path = "data/raw/company_ids_and_other.csv"
    
    try:
        # Read CSV, skip first line (report title)
        df = pd.read_csv(csv_path, skiprows=1)
        
        # Filter for Tier 1-3 only
        tier_filter = df['tier'].isin(['Tier 1', 'Tier 2', 'Tier 3'])
        filtered_companies = df[tier_filter]
        
        print(f"📊 Available companies by tier:")
        print(filtered_companies['tier'].value_counts())
        
        # Sample companies if we have more than target
        if len(filtered_companies) > target_count:
            sampled_companies = filtered_companies.sample(n=target_count, random_state=42)
        else:
            sampled_companies = filtered_companies
            
        # Convert to list of dictionaries
        companies = []
        for _, row in sampled_companies.iterrows():
            companies.append({
                'company_id': str(row['company_id']),
                'company_name': row['company_name'],
                'tier': row['tier'],
                'account_manager': row['rep_name']
            })
            
        print(f"✅ Selected {len(companies)} companies for analysis")
        return companies
        
    except Exception as e:
        print(f"❌ Error reading company data: {e}")
        return []


async def test_company_async(session: aiohttp.ClientSession, company_data: Dict[str, Any], 
                           bearer_token: str, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test a single company asynchronously
    
    Args:
        session: aiohttp session
        company_data: Company information dictionary
        bearer_token: API bearer token
        base_url: API base URL
        
    Returns:
        Dictionary with company data and API response
    """
    url = f"{base_url}/api/v1/sc-fill-rate-company"
    company_id = company_data['company_id']
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    request_body = {"input": company_id}
    
    try:
        async with session.post(url, json=request_body, headers=headers, timeout=30) as response:
            test_timestamp = get_cst_timestamp()
            
            if response.status == 200:
                response_data = await response.json()
                
                if "output" in response_data:
                    parsed_data = json.loads(response_data["output"])
                    
                    # Enhanced result with company metadata
                    result = {
                        "company_id": company_id,
                        "company_name": company_data['company_name'],
                        "tier": company_data['tier'],
                        "account_manager": company_data['account_manager'],
                        "test_timestamp_cst": test_timestamp.isoformat(),
                        "api_response": parsed_data,
                        "success": True,
                        "has_email_recommendations": any(
                            rec.get('type') == 'email' 
                            for rec in parsed_data.get('recommendations', [])
                        )
                    }
                    
                    return result
                    
            # Handle errors
            error_text = await response.text()
            return {
                "company_id": company_id,
                "company_name": company_data['company_name'],
                "tier": company_data['tier'],
                "test_timestamp_cst": test_timestamp.isoformat(),
                "success": False,
                "error": f"HTTP {response.status}: {error_text}"
            }
            
    except Exception as e:
        return {
            "company_id": company_id,
            "company_name": company_data['company_name'],
            "tier": company_data['tier'],
            "test_timestamp_cst": get_cst_timestamp().isoformat(),
            "success": False,
            "error": str(e)
        }


async def run_batch_analysis(companies: List[Dict[str, Any]], bearer_token: str, 
                           max_concurrent: int = 25) -> List[Dict[str, Any]]:
    """
    Run batch analysis with high concurrency
    
    Args:
        companies: List of company data dictionaries
        bearer_token: API bearer token
        max_concurrent: Maximum concurrent requests
        
    Returns:
        List of results from all companies
    """
    print(f"🚀 Starting batch analysis of {len(companies)} companies")
    print(f"⚡ Max concurrent requests: {max_concurrent}")
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_test(session, company_data):
        async with semaphore:
            return await test_company_async(session, company_data, bearer_token)
    
    # Run all requests concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [limited_test(session, company_data) for company_data in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and convert to regular results
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Exception for company {companies[i]['company_id']}: {result}")
            valid_results.append({
                "company_id": companies[i]['company_id'],
                "company_name": companies[i]['company_name'],
                "tier": companies[i]['tier'],
                "success": False,
                "error": str(result)
            })
        else:
            valid_results.append(result)
    
    return valid_results


def analyze_email_recommendations(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the batch results to extract email recommendations
    
    Args:
        results: List of batch test results
        
    Returns:
        Analysis summary dictionary
    """
    email_recommendations = []
    success_count = 0
    email_company_count = 0
    
    tier_breakdown = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0}
    
    for result in results:
        if result['success']:
            success_count += 1
            tier_breakdown[result['tier']] += 1
            
            if result.get('has_email_recommendations', False):
                email_company_count += 1
                
                # Extract email recommendations
                for rec in result['api_response'].get('recommendations', []):
                    if rec.get('type') == 'email':
                        email_recommendations.append({
                            "company_id": result['company_id'],
                            "company_name": result['company_name'],
                            "tier": result['tier'],
                            "account_manager": result['account_manager'],
                            "email_action": rec.get('action', ''),
                            "priority": rec.get('priority', ''),
                            "confidence": rec.get('confidence', 0)
                        })
    
    analysis = {
        "batch_summary": {
            "total_companies_tested": len(results),
            "successful_tests": success_count,
            "companies_with_email_recs": email_company_count,
            "email_recommendations_found": len(email_recommendations),
            "tier_breakdown": tier_breakdown
        },
        "email_recommendations": email_recommendations
    }
    
    return analysis


def save_batch_results(results: List[Dict[str, Any]], analysis: Dict[str, Any], 
                      output_dir: Path) -> Path:
    """
    Save comprehensive batch results
    
    Args:
        results: Raw batch results
        analysis: Email analysis results
        output_dir: Output directory path
        
    Returns:
        Path to saved file
    """
    cst_now = get_cst_timestamp()
    
    # Create comprehensive data structure
    batch_data = {
        "batch_info": {
            "timestamp_cst": cst_now.isoformat(),
            "date": cst_now.strftime("%Y-%m-%d"),
            "time": cst_now.strftime("%H:%M:%S CST"),
            "purpose": "Email classification analysis - 250 company batch",
            "tiers_included": ["Tier 1", "Tier 2", "Tier 3"]
        },
        "analysis_summary": analysis,
        "raw_results": results
    }
    
    # Save main results file
    filename = f"email_classification_batch_{cst_now.strftime('%Y-%m-%d_%H-%M-%S')}_CST.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(batch_data, f, indent=2)
    
    return filepath


def print_analysis_summary(analysis: Dict[str, Any]):
    """Print a formatted summary of the analysis"""
    summary = analysis['batch_summary']
    
    print(f"\n{'='*80}")
    print("📊 EMAIL CLASSIFICATION BATCH ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"📈 Total Companies Tested: {summary['total_companies_tested']}")
    print(f"✅ Successful Tests: {summary['successful_tests']}")
    print(f"📧 Companies with Email Recommendations: {summary['companies_with_email_recs']}")
    print(f"📝 Total Email Recommendations Found: {summary['email_recommendations_found']}")
    
    print(f"\n🎯 Tier Breakdown:")
    for tier, count in summary['tier_breakdown'].items():
        percentage = (count / summary['successful_tests'] * 100) if summary['successful_tests'] > 0 else 0
        print(f"   {tier}: {count} companies ({percentage:.1f}%)")
    
    print(f"\n📧 Sample Email Recommendations:")
    for i, rec in enumerate(analysis['email_recommendations'][:5]):
        print(f"   {i+1}. [{rec['tier']}] {rec['company_name']}: {rec['email_action'][:80]}...")
    
    if len(analysis['email_recommendations']) > 5:
        print(f"   ... and {len(analysis['email_recommendations']) - 5} more")
    
    print(f"{'='*80}")


async def main():
    """Main execution function"""
    bearer_token = os.getenv("API_BEARER_TOKEN", "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6")
    
    print("🎯 EMAIL CLASSIFICATION BATCH ANALYSIS")
    print("=" * 80)
    
    # Step 1: Get companies
    companies = get_tier_1_to_3_companies(target_count=250)
    if not companies:
        print("❌ No companies found. Exiting.")
        return
    
    # Step 2: Create output directory
    output_dir = create_output_directory()
    print(f"📁 Output Directory: {output_dir}")
    
    # Step 3: Run batch analysis
    start_time = get_cst_timestamp()
    results = await run_batch_analysis(companies, bearer_token, max_concurrent=25)
    end_time = get_cst_timestamp()
    
    duration = (end_time - start_time).total_seconds()
    print(f"⏱️  Batch completed in {duration:.2f} seconds")
    
    # Step 4: Analyze results
    analysis = analyze_email_recommendations(results)
    
    # Step 5: Save results
    saved_file = save_batch_results(results, analysis, output_dir)
    
    # Step 6: Print summary
    print_analysis_summary(analysis)
    print(f"\n💾 Results saved to: {saved_file}")


if __name__ == "__main__":
    asyncio.run(main())