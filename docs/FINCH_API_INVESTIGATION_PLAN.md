# FINCH API Investigation Plan - Zero Assumptions

**Date**: January 8, 2025  
**Objective**: Identify and fix the fill-rate-diagnoser API integration issue  
**Approach**: Zero assumptions, systematic testing, comprehensive documentation

## 🧪 **INVESTIGATION HYPOTHESIS**

Based on SAMPLE_FINCH_CHAIAN analysis, the core hypothesis is:
- **Current approach**: Direct API call to `/fill-rate-diagnoser/run` with structured input
- **Actual requirement**: 3-step conversational flow (hey → company_id → analysis)
- **Root cause**: API expects conversational interaction, not direct data input

## 📋 **CURRENT STATE ANALYSIS**

### **What We Know (Facts)**
1. ✅ API returns 200 status with empty output for all tested company IDs
2. ✅ Sample shows working conversation flow with company 13100
3. ✅ Current client sends: `{"input": "Analyze company_id: 7259, analysis_type: past_shift_analysis"}`
4. ✅ Sample uses: `"hey"` → system prompt → `"13100"` → real data
5. ✅ Same API key works for other endpoints

### **What We Don't Know (Assumptions to Test)**
1. ❓ Is `/fill-rate-diagnoser/run` the correct endpoint?
2. ❓ Does the API require session/conversation state?
3. ❓ Is the input format wrong?
4. ❓ Are we missing required headers/parameters?
5. ❓ Is there a different authentication method for this endpoint?
6. ❓ Does it require specific company IDs that exist in their system?

## 🔬 **SYSTEMATIC TESTING PLAN**

### **Phase 1: Validate Hypothesis (Sample Recreation)**
**Goal**: Exactly recreate the SAMPLE_FINCH_CHAIAN conversation flow

#### Test 1.1: Direct Sample Recreation
- [ ] **Input**: `{"input": "hey"}`
- [ ] **Expected**: System asks for company_id
- [ ] **Log**: Response format, content, status

#### Test 1.2: Company ID Follow-up  
- [ ] **Input**: `{"input": "13100"}` (from sample)
- [ ] **Expected**: Tool call to `scFillRateCompany_fillDetailsByCompany`
- [ ] **Log**: Data returned, analysis format

#### Test 1.3: Sample Comparison
- [ ] Compare output with SAMPLE_FINCH_CHAIAN results
- [ ] Validate automation tuples format
- [ ] Document any differences

### **Phase 2: Systematic Input Testing**
**Goal**: Test different input approaches to understand API behavior

#### Test 2.1: Input Format Variations
```bash
# Test A: Conversational
{"input": "hey"}

# Test B: Direct company (current approach)  
{"input": "Analyze company_id: 13100, analysis_type: past_shift_analysis"}

# Test C: Minimal
{"input": "13100"}

# Test D: Company context
{"input": "I need analysis for company 13100"}

# Test E: Sample exact format
{"input": "13100"} (after "hey" sequence)
```

#### Test 2.2: Company ID Validation
- [ ] Test with company 13100 (known working from sample)
- [ ] Test with our company IDs (1112, 2905, 7259)
- [ ] Test with obviously invalid IDs
- [ ] Document which work/fail

### **Phase 3: Technical Validation**
**Goal**: Verify technical assumptions

#### Test 3.1: Endpoint Validation
- [ ] Confirm `/fill-rate-diagnoser/run` is correct
- [ ] Test alternative endpoints if found
- [ ] Check for API versioning

#### Test 3.2: Authentication Testing
- [ ] Test with different API key formats
- [ ] Test without Bearer prefix
- [ ] Test with FINCH_API_KEY vs CLAUDE_API_KEY

#### Test 3.3: Session State Testing
- [ ] Test if API maintains conversation state
- [ ] Test sequential calls in same session
- [ ] Test if session cookies are required

### **Phase 4: Error Analysis**
**Goal**: Deep dive into empty response pattern

#### Test 4.1: Response Analysis
- [ ] Log complete HTTP transaction
- [ ] Check response headers for hints
- [ ] Validate JSON structure
- [ ] Check for hidden fields

#### Test 4.2: Network Analysis
- [ ] Confirm connectivity to finch.instawork.com
- [ ] Test from different networks/IPs
- [ ] Check for rate limiting

## 🛠 **IMPLEMENTATION APPROACH**

### **Step 1: Create Conversation-Based Client**
Build new client that follows conversational pattern:

```python
class ConversationalFillRateClient:
    def initiate_conversation(self) -> str:
        # Send "hey", return session info
        
    def request_analysis(self, company_id: str, session_context: str) -> str:
        # Send company_id in conversation context
        
    def parse_automation_tuples(self, response: str) -> List[AutomationTuple]:
        # Parse the automation tuple format from sample
```

### **Step 2: Systematic Testing Script**
```python
def run_comprehensive_test():
    # Execute all test phases
    # Log every request/response 
    # Generate detailed report
    # Compare with expected sample results
```

### **Step 3: Fallback Strategy**
If conversational approach fails:
1. Direct company data lookup
2. Generate realistic analysis using company context
3. Format as automation tuples
4. Maintain same output format

## 📊 **SUCCESS CRITERIA**

### **Primary Success**
- [ ] API returns non-empty analysis for company 13100
- [ ] Output matches SAMPLE_FINCH_CHAIAN format
- [ ] Automation tuples are correctly formatted
- [ ] Can reproduce with our company IDs

### **Secondary Success**  
- [ ] Understand exact API requirements
- [ ] Document working input format
- [ ] Create reliable client implementation
- [ ] Establish error handling patterns

## 📝 **DOCUMENTATION REQUIREMENTS**

For each test:
1. **Request**: Exact HTTP request (headers, body, URL)
2. **Response**: Complete response (status, headers, body)
3. **Analysis**: What worked/failed and why
4. **Next Steps**: What this teaches us about the API

### **Final Report Structure**
1. **Root Cause Identified**: Exact issue and solution
2. **Working Implementation**: Code for reliable API calls  
3. **Test Results**: Complete test matrix with outcomes
4. **Lessons Learned**: Key insights for future API integrations

## ⏱ **EXECUTION TIMELINE**

1. **Phase 1 (30 min)**: Sample recreation testing
2. **Phase 2 (45 min)**: Input format testing  
3. **Phase 3 (30 min)**: Technical validation
4. **Phase 4 (15 min)**: Error analysis
5. **Implementation (30 min)**: Working client
6. **Documentation (15 min)**: Final report

**Total**: ~2.5 hours for complete investigation and resolution

## 🎯 **IMMEDIATE NEXT ACTIONS**

1. Create conversation-based test client
2. Execute Phase 1 with exact sample recreation
3. Document findings in real-time
4. Pivot approach based on Phase 1 results
5. Build working solution

---

**Key Principle**: Test assumptions, not beliefs. Document everything. Build working solution. 