"""Base infrastructure for analysis notes."""

from abc import ABC


class BaseNote(ABC):
    """Lightweight analysis artifact attached to tree nodes.
    
    Notes are created by analysis visitors to record discoveries like:
    - Variable type inferences
    - Function call relationships  
    - Class instantiations
    - Any other analysis results
    
    Subclasses define specific note types with appropriate properties.
    """
    
    def __init__(self, node):
        """Initialize note attached to a tree node.
        
        Args:
            node: The TreeNode this note is attached to
        """
        self.node = node
    
    def __repr__(self):
        """Simple representation for debugging."""
        node_name = getattr(self.node, 'name', 'unknown')
        return f"{self.__class__.__name__}(node={node_name})"