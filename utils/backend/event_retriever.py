import sqlite3
from datetime import datetime


class EventRetriever:
    """
    Focuses on retrieving and formatting events from the database.
    Works with DatabaseManager for database operations.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the event retriever with a database manager.
        
        Args:
            database_manager: Instance of DatabaseManager for database operations
        """
        self.db_manager = database_manager
    
    def get_all_events(self, date_from=None, date_to=None, limit=None, offset=0):
        """
        Retrieve events from the database with optional filtering and pagination.
        
        Args:
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            
        Returns:
            list: List of event dictionaries
        """
        # Base query to get all events
        query = 'SELECT * FROM timetable'
        params = []
        
        # Add date range filtering
        conditions = []
        if date_from:
            conditions.append('date >= ?')
            params.append(date_from)
        if date_to:
            conditions.append('date <= ?')
            params.append(date_to)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY date, time_range'
        
        # Execute the query
        events = self.db_manager.execute_query(query, params, 'all')
        
        # Get completed recurring event dates to filter them out
        completed_query = 'SELECT event_id, date FROM completed_recurring_dates'
        completed_conditions = []
        completed_params = []
        
        if date_from:
            completed_conditions.append('date >= ?')
            completed_params.append(date_from)
        if date_to:
            completed_conditions.append('date <= ?')
            completed_params.append(date_to)
        
        if completed_conditions:
            completed_query += ' WHERE ' + ' AND '.join(completed_conditions)
        
        completed_results = self.db_manager.execute_query(completed_query, completed_params, 'all')
        
        # Create a set of (event_id, date) tuples for completed recurring events
        completed_events = {(row['event_id'], row['date']) for row in completed_results}
        
        # Filter out completed recurring event instances
        filtered_events = []
        for event in events:
            event_id = event['id']
            event_date = event['date']
            is_recurring = event.get('recurrence_rule') and event['recurrence_rule'].strip() != ''
            
            # Include the event if it's not recurring or if it's a recurring event that hasn't been completed
            if not is_recurring or (event_id, event_date) not in completed_events:
                filtered_events.append(event)
        
        # Add source flag to each event
        for event in filtered_events:
            event['source'] = 'timetable'
        
        # Apply pagination
        if limit is not None:
            start_idx = offset
            end_idx = offset + limit
            filtered_events = filtered_events[start_idx:end_idx]
        
        return filtered_events
    
    def get_events_iterator(self, date_from=None, date_to=None, batch_size=100):
        """
        Return an iterator that retrieves events in batches to avoid loading all events into memory.
        
        Args:
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            batch_size (int): Number of events to retrieve in each batch
            
        Returns:
            iterator: Iterator yielding batches of events
        """
        offset = 0
        while True:
            batch = self.get_all_events(date_from, date_to, batch_size, offset)
            if not batch:
                break
            yield batch
            offset += batch_size
            if len(batch) < batch_size:
                break
    
    def get_events_for_date(self, date, limit=None, offset=0):
        """
        Retrieve all events for a specific date.
        
        Args:
            date (str): Date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            
        Returns:
            list: List of event dictionaries for the specified date
        """
        # First get all events for this date
        query = '''
        SELECT t.* FROM timetable t
        WHERE t.date = ?
        '''
        
        events = self.db_manager.execute_query(query, (date,), 'all')
        
        # Get completed recurring events for this date to filter them out
        completed_query = '''
        SELECT t.id FROM timetable t
        JOIN completed_recurring_dates c ON t.id = c.event_id
        WHERE t.recurrence_rule IS NOT NULL 
        AND t.recurrence_rule != ''
        AND c.date = ?
        '''
        
        completed_result = self.db_manager.execute_query(completed_query, (date,), 'all')
        
        completed_recurring_event_ids = {row['id'] for row in completed_result}
        
        # Filter out completed recurring events
        filtered_events = [event for event in events if event['id'] not in completed_recurring_event_ids]
        
        # Add source flag to each event
        for event in filtered_events:
            event['source'] = 'timetable'
        
        # Apply pagination
        if limit is not None:
            start_idx = offset
            end_idx = offset + limit
            filtered_events = filtered_events[start_idx:end_idx]
        
        return filtered_events
    
    def format_events_as_llm_output(self, events=None, include_header=False, date_from=None, date_to=None, limit=None, offset=0):
        """
        Format events as a string in the format expected by the LLM.
        
        Args:
            events (list, optional): List of events to format. If None, events are retrieved based on filters.
            include_header (bool): Whether to include the header in the output
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            
        Returns:
            str: Formatted events string
        """
        if events is None:
            events = self.get_all_events(date_from=date_from, date_to=date_to, limit=limit, offset=offset)
        
        # Sort events by date and time
        events = sorted(events, key=lambda x: (str(x.get('date', '')), str(x.get('time_range', ''))))
        
        # Start building the output
        output = []
        if include_header:
            output.append("日程建议：")
        
        for event in events:
            # Extract fields, handling both database and extracted event formats
            title = event.get('title', '')
            date = event.get('date', '')
            time_range = event.get('time_range', '')
            event_type = event.get('event_type', '')
            deadline = event.get('deadline', '')
            importance = event.get('importance', '')
            
            # Format each field on a new line
            event_lines = [
                f"事项: {title}",
                f"日期: {date}",
                f"时间段: {time_range}",
                f"类型: {event_type}"
            ]
            
            # Add optional fields if they exist
            if deadline:
                event_lines.append(f"截止日期：{deadline}")
            
            if importance:
                event_lines.append(f"重要程度：{importance}")
            
            # Join the event lines with newlines
            output.append("\n".join(event_lines))
        
        # Join all events with double newlines between them
        return "\n\n".join(output)
    
    def format_events_with_changes(self, old_events=None, new_events=None, include_header=False, date_from=None, date_to=None, limit=None, offset=0, show_unchanged=True):
        """
        Format events with visual indicators showing changes between old and new states.
        
        Args:
            old_events (list, optional): List of event dictionaries representing the old state. 
                                        If None, will be retrieved based on filters.
            new_events (list, optional): List of event dictionaries representing the new state.
                                        If None, will be retrieved based on filters.
            include_header (bool): Whether to include the header
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            show_unchanged (bool): Whether to include unchanged events in the output
            
        Returns:
            str: Formatted string showing changes with visual indicators:
                [+] for new events
                [-] for deleted events
                [*] for modified events
                [ ] for unchanged events (only if show_unchanged is True)
        """
        # If event lists are not provided, retrieve them based on filters
        if old_events is None:
            old_events = self.get_all_events(date_from=date_from, date_to=date_to, limit=limit, offset=offset)
        if new_events is None:
            new_events = self.get_all_events(date_from=date_from, date_to=date_to, limit=limit, offset=offset)
            
        # Create dictionaries for easy lookup
        old_events_dict = {(e.get('title', ''), e.get('date', '')): e for e in old_events}
        new_events_dict = {(e.get('title', ''), e.get('date', '')): e for e in new_events}
        
        # Collect all unique event keys
        all_keys = set(old_events_dict.keys()) | set(new_events_dict.keys())
        
        # Start building the output
        output = []
        if include_header:
            output.append("日程变更明细：")
            output.append("-" * 40)
        
        # Sort keys by date and title
        sorted_keys = sorted(all_keys, key=lambda x: (x[1], x[0]))
        
        # Create lists for changed and unchanged events
        changed_events = []
        unchanged_events = []
        
        for title, date in sorted_keys:
            old_event = old_events_dict.get((title, date))
            new_event = new_events_dict.get((title, date))
            
            if old_event and new_event:
                # Check if event was modified
                is_modified = False
                changes = []
                
                # Compare each field
                fields_to_check = [
                    ('time_range', '时间段'),
                    ('event_type', '类型'),
                    ('deadline', '截止日期'),
                    ('importance', '重要程度')
                ]
                
                for field, field_name in fields_to_check:
                    old_val = str(old_event.get(field, ''))
                    new_val = str(new_event.get(field, ''))
                    if old_val != new_val:
                        is_modified = True
                        changes.append(f"{field_name}: {old_val} → {new_val}")
                
                if is_modified:
                    # Event was modified
                    event_lines = [
                        f"[*] 事项: {title} (已修改)",
                        f"    日期: {date}",
                    ]
                    event_lines.extend(f"    {change}" for change in changes)
                    changed_events.append("\n".join(event_lines))
                elif show_unchanged:
                    # Event unchanged, only show if show_unchanged is True
                    event_lines = [
                        f"[ ] 事项: {title}",
                        f"    日期: {date}",
                        f"    时间段: {new_event.get('time_range', '')}",
                        f"    类型: {new_event.get('event_type', '')}"
                    ]
                    if new_event.get('deadline'):
                        event_lines.append(f"    截止日期：{new_event['deadline']}")
                    if new_event.get('importance'):
                        event_lines.append(f"    重要程度：{new_event['importance']}")
                    unchanged_events.append("\n".join(event_lines))
            
            elif new_event:
                # New event added
                event_lines = [
                    f"[+] 事项: {title} (新增)",
                    f"    日期: {date}",
                    f"    时间段: {new_event.get('time_range', '')}",
                    f"    类型: {new_event.get('event_type', '')}"
                ]
                if new_event.get('deadline'):
                    event_lines.append(f"    截止日期：{new_event['deadline']}")
                if new_event.get('importance'):
                    event_lines.append(f"    重要程度：{new_event['importance']}")
                changed_events.append("\n".join(event_lines))
            
            else:
                # Event was deleted
                event_lines = [
                    f"[-] 事项: {title} (已删除)",
                    f"    日期: {date}",
                    f"    时间段: {old_event.get('time_range', '')}",
                    f"    类型: {old_event.get('event_type', '')}"
                ]
                if old_event.get('deadline'):
                    event_lines.append(f"    截止日期：{old_event['deadline']}")
                if old_event.get('importance'):
                    event_lines.append(f"    重要程度：{old_event['importance']}")
                changed_events.append("\n".join(event_lines))
        
        # Combine changed and unchanged events, prioritizing changed events
        all_formatted_events = changed_events + unchanged_events
        
        # Apply limit parameter
        if limit is not None and limit > 0:
            all_formatted_events = all_formatted_events[:limit]
        
        # Add formatted events to output
        output.extend(all_formatted_events)
        
        return "\n\n".join(output)
