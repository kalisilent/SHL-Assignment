import requests
import json

def test_my_agent():
    print("Sending message to agent...")
    url = "http://127.0.0.1:8000/chat"
    
    # This is the exact format SHL will use to test your bot
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a Java developer."}
        ]
    }
    
    response = requests.post(url, json=payload)
    
    # Print the agent's response beautifully
    print("\n--- AGENT RESPONSE ---")
    
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_my_agent()