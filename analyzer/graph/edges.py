"""
Graph Edge Classes - Atlas Rewrite

Specialized edge classes for different relationships between code entities.
"""

from typing import Dict, Any
from dataclasses import dataclass
from .base import Edge


# Structural relationships (reconnaissance phase)

@dataclass
class HasPackageEdge(Edge):
    """Project has package relationship."""
    pass


@dataclass
class HasModuleEdge(Edge):
    """Package/project has module relationship."""
    pass


@dataclass
class HasClassEdge(Edge):
    """Module has class relationship."""
    pass


@dataclass
class HasFunctionEdge(Edge):
    """Module/class has function relationship."""
    pass


@dataclass
class HasImportEdge(Edge):
    """Module has import relationship."""
    pass


@dataclass
class HasStateEdge(Edge):
    """Module has state variable relationship."""
    pass


@dataclass
class HasArgumentEdge(Edge):
    """Function has argument relationship."""
    pass


@dataclass
class HasAttributeEdge(Edge):
    """Class has attribute relationship."""
    pass


@dataclass
class InheritsFromEdge(Edge):
    """Class inherits from another class."""
    pass


# Behavioral relationships (analysis phase)

@dataclass
class CallsMethodEdge(Edge):
    """Function calls another method/function."""
    pass


@dataclass
class AccessesStateEdge(Edge):
    """Function accesses state variable."""
    pass


@dataclass
class InstantiatesClassEdge(Edge):
    """Function instantiates a class."""
    pass


@dataclass
class ReturnsTypeEdge(Edge):
    """Function returns specific type."""
    pass


@dataclass
class ParameterTypeEdge(Edge):
    """Function parameter has specific type."""
    pass
