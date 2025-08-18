# socketio_events.py
"""
SocketIO event handling with complex decorator patterns and dynamic event registration.
Ultimate stress test for SocketIO.on() and SocketIO.emit() analysis.
"""
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps
import logging
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from decorators import trace, monitor_performance, validate_auth, rate_limit
from session_manager import SessionManager, UserSession
from proxy_handler import HavenProxy, DataProxy
from event_validator import EventValidator, MessageValidator

# Global state for complex SocketIO scenarios
_socketio_instance: Optional[SocketIO] = None
_haven_proxy: Optional[HavenProxy] = None
_session_manager: Optional[SessionManager] = None
EVENT_HANDLERS: Dict[str, Callable] = {}
ACTIVE_ROOMS: Dict[str, List[str]] = {}

class SocketIOEventRegistry:
    """Registry for dynamic SocketIO event management with complex patterns."""
    
    def __init__(self, socketio: SocketIO, session_manager: SessionManager):
        self.socketio = socketio
        self.session_manager = session_manager
        self.event_validator = EventValidator()
        self.message_validator = MessageValidator()
        self.registered_events: Dict[str, Callable] = {}
        self.middleware_stack: List[Callable] = []
    
    @trace
    @monitor_performance
    def register_dynamic_event(self, event_name: str, handler: Callable) -> None:
        """Register event handler dynamically with full decorator chain."""
        
        @self.socketio.on(event_name)
        @trace
        @validate_auth
        @rate_limit(calls=10, period=60)
        def wrapped_handler(*args, **kwargs):
            """Dynamically created handler with full middleware."""
            # Complex nested socketio.emit calls
            self.socketio.emit('event_received', {
                'event': event_name,
                'timestamp': self.session_manager.get_current_timestamp(),
                'session_id': self.session_manager.get_current_session_id()
            })
            
            # Call original handler with chained method calls
            result = handler(*args, **kwargs)
            
            # Conditional emit with complex data
            if self.event_validator.validate_result(result):
                self.socketio.emit(f'{event_name}_success', {
                    'result': result,
                    'validation': self.event_validator.get_validation_details()
                }, room=self.session_manager.get_user_room())
            
            return result
        
        self.registered_events[event_name] = wrapped_handler
    
    def batch_register_events(self, event_configs: List[Dict[str, Any]]) -> None:
        """Batch registration with complex SocketIO patterns."""
        for config in event_configs:
            event_name = config['name']
            
            # Factory pattern for event handlers
            handler = self.create_event_handler(config)
            
            # Dynamic decorator application
            decorated_handler = self.apply_middleware_stack(handler, config.get('middleware', []))
            
            # SocketIO registration with complex patterns
            self.socketio.on(event_name)(decorated_handler)
    
    def create_event_handler(self, config: Dict[str, Any]) -> Callable:
        """Factory method creating handlers with embedded SocketIO calls."""
        event_type = config.get('type', 'standard')
        
        if event_type == 'room_based':
            return self._create_room_handler(config)
        elif event_type == 'broadcast':
            return self._create_broadcast_handler(config)
        elif event_type == 'authenticated':
            return self._create_auth_handler(config)
        else:
            return self._create_standard_handler(config)
    
    def _create_room_handler(self, config: Dict[str, Any]) -> Callable:
        """Create room-based handler with complex SocketIO operations."""
        
        @trace
        def room_handler(data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle room-based events with multiple SocketIO calls."""
            room_name = data.get('room', 'default')
            
            # Join room with validation
            if self.session_manager.validate_room_access(room_name):
                join_room(room_name)
                
                # Emit to specific room
                self.socketio.emit('user_joined_room', {
                    'user_id': self.session_manager.get_current_user_id(),
                    'room': room_name,
                    'timestamp': self.session_manager.get_current_timestamp()
                }, room=room_name)
                
                # Emit to all rooms
                for active_room in ACTIVE_ROOMS.get(room_name, []):
                    self.socketio.emit('room_activity', {
                        'source_room': room_name,
                        'activity_type': 'user_join'
                    }, room=active_room)
            
            return {'status': 'success', 'room': room_name}
        
        return room_handler
    
    def _create_broadcast_handler(self, config: Dict[str, Any]) -> Callable:
        """Create broadcast handler with complex emit patterns."""
        
        @monitor_performance
        @validate_auth
        def broadcast_handler(data: Dict[str, Any]) -> None:
            """Handle broadcast events with multiple emit strategies."""
            message = data.get('message', '')
            
            # Validate message
            if self.message_validator.validate_message(message):
                # Global broadcast
                self.socketio.emit('global_message', {
                    'message': message,
                    'sender': self.session_manager.get_current_user_id(),
                    'timestamp': self.session_manager.get_current_timestamp()
                }, broadcast=True)
                
                # Targeted broadcasts
                for user_id in self.session_manager.get_active_users():
                    user_room = self.session_manager.get_user_room(user_id)
                    
                    # Personalized emit to each user
                    self.socketio.emit('personal_message', {
                        'message': message,
                        'personalized': True,
                        'recipient': user_id
                    }, room=user_room)
        
        return broadcast_handler

@trace
def register_events(socketio: SocketIO, haven_proxy: HavenProxy) -> None:
    """
    Primary event registration function with complex SocketIO patterns.
    Ultimate stress test for decorator analysis and SocketIO emit tracking.
    """
    global _socketio_instance, _haven_proxy, _session_manager
    
    _socketio_instance = socketio
    _haven_proxy = haven_proxy
    _session_manager = SessionManager(haven_proxy)
    
    # Create registry for dynamic events
    registry = SocketIOEventRegistry(socketio, _session_manager)
    
    @socketio.on("connect")
    @trace
    @monitor_performance
    def handle_connect(auth: Optional[Dict[str, Any]] = None) -> None:
        """Handle client connection with complex authentication and session setup."""
        session_id = _session_manager.create_session()
        
        if auth and auth.get('is_runner'):
            logging.info("Connection from scenario runner detected.")
            
            # Special runner handling with multiple emits
            socketio.emit('runner_connected', {
                'session_id': session_id,
                'capabilities': _haven_proxy.get_runner_capabilities(),
                'timestamp': _session_manager.get_current_timestamp()
            })
            
            # Join special runner room
            join_room('runners')
            socketio.emit('runner_room_joined', {
                'session_id': session_id
            }, room='runners')
        
        elif auth and _haven_proxy.validate_user_credentials(auth):
            user_id = auth.get('user_id')
            
            # Standard user connection
            user_session = _session_manager.create_user_session(user_id, session_id)
            
            # Complex emit chain
            socketio.emit('connection_established', {
                'session_id': session_id,
                'user_id': user_id,
                'preferences': _haven_proxy.get_user_preferences(user_id)
            })
            
            # Join user-specific room
            user_room = f"user_{user_id}"
            join_room(user_room)
            
            # Notify other users
            socketio.emit('user_connected', {
                'user_id': user_id,
                'timestamp': _session_manager.get_current_timestamp()
            }, broadcast=True, include_self=False)
        
        else:
            # Guest connection
            socketio.emit('guest_connected', {
                'session_id': session_id,
                'limitations': _haven_proxy.get_guest_limitations()
            })
    
    @socketio.on("disconnect")
    @trace
    def handle_disconnect() -> None:
        """Handle client disconnection with cleanup and notifications."""
        session_id = _session_manager.get_current_session_id()
        user_id = _session_manager.get_current_user_id()
        
        if user_id:
            # User disconnection
            _session_manager.cleanup_user_session(user_id)
            
            # Notify remaining users
            socketio.emit('user_disconnected', {
                'user_id': user_id,
                'timestamp': _session_manager.get_current_timestamp()
            }, broadcast=True)
            
            # Leave all rooms
            for room in _session_manager.get_user_rooms(user_id):
                leave_room(room)
                socketio.emit('user_left_room', {
                    'user_id': user_id,
                    'room': room
                }, room=room)
        
        _session_manager.destroy_session(session_id)
    
    @socketio.on("join_room")
    @trace
    @validate_auth
    @rate_limit(calls=5, period=30)
    def handle_join_room(data: Dict[str, Any]) -> None:
        """Handle room joining with complex validation and notifications."""
        room_name = data.get('room')
        user_id = _session_manager.get_current_user_id()
        
        if _haven_proxy.validate_room_access(user_id, room_name):
            join_room(room_name)
            
            # Multiple emit patterns
            socketio.emit('room_joined', {
                'room': room_name,
                'user_id': user_id,
                'timestamp': _session_manager.get_current_timestamp()
            })
            
            # Notify room members
            socketio.emit('new_room_member', {
                'user_id': user_id,
                'user_info': _haven_proxy.get_user_info(user_id)
            }, room=room_name)
            
            # Update room statistics
            room_stats = _haven_proxy.get_room_statistics(room_name)
            socketio.emit('room_stats_updated', room_stats, room=room_name)
    
    @socketio.on("send_message")
    @trace
    @validate_auth
    @rate_limit(calls=20, period=60)
    def handle_send_message(data: Dict[str, Any]) -> None:
        """Handle message sending with complex routing and validation."""
        message = data.get('message', '')
        target_type = data.get('target_type', 'room')
        target = data.get('target')
        
        user_id = _session_manager.get_current_user_id()
        
        # Validate message
        if not _haven_proxy.validate_message_content(message, user_id):
            socketio.emit('message_rejected', {
                'reason': 'Content validation failed',
                'timestamp': _session_manager.get_current_timestamp()
            })
            return
        
        # Process message based on target type
        if target_type == 'room':
            # Room message
            if _haven_proxy.validate_room_access(user_id, target):
                socketio.emit('room_message', {
                    'message': message,
                    'sender': user_id,
                    'sender_info': _haven_proxy.get_user_info(user_id),
                    'timestamp': _session_manager.get_current_timestamp()
                }, room=target)
                
                # Log message
                _haven_proxy.log_room_message(target, user_id, message)
        
        elif target_type == 'user':
            # Direct message
            if _haven_proxy.validate_direct_message_permission(user_id, target):
                target_room = f"user_{target}"
                
                socketio.emit('direct_message', {
                    'message': message,
                    'sender': user_id,
                    'sender_info': _haven_proxy.get_user_info(user_id),
                    'timestamp': _session_manager.get_current_timestamp()
                }, room=target_room)
                
                # Confirm to sender
                socketio.emit('message_delivered', {
                    'target': target,
                    'timestamp': _session_manager.get_current_timestamp()
                })
        
        elif target_type == 'broadcast':
            # Broadcast message (admin only)
            if _haven_proxy.validate_broadcast_permission(user_id):
                socketio.emit('broadcast_message', {
                    'message': message,
                    'sender': user_id,
                    'timestamp': _session_manager.get_current_timestamp()
                }, broadcast=True)
    
    # Complex dynamic event registration
    dynamic_events = [
        {
            'name': 'data_sync',
            'type': 'authenticated',
            'middleware': ['trace', 'validate_auth', 'rate_limit']
        },
        {
            'name': 'room_broadcast',
            'type': 'room_based',
            'middleware': ['trace', 'monitor_performance']
        },
        {
            'name': 'system_announce',
            'type': 'broadcast',
            'middleware': ['trace', 'validate_auth']
        }
    ]
    
    # Register dynamic events
    registry.batch_register_events(dynamic_events)
    
    # Register individual dynamic handlers
    for event_name in ['user_action', 'data_update', 'status_change']:
        registry.register_dynamic_event(
            event_name,
            create_dynamic_handler(event_name, _haven_proxy, _session_manager)
        )

@trace
@monitor_performance
def create_dynamic_handler(event_name: str, proxy: HavenProxy, session_manager: SessionManager) -> Callable:
    """Factory function creating dynamic handlers with embedded SocketIO calls."""
    
    def dynamic_handler(data: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically created handler with complex SocketIO emit patterns."""
        user_id = session_manager.get_current_user_id()
        
        # Validate and process data
        if proxy.validate_event_data(event_name, data, user_id):
            # Process the event
            result = proxy.process_event(event_name, data, user_id)
            
            # Complex emit based on result
            if result.get('success'):
                _socketio_instance.emit(f'{event_name}_processed', {
                    'result': result,
                    'user_id': user_id,
                    'timestamp': session_manager.get_current_timestamp()
                })
                
                # Conditional additional emits
                if result.get('notify_others'):
                    _socketio_instance.emit(f'{event_name}_notification', {
                        'source_user': user_id,
                        'data': result.get('notification_data')
                    }, broadcast=True, include_self=False)
                
                if result.get('update_room'):
                    room_name = result.get('room')
                    _socketio_instance.emit(f'{event_name}_room_update', {
                        'update_data': result.get('room_data')
                    }, room=room_name)
            
            return result
        else:
            # Emit error
            _socketio_instance.emit(f'{event_name}_error', {
                'error': 'Validation failed',
                'user_id': user_id,
                'timestamp': session_manager.get_current_timestamp()
            })
            
            return {'success': False, 'error': 'Validation failed'}
    
    return dynamic_handler

# Module-level SocketIO emit calls for testing
def emergency_broadcast(message: str, severity: str = 'high') -> None:
    """Emergency broadcast function using global SocketIO instance."""
    if _socketio_instance and _haven_proxy:
        _socketio_instance.emit('emergency_broadcast', {
            'message': message,
            'severity': severity,
            'timestamp': _session_manager.get_current_timestamp(),
            'source': 'system'
        }, broadcast=True)

def admin_notification(admin_id: str, notification: Dict[str, Any]) -> None:
    """Send notification to specific admin."""
    if _socketio_instance and _haven_proxy.validate_admin_role(admin_id):
        admin_room = f"admin_{admin_id}"
        _socketio_instance.emit('admin_notification', notification, room=admin_room)
