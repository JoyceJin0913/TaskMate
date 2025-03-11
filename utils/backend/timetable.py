from utils.backend.database_manager import DatabaseManager
from utils.backend.event_processor import EventProcessor
from utils.backend.event_retriever import EventRetriever
from utils.backend.recurrence_manager import RecurrenceManager
from utils.backend.completion_tracker import CompletionTracker


class Timetable:
    """
    Main class that ties together all components of the timetable system.
    Provides a unified interface for interacting with events, recurrence,
    and completion tracking functionality.
    """
    
    def __init__(self, database_type="sqlite", db_path="timetable.db"):
        """
        Initialize the timetable system with all necessary components.
        
        Args:
            database_type (str): Type of database to use (currently only 'sqlite' is supported)
            db_path (str): Path to the database file
        """
        # Initialize the database manager first
        self.db_manager = DatabaseManager(database_type, db_path)
        
        # Initialize all other components with the database manager
        self.event_processor = EventProcessor(self.db_manager)
        self.event_retriever = EventRetriever(self.db_manager)
        self.recurrence_manager = RecurrenceManager(self.db_manager, self.event_processor)
        self.completion_tracker = CompletionTracker(self.db_manager)
    
    # ===== Event Processing Methods =====
    
    def extract_events(self, llm_output):
        """
        Extract event information from LLM output.
        
        Args:
            llm_output (str): The output text from the LLM
            
        Returns:
            list: List of dictionaries containing event information
        """
        return self.event_processor.extract_events(llm_output)
    
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
        return self.event_processor.process_events(llm_output, handle_conflicts)
    
    def delete_past_events(self, cutoff_time=None):
        """
        Delete all events that end before the specified cutoff time.
        
        Args:
            cutoff_time (str, optional): Cutoff time in format 'YYYY-MM-DD HH:MM'.
                                      If not specified, current time is used.
                                      
        Returns:
            dict: Results of the deletion operation
        """
        return self.event_processor.delete_past_events(cutoff_time)
    
    # ===== Event Retrieval Methods =====
    
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
        return self.event_retriever.get_all_events(date_from, date_to, limit, offset)
    
    def get_events_iterator(self, date_from=None, date_to=None, batch_size=100):
        """
        Return an iterator that retrieves events in batches.
        
        Args:
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            batch_size (int): Number of events to retrieve in each batch
            
        Returns:
            iterator: Iterator yielding batches of events
        """
        return self.event_retriever.get_events_iterator(date_from, date_to, batch_size)
    
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
        return self.event_retriever.get_events_for_date(date, limit, offset)
    
    def format_events_as_llm_output(self, events=None, include_header=False, 
                                   date_from=None, date_to=None, limit=None, offset=0):
        """
        Format events as a string in the format expected by the LLM.
        
        Args:
            events (list, optional): List of events to format
            include_header (bool): Whether to include the header in the output
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            
        Returns:
            str: Formatted events string
        """
        return self.event_retriever.format_events_as_llm_output(
            events, include_header, date_from, date_to, limit, offset)
    
    def format_events_with_changes(self, old_events=None, new_events=None, include_header=False,
                                  date_from=None, date_to=None, limit=None, offset=0, show_unchanged=True):
        """
        Format events with visual indicators showing changes between old and new states.
        
        Args:
            old_events (list, optional): List of event dictionaries representing the old state
            new_events (list, optional): List of event dictionaries representing the new state
            include_header (bool): Whether to include the header
            date_from (str, optional): Start date in format 'YYYY-MM-DD'
            date_to (str, optional): End date in format 'YYYY-MM-DD'
            limit (int, optional): Maximum number of events to return
            offset (int, optional): Number of events to skip
            show_unchanged (bool): Whether to include unchanged events in the output
            
        Returns:
            str: Formatted string showing changes with visual indicators
        """
        return self.event_retriever.format_events_with_changes(
            old_events, new_events, include_header, date_from, 
            date_to, limit, offset, show_unchanged)
    
    # ===== Recurrence Management Methods =====
    
    def process_recurring_events(self, llm_output, recurrence_rule, end_date=None, handle_conflicts='error'):
        """
        Process events from LLM output and add them as recurring events.
        
        Args:
            llm_output (str): The output text from the LLM
            recurrence_rule (str): The recurrence rule ('daily', 'weekly', etc.)
            end_date (str, optional): The end date for the recurrence in 'YYYY-MM-DD' format
            handle_conflicts (str): How to handle time conflicts
            
        Returns:
            dict: Summary of operations performed
        """
        return self.recurrence_manager.process_recurring_events(
            llm_output, recurrence_rule, end_date, handle_conflicts)
    
    def apply_recurrence_to_event(self, event_id, recurrence_rule, end_date=None, handle_conflicts='error'):
        """
        Apply a recurrence rule to an existing event.
        
        Args:
            event_id (int): The ID of the event to apply recurrence to
            recurrence_rule (str): The recurrence rule ('daily', 'weekly', etc.)
            end_date (str, optional): The end date for the recurrence in 'YYYY-MM-DD' format
            handle_conflicts (str): How to handle time conflicts
            
        Returns:
            dict: Summary of operations performed
        """
        return self.recurrence_manager.apply_recurrence_to_event(
            event_id, recurrence_rule, end_date, handle_conflicts)
    
    def get_recurring_events(self):
        """
        Get all events that have a recurrence rule set.
        
        Returns:
            list: List of events with recurrence rules
        """
        return self.recurrence_manager.get_recurring_events()
    
    def remove_recurrence(self, event_id):
        """
        Remove the recurrence rule from an event.
        
        Args:
            event_id (int): The ID of the event to remove recurrence from
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.recurrence_manager.remove_recurrence(event_id)
    
    # ===== Completion Tracking Methods =====
    
    def mark_event_completed(self, event_id, completed=True, completion_notes=None, 
                            reflection_notes=None, event_date=None, actual_time_range=None):
        """
        Mark an event as completed or not completed.
        
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
        return self.completion_tracker.mark_event_completed(
            event_id, completed, completion_notes, reflection_notes, event_date, actual_time_range)
    
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
        return self.completion_tracker.get_completed_events(date_from, date_to, limit, offset)
    
    def add_task_reflection(self, task_id, reflection_notes):
        """
        Add or update reflection notes for a completed task.
        
        Args:
            task_id (int): The task ID
            reflection_notes (str): Reflection notes
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        return self.completion_tracker.add_task_reflection(task_id, reflection_notes)
    
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
        return self.completion_tracker.get_task_history(date_from, date_to, limit, offset)
    
    def get_task_reflection(self, task_id):
        """
        Get reflection notes for a specific task.
        
        Args:
            task_id (int): The task ID
            
        Returns:
            dict: Task details including reflection notes, or None if not found
        """
        return self.completion_tracker.get_task_reflection(task_id)
    
    def delete_completed_task(self, task_id):
        """
        Delete a completed task from the history.
        
        Args:
            task_id (int): The task ID
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        return self.completion_tracker.delete_completed_task(task_id)
    
    # ===== Database Management Methods =====
    
    def remove_duplicates(self):
        """
        Remove duplicate events from the database.
        
        Returns:
            dict: Summary of operation with count of removed duplicates
        """
        return self.db_manager.remove_duplicates()
