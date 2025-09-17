# Test case for ExpressionTraversal debugging: including self.b.c() pattern
# This will trigger: assignment_analyzer.py -> ExpressionTraversal.resolve_and_evaluate(call_node)

class DatabaseConnection:
    """A class representing a database connection."""
    
    def get_user_manager(self) -> 'UserManager':
        """Returns a UserManager instance."""
        return UserManager()

class UserManager:
    """A class for managing users."""
    
    def __init__(self) -> None:
        self.users = []
    
    def get_admin_panel(self) -> 'AdminPanel':
        """Returns an AdminPanel instance."""
        return AdminPanel()

class AdminPanel:
    """A class for admin operations."""
    
    def __init__(self) -> None:
        self.permissions = []

class ApplicationService:
    """A different class that uses the database connection."""
    
    def __init__(self) -> None:
        self.db_connection: DatabaseConnection = DatabaseConnection()
    
    def handle_admin_request(self) -> 'AdminPanel':
        """Method containing the self.b.c() pattern we want to test."""
        
        # This assignment with self.attribute.method() will test:
        # Pattern: y = self.b.c() where self=ApplicationService, b=db_connection, c=get_user_manager
        admin_interface: AdminPanel = self.db_connection.get_user_manager().get_admin_panel()
        
        return admin_interface

def process_data() -> 'UserManager':
    """Function containing the original assignment we want to debug."""
    # Create an instance of DatabaseConnection
    db: DatabaseConnection = DatabaseConnection()
    
    # This assignment with RHS method call will trigger ExpressionTraversal:
    # Pattern: x = a.b() where a=db, b=get_user_manager, x=user_mgr
    user_mgr: UserManager = db.get_user_manager()
    
    return user_mgr