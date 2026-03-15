import socket
import requests

try:
    ip = socket.gethostbyname('api.pageindex.ai.')
    print(f"DNS Resolution (with dot): {ip}")
except Exception as e:
    print(f"DNS Resolution (with dot) Failed: {e}")

try:
    # We can't easily pass the dot to requests because of certificate verification
    # but we can try to "warm up" the cache
    socket.gethostbyname('api.pageindex.ai')
    r = requests.get('https://api.pageindex.ai/ping', timeout=5)
    print(f"HTTPS Request after warmup: {r.status_code}")
except Exception as e:
    print(f"HTTPS Request Failed: {e}")
