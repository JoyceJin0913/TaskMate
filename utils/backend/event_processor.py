import re
from datetime import datetime, timedelta


class EventProcessor:
    """
    Handles adding, modifying, deleting, and extracting events from text.
    Works with the DatabaseManager to perform database operations.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the event processor with a database manager.
        
        Args:
            database_manager: Instance of DatabaseManager for database operations
        """
        self.db_manager = database_manager
    
    def extract_events(self, llm_output):
        """
        Extract event information from LLM output.
        
        Args:
            llm_output (str): The output text from the LLM
            
        Returns:
            list: List of dictionaries containing event information
        """
        # Pattern to match event details in the LLM output format
        pattern = r'事项:\s*(.*?)\s*日期:\s*(.*?)\s*时间段:\s*(.*?)\s*类型:\s*(.*?)(?:\s*截止日期：(.*?))?(?:\s*重要程度：(\d+))?\s*变动：(.*?)(?=\s*事项:|$)'
        
        # Find all matches with DOTALL and MULTILINE flags for handling newlines
        matches = re.finditer(pattern, llm_output, re.DOTALL | re.MULTILINE)
        
        events = []
        for match in matches:
            groups = match.groups()
            # Create event dictionary with extracted information
            event = {
                'title': groups[0].strip(),
                'date': groups[1].strip(),
                'time_range': groups[2].strip(),
                'event_type': groups[3].strip(),
                'deadline': groups[4].strip() if groups[4] else None,
                'importance': int(groups[5]) if groups[5] else 0,
                'recurrence_rule': None,  # Default to None
                'action': groups[6].strip()
            }
            events.append(event)
        
        # Debug info
        print(f"Extracted {len(events)} events from LLM output")
        for i, e in enumerate(events):
            print(f"Event {i+1}: {e['title']} - {e['date']} - {e['action']}")
        
        return events
    
    def process_events(self, llm_output, handle_conflicts='error'):
        """
        Process events from LLM output and update database accordingly.
        
        Args:
            llm_output (str): The output text from the LLM
            handle_conflicts (str): How to handle time conflicts:
                - 'error': Raise an error and don't add the event (default)
                - 'skip': Skip conflicting events silently
                - 'force': Add events anyway, ignoring conflicts
            
        Returns:
            dict: Summary of operations performed
        """
        events = self.extract_events(llm_output)
        
        summary = {
            'added': 0,
            'modified': 0,
            'deleted': 0,
            'unchanged': 0,
            'skipped': 0,
            'errors': [],
            'warnings': []
        }
        
        # Collect all modifications so we can process them together
        modifications = [event for event in events if event['action'] == '更改']
        additions = [event for event in events if event['action'] == '新增']
        deletions = [event for event in events if event['action'] == '删除']
        unchanged = [event for event in events if event['action'] == '无']
        unknown = [event for event in events if event['action'] not in ['新增', '更改', '删除', '无']]
        
        # Process deletions first
        for event in deletions:
            try:
                self._delete_event(event)
                summary['deleted'] += 1
            except Exception as e:
                summary['errors'].append(f"Error processing event '{event['title']}': {str(e)}")
        
        # Process modifications next
        # First, retrieve the current state of all events being modified
        current_events_map = {}
        future_events_map = {}
        
        # Group modifications by date for easier conflict checking
        mods_by_date = {}
        for event in modifications:
            date = event['date']
            if date not in mods_by_date:
                mods_by_date[date] = []
            mods_by_date[date].append(event)
            
            # Store the future state of this event
            event_key = f"{event['title']}|{event['date']}"
            future_events_map[event_key] = event
        
        # Process each date's modifications
        for date, date_mods in mods_by_date.items():
            # Get current events for this date
            current_events = self.get_events_for_date(date)
            
            # Store current state for reference
            for event in current_events:
                event_key = f"{event['title']}|{event['date']}"
                current_events_map[event_key] = event
            
            # Check for conflicts between modifications themselves
            for i, mod1 in enumerate(date_mods):
                try:
                    mod1_start, mod1_end = self._parse_time_range(mod1['time_range'])
                    
                    # Check against other modifications
                    conflicts = []
                    for j, mod2 in enumerate(date_mods):
                        if i == j:  # Skip self
                            continue
                            
                        try:
                            mod2_start, mod2_end = self._parse_time_range(mod2['time_range'])
                            
                            # Check for overlap
                            if (mod1_start < mod2_end and mod1_end > mod2_start):
                                conflicts.append(mod2)
                        except ValueError:
                            continue
                    
                    if conflicts and handle_conflicts == 'error':
                        conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
                        raise ValueError(f"Conflict between modifications: '{mod1['title']}' would conflict with {', '.join(conflict_details)}")
                        
                except ValueError as ve:
                    if handle_conflicts == 'error':
                        summary['errors'].append(f"Error processing event '{mod1['title']}': {str(ve)}")
                        # Skip this modification
                        date_mods[i]['skip'] = True
                    
                except Exception as e:
                    summary['errors'].append(f"Error processing event '{mod1['title']}': {str(e)}")
                    # Skip this modification
                    date_mods[i]['skip'] = True
            
            # Process the modifications that don't have conflicts with each other
            for mod in date_mods:
                if mod.get('skip'):
                    summary['skipped'] += 1
                    continue
                    
                try:
                    self._modify_event(mod)
                    summary['modified'] += 1
                except Exception as e:
                    summary['errors'].append(f"Error processing event '{mod['title']}': {str(e)}")
        
        # Process additions last, with awareness of modifications and other additions
        for event in additions:
            try:
                # Check for exact duplicates
                if self._check_duplicate_event(event):
                    summary['warnings'].append(f"Skipped duplicate event: '{event['title']}' already exists with identical details")
                    summary['skipped'] += 1
                    continue
                
                # Check for conflicts with existing events (excluding deleted ones)
                # and with newly added events
                date_events = self.get_events_for_date(event['date'])
                
                # Filter out events that we've just deleted
                date_events = [e for e in date_events if not any(
                    d['title'] == e['title'] and d['date'] == e['date'] and d['time_range'] == e['time_range']
                    for d in deletions
                )]
                
                # Add events that we've just modified or added
                for mod in modifications:
                    if mod['date'] == event['date'] and not mod.get('skip'):
                        # This is a simplified representation of the modified event
                        date_events.append({
                            'title': mod['title'],
                            'date': mod['date'],
                            'time_range': mod['time_range']
                        })
                
                # Add events that we've already processed in this batch
                for added in additions:
                    if added['date'] == event['date'] and added != event and added.get('processed'):
                        date_events.append({
                            'title': added['title'],
                            'date': added['date'],
                            'time_range': added['time_range']
                        })
                
                # Now check for conflicts
                conflicts = []
                try:
                    event_start, event_end = self._parse_time_range(event['time_range'])
                    
                    for other in date_events:
                        try:
                            other_start, other_end = self._parse_time_range(other['time_range'])
                            
                            # Check for overlap
                            if (event_start < other_end and event_end > other_start):
                                conflicts.append(other)
                        except ValueError:
                            continue
                    
                except ValueError:
                    # Skip conflict check if we can't parse time
                    pass
                
                if conflicts:
                    conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
                    conflict_msg = f"Time conflict for '{event['title']}' with events: {', '.join(conflict_details)}"
                    
                    if handle_conflicts == 'error':
                        raise ValueError(conflict_msg)
                    elif handle_conflicts == 'skip':
                        summary['warnings'].append(f"Skipped event due to {conflict_msg}")
                        summary['skipped'] += 1
                        continue
                    else:  # 'force'
                        summary['warnings'].append(f"Added event despite {conflict_msg}")
                
                # If we get here, add the event
                self._add_event_no_check(event)
                event['processed'] = True  # Mark as processed for subsequent conflict checks
                summary['added'] += 1
                
            except ValueError as ve:
                if handle_conflicts == 'error':
                    summary['errors'].append(f"Error processing event '{event['title']}': {str(ve)}")
                summary['warnings'].append(str(ve))
                summary['skipped'] += 1
                
            except Exception as e:
                summary['errors'].append(f"Error processing event '{event['title']}': {str(e)}")
        
        # Count unchanged events
        summary['unchanged'] = len(unchanged)
        
        # Process unknown actions
        for event in unknown:
            summary['errors'].append(f"Unknown action '{event['action']}' for event '{event['title']}'")
        
        return summary

    def _add_event_no_check(self, event):
        """
        Internal method to add event without duplicate/conflict checks.
        
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
    
    def _check_duplicate_event(self, event):
        """
        Check if an exact duplicate of the event already exists in the database.
        
        Args:
            event (dict): Event information
            
        Returns:
            bool: True if exact duplicate exists, False otherwise
        """
        query = '''
        SELECT COUNT(*) as count FROM timetable
        WHERE title = ? AND date = ? AND time_range = ? AND event_type = ?
        '''
        
        params = (
            event['title'],
            event['date'],
            event['time_range'],
            event['event_type']
        )
        
        result = self.db_manager.execute_query(query, params, 'one')
        return result['count'] > 0 if result else False
    
    def _parse_time_range(self, time_range):
        """
        Parse a time range string into start and end times for comparison.
        
        Args:
            time_range (str): Time range in format 'HH:MM-HH:MM'
            
        Returns:
            tuple: (start_minutes, end_minutes) where minutes are from midnight
            
        Raises:
            ValueError: If time range cannot be parsed
        """
        if not time_range or '-' not in time_range:
            raise ValueError(f"Invalid time range format: {time_range}")
            
        start_str, end_str = time_range.split('-')
        
        try:
            # Convert HH:MM to minutes from midnight for easy comparison
            start_parts = start_str.strip().split(':')
            end_parts = end_str.strip().split(':')
            
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            
            return start_minutes, end_minutes
        except (ValueError, IndexError):
            raise ValueError(f"Invalid time format in range: {time_range}")

    def _check_time_conflict(self, event):
        """
        Check if the event conflicts with existing events based on time overlap.
        
        Args:
            event (dict): Event information
            
        Returns:
            list: List of conflicting events, empty if no conflicts
        """
        # Parse event time range
        try:
            event_start, event_end = self._parse_time_range(event['time_range'])
        except ValueError:
            # Unable to parse time range, can't check for conflicts
            return []
            
        # Get all events for the same date
        date_events = self.get_events_for_date(event['date'])
        conflicts = []
        
        for db_event in date_events:
            # Skip if it's the same event being modified
            if event['action'] == '更改' and db_event.get('title') == event.get('title'):
                continue
                
            try:
                db_start, db_end = self._parse_time_range(db_event['time_range'])
                
                # Check for time overlap
                if (event_start < db_end and event_end > db_start):
                    conflicts.append(db_event)
            except ValueError:
                # Skip events with unparseable time ranges
                continue
                
        return conflicts
    
    def _add_event(self, event):
        """
        Add a new event to the database with duplicate and conflict checking.
        
        Args:
            event (dict): Event information
            
        Raises:
            ValueError: If event is a duplicate or conflicts with existing events
        """
        # Check for exact duplicate
        if self._check_duplicate_event(event):
            raise ValueError(f"Duplicate event: '{event['title']}' already exists with identical details")
            
        # Check for time conflicts
        conflicts = self._check_time_conflict(event)
        if conflicts:
            conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
            raise ValueError(f"Time conflict with existing events: {', '.join(conflict_details)}")
        
        # If checks pass, add the event
        self._add_event_no_check(event)
    
    def _modify_event(self, event):
        """
        Modify an existing event in the database with more flexible matching.
        
        Args:
            event (dict): Event information with the updated values
            
        Raises:
            ValueError: If event cannot be found for modification
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # More flexible lookup - just use title and date, not time_range
        # This way if the time changed, we can still find the event
        query = '''
        SELECT id, time_range FROM timetable
        WHERE title = ? AND date = ?
        '''
        
        params = (event['title'], event['date'])
        
        matches = self.db_manager.execute_query(query, params, 'all')
        
        if not matches:
            raise ValueError(f"Event '{event['title']}' not found for modification (no match for title+date)")
        
        # If there's only one match, use it
        if len(matches) == 1:
            event_id = matches[0]['id']
            
            # Now we can update all fields
            query = '''
            UPDATE timetable
            SET time_range = ?, event_type = ?, deadline = ?, importance = ?, recurrence_rule = ?, last_updated = ?
            WHERE id = ?
            '''
            
            params = (
                event['time_range'],
                event['event_type'],
                event['deadline'],
                event['importance'],
                event['recurrence_rule'],
                current_time,
                event_id
            )
            
            self.db_manager.execute_query(query, params)
        else:
            # Multiple matches - try to match by time_range if provided
            found = False
            for match in matches:
                # If the time range matches (or is close enough)
                if 'old_time_range' in event and match['time_range'].strip() == event['old_time_range'].strip():
                    query = '''
                    UPDATE timetable
                    SET time_range = ?, event_type = ?, deadline = ?, importance = ?, recurrence_rule = ?, last_updated = ?
                    WHERE id = ?
                    '''
                    
                    params = (
                        event['time_range'],
                        event['event_type'],
                        event['deadline'],
                        event['importance'],
                        event['recurrence_rule'],
                        current_time,
                        match['id']
                    )
                    
                    self.db_manager.execute_query(query, params)
                    found = True
                    break
            
            # If no match by old_time_range, use the first match
            if not found:
                query = '''
                UPDATE timetable
                SET time_range = ?, event_type = ?, deadline = ?, importance = ?, recurrence_rule = ?, last_updated = ?
                WHERE id = ?
                '''
                
                params = (
                    event['time_range'],
                    event['event_type'],
                    event['deadline'],
                    event['importance'],
                    event['recurrence_rule'],
                    current_time,
                    matches[0]['id']
                )
                
                self.db_manager.execute_query(query, params)
    
    def _delete_event(self, event):
        """
        Delete an event from the database.
        
        Args:
            event (dict): Event information
            
        Raises:
            ValueError: If event cannot be found for deletion
        """
        query = '''
        DELETE FROM timetable
        WHERE title = ? AND date = ? AND time_range = ?
        '''
        
        params = (
            event['title'],
            event['date'],
            event['time_range']
        )
        
        rows_affected = self.db_manager.execute_query(query, params)
        
        if rows_affected == 0:
            raise ValueError(f"Event '{event['title']}' not found for deletion")
    
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
    
    def delete_past_events(self, cutoff_time=None):
        """
        Delete all events that end before the specified cutoff time.

        Args:
            cutoff_time (str, optional): Cutoff time in format 'YYYY-MM-DD HH:MM'.
                                      If not specified, current time is used.

        Returns:
            dict: Results of the deletion operation:
                - deleted_count: Number of events deleted
                - deleted_events: List of deleted events
        """
        if cutoff_time is None:
            cutoff_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            cutoff_datetime = datetime.strptime(cutoff_time, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Invalid time format. Please use 'YYYY-MM-DD HH:MM' format")

        # Get all events to check against cutoff time
        query = 'SELECT * FROM timetable'
        all_events = self.db_manager.execute_query(query, None, 'all')
        
        deleted_events = []

        # Find events that end before the cutoff time
        for event in all_events:
            event_date = event['date']
            time_range = event['time_range']

            try:
                # Parse the event's end time
                end_time = time_range.split('-')[1].strip()
                event_end_datetime = datetime.strptime(f"{event_date} {end_time}", "%Y-%m-%d %H:%M")

                if event_end_datetime < cutoff_datetime:
                    deleted_events.append(event)
            except (ValueError, IndexError):
                continue  # Skip events with invalid time formats

        # Delete the identified events
        if deleted_events:
            event_ids = [event['id'] for event in deleted_events]
            id_placeholders = ', '.join(['?'] * len(event_ids))
            
            query = f'DELETE FROM timetable WHERE id IN ({id_placeholders})'
            self.db_manager.execute_query(query, event_ids)

        return {
            'deleted_count': len(deleted_events),
            'deleted_events': deleted_events
        }
