"""
Specialized Visitors Package - Code Atlas

This package contains all specialized visitor implementations for the refactored Atlas system.

Resolution Visitors (Phase 3):
- SimpleResolutionVisitor: Basic single-name resolution
- ChainResolutionVisitor: Complex attribute chain resolution  
- InheritanceResolutionVisitor: Inheritance-based resolution
- ExternalResolutionVisitor: External library resolution

Analysis Visitors (Phase 1):
- EmitVisitor: SocketIO emit detection
- CallVisitor: Method call analysis
- AssignmentVisitor: Variable assignment tracking

Reconnaissance Visitors (Phase 2):  
- ImportReconVisitor: Import statement processing
- ClassReconVisitor: Class definition processing
- FunctionReconVisitor: Function/method processing
- StateReconVisitor: Module state processing
"""

# Resolution visitors (Phase 3) - import with error handling
try:
    from .simple_resolution_visitor import SimpleResolutionVisitor
except ImportError:
    SimpleResolutionVisitor = None

try:
    from .chain_resolution_visitor import ChainResolutionVisitor
except ImportError:
    ChainResolutionVisitor = None

try:
    from .inheritance_resolution_visitor import InheritanceResolutionVisitor
except ImportError:
    InheritanceResolutionVisitor = None

try:
    from .external_resolution_visitor import ExternalResolutionVisitor
except ImportError:
    ExternalResolutionVisitor = None

# Analysis visitors (Phase 1) - import with error handling
try:
    from .emit_visitor import EmitVisitor
except ImportError:
    EmitVisitor = None

try:
    from .call_visitor import CallVisitor
except ImportError:
    CallVisitor = None

try:
    from .assignment_visitor import AssignmentVisitor
except ImportError:
    AssignmentVisitor = None

# Reconnaissance visitors (Phase 2) - import with error handling
try:
    from .import_recon_visitor import ImportReconVisitor
except ImportError:
    ImportReconVisitor = None

try:
    from .class_recon_visitor import ClassReconVisitor
except ImportError:
    ClassReconVisitor = None

try:
    from .function_recon_visitor import FunctionReconVisitor
except ImportError:
    FunctionReconVisitor = None

try:
    from .state_recon_visitor import StateReconVisitor
except ImportError:
    StateReconVisitor = None

# Only export visitors that were successfully imported
__all__ = []

# Resolution visitors
if SimpleResolutionVisitor:
    __all__.append('SimpleResolutionVisitor')
if ChainResolutionVisitor:
    __all__.append('ChainResolutionVisitor')
if InheritanceResolutionVisitor:
    __all__.append('InheritanceResolutionVisitor')
if ExternalResolutionVisitor:
    __all__.append('ExternalResolutionVisitor')

# Analysis visitors
if EmitVisitor:
    __all__.append('EmitVisitor')
if CallVisitor:
    __all__.append('CallVisitor')
if AssignmentVisitor:
    __all__.append('AssignmentVisitor')

# Reconnaissance visitors
if ImportReconVisitor:
    __all__.append('ImportReconVisitor')
if ClassReconVisitor:
    __all__.append('ClassReconVisitor')
if FunctionReconVisitor:
    __all__.append('FunctionReconVisitor')
if StateReconVisitor:
    __all__.append('StateReconVisitor')
