class AuthManager:
    def __init__(self):
        self.token = None
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}