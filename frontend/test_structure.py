import requests
import json

url = "http://127.0.0.1:8000/api/notes/structure"
data = {
    "note_id": "test-123",
    "content": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize nutrients from carbon dioxide and water. Photosynthesis in plants generally involves the green pigment chlorophyll and generates oxygen as a byproduct."
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
