from datetime import datetime, timedelta

def get_month_date_range(date=None):
    """
    Get the date range for a month.
    
    Args:
        date (datetime, optional): The date to get the range for. Defaults to current date.
        
    Returns:
        tuple: A tuple containing (first_day, last_day) of the month in YYYY-MM-DD format
    """
    if date is None:
        date = datetime.now()
        
    first_day = datetime(date.year, date.month, 1)
    next_month = first_day.replace(day=28) + timedelta(days=4)  # Jump to next month
    last_day = next_month.replace(day=1) - timedelta(days=1)    # Last day of current month
    
    return (
        format_date(first_day),
        format_date(last_day)
    )

def get_week_date_range(date=None):
    """
    Get the date range for a week.
    
    Args:
        date (datetime, optional): The date to get the range for. Defaults to current date.
        
    Returns:
        tuple: A tuple containing (first_day, last_day) of the week in YYYY-MM-DD format
    """
    if date is None:
        date = datetime.now()
        
    start_of_week = date - timedelta(days=date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    return (
        format_date(start_of_week),
        format_date(end_of_week)
    )

def format_date(date):
    """
    Format a date as YYYY-MM-DD.
    
    Args:
        date (datetime): The date to format
        
    Returns:
        str: The formatted date string
    """
    return date.strftime('%Y-%m-%d')

def parse_date(date_string):
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_string (str): The date string to parse
        
    Returns:
        datetime: The parsed date
    """
    try:
        year, month, day = map(int, date_string.split('-'))
        return datetime(year, month, day)
    except (ValueError, TypeError):
        return None

def parse_time_range(time_range):
    """
    Parse a time range string in HH:MM-HH:MM format.
    
    Args:
        time_range (str): The time range string
        
    Returns:
        dict: A dictionary with start_time, end_time, and duration in minutes
    """
    if not time_range or '-' not in time_range:
        return None
        
    try:
        start_str, end_str = time_range.split('-')
        
        start_hour, start_min = map(int, start_str.strip().split(':'))
        end_hour, end_min = map(int, end_str.strip().split(':'))
        
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        # Handle overnight events
        if end_minutes < start_minutes:
            end_minutes += 24 * 60  # Add 24 hours
            
        duration = end_minutes - start_minutes
        
        return {
            'start_time': {'hour': start_hour, 'minute': start_min},
            'end_time': {'hour': end_hour, 'minute': end_min},
            'start_minutes': start_minutes,
            'end_minutes': end_minutes,
            'duration_minutes': duration,
            'is_overnight': end_minutes > 24 * 60
        }
    except (ValueError, IndexError):
        return None
