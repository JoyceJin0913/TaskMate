from flask import render_template, request, jsonify
from datetime import datetime, timedelta
from utils.backend.timetable import Timetable
from utils.query_api import query_api

# Create TimetableProcessor instance
timetable_processor = Timetable()

def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route('/')
    def index():
        """Render the main page"""
        return render_template('index.html')

    @app.route('/api/events')
    def get_events():
        """Get events API"""
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # Convert limit and offset to integers (if provided)
        if limit:
            limit = int(limit)
        if offset:
            offset = int(offset)
        
        # If no date range is provided, default to current month
        if not date_from and not date_to:
            today = datetime.now()
            first_day = datetime(today.year, today.month, 1)
            last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            date_from = first_day.strftime('%Y-%m-%d')
            date_to = last_day.strftime('%Y-%m-%d')
        
        # Get incomplete events from the database
        events = timetable_processor.get_all_events(
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        # Add explicit flags to each event
        for event in events:
            event['is_completed'] = False
            event['event_type'] = event.get('event_type', '未知')
            event['can_complete'] = True
            event['can_delete'] = False
        
        # Get completed events
        include_completed = request.args.get('include_completed', 'true').lower() == 'true'
        if include_completed:
            completed_events = timetable_processor.get_completed_events(date_from=date_from, date_to=date_to)
            # Add explicit flags to completed events
            for event in completed_events:
                event['is_completed'] = True
                event['event_type'] = event.get('event_type', '未知') + ' (已完成)'
                event['can_complete'] = False
                event['can_delete'] = True
            events.extend(completed_events)
        
        return jsonify(events)

    @app.route('/api/events/<date>')
    def get_events_for_date(date):
        """Get events for a specific date"""
        # Get incomplete events
        events = timetable_processor.get_events_for_date(date)
        
        # Add explicit flags to each event
        for event in events:
            event['is_completed'] = False
            event['event_type'] = event.get('event_type', '未知')
            event['can_complete'] = True
            event['can_delete'] = False
        
        # Get completed events
        include_completed = request.args.get('include_completed', 'true').lower() == 'true'
        if include_completed:
            completed_events = timetable_processor.get_completed_events(date_from=date, date_to=date)
            # Add explicit flags to completed events
            for event in completed_events:
                event['is_completed'] = True
                event['event_type'] = event.get('event_type', '未知') + ' (已完成)'
                event['can_complete'] = False
                event['can_delete'] = True
            events.extend(completed_events)
        
        return jsonify(events)

    @app.route('/api/events/completed', methods=['GET'])
    def get_completed_events():
        """Get completed events"""
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # Convert limit and offset to integers (if provided)
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        if offset:
            try:
                offset = int(offset)
            except ValueError:
                offset = 0
        
        # Get completed events
        events = timetable_processor.get_completed_events(date_from, date_to, limit, offset)
        
        # Add explicit flags to each event
        for event in events:
            event['is_completed'] = True
            event['event_type'] = event.get('event_type', '未知') + ' (已完成)'
            event['can_complete'] = False
            event['can_delete'] = True
        
        return jsonify(events)

    @app.route('/api/events/<int:event_id>/complete', methods=['POST'])
    def mark_event_completed(event_id):
        """Mark event as completed"""
        print(f"Received request to mark event {event_id} as completed")
        
        try:
            data = request.get_json()
            completion_notes = data.get('completion_notes')
            reflection_notes = data.get('reflection_notes')
            event_date = data.get('event_date')  # For handling recurring events on specific dates
            actual_time_range = data.get('actual_time_range')  # Actual time range when the event occurred
            
            success = timetable_processor.mark_event_completed(
                event_id, 
                completed=True, 
                completion_notes=completion_notes,
                reflection_notes=reflection_notes,
                event_date=event_date,
                actual_time_range=actual_time_range
            )
            
            if success:
                print(f"Event {event_id} successfully marked as completed")
                return jsonify({"status": "success", "message": "Event marked as completed"})
            else:
                print(f"Failed to mark event {event_id} as completed, event may not exist")
                return jsonify({"status": "error", "message": "Failed to mark event as completed"}), 400
        except Exception as e:
            print(f"Error marking event {event_id} as completed: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Error processing request: {str(e)}"}), 500

    @app.route('/api/completed-tasks/<int:task_id>', methods=['DELETE'])
    def delete_completed_task(task_id):
        """Delete a completed task"""
        print(f"Received request to delete completed task {task_id}")
        
        try:
            success = timetable_processor.delete_completed_task(task_id)
            
            if success:
                print(f"Completed task {task_id} successfully deleted")
                return jsonify({"status": "success", "message": "Completed task deleted"})
            else:
                print(f"Failed to delete completed task {task_id}, task may not exist")
                return jsonify({"status": "error", "message": "Failed to delete completed task"}), 400
        except Exception as e:
            print(f"Error deleting completed task {task_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Error processing request: {str(e)}"}), 500

    @app.route('/api/llm-query', methods=['POST'])
    def llm_query():
        """Process LLM query requests"""
        try:
            # Get request data
            data = request.json
            prompt = data.get('prompt', '')
            model = data.get('model', 'deepseek-chat')
            recurrence = data.get('recurrence', '')
            end_date = data.get('end_date', '')
            show_summary = data.get('show_summary', True)
            show_changes = data.get('show_changes', True)
            show_events = data.get('show_events', False)
            show_unchanged = data.get('show_unchanged', False)
            limit = data.get('limit', 50)
            query_type = data.get('query_type', 'future_planning')  # New: query type, default is future planning
            
            # Get current event list
            current_events = timetable_processor.format_events_as_llm_output(include_header=False, limit=limit)
            
            # Query LLM
            response = query_api(prompt, current_events, model=model)
            
            # Prepare result
            result = {
                'response': response,
                'error': None
            }
            
            # Process request based on query type
            if query_type == 'future_planning':
                # Get all events before changes (if needed to show changes)
                if show_changes:
                    old_events = timetable_processor.get_all_events(limit=None)
                
                # Process events and update database
                try:
                    if recurrence:
                        # If recurrence mode is set, use process_recurring_events method
                        summary = timetable_processor.process_recurring_events(
                            response, 
                            recurrence_rule=recurrence,
                            end_date=end_date,
                            handle_conflicts='error'
                        )
                    else:
                        # Otherwise use the regular process_events method
                        summary = timetable_processor.process_events(response)
                    
                    # Add processing summary to result
                    if show_summary:
                        summary_str = "Processing summary:\n"
                        summary_str += f"Added events: {summary['added']}\n"
                        summary_str += f"Modified events: {summary['modified']}\n"
                        summary_str += f"Deleted events: {summary['deleted']}\n"
                        summary_str += f"Unchanged events: {summary['unchanged']}\n"
                        summary_str += f"Skipped events: {summary['skipped']}\n"
                        
                        if summary['errors']:
                            summary_str += "\nErrors:\n"
                            for i, error in enumerate(summary['errors']):
                                summary_str += f"{i+1}. {error}\n"
                        
                        if summary['warnings']:
                            summary_str += "\nWarnings:\n"
                            for i, warning in enumerate(summary['warnings']):
                                summary_str += f"{i+1}. {warning}\n"
                        
                        result['summary'] = summary_str
                    
                    # Add change details to result
                    if show_changes:
                        new_events = timetable_processor.get_all_events(limit=None)
                        changes = timetable_processor.format_events_with_changes(
                            old_events, 
                            new_events, 
                            include_header=True, 
                            show_unchanged=show_unchanged,
                            limit=limit
                        )
                        result['changes'] = changes
                    
                    # Add all current events to result
                    if show_events:
                        formatted_output = timetable_processor.format_events_as_llm_output(limit=limit)
                        result['events'] = formatted_output
                        
                except ValueError as e:
                    error_message = str(e)
                    result['error'] = error_message
                    
                    # Add helpful suggestions
                    if "conflict" in error_message.lower():
                        result['error'] += "\nTip: There's a time conflict. You can modify event times or delete conflicting events."
                    if "date" in error_message.lower() or "time" in error_message.lower():
                        result['error'] += "\nTip: Date or time format error. Make sure dates are in YYYY-MM-DD format and times are in HH:MM format."
            
            elif query_type == 'historical_review':
                # Process historical review requests
                try:
                    # Extract events from LLM response
                    events = timetable_processor.extract_events(response)
                    
                    if not events:
                        raise ValueError("Could not extract valid event information from the response")
                    
                    # For each event, add to historical review database
                    for event in events:
                        # Get event ID (assuming it's included in the response)
                        event_id = event.get('id')
                        if not event_id:
                            continue
                        
                        # Add to historical review database
                        success = timetable_processor.mark_task_completed_with_history(
                            event_id,
                            completion_notes=prompt,  # Use user input as completion notes
                            reflection_notes=None  # No reflection notes initially
                        )
                        
                        if success:
                            result['message'] = "Successfully added to historical review records"
                        else:
                            result['error'] = "Failed to add historical review record"
                    
                except ValueError as e:
                    result['error'] = f"Error processing historical review request: {str(e)}"
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'response': None,
                'error': f"Error processing request: {str(e)}"
            })

    @app.route('/api/task-reflection', methods=['POST'])
    def add_task_reflection():
        """Add reflection notes to a completed task"""
        try:
            data = request.json
            task_id = data.get('task_id')
            reflection_notes = data.get('reflection_notes')
            
            if not task_id or not reflection_notes:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required parameters'
                }), 400
            
            success = timetable_processor.add_task_reflection(task_id, reflection_notes)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Reflection notes added'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to add reflection notes'
                }), 400
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }), 500

    @app.route('/api/task-history', methods=['GET'])
    def get_task_history():
        """Get task history records"""
        try:
            # Get query parameters
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            limit = request.args.get('limit')
            offset = request.args.get('offset', 0)
            
            # Convert limit and offset to integers (if provided)
            if limit:
                try:
                    limit = int(limit)
                except ValueError:
                    limit = None
            
            if offset:
                try:
                    offset = int(offset)
                except ValueError:
                    offset = 0
            
            # Get history records
            history = timetable_processor.get_task_history(
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset
            )
            
            return jsonify(history)
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error getting history records: {str(e)}'
            }), 500
