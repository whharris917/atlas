# database_manager.py
"""
Database management module for transaction handling and connection management.
Provides mock database functionality for testing decorator patterns.
"""
from typing import Any, Optional, Dict, List
from contextlib import contextmanager
import threading
import time
import logging

class DatabaseConnection:
    """Mock database connection for testing purposes."""
    
    def __init__(self, connection_id: str = "mock_conn"):
        self.connection_id = connection_id
        self.is_open = True
        self.in_transaction = False
        self.isolation_level = "READ_COMMITTED"
        self.query_count = 0
        self.last_query_time = time.time()
        self.lock = threading.RLock()
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a database query."""
        with self.lock:
            if not self.is_open:
                raise RuntimeError("Connection is closed")
            
            self.query_count += 1
            self.last_query_time = time.time()
            
            logging.debug(f"Executing query on {self.connection_id}: {query}")
            
            # Mock query execution
            if query.upper().startswith("SELECT"):
                return []
            elif query.upper().startswith(("INSERT", "UPDATE", "DELETE")):
                return 1  # Affected rows
            else:
                return None
    
    def commit(self) -> None:
        """Commit current transaction."""
        with self.lock:
            if not self.is_open:
                raise RuntimeError("Connection is closed")
            
            if self.in_transaction:
                logging.debug(f"Committing transaction on {self.connection_id}")
                self.in_transaction = False
            else:
                logging.warning(f"No active transaction to commit on {self.connection_id}")
    
    def rollback(self) -> None:
        """Rollback current transaction."""
        with self.lock:
            if not self.is_open:
                raise RuntimeError("Connection is closed")
            
            if self.in_transaction:
                logging.debug(f"Rolling back transaction on {self.connection_id}")
                self.in_transaction = False
            else:
                logging.warning(f"No active transaction to rollback on {self.connection_id}")
    
    def begin_transaction(self, isolation_level: Optional[str] = None) -> None:
        """Begin a new transaction."""
        with self.lock:
            if not self.is_open:
                raise RuntimeError("Connection is closed")
            
            if self.in_transaction:
                raise RuntimeError("Transaction already in progress")
            
            if isolation_level:
                self.isolation_level = isolation_level
            
            self.in_transaction = True
            logging.debug(f"Beginning transaction on {self.connection_id} with isolation {self.isolation_level}")
    
    def close(self) -> None:
        """Close the database connection."""
        with self.lock:
            if self.is_open:
                if self.in_transaction:
                    logging.warning(f"Closing connection {self.connection_id} with active transaction - rolling back")
                    self.rollback()
                
                self.is_open = False
                logging.debug(f"Closed connection {self.connection_id}")
    
    def is_connected(self) -> bool:
        """Check if connection is still open."""
        return self.is_open
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            'connection_id': self.connection_id,
            'is_open': self.is_open,
            'in_transaction': self.in_transaction,
            'isolation_level': self.isolation_level,
            'query_count': self.query_count,
            'last_query_time': self.last_query_time
        }

class TransactionManager:
    """Transaction manager for handling database transactions with various isolation levels."""
    
    def __init__(self, connection: DatabaseConnection, isolation_level: str = "READ_COMMITTED"):
        self.connection = connection
        self.isolation_level = isolation_level
        self.transaction_started = False
        self.start_time: Optional[float] = None
        self.operations_count = 0
    
    def begin_transaction(self) -> None:
        """Begin a new database transaction."""
        if self.transaction_started:
            raise RuntimeError("Transaction already started")
        
        try:
            self.connection.begin_transaction(self.isolation_level)
            self.transaction_started = True
            self.start_time = time.time()
            self.operations_count = 0
            logging.info(f"Transaction started with isolation level: {self.isolation_level}")
        
        except Exception as e:
            logging.error(f"Failed to begin transaction: {e}")
            raise
    
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self.transaction_started:
            raise RuntimeError("No transaction to commit")
        
        try:
            self.connection.commit()
            duration = time.time() - self.start_time if self.start_time else 0
            logging.info(f"Transaction committed successfully. Duration: {duration:.3f}s, Operations: {self.operations_count}")
            
        except Exception as e:
            logging.error(f"Failed to commit transaction: {e}")
            raise
        
        finally:
            self.transaction_started = False
            self.start_time = None
    
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if not self.transaction_started:
            raise RuntimeError("No transaction to rollback")
        
        try:
            self.connection.rollback()
            duration = time.time() - self.start_time if self.start_time else 0
            logging.warning(f"Transaction rolled back. Duration: {duration:.3f}s, Operations: {self.operations_count}")
        
        except Exception as e:
            logging.error(f"Failed to rollback transaction: {e}")
            raise
        
        finally:
            self.transaction_started = False
            self.start_time = None
    
    def close_connection(self) -> None:
        """Close the database connection."""
        if self.transaction_started:
            logging.warning("Closing connection with active transaction - rolling back")
            self.rollback_transaction()
        
        self.connection.close()
        logging.info("Database connection closed")
    
    def execute_in_transaction(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query within the current transaction."""
        if not self.transaction_started:
            raise RuntimeError("No active transaction")
        
        result = self.connection.execute(query, params)
        self.operations_count += 1
        return result
    
    @contextmanager
    def transaction_context(self):
        """Context manager for automatic transaction handling."""
        self.begin_transaction()
        try:
            yield self
            self.commit_transaction()
        except Exception:
            self.rollback_transaction()
            raise
    
    def get_transaction_info(self) -> Dict[str, Any]:
        """Get information about the current transaction."""
        return {
            'transaction_started': self.transaction_started,
            'isolation_level': self.isolation_level,
            'start_time': self.start_time,
            'operations_count': self.operations_count,
            'connection_stats': self.connection.get_stats()
        }

# Global connection pool for testing
_connection_pool: List[DatabaseConnection] = []
_pool_lock = threading.Lock()
_connection_counter = 0

def get_db_connection() -> DatabaseConnection:
    """
    Get a database connection from the pool.
    Creates a new mock connection for testing purposes.
    """
    global _connection_counter
    
    with _pool_lock:
        _connection_counter += 1
        connection_id = f"conn_{_connection_counter}"
        
        # Create new connection
        connection = DatabaseConnection(connection_id)
        _connection_pool.append(connection)
        
        logging.debug(f"Created new database connection: {connection_id}")
        return connection

def close_all_connections() -> None:
    """Close all connections in the pool."""
    with _pool_lock:
        for connection in _connection_pool:
            if connection.is_connected():
                connection.close()
        
        _connection_pool.clear()
        logging.info("All database connections closed")

def get_pool_stats() -> Dict[str, Any]:
    """Get statistics about the connection pool."""
    with _pool_lock:
        total_connections = len(_connection_pool)
        active_connections = sum(1 for conn in _connection_pool if conn.is_connected())
        
        return {
            'total_connections': total_connections,
            'active_connections': active_connections,
            'connection_details': [conn.get_stats() for conn in _connection_pool]
        }

# Additional utility functions for testing
def create_transaction_manager(isolation_level: str = "READ_COMMITTED") -> TransactionManager:
    """Create a new transaction manager with a fresh connection."""
    connection = get_db_connection()
    return TransactionManager(connection, isolation_level)

@contextmanager
def database_transaction(isolation_level: str = "READ_COMMITTED"):
    """Context manager for easy transaction handling."""
    manager = create_transaction_manager(isolation_level)
    
    try:
        with manager.transaction_context():
            yield manager
    finally:
        manager.close_connection()

# Module-level testing
if __name__ == "__main__":
    # Test the database manager
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing database_manager.py...")
    
    # Test basic connection
    conn = get_db_connection()
    print(f"Created connection: {conn.connection_id}")
    
    # Test transaction manager
    tx_manager = TransactionManager(conn, "SERIALIZABLE")
    
    try:
        tx_manager.begin_transaction()
        tx_manager.execute_in_transaction("SELECT * FROM test")
        tx_manager.commit_transaction()
        print("Transaction test passed")
    
    except Exception as e:
        print(f"Transaction test failed: {e}")
        tx_manager.rollback_transaction()
    
    finally:
        tx_manager.close_connection()
    
    # Test context manager
    try:
        with database_transaction("READ_COMMITTED") as tx:
            tx.execute_in_transaction("INSERT INTO test VALUES (1, 'test')")
            print("Context manager test passed")
    
    except Exception as e:
        print(f"Context manager test failed: {e}")
    
    # Print pool stats
    stats = get_pool_stats()
    print(f"Pool stats: {stats}")
    
    # Cleanup
    close_all_connections()
    print("Testing completed")
