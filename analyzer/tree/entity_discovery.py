"""
Entity Discovery - Atlas Rewrite

Discovers code entities (classes, functions, etc.) from AST nodes in built tree.
Phase 2 of Reconnaissance - populates tree with all code entities.
"""

import ast
from typing import List
from .nodes import ProjectNode, PackageNode, ModuleNode


class EntityDiscovery:
    """Discovers and populates code entities in an existing project tree."""
    
    def __init__(self, project: ProjectNode):
        self.project = project
    
    def discover_all_entities(self):
        """Discover all code entities in the project tree."""
        print(f"\n=== DISCOVERING CODE ENTITIES ===")
        
        self.discover_classes_and_methods()
        self.discover_module_functions()
        self.discover_state_variables()
        self.discover_imports()
        
        print("Entity discovery complete")
    
    def discover_classes_and_methods(self):
        """Discover all classes and their methods by parsing stored AST nodes."""
        print("Discovering classes and methods...")
        
        for module_node in self._get_all_modules():
            if module_node.ast_node:
                self._extract_classes_from_module(module_node)
    
    def discover_module_functions(self):
        """Discover module-level functions by parsing stored AST nodes."""
        print("Discovering module functions...")
        
        for module_node in self._get_all_modules():
            if module_node.ast_node:
                self._extract_functions_from_module(module_node)
    
    def discover_state_variables(self):
        """Discover module-level state variables by parsing stored AST nodes."""
        print("Discovering state variables...")
        
        for module_node in self._get_all_modules():
            if module_node.ast_node:
                self._extract_state_from_module(module_node)
    
    def discover_imports(self):
        """Discover import statements by parsing stored AST nodes."""
        print("Discovering imports...")
        
        for module_node in self._get_all_modules():
            if module_node.ast_node:
                self._extract_imports_from_module(module_node)
    
    def _get_all_modules(self) -> List[ModuleNode]:
        """Get all module nodes from the entire project tree."""
        modules = []
        
        # Direct modules in project
        modules.extend(self.project.list_modules())
        
        # Modules in packages (including nested packages)
        def collect_from_package(package):
            modules.extend(package.list_modules())
            for nested_package in package.list_packages():
                collect_from_package(nested_package)
        
        for package in self.project.list_packages():
            collect_from_package(package)
        
        return modules
    
    def _extract_classes_from_module(self, module_node: ModuleNode):
        """Extract all classes and their methods from a module's AST."""
        for node in ast.walk(module_node.ast_node):
            if isinstance(node, ast.ClassDef):
                # Create the class node
                class_node = module_node.create_class(
                    name=node.name,
                    line_number=getattr(node, 'lineno', 0),
                    ast_node=node
                )
                print(f"  Found class: {class_node.fqn}")
                
                # Extract methods from this class
                self._extract_methods_from_class(class_node, node)
    
    def _extract_methods_from_class(self, class_node, class_ast_node):
        """Extract all methods from a class AST node."""
        for node in class_ast_node.body:
            if isinstance(node, ast.FunctionDef):
                method_node = class_node.create_method(
                    name=node.name,
                    line_number=getattr(node, 'lineno', 0),
                    ast_node=node
                )
                print(f"    Found method: {method_node.fqn}")
                
                # Extract arguments from this method
                self._extract_arguments_from_function(method_node, node)
    
    def _extract_functions_from_module(self, module_node: ModuleNode):
        """Extract module-level functions from a module's AST."""
        for node in module_node.ast_node.body:
            if isinstance(node, ast.FunctionDef):
                function_node = module_node.create_function(
                    name=node.name,
                    line_number=getattr(node, 'lineno', 0),
                    ast_node=node
                )
                print(f"  Found function: {function_node.fqn}")
                
                # Extract arguments from this function
                self._extract_arguments_from_function(function_node, node)
    
    def _extract_arguments_from_function(self, function_node, func_ast_node):
        """Extract arguments from a function AST node."""
        for arg in func_ast_node.args.args:
            arg_type = ""
            if arg.annotation:
                try:
                    arg_type = ast.unparse(arg.annotation)
                except:
                    arg_type = "Unknown"
            
            arg_node = function_node.create_argument(
                name=arg.arg,
                arg_type=arg_type,
                ast_node=arg
            )
            print(f"      Found argument: {arg_node.fqn} : {arg_type}")
    
    def _extract_state_from_module(self, module_node: ModuleNode):
        """Extract module-level state variables from a module's AST."""
        for node in module_node.ast_node.body:
            if isinstance(node, ast.Assign):
                # Handle regular assignments like: var = value
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        state_node = module_node.create_state(
                            name=target.id,
                            line_number=getattr(node, 'lineno', 0),
                            ast_node=node
                        )
                        print(f"  Found state variable: {state_node.fqn}")
            
            elif isinstance(node, ast.AnnAssign):
                # Handle annotated assignments like: var: Type = value
                if isinstance(node.target, ast.Name):
                    state_node = module_node.create_state(
                        name=node.target.id,
                        line_number=getattr(node, 'lineno', 0),
                        ast_node=node
                    )
                    print(f"  Found annotated state variable: {state_node.fqn}")
    
    def _extract_imports_from_module(self, module_node: ModuleNode):
        """Extract import statements from a module's AST."""
        for node in module_node.ast_node.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.asname if alias.asname else alias.name
                    import_node = module_node.create_import(
                        name=import_name,
                        module_name=alias.name,
                        ast_node=node
                    )
                    print(f"  Found import: {import_node.fqn} -> {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        import_name = alias.asname if alias.asname else alias.name
                        full_module = f"{node.module}.{alias.name}"
                        import_node = module_node.create_import(
                            name=import_name,
                            module_name=full_module,
                            ast_node=node
                        )
                        print(f"  Found from-import: {import_node.fqn} -> {full_module}")


def discover_all_entities(project: ProjectNode):
    """Convenience function to discover all entities in a project tree."""
    discovery = EntityDiscovery(project)
    discovery.discover_all_entities()