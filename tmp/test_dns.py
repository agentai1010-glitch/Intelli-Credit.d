import socket
import requests

try:
    ip = socket.gethostbyname('api.pageindex.ai')
    print(f"DNS Resolution: {ip}")
except Exception as e:
    print(f"DNS Resolution Failed: {e}")

try:
    r = requests.get('https://api.pageindex.ai/ping', timeout=5)
    print(f"HTTPS Request: {r.status_code}")
except Exception as e:
    print(f"HTTPS Request Failed: {e}")
