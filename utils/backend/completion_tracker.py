from datetime import datetime

class CompletionTracker:
    """
    Manages the tracking of completed events, reflections, and task history.
    Works with the DatabaseManager for database operations.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the completion tracker with a database manager.
        
        Args:
            database_manager: Instance of DatabaseManager for database operations
        """
        self.db_manager = database_manager
    
    def mark_event_completed(self, event_id, completed=True, completion_notes=None, 
                             reflection_notes=None, event_date=None, actual_time_range=None):
        """
        Mark an event as completed or not completed.
        If marking as completed, moves the event to the completed_task table.
        
        Args:
            event_id (int): The event ID
            completed (bool): Whether the event is completed (True) or not (False)
            completion_notes (str, optional): Notes about completion
            reflection_notes (str, optional): Reflection notes
            event_date (str, optional): Date of the event, used for recurring events
            actual_time_range (str, optional): Actual time range in format "HH:MM-HH:MM"
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        if completed:
            # If marking as completed, move to completed_task table
            return self.move_completed_event_to_history(
                event_id, completion_notes, reflection_notes, event_date, actual_time_range)
        else:
            # If marking as not completed, check if it's in completed_task table
            # and move it back if necessary
            query = 'SELECT 1 FROM completed_task WHERE task_id = ?'
            params = [event_id]
            
            # Add date condition if provided
            if event_date:
                query += ' AND date = ?'
                params.append(event_date)
            
            result = self.db_manager.execute_query(query, params, 'one')
            
            if result:
                # Event is in completed_task table, move it back to timetable
                return self._restore_completed_event(event_id, event_date)
            
            return False  # No action needed if not in completed_task
    
    def _restore_completed_event(self, event_id, event_date=None):
        """
        Restore a completed event back to the timetable.
        
        Args:
            event_id (int): The event ID
            event_date (str, optional): Date of the event, used for recurring events
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        # Start a transaction
        transaction = []
        
        # Get completed task details
        query = '''
        SELECT title, date, time_range, event_type, deadline, importance 
        FROM completed_task WHERE task_id = ?
        '''
        params = [event_id]
        
        if event_date:
            query += ' AND date = ?'
            params.append(event_date)
        
        task = self.db_manager.execute_query(query, params, 'one')
        
        if not task:
            return False
        
        # First, check if this is from a recurring event that still exists
        check_recurring_query = '''
        SELECT 1 FROM timetable WHERE id = ? AND recurrence_rule IS NOT NULL AND recurrence_rule != ""
        '''
        is_recurring = self.db_manager.execute_query(check_recurring_query, [event_id], 'one')
        
        if is_recurring:
            # For recurring events, just remove from completed_recurring_dates
            delete_query = '''
            DELETE FROM completed_recurring_dates 
            WHERE event_id = ? AND date = ?
            '''
            transaction.append((delete_query, [event_id, event_date or task['date']]))
            
            # Also delete from completed_task
            delete_task_query = '''
            DELETE FROM completed_task
            WHERE task_id = ? AND date = ?
            '''
            transaction.append((delete_task_query, [event_id, event_date or task['date']]))
        else:
            # For non-recurring events, restore to timetable
            insert_query = '''
            INSERT INTO timetable (
                id, title, date, time_range, event_type, deadline, importance, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            '''
            transaction.append((insert_query, [
                event_id, task['title'], task['date'], task['time_range'], 
                task['event_type'], task['deadline'], task['importance']
            ]))
            
            # Delete from completed_task
            delete_query = '''
            DELETE FROM completed_task
            WHERE task_id = ?
            '''
            transaction.append((delete_query, [event_id]))
        
        # Execute the transaction
        return self.db_manager.execute_transaction(transaction)
    
    def move_completed_event_to_history(self, event_id, completion_notes=None, 
                                        reflection_notes=None, event_date=None, actual_time_range=None):
        """
        Move a completed event to the history (completed_task table).
        
        Args:
            event_id (int): The event ID
            completion_notes (str, optional): Notes about completion
            reflection_notes (str, optional): Reflection notes
            event_date (str, optional): Date of the event, used for recurring events
            actual_time_range (str, optional): Actual time range in format "HH:MM-HH:MM"
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        # Get event details from timetable
        query = '''
        SELECT title, date, time_range, event_type, deadline, importance, recurrence_rule
        FROM timetable WHERE id = ?
        '''
        
        event = self.db_manager.execute_query(query, [event_id], 'one')
        
        if not event:
            return False
        
        # Use provided date or the event's date
        actual_date = event_date or event['date']
        
        # Start a transaction
        transaction = []
        
        # Determine if this is a recurring event
        is_recurring = event['recurrence_rule'] is not None and event['recurrence_rule'].strip() != ''
        
        # Handle recurring events slightly differently
        if is_recurring:
            # First check if this specific occurrence is already marked completed
            check_query = '''
            SELECT 1 FROM completed_recurring_dates 
            WHERE event_id = ? AND date = ?
            '''
            already_completed = self.db_manager.execute_query(
                check_query, [event_id, actual_date], 'one')
            
            if already_completed:
                return True  # Already marked as completed
            
            # For recurring events, just mark this occurrence as completed
            recurring_query = '''
            INSERT OR REPLACE INTO completed_recurring_dates (event_id, date)
            VALUES (?, ?)
            '''
            transaction.append((recurring_query, [event_id, actual_date]))
            
            # We still add to completed_task for record keeping
            task_query = '''
            INSERT INTO completed_task (
                task_id, title, date, time_range, actual_time_range, event_type, deadline, 
                importance, completion_notes, reflection_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            transaction.append((task_query, [
                event_id, event['title'], actual_date, event['time_range'], 
                actual_time_range, event['event_type'], event['deadline'], 
                event['importance'], completion_notes, reflection_notes
            ]))
        else:
            # For non-recurring events, move to completed_task and delete from timetable
            task_query = '''
            INSERT INTO completed_task (
                task_id, title, date, time_range, actual_time_range, event_type, deadline, 
                importance, completion_notes, reflection_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            transaction.append((task_query, [
                event_id, event['title'], actual_date, event['time_range'], 
                actual_time_range, event['event_type'], event['deadline'], 
                event['importance'], completion_notes, reflection_notes
            ]))
            
            # Delete from timetable (only for non-recurring events)
            delete_query = '''
            DELETE FROM timetable WHERE id = ?
            '''
            transaction.append((delete_query, [event_id]))
        
        # Execute the transaction
        return self.db_manager.execute_transaction(transaction)
    
    def get_completed_events(self, date_from=None, date_to=None, limit=None, offset=0):
        """
        Get completed events with optional filtering by date range.
        
        Args:
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            
        Returns:
            list: List of completed events
        """
        query = 'SELECT * FROM completed_task'
        params = []
        
        # Add date range filtering
        if date_from or date_to:
            query += ' WHERE 1=1'
            
            if date_from:
                query += ' AND date >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND date <= ?'
                params.append(date_to)
        
        # Add sorting and pagination
        query += ' ORDER BY completion_date DESC'
        
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
            
            if offset:
                query += ' OFFSET ?'
                params.append(offset)
        
        # Execute the query
        events = self.db_manager.execute_query(query, params, 'all')
        
        # Add source flag to each event
        for event in events:
            event['source'] = 'completed_task'
            # Ensure id field exists (frontend might depend on this)
            if 'id' not in event and 'task_id' in event:
                event['id'] = event['task_id']
        
        return events
    
    def mark_task_completed_with_history(self, event_id, completion_notes=None, 
                                         reflection_notes=None, actual_time_range=None):
        """
        Mark a task as completed and move it to the history.
        Convenience wrapper around move_completed_event_to_history.
        
        Args:
            event_id (int): The event ID
            completion_notes (str, optional): Notes about completion
            reflection_notes (str, optional): Reflection notes
            actual_time_range (str, optional): Actual time range in format "HH:MM-HH:MM"
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        return self.move_completed_event_to_history(
            event_id, completion_notes, reflection_notes, None, actual_time_range)
    
    def add_task_reflection(self, task_id, reflection_notes):
        """
        Add or update reflection notes for a completed task.
        
        Args:
            task_id (int): The task ID
            reflection_notes (str): Reflection notes
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        query = '''
        UPDATE completed_task 
        SET reflection_notes = ?
        WHERE task_id = ? OR id = ?
        '''
        
        rows_affected = self.db_manager.execute_query(query, [reflection_notes, task_id, task_id])
        
        return rows_affected > 0
    
    def get_task_history(self, date_from=None, date_to=None, limit=None, offset=0):
        """
        Get task completion history with optional filtering by date range.
        
        Args:
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip
            
        Returns:
            list: List of task history records
        """
        # This is similar to get_completed_events but might include additional filtering
        # or data transformations specific to history reporting
        query = '''
        SELECT * FROM completed_task 
        WHERE 1=1
        '''
        params = []
        
        # Add date range filtering
        if date_from:
            query += ' AND date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND date <= ?'
            params.append(date_to)
        
        # Add sorting and pagination
        query += ' ORDER BY completion_date DESC'
        
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
            
            if offset:
                query += ' OFFSET ?'
                params.append(offset)
        
        # Execute the query
        history = self.db_manager.execute_query(query, params, 'all')
        
        return history
    
    def get_task_reflection(self, task_id):
        """
        Get reflection notes for a specific task.
        
        Args:
            task_id (int): The task ID
            
        Returns:
            dict: Task details including reflection notes, or None if not found
        """
        query = '''
        SELECT * FROM completed_task 
        WHERE task_id = ? OR id = ?
        '''
        
        result = self.db_manager.execute_query(query, [task_id, task_id], 'one')
        
        return result
    
    def delete_completed_task(self, task_id):
        """
        Delete a completed task from the history.
        
        Args:
            task_id (int): The task ID
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        # Start a transaction
        transaction = []
        
        # First get the task details to determine if it's from a recurring event
        query = 'SELECT task_id, date FROM completed_task WHERE task_id = ? OR id = ?'
        task = self.db_manager.execute_query(query, [task_id, task_id], 'one')
        
        if not task:
            return False
        
        actual_task_id = task['task_id']
        task_date = task['date']
        
        # Check if this is from a recurring event
        check_query = '''
        SELECT 1 FROM timetable t
        JOIN completed_recurring_dates c ON t.id = c.event_id
        WHERE t.id = ? AND c.date = ?
        '''
        
        is_recurring = self.db_manager.execute_query(check_query, [actual_task_id, task_date], 'one')
        
        # If it's a recurring event, also remove from completed_recurring_dates
        if is_recurring:
            recurring_query = 'DELETE FROM completed_recurring_dates WHERE event_id = ? AND date = ?'
            transaction.append((recurring_query, [actual_task_id, task_date]))
        
        # Always remove from completed_task
        task_query = 'DELETE FROM completed_task WHERE task_id = ? OR id = ?'
        transaction.append((task_query, [task_id, task_id]))
        
        # Execute the transaction
        return self.db_manager.execute_transaction(transaction)
