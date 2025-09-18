"""
Graph Core - Atlas Rewrite

Core graph data structure and operations.
"""

from typing import Dict, List, Optional, Type
from .base import Node, Edge


class CodebaseGraph:
    """In-memory graph representation of the codebase."""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.edge_index: Dict[str, List[Edge]] = {}  # source_id -> edges
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        
        # Initialize edge index for this node
        if node.id not in self.edge_index:
            self.edge_index[node.id] = []
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        
        # Update edge index
        if edge.source_id not in self.edge_index:
            self.edge_index[edge.source_id] = []
        self.edge_index[edge.source_id].append(edge)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        return self.nodes.get(node_id)
    
    def node_exists(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.nodes
    
    def get_outgoing_edges(self, node_id: str, edge_type: Optional[Type[Edge]] = None) -> List[Edge]:
        """Get all outgoing edges from a node, optionally filtered by type."""
        edges = self.edge_index.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if isinstance(e, edge_type)]
        return edges
    
    def get_connected_nodes(self, node_id: str, edge_type: Type[Edge]) -> List[Node]:
        """Get all nodes connected via a specific edge type."""
        edges = self.get_outgoing_edges(node_id, edge_type)
        return [self.nodes[edge.target_id] for edge in edges if edge.target_id in self.nodes]
    
    def get_stats(self) -> Dict[str, int]:
        """Get basic statistics about the graph."""
        stats = {"total_nodes": len(self.nodes), "total_edges": len(self.edges)}
        
        # Count nodes by type
        for node in self.nodes.values():
            node_type = type(node).__name__
            stats[f"{node_type}_count"] = stats.get(f"{node_type}_count", 0) + 1
        
        # Count edges by type  
        for edge in self.edges:
            edge_type = type(edge).__name__
            stats[f"{edge_type}_count"] = stats.get(f"{edge_type}_count", 0) + 1
        
        return stats
