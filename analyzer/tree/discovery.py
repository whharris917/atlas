"""
Project Discovery - Atlas Rewrite

Pure file I/O and AST parsing without tree construction.
Discovers project structure and prepares data for tree building.
"""

import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DiscoveredModule:
    """Data class for discovered module information."""
    name: str
    path: str
    relative_path: str
    ast_node: Optional[ast.Module]
    is_init: bool = False


@dataclass
class DiscoveredPackage:
    """Data class for discovered package information."""
    name: str
    path: str
    relative_path: str
    ast_node: Optional[ast.Module]
    modules: List[DiscoveredModule]
    nested_packages: List['DiscoveredPackage']


@dataclass
class ProjectStructure:
    """Complete discovered project structure."""
    root_path: Path
    direct_modules: List[DiscoveredModule]
    packages: List[DiscoveredPackage]


class ProjectDiscovery:
    """Discovers project structure through pure file I/O operations."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
    
    def discover_project_structure(self, target_dir: str = "sample_files") -> ProjectStructure:
        """Discover complete project structure through file I/O only."""
        scan_path = self.root_path / target_dir
        if not scan_path.exists():
            raise FileNotFoundError(f"Directory {scan_path} not found")
        
        print(f"=== DISCOVERING PROJECT STRUCTURE ===")
        print(f"Scanning: {scan_path}")
        
        # Discover all Python files and packages
        direct_modules, packages = self._scan_directory(scan_path)
        
        structure = ProjectStructure(
            root_path=self.root_path,
            direct_modules=direct_modules,
            packages=packages
        )
        
        print(f"Discovery complete: {len(direct_modules)} direct modules, {len(packages)} packages")
        return structure
    
    def _scan_directory(self, dir_path: Path) -> Tuple[List[DiscoveredModule], List[DiscoveredPackage]]:
        """Recursively scan directory and discover Python modules and packages."""
        print(f"  Scanning directory: {dir_path}")
        
        # Categorize directory contents
        python_files = []
        subdirectories = []
        
        for item in dir_path.iterdir():
            if item.is_file() and item.suffix == '.py':
                python_files.append(item)
            elif item.is_dir() and not item.name.startswith('.'):
                subdirectories.append(item)
        
        # Process direct Python modules (excluding __init__.py)
        direct_modules = []
        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue  # Handle in package processing
            
            module = self._parse_module(py_file)
            if module:
                direct_modules.append(module)
        
        # Process subdirectories as potential packages
        packages = []
        for subdir in subdirectories:
            package = self._discover_package(subdir)
            if package:
                packages.append(package)
        
        return direct_modules, packages
    
    def _discover_package(self, package_dir: Path) -> Optional[DiscoveredPackage]:
        """Discover a single package and its contents."""
        init_file = package_dir / "__init__.py"
        if not init_file.exists():
            print(f"    Skipping {package_dir.name} (not a Python package)")
            return None
        
        package_name = package_dir.name
        relative_path = str(package_dir.relative_to(self.root_path))
        
        # Parse __init__.py
        ast_node = self._parse_file(init_file)
        print(f"    Found package: {package_name} ({relative_path}/)")
        
        # Recursively discover package contents
        modules, nested_packages = self._scan_directory(package_dir)
        
        return DiscoveredPackage(
            name=package_name,
            path=str(package_dir),
            relative_path=relative_path,
            ast_node=ast_node,
            modules=modules,
            nested_packages=nested_packages
        )
    
    def _parse_module(self, py_file: Path) -> Optional[DiscoveredModule]:
        """Parse a single Python module file."""
        module_name = py_file.stem
        relative_path = str(py_file.relative_to(self.root_path))
        
        ast_node = self._parse_file(py_file)
        if ast_node:
            print(f"    Found module: {module_name} ({relative_path})")
        
        return DiscoveredModule(
            name=module_name,
            path=str(py_file),
            relative_path=relative_path,
            ast_node=ast_node
        )
    
    def _parse_file(self, file_path: Path) -> Optional[ast.Module]:
        """Parse a single Python file into AST."""
        try:
            source_code = file_path.read_text(encoding='utf-8')
            return ast.parse(source_code)
        except Exception as e:
            print(f"    Warning: Could not parse {file_path}: {e}")
            return None


def discover_project_structure(target_dir: str = "sample_files") -> ProjectStructure:
    """Convenience function to discover project structure."""
    discovery = ProjectDiscovery()
    return discovery.discover_project_structure(target_dir)