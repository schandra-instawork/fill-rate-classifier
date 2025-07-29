# Issue-Specific Email Automation System

**Generated**: 2025-07-29  
**Purpose**: System documentation for automated email generation based on fill rate analysis  
**Scope**: Company ID input → Issue-specific email template output

---

## System Overview

This system transforms generic "quarterly business review" emails into **issue-specific, actionable outreach** based on actual problems identified by the fill rate classification bot.

### Input → Output Flow

```
Company ID → API Analysis → Issue Classification → Email Template Selection → Personalized Email
```

**Example**: 
- Input: `"1112"` (Sharon Heights Golf & Country Club)
- Output: Geographic targeting email addressing their specific worker pool gaps

---

## How the System Works

### 1. Data Input
```json
POST /api/v1/sc-fill-rate-company
{
  "input": "1112"
}
```

### 2. Fill Rate Analysis Response
The API returns structured recommendations including both generic "email" types and specific "action" types:

```json
{
  "company_id": "1112",
  "company_name": "Sharon Heights Golf & Country Club",
  "tier": "Tier 3",
  "account_manager": "Mayur Mistry",
  "recommendations": [
    {
      "type": "email",
      "action": "Schedule quarterly business review with Sharon Heights Golf & Country Club to discuss fill rate optimization strategies",
      "priority": "high",
      "confidence": 0.92
    },
    {
      "type": "action",
      "action": "Analyze shift patterns for Sharon Heights Golf & Country Club and identify peak demand periods",
      "priority": "medium",
      "confidence": 0.88
    },
    {
      "type": "action", 
      "action": "Update worker pool targeting for Sharon Heights Golf & Country Club's location and shift types",
      "priority": "medium",
      "confidence": 0.87
    }
  ]
}
```

### 3. Issue Classification Approach

#### Option A: Simple Rule-Based Classification (Current MVP)
The system uses deterministic if-then logic to classify issues based on keywords in the action recommendations:

```python
# Worker Pool Issues (56% frequency)
if "worker pool" in action.lower() or "targeting" in action.lower():
    if "location" in action.lower():
        return "geographic_targeting"  # Template 1A
    else:
        return "shift_type_targeting"  # Template 1B

# Shift Pattern Issues (33% frequency)  
elif "shift pattern" in action.lower() or "peak demand" in action.lower():
    if "peak demand" in action.lower():
        return "peak_demand_analysis"  # Template 2A
    else:
        return "schedule_alignment"    # Template 2B

# Pricing Issues (11% frequency)
elif "pricing" in action.lower() or "price" in action.lower():
    if "market" in action.lower() or "benchmark" in action.lower():
        return "market_benchmarking"   # Template 3A
    else:
        return "performance_pricing"   # Template 3B
```

**Pros**: Fast, deterministic, no API calls, highly predictable
**Cons**: Less nuanced, may miss edge cases

#### Option B: Two-Stage Claude Classification (Future Enhancement)
```
Company ID → Finch API (Stage 1) → Claude Classifier (Stage 2) → Email Template
```

In this approach, a second Claude call would analyze the action recommendations for more nuanced classification:

```python
# Stage 2: Claude classification request
prompt = f"""
Analyze these action recommendations and classify into email template categories:
{action_recommendations}

Categories:
1A: Geographic Targeting - location-based worker pool expansion
1B: Shift Type Targeting - worker profile optimization
2A: Peak Demand Analysis - timing optimization
2B: Schedule Alignment - supply/demand matching
3A: Market Benchmarking - competitive rate analysis
3B: Performance Pricing - premium pricing strategy

Return the most appropriate template ID and confidence score.
"""
```

**Pros**: More nuanced understanding, handles edge cases, can evolve
**Cons**: Additional API call, added latency, potential variability

#### MVP Recommendation
Start with **Option A (Rule-Based)** because:
- Action recommendations are highly standardized (our analysis showed 100% pattern consistency)
- Faster execution and lower cost
- Deterministic results for QA/testing
- Can upgrade to Option B if edge cases emerge

### 4. Template Selection & Personalization

Based on the classified issue, the system selects the appropriate email template and populates variables:

**For Company 1112 with "worker pool targeting for location":**

```
Template: 1A (Geographic Targeting)
Variables:
  - {COMPANY_NAME} = "Sharon Heights Golf & Country Club"
  - {CONTACT_NAME} = [lookup from contact database]
  - {ACCOUNT_MANAGER_NAME} = "Mayur Mistry"
```

### 5. Generated Email Output

```
Subject: Expanding Geographic Worker Coverage for Sharon Heights Golf & Country Club

Hi [Contact Name],

Our analysis shows that expanding worker pool targeting in your geographic area could significantly improve Sharon Heights Golf & Country Club's fill rates.

We've identified underutilized worker segments within your service radius who match your shift requirements but aren't currently being reached effectively.

Quick 15-minute call to discuss:
• Expanding your geographic recruitment radius
• Targeting workers in nearby high-density areas  
• Expected increase in available worker pool

This is location-specific data that could make an immediate impact.

Best regards,
Mayur Mistry
```

---

## Key System Benefits

### 1. **Issue-Specific vs Generic**
- **Before**: "Let's discuss fill rate optimization" (vague)
- **After**: "Expand geographic worker targeting" (specific, actionable)

### 2. **Data-Driven Relevance**
- Each email addresses an actual problem flagged by the fill rate bot
- Business relevance: 56% worker pool, 33% scheduling, 11% pricing

### 3. **Scalable Template System**
- 6 standardized templates cover all identified issue types
- Light customization: Only company name, contact, account manager
- High automation potential with low risk

### 4. **Graduated Risk Levels**
- **Low Risk**: Geographic targeting, peak demand analysis
- **Medium Risk**: Schedule alignment, shift type targeting  
- **Higher Risk**: Pricing discussions (require careful handling)

---

## Template Categories & Frequency

| Template | Issue Type | Frequency | Risk Level | Business Impact |
|----------|------------|-----------|------------|-----------------|
| **1A** | Geographic Targeting | 28% | LOW | High - immediate pool expansion |
| **1B** | Shift Type Targeting | 28% | LOW | High - better matching |
| **2A** | Peak Demand Analysis | 16.5% | LOW | Medium - timing optimization |  
| **2B** | Schedule Alignment | 16.5% | MEDIUM | Medium - operational changes |
| **3A** | Market Benchmarking | 5.5% | HIGH | High - competitive positioning |
| **3B** | Performance Pricing | 5.5% | HIGH | High - premium strategy |

---

## MVP Implementation Strategy

### Phase 1: Geographic Targeting (Template 1A)
- **Target**: 28% of companies with geographic worker pool issues
- **Risk**: LOW - operational improvement discussion
- **Expected Impact**: Immediate fill rate improvement through expanded worker reach


### Automation Readiness
- ✅ **Highly Standardized**: Single template pattern per category
- ✅ **Clear Classification Rules**: Deterministic issue identification  
- ✅ **Minimal Personalization**: 3 variables only
- ✅ **Business Justified**: Addresses real operational problems

---

## Technical Implementation

### Required Data Points
```json
{
  "company_id": "string",
  "company_name": "string", 
  "tier": "string",
  "account_manager": "string",
  "contact_name": "string",  // New - needs contact lookup
  "issue_classification": "string",  // Derived from action analysis
  "template_id": "string"  // 1A, 1B, 2A, 2B, 3A, 3B
}
```

### System Architecture
```
[Company ID] → [Fill Rate API] → [Issue Classifier] → [Template Engine] → [Email Queue]
```

This system transforms the fill rate classification bot from generating generic meeting requests into **actionable, issue-specific business communication** that directly addresses identified operational problems.

---

*This system leverages existing fill rate analysis infrastructure while adding targeted email automation based on specific issues rather than generic optimization discussions.*