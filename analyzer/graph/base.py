from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import ast


class Node(ABC):
    """Base class for all graph nodes."""
    
    def __init__(self, id: str, name: str, ast_node: Optional[ast.AST] = None):
        self.id = id
        self.name = name
        self.ast_node = ast_node
        self.metadata: Dict[str, Any] = {}
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id


@dataclass
class Edge(ABC):
    """Base class for all graph edges."""
    source_id: str                   # Source node ID
    target_id: str                   # Target node ID
    
    def __post_init__(self):
        self.metadata: Dict[str, Any] = {}