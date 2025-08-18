# session_manager.py
"""
Session management system with complex state tracking and method chaining patterns.
Tests complex object relationships and cross-module dependencies.
"""
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import threading
from contextlib import contextmanager
from enum import Enum, auto

from decorators import trace, monitor_performance, validate_auth, rate_limit
from proxy_handler import HavenProxy, UserProxy, DataProxy

class SessionState(Enum):
    """Session state enumeration."""
    CREATED = auto()
    ACTIVE = auto()
    IDLE = auto()
    SUSPENDED = auto()
    EXPIRED = auto()
    TERMINATED = auto()

class UserRole(Enum):
    """User role enumeration."""
    GUEST = auto()
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()
    SYSTEM = auto()

@dataclass
class SessionMetrics:
    """Session metrics container."""
    login_time: datetime
    last_activity: datetime
    activity_count: int = 0
    data_transferred: int = 0
    errors_encountered: int = 0
    warnings_issued: int = 0
    rooms_joined: Set[str] = field(default_factory=set)
    events_emitted: int = 0
    events_received: int = 0

@dataclass
class UserSession:
    """User session data container with complex relationships."""
    session_id: str
    user_id: str
    user_role: UserRole
    state: SessionState
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    permissions: Set[str] = field(default_factory=set)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metrics: SessionMetrics = field(default_factory=lambda: SessionMetrics(datetime.now(), datetime.now()))
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if session is valid."""
        return (self.state in [SessionState.ACTIVE, SessionState.IDLE] and 
                datetime.now() < self.expires_at)
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() >= self.expires_at
    
    def time_until_expiry(self) -> timedelta:
        """Get time until session expires."""
        return self.expires_at - datetime.now()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.metrics.last_activity = self.last_activity
        self.metrics.activity_count += 1

class SessionManager:
    """Comprehensive session management with complex state tracking."""
    
    def __init__(self, haven_proxy: HavenProxy):
        self.haven_proxy = haven_proxy
        self.active_sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self.session_lock = threading.RLock()
        self.current_session_id: Optional[str] = None
        self.session_callbacks: Dict[str, List[Callable]] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.max_sessions_per_user = 3
        
        # Session event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'session_created': [],
            'session_expired': [],
            'session_terminated': [],
            'user_authenticated': [],
            'user_logout': [],
            'session_activity': []
        }
    
    @trace
    def create_session(self, user_id: Optional[str] = None, 
                      session_duration: timedelta = timedelta(hours=24),
                      ip_address: str = "unknown",
                      user_agent: str = "unknown") -> str:
        """Create new session with comprehensive setup."""
        session_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Determine user role
        if user_id:
            user_role = self._determine_user_role(user_id)
        else:
            user_role = UserRole.GUEST
            user_id = f"guest_{session_id[:8]}"
        
        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            state=SessionState.CREATED,
            created_at=current_time,
            expires_at=current_time + session_duration,
            last_activity=current_time,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Set permissions based on role
        session.permissions = self._get_role_permissions(user_role)
        
        # Load user preferences
        if user_id and self.haven_proxy.user_exists(user_id):
            session.preferences = self.haven_proxy.get_user_preferences(user_id)
        
        with self.session_lock:
            # Check session limits
            if user_id in self.user_sessions:
                if len(self.user_sessions[user_id]) >= self.max_sessions_per_user:
                    # Remove oldest session
                    oldest_session_id = self.user_sessions[user_id].pop(0)
                    if oldest_session_id in self.active_sessions:
                        self._terminate_session(oldest_session_id, "session_limit_exceeded")
            
            # Register session
            self.active_sessions[session_id] = session
            
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
            
            # Set as current session if none set
            if not self.current_session_id:
                self.current_session_id = session_id
        
        # Trigger session created event
        self._trigger_event('session_created', session)
        
        return session_id
    
    @trace
    @monitor_performance
    def create_user_session(self, user_id: str, session_id: str) -> UserSession:
        """Create authenticated user session with validation."""
        if not self.haven_proxy.validate_user_credentials({'user_id': user_id}):
            raise ValueError(f"Invalid user credentials for {user_id}")
        
        with self.session_lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Update session for authenticated user
            session.user_id = user_id
            session.user_role = self._determine_user_role(user_id)
            session.state = SessionState.ACTIVE
            session.permissions = self._get_role_permissions(session.user_role)
            session.preferences = self.haven_proxy.get_user_preferences(user_id)
            session.update_activity()
            
            # Update user session tracking
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            if session_id not in self.user_sessions[user_id]:
                self.user_sessions[user_id].append(session_id)
        
        # Trigger authentication event
        self._trigger_event('user_authenticated', session)
        
        return session
    
    @trace
    def get_current_session(self) -> Optional[UserSession]:
        """Get current active session."""
        if not self.current_session_id:
            return None
        
        with self.session_lock:
            session = self.active_sessions.get(self.current_session_id)
            if session and session.is_valid():
                session.update_activity()
                self._trigger_event('session_activity', session)
                return session
            elif session and session.is_expired():
                self._expire_session(self.current_session_id)
        
        return None
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID."""
        session = self.get_current_session()
        return session.session_id if session else None
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID."""
        session = self.get_current_session()
        return session.user_id if session else None
    
    def get_current_user(self) -> Optional[Any]:
        """Get current user object."""
        user_id = self.get_current_user_id()
        if user_id:
            return self.haven_proxy.get_user_info(user_id)
        return None
    
    def get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    @trace
    def validate_session(self, session_id: str) -> bool:
        """Validate session and update activity."""
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            if session.is_expired():
                self._expire_session(session_id)
                return False
            
            if session.is_valid():
                session.update_activity()
                self._trigger_event('session_activity', session)
                return True
        
        return False
    
    @validate_auth(required_role='user')
    def validate_room_access(self, room_name: str) -> bool:
        """Validate room access for current user."""
        session = self.get_current_session()
        if not session:
            return False
        
        # Check with haven proxy
        access_granted = self.haven_proxy.validate_room_access(session.user_id, room_name)
        
        if access_granted:
            session.metrics.rooms_joined.add(room_name)
            session.context_data[f"room_{room_name}_joined"] = datetime.now()
        
        return access_granted
    
    def get_user_room(self, user_id: Optional[str] = None) -> str:
        """Get user-specific room name."""
        if user_id is None:
            user_id = self.get_current_user_id()
        
        if user_id:
            return f"user_{user_id}"
        
        return "anonymous"
    
    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get all rooms for a user."""
        with self.session_lock:
            rooms = []
            for session_id in self.user_sessions.get(user_id, []):
                session = self.active_sessions.get(session_id)
                if session:
                    rooms.extend(list(session.metrics.rooms_joined))
            
            # Add user's personal room
            rooms.append(self.get_user_room(user_id))
            
            return list(set(rooms))  # Remove duplicates
    
    def get_active_users(self) -> List[str]:
        """Get list of active user IDs."""
        with self.session_lock:
            active_users = set()
            for session in self.active_sessions.values():
                if session.is_valid() and session.user_role != UserRole.GUEST:
                    active_users.add(session.user_id)
            
            return list(active_users)
    
    @trace
    def cleanup_user_session(self, user_id: str) -> None:
        """Cleanup all sessions for a user."""
        with self.session_lock:
            session_ids = self.user_sessions.get(user_id, []).copy()
            
            for session_id in session_ids:
                if session_id in self.active_sessions:
                    session = self.active_sessions[session_id]
                    session.state = SessionState.TERMINATED
                    self._trigger_event('user_logout', session)
                    
                    # Remove from active sessions
                    del self.active_sessions[session_id]
            
            # Clear user session tracking
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
    
    @trace
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a specific session."""
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            user_id = session.user_id
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Remove from user session tracking
            if user_id in self.user_sessions:
                if session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
                
                # Clean up empty user session list
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            # Update current session if this was it
            if self.current_session_id == session_id:
                self.current_session_id = None
            
            # Mark as terminated
            session.state = SessionState.TERMINATED
            self._trigger_event('session_terminated', session)
            
            return True
    
    def _determine_user_role(self, user_id: str) -> UserRole:
        """Determine user role based on user ID."""
        if self.haven_proxy.validate_admin_role(user_id):
            return UserRole.ADMIN
        elif self.haven_proxy.validate_moderator_role(user_id):
            return UserRole.MODERATOR
        elif user_id.startswith('guest_'):
            return UserRole.GUEST
        else:
            return UserRole.USER
    
    def _get_role_permissions(self, role: UserRole) -> Set[str]:
        """Get permissions for a user role."""
        base_permissions = {'read_public', 'join_public_rooms'}
        
        if role == UserRole.GUEST:
            return base_permissions
        elif role == UserRole.USER:
            return base_permissions | {'write_messages', 'join_private_rooms', 'create_rooms'}
        elif role == UserRole.MODERATOR:
            return base_permissions | {'write_messages', 'join_private_rooms', 'create_rooms', 
                                     'moderate_rooms', 'ban_users', 'delete_messages'}
        elif role == UserRole.ADMIN:
            return base_permissions | {'write_messages', 'join_private_rooms', 'create_rooms',
                                     'moderate_rooms', 'ban_users', 'delete_messages',
                                     'admin_panel', 'manage_users', 'system_config'}
        elif role == UserRole.SYSTEM:
            return {'all_permissions'}
        else:
            return base_permissions
    
    def _expire_session(self, session_id: str) -> None:
        """Mark session as expired."""
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if session:
                session.state = SessionState.EXPIRED
                self._trigger_event('session_expired', session)
    
    def _terminate_session(self, session_id: str, reason: str) -> None:
        """Terminate session with reason."""
        with self.session_lock:
            session = self.active_sessions.get(session_id)
            if session:
                session.state = SessionState.TERMINATED
                session.context_data['termination_reason'] = reason
                self._trigger_event('session_terminated', session)
                
                # Remove from active sessions
                self.destroy_session(session_id)
    
    def _trigger_event(self, event_name: str, session: UserSession) -> None:
        """Trigger session event handlers."""
        for handler in self.event_handlers.get(event_name, []):
            try:
                handler(session)
            except Exception as e:
                # Log error but don't fail session operation
                print(f"Error in session event handler {event_name}: {e}")
    
    @trace
    @rate_limit(calls=100, period=60)
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        with self.session_lock:
            total_sessions = len(self.active_sessions)
            active_sessions = sum(1 for s in self.active_sessions.values() if s.state == SessionState.ACTIVE)
            idle_sessions = sum(1 for s in self.active_sessions.values() if s.state == SessionState.IDLE)
            
            # User role distribution
            role_distribution = {}
            for role in UserRole:
                role_distribution[role.name] = sum(1 for s in self.active_sessions.values() if s.user_role == role)
            
            # Activity metrics
            total_activity = sum(s.metrics.activity_count for s in self.active_sessions.values())
            total_data_transferred = sum(s.metrics.data_transferred for s in self.active_sessions.values())
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'idle_sessions': idle_sessions,
                'role_distribution': role_distribution,
                'total_activity': total_activity,
                'total_data_transferred': total_data_transferred,
                'unique_users': len(self.user_sessions)
            }
    
    @contextmanager
    def session_context(self, session_id: str):
        """Context manager for session operations."""
        original_session_id = self.current_session_id
        self.current_session_id = session_id
        
        try:
            yield self.get_current_session()
        finally:
            self.current_session_id = original_session_id
    
    def add_session_event_handler(self, event_name: str, handler: Callable) -> None:
        """Add event handler for session events."""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        
        self.event_handlers[event_name].append(handler)
    
    @monitor_performance
    def periodic_cleanup(self) -> Dict[str, int]:
        """Perform periodic cleanup of expired sessions."""
        expired_count = 0
        idle_count = 0
        
        with self.session_lock:
            sessions_to_expire = []
            sessions_to_idle = []
            
            current_time = datetime.now()
            
            for session_id, session in self.active_sessions.items():
                if session.is_expired():
                    sessions_to_expire.append(session_id)
                elif (session.state == SessionState.ACTIVE and 
                      current_time - session.last_activity > timedelta(minutes=30)):
                    sessions_to_idle.append(session_id)
            
            # Expire sessions
            for session_id in sessions_to_expire:
                self._expire_session(session_id)
                expired_count += 1
            
            # Mark idle sessions
            for session_id in sessions_to_idle:
                session = self.active_sessions[session_id]
                session.state = SessionState.IDLE
                idle_count += 1
        
        return {
            'expired_sessions': expired_count,
            'idle_sessions': idle_count
        }

# Global session management functions for testing
_global_session_manager: Optional[SessionManager] = None

def initialize_session_manager(haven_proxy: HavenProxy) -> SessionManager:
    """Initialize global session manager."""
    global _global_session_manager
    _global_session_manager = SessionManager(haven_proxy)
    return _global_session_manager

def get_current_session() -> Optional[UserSession]:
    """Get current session from global manager."""
    if _global_session_manager:
        return _global_session_manager.get_current_session()
    return None

def get_current_user() -> Optional[Any]:
    """Get current user from global manager."""
    if _global_session_manager:
        return _global_session_manager.get_current_user()
    return None

def get_current_user_id() -> Optional[str]:
    """Get current user ID from global manager."""
    if _global_session_manager:
        return _global_session_manager.get_current_user_id()
    return None

# Complex session interaction patterns for testing
class SessionInteractionManager:
    """Manages complex session interactions and cross-references."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.interaction_log: List[Dict[str, Any]] = []
        self.user_relationships: Dict[str, Set[str]] = {}
        self.session_analytics = SessionAnalytics(session_manager)
    
    @trace
    def record_user_interaction(self, user1_id: str, user2_id: str, 
                               interaction_type: str, data: Dict[str, Any]) -> None:
        """Record interaction between users."""
        interaction = {
            'timestamp': datetime.now(),
            'user1': user1_id,
            'user2': user2_id,
            'type': interaction_type,
            'data': data
        }
        
        self.interaction_log.append(interaction)
        
        # Update relationships
        if user1_id not in self.user_relationships:
            self.user_relationships[user1_id] = set()
        if user2_id not in self.user_relationships:
            self.user_relationships[user2_id] = set()
        
        self.user_relationships[user1_id].add(user2_id)
        self.user_relationships[user2_id].add(user1_id)
        
        # Update session metrics
        session1 = self._get_user_session(user1_id)
        session2 = self._get_user_session(user2_id)
        
        if session1:
            session1.metrics.events_emitted += 1
        if session2:
            session2.metrics.events_received += 1
    
    def _get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get active session for user."""
        with self.session_manager.session_lock:
            for session_id in self.session_manager.user_sessions.get(user_id, []):
                session = self.session_manager.active_sessions.get(session_id)
                if session and session.is_valid():
                    return session
        return None

class SessionAnalytics:
    """Advanced session analytics with complex computations."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.analytics_cache: Dict[str, Any] = {}
        
    @trace
    @monitor_performance
    def compute_user_engagement_score(self, user_id: str) -> float:
        """Compute complex user engagement score."""
        session = self._get_user_session(user_id)
        if not session:
            return 0.0
        
        # Complex engagement calculation
        activity_score = min(session.metrics.activity_count / 100.0, 1.0)
        room_diversity = len(session.metrics.rooms_joined) / 10.0
        interaction_ratio = (session.metrics.events_emitted + session.metrics.events_received) / max(session.metrics.activity_count, 1)
        
        # Time-based factors
        session_duration = (datetime.now() - session.created_at).total_seconds() / 3600  # hours
        duration_factor = min(session_duration / 24.0, 1.0)  # Cap at 24 hours
        
        engagement_score = (activity_score * 0.4 + 
                          room_diversity * 0.2 + 
                          interaction_ratio * 0.3 + 
                          duration_factor * 0.1)
        
        return min(engagement_score, 1.0)
    
    def _get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get active session for analytics."""
        with self.session_manager.session_lock:
            for session_id in self.session_manager.user_sessions.get(user_id, []):
                session = self.session_manager.active_sessions.get(session_id)
                if session and session.is_valid():
                    return session
        return None
