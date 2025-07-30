#!/usr/bin/env python3
"""
STEP 1 ONLY: Test fill-rate-diagnoser conversational pattern
Focus: Get non-empty response from the diagnoser API
"""

import requests
import json

print("🎯 STEP 1 ONLY: TESTING FILL-RATE-DIAGNOSER")
print("Goal: Get non-empty response instead of current empty output")
print("=" * 60)

API_KEY = "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6"
URL = "https://finch.instawork.com/fill-rate-diagnoser/run"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

print("\n🚀 CURRENT APPROACH (BROKEN):")
print("Sending direct company analysis request...")

# Test current broken approach
response = requests.post(
    URL,
    json={"input": "Analyze company_id: 13100, analysis_type: past_shift_analysis"},
    headers=headers,
    timeout=30
)

print(f"Status: {response.status_code}")
result = response.json() if response.status_code == 200 else {"error": response.text}
output = result.get("output", "")
print(f"Output: '{output}' (length: {len(output)})")

print("\n🧪 CONVERSATIONAL APPROACH (HYPOTHESIS):")
print("Step 1: Sending 'hey' to initiate conversation...")

# Test conversational approach - Step 1
response1 = requests.post(
    URL,
    json={"input": "hey"},
    headers=headers,
    timeout=30
)

print(f"Status: {response1.status_code}")
if response1.status_code == 200:
    result1 = response1.json()
    output1 = result1.get("output", "")
    print(f"Output: '{output1}' (length: {len(output1)})")
    
    if "company" in output1.lower():
        print("✅ SUCCESS: System asked for company_id!")
        
        print("\nStep 2: Sending company ID '13100'...")
        response2 = requests.post(
            URL,
            json={"input": "13100"},
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response2.status_code}")
        if response2.status_code == 200:
            result2 = response2.json()
            output2 = result2.get("output", "")
            print(f"Output length: {len(output2)} chars")
            
            if len(output2) > 100:
                print("🎯 BREAKTHROUGH: Got substantial data!")
                print(f"Preview: {output2[:300]}...")
                
                # Save the full output
                with open("diagnoser_success_output.txt", "w") as f:
                    f.write(output2)
                print("\n📝 Full output saved to: diagnoser_success_output.txt")
                
            elif len(output2) > 0:
                print(f"⚠️  Got some data: '{output2}'")
            else:
                print("❌ Still empty response")
        else:
            print(f"❌ Step 2 failed: {response2.status_code}")
    else:
        print(f"⚠️  Unexpected response: '{output1}'")
else:
    print(f"❌ Step 1 failed: {response1.status_code}")

print("\n" + "=" * 60)
print("STEP 1 TEST COMPLETE")
print("Next: If conversational pattern works, implement in production") 