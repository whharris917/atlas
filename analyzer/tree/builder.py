"""
Project Builder - Atlas Rewrite

Automatically discovers and builds the project tree structure from filesystem.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set
from .foundation import ProjectNode, PackageNode, ModuleNode


class ProjectBuilder:
    """Builds project tree structure by scanning filesystem."""
    
    def __init__(self, project_name: str, root_path: str = "."):
        self.project_name = project_name
        self.root_path = Path(root_path)
        self.project = ProjectNode(project_name)
    
    def build_from_filesystem(self, target_dir: str = "sample_files") -> ProjectNode:
        """Scan filesystem and build complete project tree."""
        scan_path = self.root_path / target_dir
        if not scan_path.exists():
            raise FileNotFoundError(f"Directory {scan_path} not found")
        
        print(f"Building project tree from: {scan_path}")
        
        # Scan and build the tree structure
        self._scan_directory(scan_path, self.project)
        
        return self.project
    
    def _scan_directory(self, dir_path: Path, parent_node):
        """Recursively scan directory and build tree nodes."""
        print(f"Scanning: {dir_path}")
        
        # Track what we find
        python_files = []
        subdirectories = []
        
        # Categorize directory contents
        for item in dir_path.iterdir():
            if item.is_file() and item.suffix == '.py':
                python_files.append(item)
            elif item.is_dir() and not item.name.startswith('.'):
                subdirectories.append(item)
        
        # Create module nodes for Python files
        for py_file in python_files:
            module_name = py_file.stem
            relative_path = str(py_file.relative_to(self.root_path))
            
            # Parse AST and store it
            try:
                source_code = py_file.read_text(encoding='utf-8')
                ast_tree = ast.parse(source_code)
                print(f"  Created module: {module_name} ({relative_path})")
            except Exception as e:
                print(f"  Warning: Could not parse {py_file}: {e}")
                ast_tree = None
            
            parent_node.create_module(module_name, relative_path, ast_tree)
        
        # Process subdirectories as packages
        for subdir in subdirectories:
            # Check if it's a Python package (has __init__.py)
            init_file = subdir / "__init__.py"
            if init_file.exists():
                package_name = subdir.name
                relative_path = str(subdir.relative_to(self.root_path))
                
                # Parse __init__.py AST
                init_ast = None
                try:
                    init_source = init_file.read_text(encoding='utf-8')
                    init_ast = ast.parse(init_source)
                    print(f"  Created package: {package_name} ({relative_path}/) with __init__.py")
                except Exception as e:
                    print(f"  Warning: Could not parse {init_file}: {e}")
                    print(f"  Created package: {package_name} ({relative_path}/) without __init__.py")
                
                # Create package node with init AST
                package_node = parent_node.create_package(package_name, init_ast)
                package_node.path = relative_path  # Set path after creation
                
                # Recursively scan the package
                self._scan_directory(subdir, package_node)
            else:
                print(f"  Skipping {subdir} (no __init__.py)")


def build_sample_project() -> ProjectNode:
    """Convenience function to build the sample project."""
    builder = ProjectBuilder("sample_project")
    return builder.build_from_filesystem("sample_files")