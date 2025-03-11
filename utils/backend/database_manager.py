import sqlite3
from datetime import datetime


class DatabaseManager:
    """
    Manages database operations, schema management, and migrations for the timetable application.
    Currently supports SQLite, with potential for other database types in the future.
    """
    
    def __init__(self, database_type="sqlite", db_path="timetable.db"):
        """
        Initialize the database manager with specified database type and path.
        
        Args:
            database_type (str): 'sqlite' or other types (only sqlite supported currently)
            db_path (str): Path to SQLite database
        """
        self.database_type = database_type.lower()
        self.db_path = db_path
        
        if self.database_type == "sqlite":
            self._init_sqlite()
            self._check_and_update_table_structure()
        else:
            raise ValueError("Unsupported database type. Use 'sqlite' for now, will support others later.")
    
    def _init_sqlite(self):
        """Initialize SQLite database and create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main timetable for storing events
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time_range TEXT NOT NULL,
            event_type TEXT NOT NULL,
            deadline TEXT,
            importance INTEGER,
            recurrence_rule TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create completed_task table for storing historical completed tasks
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time_range TEXT NOT NULL,
            actual_time_range TEXT,
            event_type TEXT NOT NULL,
            deadline TEXT,
            importance INTEGER,
            completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_notes TEXT,
            reflection_notes TEXT,
            FOREIGN KEY (task_id) REFERENCES timetable(id)
        )
        ''')
        
        # Create completed_recurring_dates table for tracking completed instances of recurring events
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_recurring_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, date),
            FOREIGN KEY (event_id) REFERENCES timetable(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _check_and_update_table_structure(self, conn=None):
        """
        Check and update database table structure to ensure all necessary columns exist.
        
        Args:
            conn (sqlite3.Connection, optional): Existing database connection. If None, a new connection will be created.
        """
        if self.database_type != "sqlite":
            return
            
        close_conn = False
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            close_conn = True
            
        cursor = conn.cursor()
        
        # Check timetable columns
        cursor.execute("PRAGMA table_info(timetable)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add recurrence_rule column if it doesn't exist
        if 'recurrence_rule' not in columns:
            print("Adding recurrence_rule column to timetable")
            cursor.execute("ALTER TABLE timetable ADD COLUMN recurrence_rule TEXT")
            conn.commit()
        
        # Check completed_task columns
        cursor.execute("PRAGMA table_info(completed_task)")
        completed_columns = [column[1] for column in cursor.fetchall()]
        
        # Add actual_time_range column if it doesn't exist
        if 'actual_time_range' not in completed_columns:
            print("Adding actual_time_range column to completed_task")
            cursor.execute("ALTER TABLE completed_task ADD COLUMN actual_time_range TEXT")
            conn.commit()
        
        # If completed column exists in timetable (legacy), migrate data and remove column
        if 'completed' in columns:
            print("Migrating completed events to completed_task table")
            self._migrate_completed_events(conn)
            
            # SQLite doesn't directly support dropping columns, so create a new table and migrate data
            print("Removing completed column from timetable")
            cursor.execute('''
            CREATE TABLE timetable_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time_range TEXT NOT NULL,
                event_type TEXT NOT NULL,
                deadline TEXT,
                importance INTEGER,
                recurrence_rule TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Copy data to new table, excluding completed column
            cursor.execute('''
            INSERT INTO timetable_new (id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated)
            SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated
            FROM timetable
            WHERE completed = 0 OR completed IS NULL
            ''')
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE timetable")
            cursor.execute("ALTER TABLE timetable_new RENAME TO timetable")
            conn.commit()
        
        if close_conn:
            conn.close()
    
    def _migrate_completed_events(self, conn):
        """
        Migrate completed events from the timetable to the completed_task table.
        Used for legacy data migration.
        
        Args:
            conn (sqlite3.Connection): Database connection
        """
        cursor = conn.cursor()
        
        # Get all completed events from the timetable
        cursor.execute('''
        SELECT id, title, date, time_range, event_type, deadline, importance
        FROM timetable
        WHERE completed = 1
        ''')
        
        completed_events = cursor.fetchall()
        
        # Add completed events to the completed_task table
        for event in completed_events:
            event_id, title, date, time_range, event_type, deadline, importance = event
            
            # Check if event already exists in completed_task table
            cursor.execute('SELECT 1 FROM completed_task WHERE task_id = ?', (event_id,))
            if cursor.fetchone() is None:
                # If it doesn't exist, add it
                cursor.execute('''
                INSERT INTO completed_task (
                    task_id, title, date, time_range, event_type, deadline, importance
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (event_id, title, date, time_range, event_type, deadline, importance))
        
        conn.commit()
    
    def remove_duplicates(self):
        """
        Remove duplicate events from the database.
        
        Returns:
            dict: Summary of operation with count of removed duplicates
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find duplicates (same title, date, time_range, and event_type)
            cursor.execute('''
            SELECT MIN(id), title, date, time_range, event_type, COUNT(*) 
            FROM timetable 
            GROUP BY title, date, time_range, event_type
            HAVING COUNT(*) > 1
            ''')
            
            duplicates = cursor.fetchall()
            removed_count = 0
            
            for dup in duplicates:
                min_id, title, date, time_range, event_type, count = dup
                
                # Delete all duplicates except the one with minimum ID
                cursor.execute('''
                DELETE FROM timetable 
                WHERE title = ? AND date = ? AND time_range = ? AND event_type = ? AND id != ?
                ''', (title, date, time_range, event_type, min_id))
                
                removed_count += count - 1
            
            # Get count of remaining events
            cursor.execute('SELECT COUNT(*) FROM timetable')
            remaining_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            return {
                'removed_duplicates': removed_count,
                'unique_events_kept': remaining_count
            }
        else:
            return {
                'removed_duplicates': 0,
                'unique_events_kept': 0,
                'error': 'Unsupported database type'
            }
    
    def get_connection(self):
        """
        Get a database connection. The caller is responsible for closing it.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            return conn
        else:
            raise ValueError("Unsupported database type")
    
    def execute_query(self, query, params=None, fetch_mode=None):
        """
        Execute a SQL query and optionally fetch results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            fetch_mode (str, optional): 'one', 'all', or None for no fetch
            
        Returns:
            Various: Query results based on fetch_mode, or cursor.rowcount if no fetch_mode
        """
        if self.database_type != "sqlite":
            raise ValueError("Unsupported database type")
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if fetch_mode == 'one':
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
            elif fetch_mode == 'all':
                return [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
                return cursor.rowcount
                
        finally:
            conn.close()
    
    def execute_transaction(self, queries_and_params):
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries_and_params (list): List of (query, params) tuples
            
        Returns:
            bool: True if transaction succeeded, False otherwise
        """
        if self.database_type != "sqlite":
            raise ValueError("Unsupported database type")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('BEGIN TRANSACTION')
            
            for query, params in queries_and_params:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                    
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Transaction failed: {e}")
            return False
            
        finally:
            conn.close()
