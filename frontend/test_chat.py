import requests
import json

url = "http://127.0.0.1:8000/api/chat"
data = {
    "message": "Summarize this note",
    "current_note_content": "Artificial Intelligence is the simulation of human intelligence processes by machines, especially computer systems. These processes include learning, reasoning, and self-correction.",
    "note_id": "test-chat-123"
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except:
        print("Response Text:", response.text)
except Exception as e:
    print(f"Error: {e}")
