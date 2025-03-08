import re
import os
import csv
import sqlite3
from datetime import datetime, timedelta, date


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
            # 确保数据库结构是最新的
            self._check_and_update_table_structure()
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
            recurrence_rule TEXT,
            completed INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建completed_task表用于存储历史复盘任务
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time_range TEXT NOT NULL,
            event_type TEXT NOT NULL,
            deadline TEXT,
            importance INTEGER,
            completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_notes TEXT,
            reflection_notes TEXT,
            FOREIGN KEY (task_id) REFERENCES timetable(id)
        )
        ''')
        
        # 检查并添加recurrence_rule列（如果不存在）
        self._check_and_update_table_structure(conn)
        
        conn.commit()
        conn.close()
    
    def _check_and_update_table_structure(self, conn=None):
        """
        检查并更新数据库表结构，确保所有必要的列都存在。
        
        Args:
            conn (sqlite3.Connection, optional): 现有的数据库连接。如果为None，将创建新连接。
        """
        if self.database_type != "sqlite":
            return
            
        close_conn = False
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            close_conn = True
            
        cursor = conn.cursor()
        
        # 获取timetable表的列信息
        cursor.execute("PRAGMA table_info(timetable)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 检查recurrence_rule列是否存在，如果不存在则添加
        if 'recurrence_rule' not in columns:
            print("Adding recurrence_rule column to timetable")
            cursor.execute("ALTER TABLE timetable ADD COLUMN recurrence_rule TEXT")
            conn.commit()
        
        # 检查completed列是否存在，如果不存在则添加
        if 'completed' not in columns:
            print("Adding completed column to timetable")
            cursor.execute("ALTER TABLE timetable ADD COLUMN completed INTEGER DEFAULT 0")
            conn.commit()
        
        if close_conn:
            conn.close()
    
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'title', 'date', 'time_range', 'event_type', 
                                'deadline', 'importance', 'recurrence_rule', 'last_updated'])
    
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
                'recurrence_rule': None,  # 默认为None
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
                'unique_events_kept': len(self.get_all_events())
            }
            
    def _add_event_no_check(self, event):
        """Internal method to add event without duplicate/conflict checks."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO timetable (title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['title'], 
                event['date'], 
                event['time_range'], 
                event['event_type'],
                event['deadline'],
                event['importance'],
                event['recurrence_rule'],
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
                    event['recurrence_rule'] or '',
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
            INSERT INTO timetable (title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['title'], 
                event['date'], 
                event['time_range'], 
                event['event_type'],
                event['deadline'],
                event['importance'],
                event['recurrence_rule'],
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
                    event['recurrence_rule'] or '',
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
                SET time_range = ?, event_type = ?, deadline = ?, importance = ?, recurrence_rule = ?, last_updated = ?
                WHERE id = ?
                ''', (
                    event['time_range'],
                    event['event_type'],
                    event['deadline'],
                    event['importance'],
                    event['recurrence_rule'],
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
                        SET time_range = ?, event_type = ?, deadline = ?, importance = ?, recurrence_rule = ?, last_updated = ?
                        WHERE id = ?
                        ''', (
                            event['time_range'],
                            event['event_type'],
                            event['deadline'],
                            event['importance'],
                            event['recurrence_rule'],
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
                    SET time_range = ?, event_type = ?, deadline = ?, importance = ?, recurrence_rule = ?, last_updated = ?
                    WHERE id = ?
                    ''', (
                        event['time_range'],
                        event['event_type'],
                        event['deadline'],
                        event['importance'],
                        event['recurrence_rule'],
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
                    rows[i][7] = event['recurrence_rule'] or ''
                    rows[i][8] = current_time
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
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM timetable'
            params = []
            
            # 添加日期范围过滤
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
            
            # 添加分页
            if limit is not None:
                query += ' LIMIT ?'
                params.append(limit)
                
                if offset:
                    query += ' OFFSET ?'
                    params.append(offset)
            
            cursor.execute(query, params)
            events = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return events
        
        elif self.database_type == "csv":
            events = []
            
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    
                    # 读取所有事件并应用过滤
                    filtered_events = []
                    for event in reader:
                        # 应用日期范围过滤
                        if date_from and event['date'] < date_from:
                            continue
                        if date_to and event['date'] > date_to:
                            continue
                        filtered_events.append(event)
                    
                    # 排序
                    filtered_events.sort(key=lambda x: (x['date'], x['time_range']))
                    
                    # 应用分页
                    if limit is not None:
                        start_idx = offset
                        end_idx = offset + limit
                        events = filtered_events[start_idx:end_idx]
                    else:
                        events = filtered_events
            
            return events
    
    def get_events_iterator(self, date_from=None, date_to=None, batch_size=100):
        """
        返回一个迭代器，按批次获取事件，避免一次性加载所有事件到内存中。
        
        Args:
            date_from (str, optional): 开始日期，格式为 'YYYY-MM-DD'
            date_to (str, optional): 结束日期，格式为 'YYYY-MM-DD'
            batch_size (int): 每批次返回的事件数量
            
        Returns:
            iterator: 事件批次的迭代器
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
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM timetable WHERE date = ? ORDER BY time_range'
            params = [date]
            
            # 添加分页
            if limit is not None:
                query += ' LIMIT ?'
                params.append(limit)
                
                if offset:
                    query += ' OFFSET ?'
                    params.append(offset)
            
            cursor.execute(query, params)
            events = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return events
        
        elif self.database_type == "csv":
            events = []
            
            if os.path.exists(self.csv_path):
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    events = [row for row in reader if row['date'] == date]
            
            events = sorted(events, key=lambda x: x['time_range'])
            
            # 应用分页
            if limit is not None:
                start_idx = offset
                end_idx = offset + limit
                events = events[start_idx:end_idx]
                
            return events
    
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
        # 如果未提供事件列表，则根据过滤条件获取
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
        
        # 创建变更事件列表，优先显示有变化的事件
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
        
        # 合并变更和未变更事件，优先显示变更事件
        all_formatted_events = changed_events + unchanged_events
        
        # 应用 limit 参数
        if limit is not None and limit > 0:
            all_formatted_events = all_formatted_events[:limit]
        
        # 添加格式化的事件到输出
        output.extend(all_formatted_events)
        
        return "\n\n".join(output)

    def delete_past_events(self, cutoff_time=None):
        """
        删除所有在指定时间之前结束的事件。

        Args:
            cutoff_time (str, optional): 截止时间，格式为 'YYYY-MM-DD HH:MM'。
                                       如果未指定，则使用当前时间。

        Returns:
            dict: 包含删除操作结果的字典：
                - deleted_count: 删除的事件数量
                - deleted_events: 被删除事件的列表
        """
        if cutoff_time is None:
            cutoff_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            cutoff_datetime = datetime.strptime(cutoff_time, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("无效的时间格式。请使用 'YYYY-MM-DD HH:MM' 格式")

        deleted_events = []

        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 首先获取所有可能需要删除的事件
            cursor.execute('SELECT * FROM timetable')
            all_events = [dict(row) for row in cursor.fetchall()]

            # 找出需要删除的事件
            for event in all_events:
                event_date = event['date']
                time_range = event['time_range']

                try:
                    # 解析事件的结束时间
                    end_time = time_range.split('-')[1].strip()
                    event_end_datetime = datetime.strptime(f"{event_date} {end_time}", "%Y-%m-%d %H:%M")

                    if event_end_datetime < cutoff_datetime:
                        deleted_events.append(event)
                except (ValueError, IndexError):
                    continue  # 跳过无效的时间格式

            # 删除符合条件的事件
            if deleted_events:
                event_ids = [str(event['id']) for event in deleted_events]
                cursor.execute(f'''
                DELETE FROM timetable
                WHERE id IN ({",".join(event_ids)})
                ''')
                conn.commit()

            conn.close()

        elif self.database_type == "csv":
            if not os.path.exists(self.csv_path):
                return {'deleted_count': 0, 'deleted_events': []}

            # 读取所有行
            rows = []
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                header = reader.fieldnames
                for row in reader:
                    event_date = row['date']
                    time_range = row['time_range']

                    try:
                        # 解析事件的结束时间
                        end_time = time_range.split('-')[1].strip()
                        event_end_datetime = datetime.strptime(f"{event_date} {end_time}", "%Y-%m-%d %H:%M")

                        if event_end_datetime < cutoff_datetime:
                            deleted_events.append(row)
                        else:
                            rows.append(row)
                    except (ValueError, IndexError):
                        rows.append(row)  # 保留无效时间格式的事件

            # 写回剩余的行
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=header)
                writer.writeheader()
                writer.writerows(rows)

        return {
            'deleted_count': len(deleted_events),
            'deleted_events': deleted_events
        }

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
        events = self.extract_events(llm_output)
        
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
                # 直接设置重复规则，不依赖于事件描述中的规则
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
                            self._add_event_no_check(occurrence_event)
                            summary['added'] += 1
                        else:
                            # Check for conflicts
                            conflicts = self._check_time_conflict(occurrence_event)
                            if conflicts and handle_conflicts == 'skip':
                                summary['skipped'] += 1
                                continue
                            elif conflicts:
                                conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
                                raise ValueError(f"Time conflict on {occurrence_event['date']} with existing events: {', '.join(conflict_details)}")
                            
                            # No conflicts or force mode, add the event
                            self._add_event_no_check(occurrence_event)
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
        """Return the number of days in a given month."""
        if month == 2:  # February
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # Leap year
                return 29
            return 28
        elif month in [4, 6, 9, 11]:  # April, June, September, November
            return 30
        else:
            return 31

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
        
        # 确保数据库结构是最新的
        if self.database_type == "sqlite":
            self._check_and_update_table_structure()
        
        # 获取原始事件
        original_event = None
        
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT title, date, time_range, event_type, deadline, importance
            FROM timetable WHERE id = ?
            ''', (event_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                raise ValueError(f"Event with ID {event_id} not found")
                
            original_event = {
                'title': result[0],
                'date': result[1],
                'time_range': result[2],
                'event_type': result[3],
                'deadline': result[4],
                'importance': result[5],
                'recurrence_rule': recurrence_rule,
                'action': '新增'  # 标记为新增，因为我们要创建新的重复事件
            }
            
        elif self.database_type == "csv":
            if not os.path.exists(self.csv_path):
                raise ValueError("CSV file does not exist")
                
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)
                
                # 检查CSV文件是否有recurrence_rule列
                if len(header) <= 7 or header[7] != 'recurrence_rule':
                    summary['warnings'].append("recurrence_rule column does not exist in the CSV file, it will be added")
                    # 我们将在后面处理这个问题
                
                for row in reader:
                    if int(row[0]) == event_id:
                        original_event = {
                            'title': row[1],
                            'date': row[2],
                            'time_range': row[3],
                            'event_type': row[4],
                            'deadline': row[5] if row[5] else None,
                            'importance': int(row[6]) if row[6] else 0,
                            'recurrence_rule': recurrence_rule,
                            'action': '新增'  # 标记为新增，因为我们要创建新的重复事件
                        }
                        break
                        
            if not original_event:
                raise ValueError(f"Event with ID {event_id} not found")
        
        # 设置默认结束日期为一年后
        if end_date is None:
            default_end = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            end_date = default_end
            summary['warnings'].append(f"No end date provided, defaulting to one year: {default_end}")
        
        try:
            # 获取初始日期
            start_date = datetime.strptime(original_event['date'], '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            
            # 生成所有重复日期
            occurrences = self._generate_occurrences(start_date, recurrence_rule, end_date_obj)
            
            # 跳过第一个日期，因为它已经存在
            occurrences = occurrences[1:] if len(occurrences) > 1 else []
            
            # 为每个重复日期添加事件
            for occurrence_date in occurrences:
                # 创建事件副本并更新日期
                occurrence_event = original_event.copy()
                occurrence_event['date'] = occurrence_date.strftime('%Y-%m-%d')
                
                try:
                    # 根据冲突处理策略添加事件
                    if handle_conflicts == 'force':
                        self._add_event_no_check(occurrence_event)
                        summary['added'] += 1
                    else:
                        # 检查冲突
                        conflicts = self._check_time_conflict(occurrence_event)
                        if conflicts and handle_conflicts == 'skip':
                            summary['skipped'] += 1
                            continue
                        elif conflicts:
                            conflict_details = [f"'{c['title']}' ({c['time_range']})" for c in conflicts]
                            raise ValueError(f"Time conflict on {occurrence_event['date']} with existing events: {', '.join(conflict_details)}")
                        
                        # 无冲突或强制模式，添加事件
                        self._add_event_no_check(occurrence_event)
                        summary['added'] += 1
                except ValueError as e:
                    if handle_conflicts == 'error':
                        # 重新抛出错误以停止处理
                        raise
                    summary['errors'].append(str(e))
                    summary['skipped'] += 1
            
            # 更新原始事件的重复规则
            if self.database_type == "sqlite":
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    # 检查recurrence_rule列是否存在
                    cursor.execute("PRAGMA table_info(timetable)")
                    columns = [column[1] for column in cursor.fetchall()]
                    
                    if 'recurrence_rule' not in columns:
                        # 添加recurrence_rule列
                        cursor.execute("ALTER TABLE timetable ADD COLUMN recurrence_rule TEXT")
                        conn.commit()
                        summary['warnings'].append("Added recurrence_rule column to the database")
                    
                    cursor.execute('''
                    UPDATE timetable SET recurrence_rule = ? WHERE id = ?
                    ''', (recurrence_rule, event_id))
                    
                    conn.commit()
                    conn.close()
                except sqlite3.OperationalError as e:
                    summary['errors'].append(f"Error updating recurrence rule: {e}")
                
            elif self.database_type == "csv":
                rows = []
                with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    rows = list(reader)
                
                # 检查是否需要添加recurrence_rule列
                header = rows[0]
                if len(header) <= 7 or header[7] != 'recurrence_rule':
                    # 添加recurrence_rule列到标题
                    if len(header) <= 7:
                        header.append('recurrence_rule')
                    else:
                        header[7] = 'recurrence_rule'
                    
                    # 为所有行添加空的recurrence_rule值
                    for i in range(1, len(rows)):
                        if len(rows[i]) <= 7:
                            rows[i].append('')
                    
                    summary['warnings'].append("Added recurrence_rule column to the CSV file")
                
                # 更新事件的recurrence_rule
                for i, row in enumerate(rows):
                    if i > 0 and int(row[0]) == event_id:
                        if len(row) <= 7:
                            row.append(recurrence_rule)
                        else:
                            row[7] = recurrence_rule
                        break
                
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)
            
        except Exception as e:
            summary['errors'].append(f"Error applying recurrence to event ID {event_id}: {str(e)}")
        
        return summary

    def get_recurring_events(self):
        """
        Get all events that have a recurrence rule set.
        
        Returns:
            list: List of events with recurrence rules
        """
        recurring_events = []
        
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 首先检查recurrence_rule列是否存在
            cursor.execute("PRAGMA table_info(timetable)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'recurrence_rule' not in columns:
                print("Warning: recurrence_rule column does not exist in the database")
                conn.close()
                return []
            
            try:
                cursor.execute('''
                SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule
                FROM timetable
                WHERE recurrence_rule IS NOT NULL AND recurrence_rule != ''
                ORDER BY date
                ''')
                
                for row in cursor.fetchall():
                    event = {
                        'id': row[0],
                        'title': row[1],
                        'date': row[2],
                        'time_range': row[3],
                        'event_type': row[4],
                        'deadline': row[5],
                        'importance': row[6],
                        'recurrence_rule': row[7]
                    }
                    recurring_events.append(event)
            except sqlite3.OperationalError as e:
                print(f"Error querying recurring events: {e}")
                # 尝试更新表结构
                self._check_and_update_table_structure(conn)
                print("Database structure has been updated. Please try again.")
                
            conn.close()
            
        elif self.database_type == "csv":
            if not os.path.exists(self.csv_path):
                return []
                
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)
                
                # 检查CSV文件是否有recurrence_rule列
                if len(header) <= 7 or header[7] != 'recurrence_rule':
                    print("Warning: recurrence_rule column does not exist in the CSV file")
                    return []
                
                for row in reader:
                    if len(row) > 7 and row[7]:  # 检查recurrence_rule是否存在且非空
                        event = {
                            'id': int(row[0]),
                            'title': row[1],
                            'date': row[2],
                            'time_range': row[3],
                            'event_type': row[4],
                            'deadline': row[5] if row[5] else None,
                            'importance': int(row[6]) if row[6] else 0,
                            'recurrence_rule': row[7]
                        }
                        recurring_events.append(event)
        
        return recurring_events
        
    def remove_recurrence(self, event_id):
        """
        Remove the recurrence rule from an event.
        
        Args:
            event_id (int): The ID of the event to remove recurrence from
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 首先检查recurrence_rule列是否存在
            cursor.execute("PRAGMA table_info(timetable)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'recurrence_rule' not in columns:
                print("Warning: recurrence_rule column does not exist in the database")
                conn.close()
                return False
            
            try:
                cursor.execute('''
                UPDATE timetable SET recurrence_rule = NULL
                WHERE id = ?
                ''', (event_id,))
                
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                
                return affected > 0
            except sqlite3.OperationalError as e:
                print(f"Error removing recurrence: {e}")
                # 尝试更新表结构
                self._check_and_update_table_structure(conn)
                print("Database structure has been updated. Please try again.")
                conn.close()
                return False
            
        elif self.database_type == "csv":
            if not os.path.exists(self.csv_path):
                return False
                
            rows = []
            found = False
            
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
                
                # 检查CSV文件是否有recurrence_rule列
                header = rows[0]
                if len(header) <= 7 or header[7] != 'recurrence_rule':
                    print("Warning: recurrence_rule column does not exist in the CSV file")
                    return False
                
            for i, row in enumerate(rows):
                if i > 0 and int(row[0]) == event_id:
                    if len(row) > 7:  # 确保行有足够的列
                        rows[i][7] = ''  # 清空recurrence_rule
                        found = True
                    break
                    
            if found:
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows)
                    
            return found

    def mark_event_completed(self, event_id, completed=True):
        """
        标记事件为已完成或未完成。
        
        Args:
            event_id (int): 事件ID
            completed (bool): 是否已完成，默认为True
        
        Returns:
            bool: 操作是否成功
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 将布尔值转换为整数（0或1）
                completed_int = 1 if completed else 0
                
                # 更新事件的完成状态
                cursor.execute(
                    'UPDATE timetable SET completed = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?',
                    (completed_int, event_id)
                )
                
                conn.commit()
                success = cursor.rowcount > 0
                conn.close()
                return success
            except Exception as e:
                print(f"Error marking event as completed: {e}")
                conn.close()
                return False
        elif self.database_type == "csv":
            # 读取所有事件
            events = []
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['id'] == str(event_id):
                        row['completed'] = '1' if completed else '0'
                        row['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    events.append(row)
            
            # 写回所有事件
            try:
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(events)
                return True
            except Exception as e:
                print(f"Error marking event as completed in CSV: {e}")
                return False
    
    def get_completed_events(self, date_from=None, date_to=None, limit=None, offset=0):
        """
        获取已完成的事件。
        
        Args:
            date_from (str, optional): 开始日期，格式为'YYYY-MM-DD'
            date_to (str, optional): 结束日期，格式为'YYYY-MM-DD'
            limit (int, optional): 最大返回事件数
            offset (int, optional): 跳过的事件数
        
        Returns:
            list: 已完成事件列表
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM timetable WHERE completed = 1'
            params = []
            
            # 添加日期范围过滤
            if date_from:
                query += ' AND date >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND date <= ?'
                params.append(date_to)
            
            # 添加排序
            query += ' ORDER BY date DESC, time_range'
            
            # 添加分页
            if limit is not None:
                query += ' LIMIT ?'
                params.append(limit)
                
                if offset:
                    query += ' OFFSET ?'
                    params.append(offset)
            
            cursor.execute(query, params)
            events = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return events
        elif self.database_type == "csv":
            events = []
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('completed') == '1':
                        # 日期范围过滤
                        if date_from and row['date'] < date_from:
                            continue
                        if date_to and row['date'] > date_to:
                            continue
                        events.append(row)
            
            # 排序
            events.sort(key=lambda x: (x['date'], x['time_range']), reverse=True)
            
            # 分页
            if offset:
                events = events[offset:]
            if limit is not None:
                events = events[:limit]
                
            return events

    def mark_task_completed_with_history(self, event_id, completion_notes=None, reflection_notes=None):
        """
        将任务标记为已完成，并将其添加到历史记录中。
        
        Args:
            event_id (int): 任务ID
            completion_notes (str, optional): 完成情况备注
            reflection_notes (str, optional): 复盘笔记
            
        Returns:
            bool: 操作是否成功
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 首先获取任务详情
                cursor.execute('''
                SELECT title, date, time_range, event_type, deadline, importance
                FROM timetable WHERE id = ?
                ''', (event_id,))
                
                task = cursor.fetchone()
                if not task:
                    raise ValueError(f"Task with ID {event_id} not found")
                
                # 将任务标记为已完成
                cursor.execute(
                    'UPDATE timetable SET completed = 1, last_updated = CURRENT_TIMESTAMP WHERE id = ?',
                    (event_id,)
                )
                
                # 添加到历史记录
                cursor.execute('''
                INSERT INTO completed_task (
                    task_id, title, date, time_range, event_type, deadline, 
                    importance, completion_notes, reflection_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id, task[0], task[1], task[2], task[3], task[4], 
                    task[5], completion_notes, reflection_notes
                ))
                
                conn.commit()
                success = cursor.rowcount > 0
                conn.close()
                return success
                
            except Exception as e:
                print(f"Error marking task as completed: {e}")
                conn.close()
                return False
                
    def add_task_reflection(self, task_id, reflection_notes):
        """
        为已完成的任务添加或更新复盘笔记。
        
        Args:
            task_id (int): 任务ID
            reflection_notes (str): 复盘笔记
            
        Returns:
            bool: 操作是否成功
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 更新复盘笔记
                cursor.execute('''
                UPDATE completed_task 
                SET reflection_notes = ?
                WHERE task_id = ?
                ''', (reflection_notes, task_id))
                
                conn.commit()
                success = cursor.rowcount > 0
                conn.close()
                return success
                
            except Exception as e:
                print(f"Error adding reflection notes: {e}")
                conn.close()
                return False
                
    def get_task_history(self, date_from=None, date_to=None, limit=None, offset=0):
        """
        获取任务完成历史记录。
        
        Args:
            date_from (str, optional): 开始日期，格式为'YYYY-MM-DD'
            date_to (str, optional): 结束日期，格式为'YYYY-MM-DD'
            limit (int, optional): 最大返回记录数
            offset (int, optional): 跳过的记录数
            
        Returns:
            list: 历史记录列表
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
            SELECT * FROM completed_task 
            WHERE 1=1
            '''
            params = []
            
            # 添加日期范围过滤
            if date_from:
                query += ' AND date >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND date <= ?'
                params.append(date_to)
            
            # 添加排序
            query += ' ORDER BY completion_date DESC'
            
            # 添加分页
            if limit is not None:
                query += ' LIMIT ?'
                params.append(limit)
                
                if offset:
                    query += ' OFFSET ?'
                    params.append(offset)
            
            cursor.execute(query, params)
            history = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return history
            
        elif self.database_type == "csv":
            # 实现CSV文件的历史记录获取逻辑
            # 这里需要根据CSV文件的存储格式来实现
            raise NotImplementedError("CSV文件的历史记录获取逻辑尚未实现")

    def get_task_reflection(self, task_id):
        """
        获取特定任务的复盘记录。
        
        Args:
            task_id (int): 任务ID
            
        Returns:
            dict: 任务的复盘记录
        """
        if self.database_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM completed_task 
            WHERE task_id = ?
            ''', (task_id,))
            
            result = cursor.fetchone()
            reflection = dict(result) if result else None
            
            conn.close()
            return reflection
        elif self.database_type == "csv":
            # 实现CSV文件的复盘记录获取逻辑
            # 这里需要根据CSV文件的存储格式来实现
            raise NotImplementedError("CSV文件的复盘记录获取逻辑尚未实现")
