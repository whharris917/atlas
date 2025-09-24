
def typed_function(name: str, age: int) -> str:
    """Function with complete type annotations."""
    return f"{name} is {age} years old"

def partially_typed(name: str, age) -> str:
    """Function with partial type annotations."""
    return f"{name} is {age} years old"

def untyped_function(name, age):
    """Function with no type annotations."""
    return f"{name} is {age} years old"

class UserService:
    def process_user(self, user_id: int, callback):
        """Method with mixed annotations."""
        pass

    def get_stats(self):
        """Method with no annotations."""  
        pass
