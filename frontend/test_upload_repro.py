import requests
import os

# Create a dummy PDF file
with open("test.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n%...\nHello World")

url = "http://localhost:8000/api/upload"
files = {'file': ('test.pdf', open('test.pdf', 'rb'), 'application/pdf')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists("test.pdf"):
        os.remove("test.pdf")
