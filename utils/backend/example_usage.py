from timetable import Timetable
from datetime import datetime, timedelta

def main():
    """
    Example usage of the Timetable system.
    This demonstrates the main functionality of the system.
    """
    # Initialize the timetable system
    print("Initializing Timetable system...")
    timetable = Timetable(db_path="example_timetable.db")
    
    # Process events from an LLM output
    llm_output = """
    事项: 团队会议
    日期: 2025-03-15
    时间段: 09:00-10:30
    类型: 工作
    重要程度：5
    变动：新增

    事项: 项目演示
    日期: 2025-03-16
    时间段: 14:00-15:30
    类型: 工作
    截止日期：2025-03-16
    重要程度：8
    变动：新增
    
    事项: 健身锻炼
    日期: 2025-03-15
    时间段: 18:00-19:00
    类型: 个人
    重要程度：4
    变动：新增
    """
    
    print("\nProcessing events from LLM output...")
    result = timetable.process_events(llm_output)
    print(f"Added {result['added']} events, modified {result['modified']}, deleted {result['deleted']}")
    
    # Retrieve and display events for a specific date
    print("\nRetrieving events for 2025-03-15:")
    events = timetable.get_events_for_date("2025-03-15")
    for event in events:
        print(f"- {event['title']} ({event['time_range']}): {event['event_type']}")
    
    # Set up a recurring event
    recurring_llm_output = """
    事项: 每日站会
    日期: 2025-03-15
    时间段: 08:30-09:00
    类型: 工作
    重要程度：6
    变动：新增
    """
    
    print("\nSetting up a recurring event...")
    recurrence_result = timetable.process_recurring_events(
        recurring_llm_output, "weekdays", "2025-03-30")
    print(f"Added {recurrence_result['added']} recurring event instances")
    
    # Modify an event
    modify_llm_output = """
    事项: 团队会议
    日期: 2025-03-15
    时间段: 10:00-11:30
    类型: 工作
    重要程度：6
    变动：更改
    """
    
    print("\nModifying an event...")
    modify_result = timetable.process_events(modify_llm_output)
    print(f"Modified {modify_result['modified']} events")
    
    # Mark an event as completed
    print("\nMarking 'health checkup' as completed...")
    # First, get the event ID
    events = timetable.get_events_for_date("2025-03-15")
    for event in events:
        if event['title'] == "健身锻炼":
            event_id = event['id']
            timetable.mark_event_completed(
                event_id, 
                completion_notes="完成了45分钟的有氧运动和力量训练",
                actual_time_range="18:15-19:10"
            )
            print(f"Marked 'health checkup' (ID: {event_id}) as completed")
    
    # Format events for LLM
    print("\nFormatting events for LLM:")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    formatted_events = timetable.format_events_as_llm_output(
        date_from="2025-03-15", 
        date_to=next_week,
        include_header=True
    )
    print(formatted_events)
    
    # Get completed events
    print("\nRetrieving completed events:")
    completed_events = timetable.get_completed_events()
    for event in completed_events:
        print(f"- {event['title']} ({event['date']}): {event.get('completion_notes', 'No notes')}")
    
    # Add reflection to a completed task
    if completed_events:
        task_id = completed_events[0]['task_id']
        print(f"\nAdding reflection to task {task_id}...")
        timetable.add_task_reflection(
            task_id,
            "这次锻炼感觉很好，以后应该更多地关注力量训练部分。"
        )
        print("Reflection added")
    
    print("\nTimetable system demonstration completed.")

if __name__ == "__main__":
    main()
