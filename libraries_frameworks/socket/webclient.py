import requests

resp = requests.get("http://127.0.0.1:7000/hello")
print("HTTP client received:", resp.text)
