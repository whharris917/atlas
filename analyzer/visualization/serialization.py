"""
Serialization Mixin - Atlas Project Trees

Provides JSON serialization capability for project trees.
Completely decoupled from core tree infrastructure.
"""

from typing import Dict, Any, List


class SerializationMixin:
    """
    Mixin providing JSON serialization for Atlas project trees.
    
    Designed to be mixed into ProjectNode to provide .dump() capability
    while keeping visualization concerns orthogonal to core tree logic.
    """
    
    def dump(self) -> Dict[str, Any]:
        """
        Serialize complete project tree to JSON-compatible dict.
        
        Returns nested dictionary containing:
        - All nodes with type, name, FQN, line numbers
        - Complete parent-child relationships
        - Type information (when present)
        - Violations (inline with nodes)
        
        Does not include raw AST nodes (not JSON-serializable).
        
        Returns:
            dict: Complete tree structure with all analysis results
            
        Example:
            >>> project = build_complete_atlas('sample_files')
            >>> data = project.dump()
            >>> import json
            >>> with open('project.json', 'w') as f:
            ...     json.dump(data, f, indent=2)
        """
        return self._serialize_node(self)
    
    def save_dump(self, filepath: str = 'atlas_dump.json', indent: int = 2) -> None:
        """
        Serialize and save project tree to JSON file.
        
        Convenience method that combines dump() with file writing.
        
        Args:
            filepath: Path where JSON file should be saved (default: 'atlas_dump.json')
            indent: JSON indentation level for readability (default: 2, use None for compact)
            
        Example:
            >>> project = build_complete_atlas('sample_files')
            >>> project.save_dump('my_project.json')
            >>> project.save_dump('compact.json', indent=None)  # No indentation
        """
        import json
        
        data = self.dump()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
        
        # Calculate file size for feedback
        import os
        file_size = os.path.getsize(filepath)
        
        print(f"✓ Project tree serialized to: {filepath}")
        print(f"  File size: {file_size:,} bytes")
        
        # Count nodes
        node_count = self._count_nodes_recursive(data)
        print(f"  Nodes serialized: {node_count}")
    
    def _serialize_node(self, node) -> Dict[str, Any]:
        """
        Recursively serialize a node and all its children.
        
        Args:
            node: The node to serialize
            
        Returns:
            dict: Node data with nested children
        """
        # Basic node information
        result = {
            'type': node.__class__.__name__.replace('Node', ''),
        }
        
        # Add name if present
        if hasattr(node, 'name'):
            result['name'] = node.name
        
        # Add FQN if available
        if hasattr(node, 'fqn'):
            result['fqn'] = node.fqn
        
        # Add line number if available
        if hasattr(node, 'line_number'):
            line = node.line_number
            if line > 0:  # Only include meaningful line numbers
                result['line'] = line
        
        # Add violations if present
        if hasattr(node, '_violations') and node._violations:
            result['violations'] = [
                {
                    'type': v.__class__.__name__,
                    'message': str(v)
                }
                for v in node._violations
            ]
        
        # Add type information flag if present
        if hasattr(node, '_type') and node._type is not None:
            result['has_type'] = True
        
        # Collect and serialize all children
        children = self._collect_children(node)
        
        if children:
            result['children'] = [
                self._serialize_node(child) 
                for child in children
            ]
        
        return result
    
    def _collect_children(self, node) -> List:
        """
        Collect all children from a node's various collections.
        
        Args:
            node: The node to collect children from
            
        Returns:
            List of child nodes
        """
        children = []
        
        # Standard collection attributes to check
        collection_attrs = [
            '_packages',
            '_modules',
            '_classes',
            '_functions',
            '_arguments',
            '_class_attributes',
            '_instance_attributes',
            '_imports',
            '_from_imports',
            '_state'
        ]
        
        for attr in collection_attrs:
            if hasattr(node, attr):
                collection = getattr(node, attr)
                if isinstance(collection, list):
                    children.extend(collection)
        
        # Single children
        if hasattr(node, '_return') and node._return is not None:
            children.append(node._return)
        
        # Type child (treat as first-class child, not special case)
        if hasattr(node, '_type') and node._type is not None:
            children.append(node._type)
        
        return children
    
    def _count_nodes_recursive(self, data: Dict[str, Any]) -> int:
        """
        Count total number of nodes in serialized tree.
        
        Args:
            data: Serialized node dictionary
            
        Returns:
            Total node count including all descendants
        """
        count = 1  # Count this node
        
        if 'children' in data:
            for child in data['children']:
                count += self._count_nodes_recursive(child)
        
        return count