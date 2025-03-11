from datetime import datetime, timedelta, date


class RecurrenceManager:
    """
    Manages recurring events and their occurrences.
    Works with the DatabaseManager for database operations.
    """
    
    def __init__(self, database_manager, event_processor=None):
        """
        Initialize the recurrence manager with a database manager and optionally an event processor.
        
        Args:
            database_manager: Instance of DatabaseManager for database operations
            event_processor: Optional instance of EventProcessor for event processing operations
        """
        self.db_manager = database_manager
        self.event_processor = event_processor
    
    def process_recurring_events(self, llm_output, recurrence_rule, end_date=None, handle_conflicts='error'):
        """
        Process events from LLM output and add them as recurring events.
        
        Args:
            llm_output (str): The output text from the LLM
            recurrence_rule (str): The recurrence rule for the events:
                - 'daily': Event repeats every day
                - 'weekly': Event repeats every week on the same day
                - 'weekdays': Event repeats every weekday (Monday to Friday)
                - 'monthly': Event repeats every month on the same day
                - 'yearly': Event repeats every year on the same date
            end_date (str, optional): The end date for the recurrence in 'YYYY-MM-DD' format.
                If None, the event will recur indefinitely (or up to one year by default).
            handle_conflicts (str): How to handle time conflicts:
                - 'error': Raise an error and don't add the event (default)
                - 'skip': Skip conflicting events silently
                - 'force': Add events anyway, ignoring conflicts
            
        Returns:
            dict: Summary of operations performed
        """
        if self.event_processor is None:
            raise ValueError("EventProcessor is required for this operation but was not provided")
        
        # Extract events from the LLM output
        events = self.event_processor.extract_events(llm_output)
        
        summary = {
            'added': 0,
            'skipped': 0,
            'errors': [],
            'warnings': []
        }
        
        # Only process new events for recurrence
        additions = [event for event in events if event['action'] == '新增']
        
        if not additions:
            summary['warnings'].append("No new events found to set as recurring")
            return summary
            
        # Set a default end date of one year from now if none provided
        if end_date is None:
            default_end = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            end_date = default_end
            summary['warnings'].append(f"No end date provided, defaulting to one year: {default_end}")
        
        for event in additions:
            try:
                # Set the recurrence rule directly
                event['recurrence_rule'] = recurrence_rule
                
                # Get the initial date of the event
                start_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
                
                # Generate all occurrences based on the recurrence rule
                occurrences = self._generate_occurrences(start_date, recurrence_rule, end_date_obj)
                
                # Add each occurrence as a separate event
                for occurrence_date in occurrences:
                    # Create a copy of the event with the new date
                    occurrence_event = event.copy()
                    occurrence_event['date'] = occurrence_date.strftime('%Y-%m-%d')
                    
                    try:
                        # Try to add the event, respecting conflict handling
                        if handle_conflicts == 'force':
                            self.event_processor._add_event_no_check(occurrence_event)
                            summary['added'] += 1
                        else:
                            # Check for conflicts
                            conflicts = self.event_processor._check_time_conflict(occurrence_event)
                            if conflicts and handle_conflicts == 'skip':
                                summary['skipped'] += 1
                                continue
                            elif conflicts:
                                conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
                                raise ValueError(f"Time conflict on {occurrence_event['date']} with existing events: {', '.join(conflict_details)}")
                            
                            # No conflicts or force mode, add the event
                            self.event_processor._add_event_no_check(occurrence_event)
                            summary['added'] += 1
                    except ValueError as e:
                        if handle_conflicts == 'error':
                            # Re-raise the error to stop processing
                            raise
                        summary['errors'].append(str(e))
                        summary['skipped'] += 1
                
            except Exception as e:
                summary['errors'].append(f"Error processing recurring event '{event['title']}': {str(e)}")
                
        return summary
    
    def apply_recurrence_to_event(self, event_id, recurrence_rule, end_date=None, handle_conflicts='error'):
        """
        Apply a recurrence rule to an existing event.
        
        Args:
            event_id (int): The ID of the event to apply recurrence to
            recurrence_rule (str): The recurrence rule for the events:
                - 'daily': Event repeats every day
                - 'weekly': Event repeats every week on the same day
                - 'weekdays': Event repeats every weekday (Monday to Friday)
                - 'monthly': Event repeats every month on the same day
                - 'yearly': Event repeats every year on the same date
            end_date (str, optional): The end date for the recurrence in 'YYYY-MM-DD' format.
                If None, the event will recur indefinitely (or up to one year by default).
            handle_conflicts (str): How to handle time conflicts:
                - 'error': Raise an error and don't add the event (default)
                - 'skip': Skip conflicting events silently
                - 'force': Add events anyway, ignoring conflicts
                
        Returns:
            dict: Summary of operations performed
        """
        summary = {
            'added': 0,
            'skipped': 0,
            'errors': [],
            'warnings': []
        }
        
        # Get the original event
        query = '''
        SELECT title, date, time_range, event_type, deadline, importance
        FROM timetable WHERE id = ?
        '''
        
        original_event = self.db_manager.execute_query(query, (event_id,), 'one')
        
        if not original_event:
            raise ValueError(f"Event with ID {event_id} not found")
        
        # Set the recurrence rule on the original event
        update_query = '''
        UPDATE timetable SET recurrence_rule = ? WHERE id = ?
        '''
        
        self.db_manager.execute_query(update_query, (recurrence_rule, event_id))
        
        # Create a dictionary format of the original event with the recurrence rule
        original_event_dict = {
            'title': original_event['title'],
            'date': original_event['date'],
            'time_range': original_event['time_range'],
            'event_type': original_event['event_type'],
            'deadline': original_event['deadline'],
            'importance': original_event['importance'],
            'recurrence_rule': recurrence_rule,
            'action': '新增'  # Mark as 'add' since we're creating new recurrences
        }
        
        # Set default end date to one year later if not provided
        if end_date is None:
            default_end = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            end_date = default_end
            summary['warnings'].append(f"No end date provided, defaulting to one year: {default_end}")
        
        # Generate all occurrences of the recurring event
        start_date = datetime.strptime(original_event['date'], '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        occurrences = self._generate_occurrences(start_date, recurrence_rule, end_date_obj)
        
        # Skip the first occurrence as it's the original event
        occurrences = occurrences[1:]
        
        # Add each occurrence as a new event
        for occurrence_date in occurrences:
            occurrence_event = original_event_dict.copy()
            occurrence_event['date'] = occurrence_date.strftime('%Y-%m-%d')
            
            try:
                # Handle conflicts according to the specified strategy
                if handle_conflicts == 'force':
                    if self.event_processor:
                        self.event_processor._add_event_no_check(occurrence_event)
                    else:
                        self._add_event_direct(occurrence_event)
                    summary['added'] += 1
                else:
                    # Check for conflicts if we have an event processor
                    conflicts = []
                    if self.event_processor:
                        conflicts = self.event_processor._check_time_conflict(occurrence_event)
                    
                    if conflicts and handle_conflicts == 'skip':
                        summary['skipped'] += 1
                        continue
                    elif conflicts:
                        conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
                        raise ValueError(f"Time conflict on {occurrence_event['date']} with existing events: {', '.join(conflict_details)}")
                    
                    # No conflicts, add the event
                    if self.event_processor:
                        self.event_processor._add_event_no_check(occurrence_event)
                    else:
                        self._add_event_direct(occurrence_event)
                    summary['added'] += 1
            except ValueError as e:
                if handle_conflicts == 'error':
                    raise
                summary['errors'].append(str(e))
                summary['skipped'] += 1
        
        return summary
    
    def _add_event_direct(self, event):
        """
        Add an event directly to the database without using EventProcessor.
        Used as a fallback when no EventProcessor is provided.
        
        Args:
            event (dict): Event information
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        query = '''
        INSERT INTO timetable (title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            event['title'], 
            event['date'], 
            event['time_range'], 
            event['event_type'],
            event['deadline'],
            event['importance'],
            event['recurrence_rule'],
            current_time
        )
        
        self.db_manager.execute_query(query, params)
    
    def get_recurring_events(self):
        """
        Get all events that have a recurrence rule set.
        
        Returns:
            list: List of events with recurrence rules
        """
        query = '''
        SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule
        FROM timetable
        WHERE recurrence_rule IS NOT NULL AND recurrence_rule != ''
        ORDER BY date
        '''
        
        events = self.db_manager.execute_query(query, None, 'all')
        
        return events
    
    def remove_recurrence(self, event_id):
        """
        Remove the recurrence rule from an event.
        
        Args:
            event_id (int): The ID of the event to remove recurrence from
            
        Returns:
            bool: True if successful, False otherwise
        """
        query = '''
        UPDATE timetable SET recurrence_rule = NULL
        WHERE id = ?
        '''
        
        affected_rows = self.db_manager.execute_query(query, (event_id,))
        
        return affected_rows > 0
    
    def _generate_occurrences(self, start_date, recurrence_rule, end_date=None):
        """
        Generate all occurrence dates for a recurring event.
        
        Args:
            start_date (date): The start date of the recurrence
            recurrence_rule (str): The recurrence rule ('daily', 'weekly', etc.)
            end_date (date, optional): The end date of the recurrence
            
        Returns:
            list: List of date objects for all occurrences
        """
        occurrences = [start_date]
        current_date = start_date
        
        # Default end date is one year from start if none provided
        if end_date is None:
            end_date = start_date.replace(year=start_date.year + 1)
        
        # Generate dates based on recurrence rule
        while current_date < end_date:
            if recurrence_rule == 'daily':
                current_date = current_date + timedelta(days=1)
            elif recurrence_rule == 'weekly':
                current_date = current_date + timedelta(days=7)
            elif recurrence_rule == 'weekdays':
                current_date = current_date + timedelta(days=1)
                # Skip weekends
                while current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    current_date = current_date + timedelta(days=1)
            elif recurrence_rule == 'monthly':
                # Move to the next month, same day
                month = current_date.month + 1
                year = current_date.year
                if month > 12:
                    month = 1
                    year += 1
                
                # Handle month length differences
                day = min(current_date.day, self._get_days_in_month(year, month))
                current_date = date(year, month, day)
            elif recurrence_rule == 'yearly':
                # Move to the next year, same month and day
                try:
                    current_date = current_date.replace(year=current_date.year + 1)
                except ValueError:
                    # Handle February 29 in leap years
                    if current_date.month == 2 and current_date.day == 29:
                        current_date = date(current_date.year + 1, 3, 1)
            else:
                raise ValueError(f"Unsupported recurrence rule: {recurrence_rule}")
                
            if current_date <= end_date:
                occurrences.append(current_date)
                
        return occurrences
    
    def _get_days_in_month(self, year, month):
        """
        Return the number of days in a given month.
        
        Args:
            year (int): Year
            month (int): Month (1-12)
            
        Returns:
            int: Number of days in the month
        """
        if month == 2:  # February
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # Leap year
                return 29
            return 28
        elif month in [4, 6, 9, 11]:  # April, June, September, November
            return 30
        else:
            return 31
