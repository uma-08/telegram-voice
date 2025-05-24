import requests
import json

def test_backend():
    # Test the webhook endpoint
    url = "https://voice-recorder-8a6l.onrender.com/webhook"
    data = {"type": "test"}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_backend() 