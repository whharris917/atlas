"""
Expression Finder - Atlas Rewrite

Analyzes Python code to find and categorize all expression nodes.
This is the foundation for our unified Expression Traversal engine.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any


class ExpressionFinder(ast.NodeVisitor):
    """Finds and categorizes all expression nodes in an AST."""
    
    def __init__(self):
        self.expressions = []
    
    def visit(self, node):
        """Visit each node and collect expression information."""
        # Check if this node is an expression
        if isinstance(node, ast.expr):
            expr_info = {
                'type': type(node).__name__,
                'node': node,
                'line': getattr(node, 'lineno', 'unknown')
            }
            
            # Add specific details for different expression types
            if isinstance(node, ast.Name):
                expr_info['details'] = f"name='{node.id}'"
            elif isinstance(node, ast.Attribute):
                expr_info['details'] = f"attr='{node.attr}'"
            elif isinstance(node, ast.Call):
                expr_info['details'] = "function call"
            elif isinstance(node, ast.Constant):
                expr_info['details'] = f"value={repr(node.value)}"
            elif isinstance(node, ast.Subscript):
                expr_info['details'] = "subscript access"
            elif isinstance(node, ast.BinOp):
                expr_info['details'] = "binary operation"
            elif isinstance(node, ast.Compare):
                expr_info['details'] = "comparison"
            else:
                expr_info['details'] = "other"
            
            self.expressions.append(expr_info)
        
        self.generic_visit(node)
    
    def get_expressions(self) -> List[Dict[str, Any]]:
        """Return all found expressions."""
        return self.expressions


def analyze_file(file_path: str) -> List[Dict[str, Any]]:
    """Analyze a Python file and return all expressions found."""
    # Read the file
    with open(file_path, 'r') as f:
        source_code = f.read()
    
    # Parse into AST
    tree = ast.parse(source_code)
    
    # Find expressions
    finder = ExpressionFinder()
    finder.visit(tree)
    
    return finder.get_expressions()


def print_expression_analysis(file_path: str):
    """Print detailed analysis of expressions in a Python file."""
    print(f"Analyzing expressions in: {file_path}")
    print("=" * 60)
    
    try:
        expressions = analyze_file(file_path)
        
        print(f"Found {len(expressions)} expression nodes:")
        print("-" * 60)
        
        for i, expr in enumerate(expressions, 1):
            print(f"{i:2}. Line {expr['line']:2} | {expr['type']:12} | {expr['details']}")
        
        # Summary by type
        print("\n" + "=" * 60)
        print("Summary by expression type:")
        print("-" * 30)
        
        type_counts = {}
        for expr in expressions:
            expr_type = expr['type']
            type_counts[expr_type] = type_counts.get(expr_type, 0) + 1
        
        for expr_type, count in sorted(type_counts.items()):
            print(f"{expr_type:15} : {count:2}")
            
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except SyntaxError as e:
        print(f"Syntax error in file: {e}")
    except Exception as e:
        print(f"Error analyzing file: {e}")


if __name__ == "__main__":
    # Analyze the sample file
    sample_path = "sample_files/sample.py"
    print_expression_analysis(sample_path)
