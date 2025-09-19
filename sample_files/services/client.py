import requests
from .auth import AuthManager

class HTTPClient:
    def __init__(self):
        self.auth = AuthManager()
    
    def get(self, url):
        headers = self.auth.get_headers()
        return requests.get(url, headers=headers)