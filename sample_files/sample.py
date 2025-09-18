class User:
    def __init__(self, name):
        self.name = name
        self.profile = Profile()
    
    def get_status(self):
        return self.profile.status

class Profile:
    def __init__(self):
        self.status = "active"
    
    def get_summary(self):
        return {"status": self.status, "info": "user profile"}

# Module-level code
user = User("Alice")
status = user.get_status()
summary = user.profile.get_summary()
nested_access = user.profile.get_summary()["status"]
