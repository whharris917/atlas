# demo.py

import ast
import logging
from rich.logging import RichHandler

# Import the actual classes from our new modules
from analyzer.expression_traversal import ExpressionTraversal
from analyzer.scope_manager import ScopeManager
from analyzer.assignment_analyzer import AssignmentAnalyzer

# --- Mocking `utils.get_source` ---
# Since we are not refactoring utils.py, we'll create a mock version of
# get_source for our demo to work without touching that file.
def mock_get_source(node: ast.AST) -> str:
    """A mock version of get_source that returns a placeholder."""
    if hasattr(node, 'lineno'):
        return f"demo.py:L{node.lineno}"
    return "demo.py"

# Monkey-patch the function in the analyzer module so it uses our mock version.
import analyzer.assignment_analyzer
analyzer.assignment_analyzer.get_source = mock_get_source


# --- Mock Data and Configuration ---

MOCK_RECON_DATA = {
    "my_module.User": {
        "fqn": "my_module.User",
        "type": "class",
        "attributes": {
            "name": "builtins.str",
            "get_profile": "my_module.User.get_profile"
        }
    },
    "my_module.UserProfile": {
        "fqn": "my_module.UserProfile",
        "type": "class",
        "attributes": {
            "name": "builtins.str"
        }
    },
    "my_module.User.get_profile": {
        "fqn": "my_module.User.get_profile",
        "type": "function",
        "return_type": "my_module.UserProfile"
    },
    "my_module.get_user_by_id": {
        "fqn": "my_module.get_user_by_id",
        "type": "function",
        "return_type": "my_module.User"
    }
}

# --- Main Demo Logic ---

def setup_logging():
    """
    Configures a logger with a custom filter to handle the 'meta' field.
    """
    # This custom filter adds a default 'meta' value if it's missing.
    class MetaFilter(logging.Filter):
        def filter(self, record):
            if not hasattr(record, 'meta'):
                # Use a simple placeholder for logs without explicit meta info.
                record.meta = 'narrative'
            return True

    # Get the logger instance for our application.
    log = logging.getLogger("atlas")
    log.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times if this function is called again.
    if not log.handlers:
        # Add our custom filter.
        log.addFilter(MetaFilter())

        # Configure the RichHandler for pretty console output.
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        
        # Define the format string that includes our 'meta' field.
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - [%(meta)s] - %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)
        
        # Prevent the log messages from being passed to the root logger.
        log.propagate = False

    return log


def main():
    """
    Runs a demonstration of the ExpressionTraversal and AssignmentAnalyzer.
    """
    logger = setup_logging()

    logger.info("--- DEMO START ---")
    logger.info("This script demonstrates the core functionality of the new analysis engine.")

    # 1. Initialization
    scope_manager = ScopeManager()
    scope_manager.push_scope() # CORRECTED: Changed from enter_scope to push_scope
    traversal_engine = ExpressionTraversal(MOCK_RECON_DATA, scope_manager, "my_module")
    assignment_analyzer = AssignmentAnalyzer(traversal_engine, scope_manager)

    # --- SCENARIO 1: Handle a standard assignment ---
    logger.info("\n--- SCENARIO 1: Analyzing a standard assignment ---")
    logger.info("Analyzing code: new_user = get_user_by_id(42)")
    assignment_node = ast.Assign(
        targets=[ast.Name(id='new_user', ctx=ast.Store(), lineno=10)],
        value=ast.Call(
            func=ast.Name(id='get_user_by_id', ctx=ast.Load(), lineno=10),
            args=[ast.Constant(value=42)], keywords=[], lineno=10
        ), lineno=10
    )
    assignment_analyzer.analyze_assignment(assignment_node)

    # --- SCENARIO 2: Handle an annotated assignment ---
    logger.info("\n--- SCENARIO 2: Analyzing an annotated assignment ---")
    logger.info("Analyzing code: user_profile: UserProfile = new_user.get_profile()")
    ann_assign_node = ast.AnnAssign(
        target=ast.Name(id='user_profile', ctx=ast.Store(), lineno=15),
        annotation=ast.Name(id='UserProfile', ctx=ast.Load(), lineno=15),
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='new_user', ctx=ast.Load(), lineno=15),
                attr='get_profile', ctx=ast.Load(), lineno=15
            ),
            args=[], keywords=[], lineno=15
        ),
        simple=1, lineno=15
    )
    
    assignment_analyzer.analyze_annotated_assignment(ann_assign_node)


    # --- SCENARIO 3: Evaluate an expression using variables from both assignments ---
    logger.info("\n--- SCENARIO 3: Evaluating an expression using the new local variables ---")
    logger.info("Analyzing code: user_profile.name")

    expression_node = ast.Attribute(
        value=ast.Name(id='user_profile', ctx=ast.Load(), lineno=20),
        attr='name',
        ctx=ast.Load(), lineno=20
    )

    _, final_type = traversal_engine.resolve_and_evaluate(expression_node)

    logger.info("\n--- DEMO COMPLETE ---")
    logger.info(f"Final evaluated type for 'user_profile.name': {final_type}")
    if final_type == "builtins.str":
        logger.info("✅ SUCCESS: The final type is correct!")
    else:
        logger.error(f"❌ FAILURE: Expected 'builtins.str', but got '{final_type}'.")


if __name__ == "__main__":
    main()
