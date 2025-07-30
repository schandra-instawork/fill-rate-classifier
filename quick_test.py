import requests

API_KEY = "f1e14498dbb9b29a7abdd16fad04baa39ac29197a84f21160162516c1edcdff6"
URL = "https://finch.instawork.com/fill-rate-diagnoser/run"
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

print("Testing conversational pattern...")

# Step 1
r1 = requests.post(URL, json={"input": "hey"}, headers=headers, timeout=30)
print(f"Step 1 status: {r1.status_code}")

if r1.status_code == 200:
    out1 = r1.json().get("output", "")
    print(f"Step 1 output: {out1}")
    
    if "company" in out1.lower():
        print("SUCCESS: Got company request!")
        
        # Step 2
        r2 = requests.post(URL, json={"input": "13100"}, headers=headers, timeout=30)
        print(f"Step 2 status: {r2.status_code}")
        
        if r2.status_code == 200:
            out2 = r2.json().get("output", "")
            print(f"Step 2 length: {len(out2)}")
            
            if len(out2) > 100:
                print("BREAKTHROUGH: Got data!")
                print(f"Preview: {out2[:200]}...")
            else:
                print(f"Still empty: '{out2}'")
    else:
        print(f"Unexpected: {out1}")
else:
    print(f"Failed: {r1.status_code}")

print("Test complete") 