"""
Tree Visualizer for Atlas Project Trees

Simple, clean hierarchical visualization using indentation and node __repr__ methods.
Integrates directly with ProjectNode via visualization API.
"""

from typing import Set, Any


class TreeVisualizer:
    """Simple tree visualizer that uses hierarchical indentation."""
    
    def __init__(self, indent_size: int = 2, show_container_nodes: bool = False):
        """
        Initialize the tree visualizer.
        
        Args:
            indent_size: Number of spaces per indentation level
            show_container_nodes: Whether to display ContainerNodes (False by default)
        """
        self.indent_size = indent_size
        self.show_container_nodes = show_container_nodes
    
    def view(self, project_node) -> str:
        """
        Generate a hierarchical text representation of the project tree.
        
        Args:
            project_node: The root ProjectNode to visualize
            
        Returns:
            String representation of the tree structure
        """
        lines = []
        self._render_node(project_node, 0, lines, set())
        return "\n".join(lines)
    
    def print(self, project_node) -> None:
        """
        Print the hierarchical tree representation to the terminal.
        
        Args:
            project_node: The root ProjectNode to visualize
        """
        output = self.view(project_node)
        print(output)
    
    def _render_node(self, node, depth: int, lines: list, visited: Set[int]) -> None:
        """
        Recursively render a node and its children.
        
        Args:
            node: Current node to render
            depth: Current depth in the tree (for indentation)
            lines: List to accumulate output lines
            visited: Set of visited node IDs to prevent infinite recursion
        """
        # Prevent infinite recursion
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        
        # Check if this is a ContainerNode and we should skip it
        is_container_node = self._is_container_node(node)
        
        if not is_container_node or self.show_container_nodes:
            # Create indentation based on depth
            indent = " " * (depth * self.indent_size)
            
            # Use the node's __repr__ for display
            node_display = repr(node)
            
            # Add the line
            lines.append(f"{indent}{node_display}")
        
        # Always render children, but adjust depth based on whether we displayed this node
        child_depth = depth + 1 if (not is_container_node or self.show_container_nodes) else depth
        
        # Render all children
        children = self._get_all_children(node)
        for child in children:
            self._render_node(child, child_depth, lines, visited)
    
    def _is_container_node(self, node) -> bool:
        """
        Check if a node is a ContainerNode.
        
        Args:
            node: Node to check
            
        Returns:
            True if the node is a ContainerNode, False otherwise
        """
        # Check if the node's class name contains 'Container' or is a known container type
        class_name = node.__class__.__name__
        return ('Container' in class_name or 
                class_name in ['StateContainerNode', 'ImportNode', 'ImportFromNode'])
    
    def _get_all_children(self, node) -> list:
        """
        Extract all children from a node using Atlas navigation patterns.
        
        Args:
            node: Node to extract children from
            
        Returns:
            List of all child nodes
        """
        children = []
        
        # Try common Atlas collection attributes with correct names based on diagnostic
        collection_attrs = [
            '_packages', '_modules', '_classes', '_methods',  # Changed _functions to _methods
            '_arguments', '_returns', '_attributes', '_imports', 
            '_violations', '_types'
        ]
        
        for attr_name in collection_attrs:
            if hasattr(node, attr_name):
                try:
                    attr_value = getattr(node, attr_name)
                    if isinstance(attr_value, list):
                        children.extend(attr_value)
                except:
                    pass  # Skip if attribute access fails
        
        return children