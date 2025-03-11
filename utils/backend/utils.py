import re
from datetime import datetime, timedelta

class TimetableUtils:
    """
    Utility functions for timetable operations that may be used across multiple components.
    """
    
    @staticmethod
    def parse_time_range(time_range):
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
    
    @staticmethod
    def format_time_range(start_minutes, end_minutes):
        """
        Format minutes from midnight into a time range string.
        
        Args:
            start_minutes (int): Start time in minutes from midnight
            end_minutes (int): End time in minutes from midnight
            
        Returns:
            str: Formatted time range string 'HH:MM-HH:MM'
        """
        start_hours = start_minutes // 60
        start_mins = start_minutes % 60
        
        end_hours = end_minutes // 60
        end_mins = end_minutes % 60
        
        return f"{start_hours:02d}:{start_mins:02d}-{end_hours:02d}:{end_mins:02d}"
    
    @staticmethod
    def get_days_in_month(year, month):
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
    
    @staticmethod
    def validate_date_format(date_str):
        """
        Validate if a string has the correct date format 'YYYY-MM-DD'.
        
        Args:
            date_str (str): Date string to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not date_str:
            return False
            
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, date_str):
            return False
            
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_date_range(start_date, end_date):
        """
        Generate a list of dates between start_date and end_date, inclusive.
        
        Args:
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            list: List of date strings in 'YYYY-MM-DD' format
        """
        if not TimetableUtils.validate_date_format(start_date) or not TimetableUtils.validate_date_format(end_date):
            raise ValueError("Invalid date format. Use 'YYYY-MM-DD'")
            
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        date_list = []
        current = start
        
        while current <= end:
            date_list.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
            
        return date_list
    
    @staticmethod
    def get_next_occurrence(base_date, recurrence_rule):
        """
        Calculate the next occurrence date based on a recurrence rule.
        
        Args:
            base_date (str): Base date in format 'YYYY-MM-DD'
            recurrence_rule (str): Recurrence rule ('daily', 'weekly', etc.)
            
        Returns:
            str: Next occurrence date in format 'YYYY-MM-DD'
        """
        if not TimetableUtils.validate_date_format(base_date):
            raise ValueError("Invalid date format. Use 'YYYY-MM-DD'")
            
        date_obj = datetime.strptime(base_date, '%Y-%m-%d')
        
        if recurrence_rule == 'daily':
            next_date = date_obj + timedelta(days=1)
        elif recurrence_rule == 'weekly':
            next_date = date_obj + timedelta(days=7)
        elif recurrence_rule == 'weekdays':
            next_date = date_obj + timedelta(days=1)
            # Skip weekends
            while next_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                next_date = next_date + timedelta(days=1)
        elif recurrence_rule == 'monthly':
            # Move to the next month, same day
            year = date_obj.year
            month = date_obj.month + 1
            
            if month > 12:
                month = 1
                year += 1
                
            # Handle month length differences
            day = min(date_obj.day, TimetableUtils.get_days_in_month(year, month))
            next_date = datetime(year, month, day)
        elif recurrence_rule == 'yearly':
            # Move to the next year, same month and day
            try:
                next_date = date_obj.replace(year=date_obj.year + 1)
            except ValueError:
                # Handle February 29 in leap years
                if date_obj.month == 2 and date_obj.day == 29:
                    next_date = datetime(date_obj.year + 1, 3, 1)
        else:
            raise ValueError(f"Unsupported recurrence rule: {recurrence_rule}")
            
        return next_date.strftime('%Y-%m-%d')
    
    @staticmethod
    def has_time_conflict(time_range1, time_range2):
        """
        Check if two time ranges have a conflict (overlap).
        
        Args:
            time_range1 (str): First time range in format 'HH:MM-HH:MM'
            time_range2 (str): Second time range in format 'HH:MM-HH:MM'
            
        Returns:
            bool: True if there is a conflict, False otherwise
        """
        try:
            start1, end1 = TimetableUtils.parse_time_range(time_range1)
            start2, end2 = TimetableUtils.parse_time_range(time_range2)
            
            # Check for overlap
            return start1 < end2 and end1 > start2
        except ValueError:
            # If we can't parse either time range, assume no conflict
            return False
