# Finch Conversational API Integration Strategy

## Problem Statement
Finch (Instawork's AI playground) uses a conversational interface rather than traditional REST API endpoints. To programmatically extract risk analysis data, we need to simulate the conversation flow and parse responses.

## API Structure Analysis

### Base URL
```
https://finch.instawork.com/playground/[SESSION_ID]
```

### Agent: SC Fill Rate - Company
**Purpose:** Analyzes workforce risk and provides actionable automation tuples  
**Input:** Company ID  
**Output:** Detailed risk analysis with automation recommendations

## Conversation Flow Pattern

### 1. Initial Greeting
```
USER: "hey"
AI: "Hello! Please provide a company_id so I can begin the detailed risk analysis for your portfolio."
```

### 2. Company ID Submission
```
USER: "[COMPANY_ID]" (e.g., "7259")
AI: "I will call the following tool(s): scFillRateCompany_fillDetailsByCompany for you."
```

### 3. Analysis Continuation
```
USER: "continue analysis"
AI: [Returns full detailed risk analysis report]
```

## Python Implementation Strategy

### Core Wrapper Class
```python
import requests
import re
import json
from typing import Dict, List, Tuple, Optional

class FinchAPIWrapper:
    def __init__(self, session_url: str):
        self.session_url = session_url
        self.session = requests.Session()
        self.conversation_history = []
    
    def send_message(self, message: str) -> str:
        """Send message to Finch conversational API"""
        # Implementation depends on Finch's actual API structure
        # May require WebSocket, POST requests, or other methods
        pass
    
    def get_company_risk_analysis(self, company_id: int) -> Dict:
        """Execute full conversation flow to get risk analysis"""
        
        # Step 1: Initial greeting
        response1 = self.send_message("hey")
        
        # Step 2: Submit company ID
        response2 = self.send_message(str(company_id))
        
        # Step 3: Request full analysis
        response3 = self.send_message("continue analysis")
        
        # Parse the final response into structured data
        return self.parse_risk_analysis(response3)
    
    def parse_risk_analysis(self, raw_response: str) -> Dict:
        """Parse conversational response into structured data"""
        return {
            "company_id": self.extract_company_id(raw_response),
            "worker_risk_assessment": self.extract_worker_risks(raw_response),
            "shift_groups": self.extract_shift_groups(raw_response),
            "patterns": self.extract_patterns(raw_response),
            "automation_tuples": self.extract_automation_tuples(raw_response)
        }
```

### Response Parsing Strategy

#### 1. Extract Automation Tuples
```python
def extract_automation_tuples(self, response: str) -> List[Tuple]:
    """Extract actionable automation tuples from response"""
    tuples = []
    
    # Pattern for immediate actions (0-4hrs)
    immediate_pattern = r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*(\d+)\)'
    
    # Find all tuple matches
    matches = re.findall(immediate_pattern, response)
    
    for match in matches:
        action_type, message, category, priority_hours = match
        tuples.append({
            "action_type": action_type,
            "message": message,
            "category": category,
            "priority_hours": int(priority_hours),
            "urgency": self.categorize_urgency(int(priority_hours))
        })
    
    return tuples

def categorize_urgency(self, hours: int) -> str:
    if hours <= 4:
        return "IMMEDIATE"
    elif hours <= 72:
        return "PATTERN-BASED"
    else:
        return "PREVENTIVE"
```

#### 2. Extract Risk Metrics
```python
def extract_worker_risks(self, response: str) -> Dict:
    """Extract worker risk assessment data"""
    # Parse reliability scores
    reliability_pattern = r'reliability.*?(\d+\.\d+)'
    reliability_scores = re.findall(reliability_pattern, response)
    
    # Parse worker levels
    level_pattern = r'worker_level.*?"([^"]+)"'
    worker_levels = re.findall(level_pattern, response)
    
    return {
        "reliability_scores": [float(score) for score in reliability_scores],
        "worker_levels": worker_levels,
        "high_risk_count": len([s for s in reliability_scores if float(s) < 70]),
        "missing_distance_data": "Distance data is missing" in response
    }
```

#### 3. Extract Shift Group Data
```python
def extract_shift_groups(self, response: str) -> List[Dict]:
    """Extract shift group analysis"""
    shift_groups = []
    
    # Pattern for shift group data
    shift_pattern = r'Shift Group:\s*(\d+)\s*\((\d+)\s*shifts,\s*(\d+)\s*filled\)'
    matches = re.findall(shift_pattern, response)
    
    for match in matches:
        group_id, total_shifts, filled_shifts = match
        shift_groups.append({
            "shift_group_id": int(group_id),
            "total_shifts": int(total_shifts),
            "filled_shifts": int(filled_shifts),
            "fill_rate": round((int(filled_shifts) / int(total_shifts)) * 100, 2)
        })
    
    return shift_groups
```

## Integration Usage

### Simple Function Call
```python
def get_company_analysis(company_id: int) -> Dict:
    """Main function to get structured analysis data"""
    
    # Initialize wrapper with session
    api = FinchAPIWrapper("https://finch.instawork.com/playground/new")
    
    # Execute conversation flow
    analysis = api.get_company_risk_analysis(company_id)
    
    return analysis

# Usage
company_data = get_company_analysis(7259)
automation_actions = company_data["automation_tuples"]
```

### Batch Processing
```python
def analyze_multiple_companies(company_ids: List[int]) -> Dict[int, Dict]:
    """Analyze multiple companies in sequence"""
    results = {}
    
    for company_id in company_ids:
        try:
            results[company_id] = get_company_analysis(company_id)
        except Exception as e:
            results[company_id] = {"error": str(e)}
    
    return results
```

## Key Implementation Considerations

### 1. Session Management
- Each conversation may require a new session
- Handle session timeouts and reconnection
- Manage conversation state properly

### 2. Response Timing
- Allow time for AI processing between messages
- Implement retry logic for failed requests
- Handle rate limiting gracefully

### 3. Error Handling
```python
class FinchAPIException(Exception):
    pass

def handle_api_errors(response: str) -> None:
    if "error" in response.lower():
        raise FinchAPIException(f"API Error: {response}")
    if "please provide" in response.lower():
        raise FinchAPIException("Invalid company_id or missing parameter")
```

### 4. Data Validation
```python
def validate_analysis_response(data: Dict) -> bool:
    """Ensure response contains expected data structure"""
    required_keys = ["automation_tuples", "worker_risk_assessment", "shift_groups"]
    return all(key in data for key in required_keys)
```

## Expected Output Format

```python
{
    "company_id": 7259,
    "company_name": "Arrillaga Family Dining Commons, Bay Area, CA",
    "worker_risk_assessment": {
        "reliability_scores": [91.52, 87.81, 30.02, 86.36, 37.1],
        "high_risk_count": 2,
        "missing_distance_data": True
    },
    "shift_groups": [
        {
            "shift_group_id": 916775,
            "total_shifts": 5,
            "filled_shifts": 4,
            "fill_rate": 80.0
        }
    ],
    "automation_tuples": [
        {
            "action_type": "action",
            "message": "Multiple shifts in the next 24-48hrs have >30% high-risk workers",
            "category": "emergency_staffing",
            "priority_hours": 2,
            "urgency": "IMMEDIATE"
        }
    ]
}
```

## Next Steps for Claude Code Agent

1. **Reverse Engineer API Calls**: Inspect network traffic to understand actual HTTP requests
2. **Build Authentication**: Determine how to authenticate with Finch programmatically  
3. **Implement WebSocket/HTTP Client**: Create reliable communication layer
4. **Test Conversation Flow**: Validate that the 3-step conversation works consistently
5. **Create Robust Parser**: Handle variations in AI response format
6. **Add Monitoring**: Log conversation flows for debugging and optimization