"""
API路由模块，负责处理HTTP请求
"""

from flask import request, jsonify, render_template
from datetime import datetime, timedelta
from src.event_processing.event_processor import EventProcessor
from src.api.llm_client import query_api

class APIRoutes:
    """API路由处理类"""
    
    def __init__(self, app, event_processor=None):
        """
        初始化API路由
        
        Args:
            app (Flask): Flask应用实例
            event_processor (EventProcessor, optional): 事件处理器实例
        """
        self.app = app
        self.event_processor = event_processor or EventProcessor()
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册所有路由"""
        # 主页
        self.app.add_url_rule('/', 'index', self.index)
        
        # 事件API
        self.app.add_url_rule('/api/events', 'get_events', self.get_events)
        self.app.add_url_rule('/api/events/<date>', 'get_events_for_date', self.get_events_for_date)
        self.app.add_url_rule('/api/events/completed', 'get_completed_events', self.get_completed_events, methods=['GET'])
        self.app.add_url_rule('/api/events/<int:event_id>/complete', 'mark_event_completed', self.mark_event_completed, methods=['POST'])
        self.app.add_url_rule('/api/completed-tasks/<int:task_id>', 'delete_completed_task', self.delete_completed_task, methods=['DELETE'])
        
        # LLM查询API
        self.app.add_url_rule('/api/llm-query', 'llm_query', self.llm_query, methods=['POST'])
        
        # 任务反思API
        self.app.add_url_rule('/api/task-reflection', 'add_task_reflection', self.add_task_reflection, methods=['POST'])
        self.app.add_url_rule('/api/task-history', 'get_task_history', self.get_task_history, methods=['GET'])
    
    def index(self):
        """渲染主页"""
        return render_template('index.html')
    
    def get_events(self):
        """获取事件API"""
        # 获取查询参数
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # 转换limit和offset为整数（如果提供）
        if limit:
            limit = int(limit)
        if offset:
            offset = int(offset)
        
        # 如果没有提供日期范围，默认显示当前月份
        if not date_from and not date_to:
            today = datetime.now()
            first_day = datetime(today.year, today.month, 1)
            last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            date_from = first_day.strftime('%Y-%m-%d')
            date_to = last_day.strftime('%Y-%m-%d')
        
        # 从数据库获取未完成事件
        events = self.event_processor.event_manager.get_all_events(
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        # 为每个事件添加明确的标志
        for event in events:
            event['completed'] = False
        
        return jsonify(events)
    
    def get_events_for_date(self, date):
        """获取指定日期的事件API"""
        # 获取查询参数
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # 转换limit和offset为整数（如果提供）
        if limit:
            limit = int(limit)
        if offset:
            offset = int(offset)
        
        # 从数据库获取指定日期的事件
        events = self.event_processor.event_manager.get_events_for_date(
            date=date,
            limit=limit,
            offset=offset
        )
        
        return jsonify(events)
    
    def get_completed_events(self):
        """获取已完成事件API"""
        # 获取查询参数
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # 转换limit和offset为整数（如果提供）
        if limit:
            limit = int(limit)
        if offset:
            offset = int(offset)
        
        # 从数据库获取已完成事件
        # 注意：这里需要在EventManager中添加get_completed_events方法
        completed_events = []  # 暂时返回空列表，需要实现get_completed_events方法
        
        return jsonify(completed_events)
    
    def mark_event_completed(self, event_id):
        """标记事件为已完成API"""
        # 获取请求数据
        data = request.json
        completion_notes = data.get('completion_notes', '')
        reflection_notes = data.get('reflection_notes', '')
        actual_time_range = data.get('actual_time_range', '')
        
        # 标记事件为已完成
        # 注意：这里需要在EventManager中添加mark_event_completed方法
        result = {'success': False, 'message': '功能尚未实现'}  # 暂时返回失败，需要实现mark_event_completed方法
        
        return jsonify(result)
    
    def delete_completed_task(self, task_id):
        """删除已完成任务API"""
        # 删除已完成任务
        # 注意：这里需要在EventManager中添加delete_completed_task方法
        result = {'success': False, 'message': '功能尚未实现'}  # 暂时返回失败，需要实现delete_completed_task方法
        
        return jsonify(result)
    
    def llm_query(self):
        """处理LLM查询请求"""
        try:
            # 获取请求数据
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
            query_type = data.get('query_type', 'future_planning')  # 新增：查询类型，默认为未来规划
            
            # 获取当前事件列表
            current_events = self.event_processor.format_events_as_llm_output(include_header=False, limit=limit)
            
            # 查询LLM
            response = query_api(prompt, current_events, model=model)
            
            # 准备返回结果
            result = {
                'response': response,
                'error': None
            }
            
            # 如果需要处理事件，则处理LLM输出
            if data.get('process_events', True):
                # 获取修改前的所有事件（如果需要显示变更）
                if show_changes:
                    old_events = self.event_processor.event_manager.get_all_events(limit=limit)
                
                # 处理事件并更新数据库
                try:
                    if recurrence:
                        # 如果设置了重复模式，使用process_recurring_events方法
                        summary = self.event_processor.process_recurring_events(
                            response, 
                            recurrence_rule=recurrence,
                            end_date=end_date,
                            handle_conflicts='error'
                        )
                    else:
                        # 否则使用普通的process_events方法
                        summary = self.event_processor.process_events(response)
                    
                    if show_summary:
                        result['summary'] = summary
                        
                    # 显示变更（如果需要）
                    if show_changes:
                        new_events = self.event_processor.event_manager.get_all_events(limit=limit)
                        changes = self.event_processor.format_events_with_changes(
                            old_events, 
                            new_events, 
                            include_header=True, 
                            show_unchanged=show_unchanged
                        )
                        result['changes'] = changes
                    
                    # 显示当前所有事件（如果需要）
                    if show_events:
                        formatted_output = self.event_processor.format_events_as_llm_output(limit=limit)
                        result['events'] = formatted_output
                except Exception as e:
                    result['error'] = f"处理事件时出错: {str(e)}"
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f"处理LLM查询请求时出错: {str(e)}"})
    
    def add_task_reflection(self):
        """添加任务反思API"""
        # 获取请求数据
        data = request.json
        task_id = data.get('task_id')
        reflection_notes = data.get('reflection_notes', '')
        
        # 添加任务反思
        # 注意：这里需要在EventManager中添加add_task_reflection方法
        result = {'success': False, 'message': '功能尚未实现'}  # 暂时返回失败，需要实现add_task_reflection方法
        
        return jsonify(result)
    
    def get_task_history(self):
        """获取任务历史API"""
        # 获取查询参数
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # 转换limit和offset为整数（如果提供）
        if limit:
            limit = int(limit)
        if offset:
            offset = int(offset)
        
        # 从数据库获取任务历史
        # 注意：这里需要在EventManager中添加get_task_history方法
        task_history = []  # 暂时返回空列表，需要实现get_task_history方法
        
        return jsonify(task_history) 