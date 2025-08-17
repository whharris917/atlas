"""
Specialized AST Visitors

Focused visitors for specific analysis and reconnaissance concerns.

Phase 1 visitors handle analysis pass specialization:
- EmitVisitor: SocketIO emit detection and context tracking
- CallVisitor: Method call analysis and chain resolution
- AssignmentVisitor: Variable assignment tracking and state management

Phase 2 visitors handle reconnaissance pass specialization:
- ImportReconVisitor: Import processing and external library detection
- ClassReconVisitor: Class definition and inheritance tracking
- FunctionReconVisitor: Function/method definition and signature extraction
- StateReconVisitor: Module state variables and assignments

Part of the Atlas refactoring project to modularize analysis components.
"""

# Phase 1 - Analysis specialized visitors
from .emit_visitor import EmitVisitor
from .call_visitor import CallVisitor  
from .assignment_visitor import AssignmentVisitor

# Phase 2 - Reconnaissance specialized visitors
from .import_recon_visitor import ImportReconVisitor
from .class_recon_visitor import ClassReconVisitor
from .function_recon_visitor import FunctionReconVisitor
from .state_recon_visitor import StateReconVisitor

__all__ = [
    # Phase 1 - Analysis visitors
    'EmitVisitor',
    'CallVisitor',
    'AssignmentVisitor',
    # Phase 2 - Reconnaissance visitors
    'ImportReconVisitor',
    'ClassReconVisitor',
    'FunctionReconVisitor',
    'StateReconVisitor'
]
