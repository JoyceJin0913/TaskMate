import re
import os
import csv
import sqlite3
from datetime import datetime


class TimetableProcessor:
    """Process timetable information from LLM outputs and manage database operations."""
    
    def __init__(self, database_type="sqlite", db_path="timetable.db", csv_path="timetable.csv"):
        """
        Initialize the processor with specified database type and path.
        
        Args:
            database_type (str): 'sqlite' or 'csv'
            db_path (str): Path to SQLite database
            csv_path (str): Path to CSV file
        """
        self.database_type = database_type.lower()
        self.db_path = db_path
        self.csv_path = csv_path
        
        if self.database_type == "sqlite":
            self._init_sqlite()
        elif self.database_type == "csv":
            self._init_csv()
        else:
            raise ValueError("Unsupported database type. Use 'sqlite' or 'csv'.")
    
    def _init_sqlite(self):
        """Initialize SQLite database and create table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time_range TEXT NOT NULL,
            event_type TEXT NOT NULL,
            deadline TEXT,
            importance INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'title', 'date', 'time_range', 'event_type', 
                                'deadline', 'importance', 'last_updated'])
    
    def extract_events(self, llm_output):
        """
        Extract event information from LLM output.
        
        Args:
            llm_output (str): The output text from the LLM
            
        Returns:
            list: List of dictionaries containing event information
        """
        # More robust pattern to match event details regardless of surrounding text
        pattern = r'事项:\s*(.*?)\s*日期:\s*(.*?)\s*时间段:\s*(.*?)\s*类型:\s*(.*?)(?:\s*截止日期：(.*?))?(?:\s*重要程度：(\d+))?\s*变动：(.*?)(?=\s*事项:|$)'
        
        # Find all matches - using DOTALL and MULTILINE flags for newline handling
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
        
        # First, collect all modifications so we can process them together
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
        
        # Process modifications next, with awareness of all modifications in the batch
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
            
            conn.commit()
            conn.close()
            
            return {
                'removed_duplicates': removed_count,
                'unique_events_kept': len(self.get_all_events())
            }
        
        elif self.database_type == "csv":
            if not os.path.exists(self.csv_path):
                return {'removed_duplicates': 0, 'unique_events_kept': 0}
                
            # Read all rows
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
                
            if len(rows) <= 1:  # Just header or empty
                return {'removed_duplicates': 0, 'unique_events_kept': 0}
                
            header = rows[0]
            data_rows = rows[1:]
            
            # Find unique events based on title, date, time_range, event_type
            unique_rows = []
            seen_events = set()
            removed_count = 0
            
            for row in data_rows:
                if len(row) < 5:  # Skip malformed rows
                    continue
                    
                # Create a unique identifier for each event
                event_key = f"{row[1]}|{row[2]}|{row[3]}|{row[4]}"
                
                if event_key not in seen_events:
                    seen_events.add(event_key)
                    unique_rows.append(row)
                else:
                    removed_count += 1
            
            # Write back the unique rows
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(header)
                writer.writerows(unique_rows)
            
            return {
                'removed_duplicates': removed_count,
                'unique_events_kept': len(unique_rows)
            }
            
    def _add_event_no_check(self, event):
        """Internal method to add event without duplicate/conflict checks."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO timetable (title, date, time_range, event_type, deadline, importance, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['title'], 
                event['date'], 
                event['time_range'], 
                event['event_type'],
                event['deadline'],
                event['importance'],
                current_time
            ))
            
            conn.commit()
            conn.close()
        
        elif self.database_type == "csv":
            # Read existing CSV to determine next ID
            next_id = 1
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    rows = list(reader)
                    if len(rows) > 1:  # More than just the header
                        next_id = max([int(row[0]) for row in rows[1:] if row[0].isdigit()], default=0) + 1
            
            # Append new event
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    next_id,
                    event['title'],
                    event['date'],
                    event['time_range'],
                    event['event_type'],
                    event['deadline'] or '',
                    event['importance'],
                    current_time
                ])
    
    def _check_duplicate_event(self, event):
        """
        Check if an exact duplicate of the event already exists in the database.
        
        Args:
            event (dict): Event information
            
        Returns:
            bool: True if exact duplicate exists, False otherwise
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM timetable
            WHERE title = ? AND date = ? AND time_range = ? AND event_type = ?
            ''', (
                event['title'],
                event['date'],
                event['time_range'],
                event['event_type']
            ))
            
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
            
        elif self.database_type == "csv":
            if not os.path.exists(self.csv_path):
                return False
                
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if (len(row) > 4 and
                        row[1] == event['title'] and
                        row[2] == event['date'] and
                        row[3] == event['time_range'] and
                        row[4] == event['event_type']):
                        return True
            
            return False
    
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
    
    def _add_event(self, event):
        """Add a new event to the database with duplicate and conflict checking."""
        # Check for exact duplicate
        if self._check_duplicate_event(event):
            raise ValueError(f"Duplicate event: '{event['title']}' already exists with identical details")
            
        # Check for time conflicts
        conflicts = self._check_time_conflict(event)
        if conflicts:
            conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
            raise ValueError(f"Time conflict with existing events: {', '.join(conflict_details)}")
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO timetable (title, date, time_range, event_type, deadline, importance, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['title'], 
                event['date'], 
                event['time_range'], 
                event['event_type'],
                event['deadline'],
                event['importance'],
                current_time
            ))
            
            conn.commit()
            conn.close()
        
        elif self.database_type == "csv":
            # Read existing CSV to determine next ID
            next_id = 1
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    rows = list(reader)
                    if len(rows) > 1:  # More than just the header
                        next_id = max([int(row[0]) for row in rows[1:] if row[0].isdigit()], default=0) + 1
            
            # Append new event
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    next_id,
                    event['title'],
                    event['date'],
                    event['time_range'],
                    event['event_type'],
                    event['deadline'] or '',
                    event['importance'],
                    current_time
                ])
    
    def _modify_event(self, event):
        """Modify an existing event in the database with more flexible matching."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # More flexible lookup - just use title and date, not time_range
            # This way if the time changed, we can still find the event
            cursor.execute('''
            SELECT id, time_range FROM timetable
            WHERE title = ? AND date = ?
            ''', (
                event['title'],
                event['date']
            ))
            
            matches = cursor.fetchall()
            if not matches:
                raise ValueError(f"Event '{event['title']}' not found for modification (no match for title+date)")
            
            # If there's only one match, use it
            if len(matches) == 1:
                event_id = matches[0][0]
                
                # Now we can update all fields
                cursor.execute('''
                UPDATE timetable
                SET time_range = ?, event_type = ?, deadline = ?, importance = ?, last_updated = ?
                WHERE id = ?
                ''', (
                    event['time_range'],
                    event['event_type'],
                    event['deadline'],
                    event['importance'],
                    current_time,
                    event_id
                ))
            else:
                # Multiple matches - try to match by time_range if provided
                found = False
                for event_id, db_time_range in matches:
                    # If the time range matches (or is close enough)
                    if event.get('old_time_range') and db_time_range.strip() == event['old_time_range'].strip():
                        cursor.execute('''
                        UPDATE timetable
                        SET time_range = ?, event_type = ?, deadline = ?, importance = ?, last_updated = ?
                        WHERE id = ?
                        ''', (
                            event['time_range'],
                            event['event_type'],
                            event['deadline'],
                            event['importance'],
                            current_time,
                            event_id
                        ))
                        found = True
                        break
                
                # If no match by old_time_range, use the first match
                if not found:
                    event_id = matches[0][0]
                    cursor.execute('''
                    UPDATE timetable
                    SET time_range = ?, event_type = ?, deadline = ?, importance = ?, last_updated = ?
                    WHERE id = ?
                    ''', (
                        event['time_range'],
                        event['event_type'],
                        event['deadline'],
                        event['importance'],
                        current_time,
                        event_id
                    ))
            
            conn.commit()
            conn.close()
        
        elif self.database_type == "csv":
            rows = []
            found = False
            
            # Read all rows
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
            
            # Update any row that matches by title and date
            for i, row in enumerate(rows):
                if i > 0 and row[1].strip() == event['title'].strip() and row[2].strip() == event['date'].strip():
                    rows[i][3] = event['time_range']
                    rows[i][4] = event['event_type']
                    rows[i][5] = event['deadline'] or ''
                    rows[i][6] = str(event['importance'])
                    rows[i][7] = current_time
                    found = True
            
            if not found:
                raise ValueError(f"Event '{event['title']}' not found for modification")
            
            # Write all rows back
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
    
    def _delete_event(self, event):
        """Delete an event from the database."""
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM timetable
            WHERE title = ? AND date = ? AND time_range = ?
            ''', (
                event['title'],
                event['date'],
                event['time_range']
            ))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Event '{event['title']}' not found for deletion")
            
            conn.commit()
            conn.close()
        
        elif self.database_type == "csv":
            rows = []
            found = False
            
            # Read all rows
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
            
            # Filter out the matching row
            new_rows = [rows[0]]  # Keep header
            for i, row in enumerate(rows):
                if i > 0:
                    if row[1] == event['title'] and row[2] == event['date'] and row[3] == event['time_range']:
                        found = True
                    else:
                        new_rows.append(row)
            
            if not found:
                raise ValueError(f"Event '{event['title']}' not found for deletion")
            
            # Write remaining rows back
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(new_rows)
    
    def get_all_events(self):
        """Retrieve all events from the database."""
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM timetable ORDER BY date, time_range')
            events = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return events
        
        elif self.database_type == "csv":
            events = []
            
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    events = list(reader)
            
            return events
            
    def format_events_as_llm_output(self, events=None, include_header=False):
        """
        Format events in the same structure as LLM output but without the '变动' field.
        
        Args:
            events (list, optional): List of event dictionaries. If None, retrieves all events from database.
            include_header (bool): Whether to include the '日程建议：' header.
            
        Returns:
            str: Formatted string in LLM output style
        """
        if events is None:
            events = self.get_all_events()
        
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
        
    def get_events_for_date(self, date):
        """
        Retrieve all events for a specific date.
        
        Args:
            date (str): Date in format 'YYYY-MM-DD'
            
        Returns:
            list: List of event dictionaries for the specified date
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM timetable WHERE date = ? ORDER BY time_range', (date,))
            events = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return events
        
        elif self.database_type == "csv":
            events = []
            
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    events = [row for row in reader if row['date'] == date]
            
            return sorted(events, key=lambda x: x['time_range'])

    def format_events_with_changes(self, old_events, new_events, include_header=False):
        """
        Format events with visual indicators showing changes between old and new states.
        
        Args:
            old_events (list): List of event dictionaries representing the old state
            new_events (list): List of event dictionaries representing the new state
            include_header (bool): Whether to include the header
            
        Returns:
            str: Formatted string showing changes with visual indicators:
                [+] for new events
                [-] for deleted events
                [*] for modified events
                [ ] for unchanged events
        """
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
                else:
                    # Event unchanged
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
            
            output.append("\n".join(event_lines))
        
        return "\n\n".join(output)
