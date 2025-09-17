"""
The main entry point for the application.
"""
from models import User, ServiceA

class App:
    """A simple application class to provide a 'self' context."""
    def __init__(self):
        """Initializes the app and the first service."""
        self.a = ServiceA()
        self.user = User("Alice", "alice@example.com")

    def run_complex_chain(self):
        """Executes the self.a.b().c().d() chain."""
        print("\n--- Running Complex Chain ---")
        # This line is the primary target for our analysis
        result = self.a.b().c().d()
        print(f"Chain call result: '{result}'")

    def run_simple_logic(self):
        """Runs the original, simpler logic."""
        print("--- Running Simple Logic ---")
        user_info = self.user.get_info()
        print(user_info)

def run_main_logic():
    """Contains the main logic for the script."""
    app_instance = App()
    app_instance.run_simple_logic()
    app_instance.run_complex_chain()


if __name__ == "__main__":
    run_main_logic()
