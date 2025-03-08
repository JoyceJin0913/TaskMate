from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime, timedelta
from schedule_parser import TimetableProcessor
from query_api import query_api

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 创建TimetableProcessor实例
timetable_processor = TimetableProcessor()

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/events')
def get_events():
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
    events = timetable_processor.get_all_events(
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    # 为每个事件添加明确的标志
    for event in events:
        event['is_completed'] = False
        event['event_type'] = event.get('event_type', '未知')
        event['can_complete'] = True
        event['can_delete'] = False
    
    # 获取已完成事件
    include_completed = request.args.get('include_completed', 'true').lower() == 'true'
    if include_completed:
        completed_events = timetable_processor.get_completed_events(date_from=date_from, date_to=date_to)
        # 为已完成事件添加明确的标志
        for event in completed_events:
            event['is_completed'] = True
            event['event_type'] = event.get('event_type', '未知') + ' (已完成)'
            event['can_complete'] = False
            event['can_delete'] = True
        events.extend(completed_events)
    
    return jsonify(events)

@app.route('/api/events/<date>')
def get_events_for_date(date):
    """获取指定日期的事件"""
    # 获取未完成事件
    events = timetable_processor.get_events_for_date(date)
    
    # 为每个事件添加明确的标志
    for event in events:
        event['is_completed'] = False
        event['event_type'] = event.get('event_type', '未知')
        event['can_complete'] = True
        event['can_delete'] = False
    
    # 获取已完成事件
    include_completed = request.args.get('include_completed', 'true').lower() == 'true'
    if include_completed:
        completed_events = timetable_processor.get_completed_events(date_from=date, date_to=date)
        # 为已完成事件添加明确的标志
        for event in completed_events:
            event['is_completed'] = True
            event['event_type'] = event.get('event_type', '未知') + ' (已完成)'
            event['can_complete'] = False
            event['can_delete'] = True
        events.extend(completed_events)
    
    return jsonify(events)

@app.route('/api/events/completed', methods=['GET'])
def get_completed_events():
    """获取已完成的事件"""
    # 获取查询参数
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    limit = request.args.get('limit')
    offset = request.args.get('offset', 0)
    
    # 转换limit和offset为整数（如果提供）
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
    
    # 获取已完成事件
    events = timetable_processor.get_completed_events(date_from, date_to, limit, offset)
    
    # 为每个事件添加明确的标志
    for event in events:
        event['is_completed'] = True
        event['event_type'] = event.get('event_type', '未知') + ' (已完成)'
        event['can_complete'] = False
        event['can_delete'] = True
    
    return jsonify(events)

@app.route('/api/events/<int:event_id>/complete', methods=['POST'])
def mark_event_completed(event_id):
    """标记事件为已完成"""
    print(f"收到标记事件 {event_id} 为已完成的请求")
    
    # 获取完成状态和备注信息
    data = request.get_json() or {}
    completed = data.get('completed', True)
    completion_notes = data.get('completion_notes')
    reflection_notes = data.get('reflection_notes')
    event_date = data.get('date')  # 获取日期信息，用于处理周期性事件
    
    # 记录更多请求详情
    print(f"请求详情: completed={completed}, date={event_date}, notes={completion_notes}")
    
    try:
        # 标记事件完成状态
        success = timetable_processor.mark_event_completed(
            event_id, 
            completed, 
            completion_notes, 
            reflection_notes,
            event_date  # 传递日期信息
        )
        
        if success:
            print(f"事件 {event_id} 已成功标记为{'已' if completed else '未'}完成，日期: {event_date}")
            return jsonify({"status": "success", "message": "事件状态已更新", "event_id": event_id, "date": event_date})
        else:
            print(f"标记事件 {event_id} 失败，可能事件不存在或已被处理，日期: {event_date}")
            return jsonify({"status": "error", "message": "更新事件状态失败"}), 400
    except Exception as e:
        print(f"处理事件 {event_id} 时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"处理请求时发生错误: {str(e)}"}), 500

@app.route('/api/completed-tasks/<int:task_id>', methods=['DELETE'])
def delete_completed_task(task_id):
    """删除已完成的任务"""
    print(f"收到删除已完成任务 {task_id} 的请求")
    
    try:
        success = timetable_processor.delete_completed_task(task_id)
        
        if success:
            print(f"已完成任务 {task_id} 已成功删除")
            return jsonify({"status": "success", "message": "已完成任务已删除"})
        else:
            print(f"删除已完成任务 {task_id} 失败，可能任务不存在")
            return jsonify({"status": "error", "message": "删除已完成任务失败"}), 400
    except Exception as e:
        print(f"删除已完成任务 {task_id} 时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"处理请求时发生错误: {str(e)}"}), 500

@app.route('/api/llm-query', methods=['POST'])
def llm_query():
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
        current_events = timetable_processor.format_events_as_llm_output(include_header=False, limit=limit)
        
        # 查询LLM
        response = query_api(prompt, current_events, model=model)
        
        # 准备返回结果
        result = {
            'response': response,
            'error': None
        }
        
        # 根据查询类型处理请求
        if query_type == 'future_planning':
            # 获取修改前的所有事件（如果需要显示变更）
            if show_changes:
                old_events = timetable_processor.get_all_events(limit=None)
            
            # 处理事件并更新数据库
            try:
                if recurrence:
                    # 如果设置了重复模式，使用 process_recurring_events 方法
                    summary = timetable_processor.process_recurring_events(
                        response, 
                        recurrence_rule=recurrence,
                        end_date=end_date,
                        handle_conflicts='error'
                    )
                else:
                    # 否则使用普通的 process_events 方法
                    summary = timetable_processor.process_events(response)
                
                # 添加处理摘要到结果
                if show_summary:
                    summary_str = "处理摘要：\n"
                    summary_str += f"新增事件: {summary['added']}\n"
                    summary_str += f"修改事件: {summary['modified']}\n"
                    summary_str += f"删除事件: {summary['deleted']}\n"
                    summary_str += f"未变化事件: {summary['unchanged']}\n"
                    summary_str += f"跳过事件: {summary['skipped']}\n"
                    
                    if summary['errors']:
                        summary_str += "\n错误信息:\n"
                        for i, error in enumerate(summary['errors']):
                            summary_str += f"{i+1}. {error}\n"
                    
                    if summary['warnings']:
                        summary_str += "\n警告信息:\n"
                        for i, warning in enumerate(summary['warnings']):
                            summary_str += f"{i+1}. {warning}\n"
                    
                    result['summary'] = summary_str
                
                # 添加变更详情到结果
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
                
                # 添加当前所有事件到结果
                if show_events:
                    formatted_output = timetable_processor.format_events_as_llm_output(limit=limit)
                    result['events'] = formatted_output
                    
            except ValueError as e:
                error_message = str(e)
                result['error'] = error_message
                
                # 添加提示信息
                if "conflict" in error_message.lower():
                    result['error'] += "\n提示：事件时间冲突。您可以修改事件时间或删除冲突的事件。"
                if "date" in error_message.lower() or "time" in error_message.lower():
                    result['error'] += "\n提示：日期或时间格式错误。请确保日期格式为YYYY-MM-DD，时间格式为HH:MM。"
        
        elif query_type == 'historical_review':
            # 处理历史复盘请求
            try:
                # 从LLM响应中提取事件
                events = timetable_processor.extract_events(response)
                
                if not events:
                    raise ValueError("未能从响应中提取到有效的事件信息")
                
                # 对于每个事件，添加到历史复盘数据库
                for event in events:
                    # 获取事件ID（假设在响应中包含了事件ID）
                    event_id = event.get('id')
                    if not event_id:
                        continue
                    
                    # 添加到历史复盘数据库
                    success = timetable_processor.mark_task_completed_with_history(
                        event_id,
                        completion_notes=prompt,  # 使用用户输入作为完成情况备注
                        reflection_notes=None  # 初始时没有复盘笔记
                    )
                    
                    if success:
                        result['message'] = "已成功添加到历史复盘记录"
                    else:
                        result['error'] = "添加历史复盘记录失败"
                
            except ValueError as e:
                result['error'] = f"处理历史复盘请求时出错: {str(e)}"
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'response': None,
            'error': f"处理请求时发生错误: {str(e)}"
        })

@app.route('/api/task-reflection', methods=['POST'])
def add_task_reflection():
    """为已完成的任务添加复盘笔记"""
    try:
        data = request.json
        task_id = data.get('task_id')
        reflection_notes = data.get('reflection_notes')
        
        if not task_id or not reflection_notes:
            return jsonify({
                'status': 'error',
                'message': '缺少必要的参数'
            }), 400
        
        success = timetable_processor.add_task_reflection(task_id, reflection_notes)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '复盘笔记已添加'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '添加复盘笔记失败'
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'处理请求时发生错误: {str(e)}'
        }), 500

@app.route('/api/task-history', methods=['GET'])
def get_task_history():
    """获取任务历史记录"""
    try:
        # 获取查询参数
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = request.args.get('limit')
        offset = request.args.get('offset', 0)
        
        # 转换limit和offset为整数（如果提供）
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
        
        # 获取历史记录
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
            'message': f'获取历史记录时发生错误: {str(e)}'
        }), 500

# 确保templates和static目录存在
def ensure_directories():
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

# 创建HTML模板
def create_templates():
    index_html = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskMate</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>TaskMate</h1>
            <div class="date-controls">
                <!-- 月视图导航 -->
                <div id="month-navigation" class="navigation-controls active">
                    <button id="prev-month">上个月</button>
                    <span id="current-month"></span>
                    <button id="next-month">下个月</button>
                </div>
                
                <!-- 周视图导航 -->
                <div id="week-navigation" class="navigation-controls">
                    <button id="prev-week">上一周</button>
                    <span id="current-week"></span>
                    <button id="next-week">下一周</button>
                </div>
                
                <!-- 日视图导航 -->
                <div id="day-navigation" class="navigation-controls">
                    <button id="prev-day">前一天</button>
                    <span id="current-day"></span>
                    <button id="next-day">后一天</button>
                </div>
            </div>
        </header>
        
        <div class="view-controls">
            <button id="month-view" class="active">月视图</button>
            <button id="week-view">周视图</button>
            <button id="day-view">日视图</button>
            <button id="list-view">列表视图</button>
            <button id="completed-view">已完成</button>
            <button id="llm-view">LLM查询</button>
        </div>
        
        <!-- 视图容器 -->
        <div id="calendar-container">
            <!-- 月视图 -->
            <div id="month-grid" class="view active"></div>
            
            <!-- 周视图 -->
            <div id="week-grid" class="view"></div>
            
            <!-- 日视图 -->
            <div id="day-grid" class="view"></div>
            
            <!-- 列表视图 -->
            <div id="list-grid" class="view"></div>
            
            <!-- 已完成视图 -->
            <div id="completed-grid" class="view"></div>
            
            <!-- LLM查询视图 -->
            <div id="llm-grid" class="view">
                <div class="llm-container">
                    <h2>LLM日程规划助手</h2>
                    <div class="llm-form">
                        <div class="form-group">
                            <label>选择操作模式：</label>
                            <div class="radio-group">
                                <input type="radio" id="mode-future-planning" name="query_type" value="future_planning" checked>
                                <label for="mode-future-planning">未来规划</label>
                                
                                <input type="radio" id="mode-historical-review" name="query_type" value="historical_review">
                                <label for="mode-historical-review">历史复盘</label>
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="llm-prompt">请输入您的需求：</label>
                            <textarea id="llm-prompt" rows="4" placeholder="未来规划示例：明天下午三点要开会，需要提前准备一个小时&#10;历史复盘示例：记录完成了周二的项目评审会议"></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>选择模型：</label>
                            <div class="radio-group">
                                <input type="radio" id="model-deepseek-chat" name="model" value="deepseek-chat" checked>
                                <label for="model-deepseek-chat">DeepSeek V3</label>

                                <input type="radio" id="model-deepseek-reasoner" name="model" value="deepseek-reasoner" checked>
                                <label for="model-deepseek-reasoner">DeepSeek R1 (Slow)</label>
                                
                                <input type="radio" id="model-gpt4" name="model" value="gpt-4o">
                                <label for="model-gpt4">GPT-4o</label>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label>重复设置：</label>
                            <select id="recurrence">
                                <option value="">不重复</option>
                                <option value="daily">每天</option>
                                <option value="weekly">每周</option>
                                <option value="weekdays">工作日</option>
                                <option value="monthly">每月</option>
                                <option value="yearly">每年</option>
                            </select>
                            
                            <div id="end-date-container" class="hidden">
                                <label for="end-date">结束日期：</label>
                                <input type="date" id="end-date">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label>显示选项：</label>
                            <div class="checkbox-group">
                                <input type="checkbox" id="show-summary" checked>
                                <label for="show-summary">显示处理摘要</label>
                                
                                <input type="checkbox" id="show-changes" checked>
                                <label for="show-changes">显示变更详情</label>
                                
                                <input type="checkbox" id="show-events">
                                <label for="show-events">显示所有事件</label>
                                
                                <input type="checkbox" id="show-unchanged">
                                <label for="show-unchanged">显示未变化事件</label>
                            </div>
                        </div>
                        
                        <div class="form-actions">
                            <button id="submit-llm" class="primary-button">提交查询</button>
                            <div id="loading-indicator" class="hidden">
                                <div class="spinner"></div>
                                <span>正在处理...</span>
                            </div>
                        </div>
                    </div>
                    
                    <div id="llm-results" class="hidden">
                        <h3>处理结果</h3>
                        <div class="result-section">
                            <h4>模型回复</h4>
                            <pre id="llm-response"></pre>
                        </div>
                        
                        <div id="summary-section" class="result-section hidden">
                            <h4>处理摘要</h4>
                            <pre id="summary-content"></pre>
                        </div>
                        
                        <div id="changes-section" class="result-section hidden">
                            <h4>事件变更</h4>
                            <pre id="changes-content"></pre>
                        </div>
                        
                        <div id="events-section" class="result-section hidden">
                            <h4>当前所有事件</h4>
                            <pre id="events-content"></pre>
                        </div>
                        
                        <div id="error-section" class="result-section hidden">
                            <h4>错误信息</h4>
                            <pre id="error-content"></pre>
                        </div>
                        
                        <button id="new-query" class="secondary-button">新的查询</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="event-details" class="hidden">
            <div class="event-details-header">
                <h2>事件详情</h2>
                <button id="close-details">关闭</button>
            </div>
            <div id="event-details-content"></div>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

# 创建CSS样式
def create_css():
    css = '''
/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* 通知样式 */
.notification {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    background-color: #4CAF50;
    color: white;
    border-radius: 4px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    z-index: 1100;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.3s, transform 0.3s;
}

.notification.show {
    opacity: 1;
    transform: translateY(0);
}

.notification.error {
    background-color: #f44336;
}

.notification.warning {
    background-color: #ff9800;
}

.notification.info {
    background-color: #2196F3;
}

/* 头部样式 */
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ddd;
}

h1 {
    font-size: 24px;
    color: #2c3e50;
}

.date-controls {
    display: flex;
    align-items: center;
    gap: 10px;
}

.navigation-controls {
    display: none;
    align-items: center;
    gap: 10px;
}

.navigation-controls.active {
    display: flex;
}

button {
    padding: 8px 12px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #45a049;
}

.view-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.view-controls button {
    background-color: #ddd;
    color: #333;
}

.view-controls button.active {
    background-color: #4CAF50;
    color: white;
}

/* 视图容器 */
#calendar-container {
    position: relative;
    height: 700px; /* 固定高度 */
    width: 100%;
    overflow-y: auto; /* 添加垂直滚动条 */
    overflow-x: hidden; /* 隐藏水平滚动条 */
    scroll-behavior: smooth; /* 平滑滚动 */
}

/* 视图样式 */
.view {
    display: none;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: auto; /* 改为auto，根据内容自动调整高度 */
}

.view.active {
    display: block;
}

/* 月视图样式 */
#month-grid {
    display: none;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
}

#month-grid.active {
    display: grid;
}

.day-cell {
    min-height: 100px;
    background-color: white;
    border-radius: 4px;
    padding: 5px;
    border: 1px solid #ddd;
}

.day-header {
    text-align: center;
    font-weight: bold;
    padding: 5px;
    background-color: #f0f0f0;
    border-radius: 4px 4px 0 0;
}

.day-number {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 5px;
}

.event-item {
    margin: 2px 0;
    padding: 2px 25px 2px 5px; /* 增加右侧内边距，为删除按钮留出空间 */
    border-radius: 3px;
    font-size: 12px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    cursor: pointer;
    position: relative;
}

/* 已完成事件样式 */
.event-item.completed {
    text-decoration: line-through;
    opacity: 0.7;
    background-color: #f0f0f0 !important;
    color: #666 !important;
    border-left: 3px solid #999 !important;
}

/* 周视图和日视图中的已完成事件样式 */
.day-column .event-item.completed {
    text-decoration: line-through;
    opacity: 0.7;
    background-color: rgba(240, 240, 240, 0.9) !important;
    color: #666 !important;
    border-left: 3px solid #999 !important;
}

/* 完成按钮样式 */
.complete-button {
    position: absolute;
    right: 3px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 1px solid #ccc;
    background-color: white;
    color: #4CAF50;
    font-size: 10px;
    line-height: 1;
    padding: 0;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
}

/* 周视图和日视图中的完成按钮样式 */
.day-column .complete-button {
    right: 5px;
    top: 5px;
    transform: none;
    background-color: rgba(255, 255, 255, 0.9);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.complete-button:hover {
    background-color: #f0f0f0;
}

/* 已完成视图样式 */
#completed-grid {
    padding: 10px;
}

#completed-grid h2 {
    margin-bottom: 20px;
    color: #333;
}

.date-group {
    margin-bottom: 20px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.date-group h3 {
    margin-bottom: 10px;
    color: #666;
    font-size: 16px;
}

.events-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

/* 列表视图中的事件项样式 */
.events-list .event-item {
    padding: 8px 10px;
    border-radius: 4px;
    margin: 0;
    position: relative;
    display: flex;
    align-items: center;
}

.events-list .event-item .complete-button {
    position: absolute;
    right: 10px;
}

.empty-message, .error-message {
    padding: 20px;
    text-align: center;
    color: #666;
}

.error-message {
    color: #d9534f;
}

/* 操作按钮样式 */
.action-button {
    margin-top: 10px;
    padding: 5px 10px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
}

.action-button:hover {
    background-color: #45a049;
}

/* 时间轴样式 */
.time-column {
    background-color: #f9f9f9;
    border-right: 1px solid #ddd;
    min-height: 990px; /* 与日期列保持一致 */
    position: sticky; /* 使时间列固定 */
    left: 0; /* 固定在左侧 */
    z-index: 50; /* 确保在最上层 */
}

.time-cell {
    text-align: right;
    padding: 5px 10px 5px 5px;
    font-size: 12px;
    height: 40px; /* 固定高度，与事件位置计算匹配 */
    line-height: 30px; /* 垂直居中 */
    border-bottom: 1px dashed #eee; /* 添加分隔线 */
    color: #666;
}

.week-day-column, .day-column {
    background-color: white;
    border: 1px solid #ddd;
    min-height: 990px; /* 24小时 * 40px + 30px头部 = 990px */
    position: relative;
    height: 100%; /* 确保列高度填满容器 */
}

.week-day-header {
    text-align: center;
    padding: 5px;
    background-color: #f0f0f0;
    font-weight: bold;
    height: 30px; /* 固定高度，与事件位置计算匹配 */
    line-height: 20px; /* 垂直居中 */
    border-bottom: 1px solid #ddd;
    position: sticky; /* 使头部固定 */
    top: 0; /* 固定在顶部 */
    z-index: 40; /* 确保在事件上层 */
}

/* 小时线样式 */
.hour-line {
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background-color: #eee;
    z-index: 1;
}

/* 当前时间指示线 */
.current-time-indicator {
    position: absolute;
    left: 0;
    right: 0;
    height: 2px;
    background-color: #f44336;
    z-index: 20;
    box-shadow: 0 0 5px rgba(244, 67, 54, 0.5); /* 添加阴影效果 */
}

/* 周视图和日视图中的事件样式 */
.week-day-column .event-item,
.day-column .event-item {
    position: absolute;
    left: 5px;
    right: 5px;
    padding: 5px;
    z-index: 10;
    min-height: 25px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    overflow: hidden;
    border-left: 3px solid;
}

.event-item.type-meeting {
    background-color: #bbdefb;
    border-left-color: #2196F3;
}

.event-item.type-task {
    background-color: #c8e6c9;
    border-left-color: #4CAF50;
}

.event-item.type-deadline {
    background-color: #ffcdd2;
    border-left-color: #F44336;
}

.event-item.type-other {
    background-color: #e1bee7;
    border-left-color: #9C27B0;
}

/* 周视图样式 */
#week-grid {
    display: none;
    grid-template-columns: 60px repeat(7, 1fr);
    gap: 5px;
    height: auto; /* 根据内容自动调整高度 */
    min-height: 1000px; /* 确保有足够的高度 */
    position: relative; /* 确保定位正确 */
}

#week-grid.active {
    display: grid;
}

/* 日视图样式 */
#day-grid {
    display: none;
    grid-template-columns: 60px 1fr;
    gap: 5px;
    height: auto; /* 根据内容自动调整高度 */
    min-height: 1000px; /* 确保有足够的高度 */
    position: relative; /* 确保定位正确 */
}

#day-grid.active {
    display: grid;
}

/* 列表视图样式 */
#list-grid {
    display: none;
    background-color: white;
    border-radius: 4px;
    padding: 10px;
    border: 1px solid #ddd;
}

#list-grid.active {
    display: block;
}

.list-date-header {
    font-weight: bold;
    margin: 10px 0;
    padding-bottom: 5px;
    border-bottom: 1px solid #ddd;
}

.list-event-item {
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 4px;
    cursor: pointer;
}

/* LLM查询视图样式 */
#llm-grid {
    display: none;
    background-color: white;
    border-radius: 4px;
    padding: 20px;
    border: 1px solid #ddd;
}

#llm-grid.active {
    display: block;
}

.llm-container {
    max-width: 800px;
    margin: 0 auto;
}

.llm-form {
    margin-top: 20px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

.form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
    font-size: 14px;
    resize: vertical;
}

.radio-group, .checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-top: 5px;
    padding: 10px;
    background-color: #f5f5f5;
    border-radius: 4px;
}

.radio-group input[type="radio"] {
    margin-right: 5px;
}

.radio-group label {
    font-weight: normal;
    margin-bottom: 0;
    cursor: pointer;
    padding: 5px 10px;
    border-radius: 3px;
    transition: background-color 0.2s;
}

.radio-group label:hover {
    background-color: #e0e0e0;
}

.radio-group input[type="radio"]:checked + label {
    background-color: #4CAF50;
    color: white;
}

select {
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
    min-width: 150px;
}

#end-date-container {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}

#end-date-container label {
    margin-bottom: 0;
}

#end-date-container input[type="date"] {
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.form-actions {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-top: 30px;
}

.primary-button {
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
}

.secondary-button {
    padding: 10px 20px;
    background-color: #f0f0f0;
    color: #333;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

.primary-button:hover {
    background-color: #45a049;
}

.secondary-button:hover {
    background-color: #e0e0e0;
}

#loading-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
}

.spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top-color: #4CAF50;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

#llm-results {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
}

.result-section {
    margin-bottom: 20px;
}

.result-section h4 {
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 1px solid #eee;
}

.result-section pre {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 4px;
    overflow-x: auto;
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 14px;
    line-height: 1.5;
}

#error-section pre {
    background-color: #fff0f0;
    border-left: 3px solid #f44336;
}

/* 事件详情样式 */
#event-details {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    padding: 20px;
}

.event-details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ddd;
}

#event-details-content {
    line-height: 1.8;
}

.hidden {
    display: none !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
    #month-grid {
        grid-template-columns: repeat(7, 1fr);
    }
    
    .day-cell {
        min-height: 60px;
    }
    
    #week-grid {
        grid-template-columns: 40px repeat(7, 1fr);
    }
    
    #event-details {
        width: 90%;
    }
}

/* 加载指示器样式 */
.loading-indicator {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 周期性事件样式 */
.recur-icon {
    display: inline-block;
    margin-left: 5px;
    font-size: 12px;
    opacity: 0.7;
}

.event-item[data-recurring="true"] {
    position: relative;
    border-left: 3px solid #4a6da7;
}

.event-item[data-recurring="true"]::after {
    content: '🔄';
    position: absolute;
    right: 30px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 10px;
    opacity: 0.6;
}

/* 正在完成中的事件样式 */
.event-item.completing {
    opacity: 0.5;
    pointer-events: none;
    transition: all 0.5s ease;
}

/* 删除按钮样式 */
.delete-button {
    position: absolute;
    right: 3px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 1px solid #ccc;
    background-color: white;
    color: #f44336;
    font-size: 10px;
    line-height: 1;
    padding: 0;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
}

/* 周视图和日视图中的删除按钮样式 */
.day-column .delete-button {
    right: 5px;
    top: 5px;
    transform: none;
    background-color: rgba(255, 255, 255, 0.9);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.delete-button:hover {
    background-color: #f44336;
    color: white;
}
    '''
    
    with open('static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

# 创建JavaScript脚本
def create_js():
    js = '''
// 全局变量
let currentDate = new Date();
let currentView = 'month'; // 当前视图类型：month, week, day, list
let events = [];

// 用于跟踪正在处理的事件ID
let processingEvents = new Set();
// 用于跟踪已处理完成的事件ID，防止重复处理
let completedEvents = new Set();

// 用于跟踪加载状态
let isLoadingEvents = false;
let loadEventsRetryCount = 0;
const MAX_RETRY_COUNT = 3;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM加载完成");
    
    // 初始化视图
    initializeView();
    
    // 绑定月份导航按钮事件
    document.getElementById('prev-month').addEventListener('click', previousMonth);
    document.getElementById('next-month').addEventListener('click', nextMonth);
    
    // 绑定周导航按钮事件
    document.getElementById('prev-week').addEventListener('click', previousWeek);
    document.getElementById('next-week').addEventListener('click', nextWeek);
    
    // 绑定日导航按钮事件
    document.getElementById('prev-day').addEventListener('click', previousDay);
    document.getElementById('next-day').addEventListener('click', nextDay);
    
    // 视图切换按钮
    document.querySelectorAll('.view-controls button').forEach(button => {
        button.addEventListener('click', function() {
            // 获取视图类型
            const viewType = this.id.replace('-view', '');
            switchView(viewType);
        });
    });
    
    // 关闭事件详情
    document.getElementById('close-details').addEventListener('click', function() {
        document.getElementById('event-details').classList.add('hidden');
    });
});

// 初始化视图
function initializeView() {
    console.log("初始化视图");
    
    // 设置默认视图为月视图
    currentView = 'month';
    
    // 激活月视图按钮
    document.getElementById('month-view').classList.add('active');
    
    // 激活月视图导航
    document.getElementById('month-navigation').classList.add('active');
    
    // 激活月视图网格
    document.getElementById('month-grid').classList.add('active');
    
    // 更新日期显示
    updateDateDisplay();
    
    // 加载事件数据
    loadEvents();
}

// 切换视图
function switchView(viewType) {
    console.log("切换视图到:", viewType);
    
    // 更新当前视图
    currentView = viewType;
    
    // 更新视图按钮状态
    document.querySelectorAll('.view-controls button').forEach(button => {
        button.classList.toggle('active', button.id === `${viewType}-view`);
    });
    
    // 更新导航控件显示
    document.querySelectorAll('.navigation-controls').forEach(nav => {
        nav.classList.remove('active');
    });
    
    // 显示对应的导航控件
    if (viewType === 'month') {
        document.getElementById('month-navigation').classList.add('active');
    } else if (viewType === 'week') {
        document.getElementById('week-navigation').classList.add('active');
    } else if (viewType === 'day') {
        document.getElementById('day-navigation').classList.add('active');
    }
    
    // 隐藏所有视图
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    // 显示选中的视图
    document.getElementById(`${viewType}-grid`).classList.add('active');
    
    // 更新日期显示
    updateDateDisplay();
    
    // 根据视图类型加载事件
    if (viewType === 'completed') {
        renderCompletedView();
    } else if (viewType !== 'llm') {
        loadEvents();
    }
}

// 更新日期显示
function updateDateDisplay() {
    const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    
    // 更新月份显示
    document.getElementById('current-month').textContent = `${currentDate.getFullYear()}年 ${monthNames[currentDate.getMonth()]}`;
    
    // 更新周显示
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    
    const startMonth = startOfWeek.getMonth() + 1;
    const endMonth = endOfWeek.getMonth() + 1;
    
    document.getElementById('current-week').textContent = 
        `${startOfWeek.getFullYear()}年${startMonth}月${startOfWeek.getDate()}日 - ${endOfWeek.getMonth() + 1}月${endOfWeek.getDate()}日`;
    
    // 更新日显示
    document.getElementById('current-day').textContent = 
        `${currentDate.getFullYear()}年${currentDate.getMonth() + 1}月${currentDate.getDate()}日 ${weekdays[currentDate.getDay()]}`;
}

// 加载事件数据
function loadEvents(retry = false) {
    // 如果已经在加载中，则忽略请求（除非是重试）
    if (isLoadingEvents && !retry) {
        console.log("事件数据正在加载中，忽略重复请求");
        return;
    }
    
    // 设置加载状态
    isLoadingEvents = true;
    
    // 如果是重试，则增加重试计数
    if (retry) {
        loadEventsRetryCount++;
        console.log(`重试加载事件数据，第 ${loadEventsRetryCount} 次尝试`);
        if (loadEventsRetryCount > MAX_RETRY_COUNT) {
            console.error(`已达到最大重试次数 ${MAX_RETRY_COUNT}，停止重试`);
            isLoadingEvents = false;
            loadEventsRetryCount = 0;
            hideLoadingIndicator();
            showNotification('加载事件数据失败，已达到最大重试次数', 'error');
            return;
        }
    } else {
        // 如果不是重试，则重置重试计数
        loadEventsRetryCount = 0;
    }
    
    console.log("开始加载事件数据");
    
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    
    // 显示加载指示器
    showLoadingIndicator();
    
    let dateFrom, dateTo;
    
    // 根据当前视图类型确定日期范围
    switch(currentView) {
        case 'month':
            // 计算当前月份的起始日期和结束日期
            const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            // 获取前一天的日期，以包含可能的跨天事件
            const prevDayOfMonth = new Date(firstDay);
            prevDayOfMonth.setDate(prevDayOfMonth.getDate() - 1);
            
            const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            dateFrom = formatDate(prevDayOfMonth); // 从前一天开始
            dateTo = formatDate(lastDay);
            break;
            
        case 'week':
            // 计算当前周的起始日期和结束日期
            const startOfWeek = new Date(currentDate);
            startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
            
            // 获取周日前一天的日期，以包含可能的跨天事件
            const prevDayOfWeek = new Date(startOfWeek);
            prevDayOfWeek.setDate(prevDayOfWeek.getDate() - 1);
            
            const endOfWeek = new Date(startOfWeek);
            endOfWeek.setDate(startOfWeek.getDate() + 6);
            
            dateFrom = formatDate(prevDayOfWeek); // 从周日前一天开始
            dateTo = formatDate(endOfWeek);
            break;
            
        case 'day':
            // 当前日期和前一天
            const prevDay = new Date(currentDate);
            prevDay.setDate(prevDay.getDate() - 1);
            dateFrom = formatDate(prevDay); // 从前一天开始
            dateTo = formatDate(currentDate);
            break;
            
        case 'list':
        case 'completed':
            // 默认显示当前月
            const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            // 获取前一天的日期，以包含可能的跨天事件
            const prevDayOfList = new Date(firstDayOfMonth);
            prevDayOfList.setDate(prevDayOfList.getDate() - 1);
            
            const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            dateFrom = formatDate(prevDayOfList);
            dateTo = formatDate(lastDayOfMonth);
            break;
    }
    
    // 构建API URL
    let apiUrl = `/api/events?date_from=${dateFrom}&date_to=${dateTo}`;
    console.log(`加载事件数据，API URL: ${apiUrl}`);
    
    // 设置请求超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
    
    // 获取事件数据
    fetch(apiUrl, { signal: controller.signal })
        .then(response => {
            // 清除超时
            clearTimeout(timeoutId);
            
            console.log(`事件数据请求已发送，状态码: ${response.status}`);
            if (!response.ok) {
                throw new Error(`服务器响应错误: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`事件数据已加载，共 ${data.length} 个事件`);
            events = data;
            renderCurrentView();
            
            // 加载已完成事件视图（如果需要）
            if (currentView === 'completed') {
                renderCompletedView();
            }
            
            // 隐藏加载指示器
            hideLoadingIndicator();
            
            // 重置加载状态和重试计数
            isLoadingEvents = false;
            loadEventsRetryCount = 0;
        })
        .catch(error => {
            console.error('加载事件数据出错:', error);
            
            // 如果是超时或网络错误，则尝试重试
            if (error.name === 'AbortError' || error.message.includes('network') || error.message.includes('failed')) {
                console.log('网络错误或超时，将尝试重试');
                // 延迟一段时间后重试
                setTimeout(() => {
                    loadEvents(true);
                }, 1000); // 1秒后重试
            } else {
                // 其他错误，重置加载状态
                isLoadingEvents = false;
                loadEventsRetryCount = 0;
                
                // 隐藏加载指示器
                hideLoadingIndicator();
                
                // 显示错误通知
                showNotification('加载事件数据失败: ' + error.message, 'error');
            }
        });
}

// 显示加载指示器
function showLoadingIndicator() {
    // 创建加载指示器元素（如果不存在）
    let loadingIndicator = document.getElementById('global-loading-indicator');
    if (!loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'global-loading-indicator';
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(loadingIndicator);
    }
    
    // 显示加载指示器
    loadingIndicator.style.display = 'flex';
}

// 隐藏加载指示器
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('global-loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

// 格式化日期为YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 上个月
function previousMonth() {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1);
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    updateDateDisplay();
    loadEvents();
}

// 下个月
function nextMonth() {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    updateDateDisplay();
    loadEvents();
}

// 上一周
function previousWeek() {
    currentDate.setDate(currentDate.getDate() - 7);
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    updateDateDisplay();
    loadEvents();
}

// 下一周
function nextWeek() {
    currentDate.setDate(currentDate.getDate() + 7);
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    updateDateDisplay();
    loadEvents();
}

// 前一天
function previousDay() {
    currentDate.setDate(currentDate.getDate() - 1);
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    updateDateDisplay();
    loadEvents();
}

// 后一天
function nextDay() {
    currentDate.setDate(currentDate.getDate() + 1);
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    updateDateDisplay();
    loadEvents();
}

// 添加当前时间指示线并滚动到当前时间
function addCurrentTimeIndicator() {
    // 只在周视图和日视图中添加
    if (currentView !== 'week' && currentView !== 'day') return;
    
    // 获取当前时间
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    
    // 计算指示线位置
    const top = (hours + minutes / 60) * 40 + 30; // 30px是头部高度
    
    // 在周视图中添加指示线
    if (currentView === 'week') {
        const columns = document.querySelectorAll('.week-day-column');
        const today = now.getDay(); // 0-6，表示周日到周六
        
        // 只在当天的列中添加指示线
        if (columns[today]) {
            const indicator = document.createElement('div');
            indicator.className = 'current-time-indicator';
            indicator.style.top = `${top}px`;
            columns[today].appendChild(indicator);
            
            // 滚动到当前时间附近（稍微往上一点，以便看到更多未来的事件）
            setTimeout(() => {
                const container = document.getElementById('calendar-container');
                container.scrollTop = Math.max(0, top - 200); // 滚动到当前时间上方200px处
            }, 100);
        }
    }
    
    // 在日视图中添加指示线
    if (currentView === 'day') {
        const column = document.querySelector('.day-column');
        if (column) {
            const indicator = document.createElement('div');
            indicator.className = 'current-time-indicator';
            indicator.style.top = `${top}px`;
            column.appendChild(indicator);
            
            // 滚动到当前时间附近（稍微往上一点，以便看到更多未来的事件）
            setTimeout(() => {
                const container = document.getElementById('calendar-container');
                container.scrollTop = Math.max(0, top - 200); // 滚动到当前时间上方200px处
            }, 100);
        }
    }
}

// 渲染当前视图
function renderCurrentView() {
    console.log("渲染当前视图:", currentView);
    
    // 清空所有视图
    document.getElementById('month-grid').innerHTML = '';
    document.getElementById('week-grid').innerHTML = '';
    document.getElementById('day-grid').innerHTML = '';
    document.getElementById('list-grid').innerHTML = '';
    
    // 根据当前视图类型渲染对应的视图
    switch(currentView) {
        case 'month':
            renderMonthView();
            break;
        case 'week':
            renderWeekView();
            break;
        case 'day':
            renderDayView();
            break;
        case 'list':
            renderListView();
            break;
    }
    
    // 添加当前时间指示线
    addCurrentTimeIndicator();
}

// 渲染月视图
function renderMonthView() {
    const monthGrid = document.getElementById('month-grid');
    monthGrid.innerHTML = ''; // 清空内容
    
    // 添加星期标题
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    weekdays.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        dayHeader.textContent = day;
        monthGrid.appendChild(dayHeader);
    });
    
    // 获取当前月的第一天是星期几
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const firstDayOfWeek = firstDay.getDay();
    
    // 获取当前月的天数
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const daysInMonth = lastDay.getDate();
    
    // 添加上个月的占位日期
    for (let i = 0; i < firstDayOfWeek; i++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'day-cell empty';
        monthGrid.appendChild(dayCell);
    }
    
    // 添加当前月的日期
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'day-cell';
        
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day;
        dayCell.appendChild(dayNumber);
        
        // 检查当天是否有事件
        const currentDateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayEvents = events.filter(event => event.date === currentDateStr);
        
        // 添加事件到日期单元格
        dayEvents.forEach(event => {
            renderEventItem(event, dayCell);
        });
        
        monthGrid.appendChild(dayCell);
    }
    
    // 计算需要添加的下个月占位日期数量
    const totalCells = 42; // 6行7列
    const remainingCells = totalCells - (firstDayOfWeek + daysInMonth);
    
    // 添加下个月的占位日期
    for (let i = 0; i < remainingCells; i++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'day-cell empty';
        monthGrid.appendChild(dayCell);
    }
}

// 渲染事件项
function renderEventItem(event, container, options = {}) {
    const eventItem = document.createElement('div');
    const isCompleted = event.is_completed === true || event.source === 'completed_task';
    
    // 设置事件项的类名
    eventItem.className = `event-item type-${event.event_type.toLowerCase().replace(/\s+\(已完成\)$/, '')}`;
    
    // 如果事件已完成，添加已完成样式
    if (isCompleted) {
        eventItem.classList.add('completed');
    }
    
    // 设置事件内容
    if (options.customContent) {
        eventItem.textContent = options.customContent;
    } else if (options.showTimeRange) {
        eventItem.textContent = `${event.time_range}: ${event.title}`;
    } else {
        eventItem.textContent = event.title;
    }
    
    // 设置事件ID和日期（用于处理周期性事件）
    eventItem.dataset.eventId = event.id;
    eventItem.dataset.date = event.date;
    
    // 检查是否为周期性事件
    const isRecurring = event.recurrence_rule && event.recurrence_rule.trim() !== '';
    if (isRecurring) {
        eventItem.dataset.recurring = 'true';
    }
    
    // 添加点击事件显示详情
    eventItem.addEventListener('click', function() {
        showEventDetails(event);
    });
    
    // 添加按钮
    if (!options.hideButtons) {
        if (isCompleted) {
            // 已完成事件 - 添加删除按钮
            const deleteButton = document.createElement('button');
            deleteButton.className = 'delete-button';
            deleteButton.textContent = '×';
            deleteButton.title = '删除事件';
            
            // 阻止事件冒泡，避免点击按钮时触发事件详情
            deleteButton.addEventListener('click', function(e) {
                e.stopPropagation();
                // 检查事件是否已经处理完成
                if (completedEvents.has(event.id)) {
                    console.log(`事件 ${event.id} 已经处理完成，忽略删除请求`);
                    return;
                }
                
                // 显示一次确认对话框
                if (!confirm('确定要删除这个已完成的任务吗？')) {
                    return;
                }
                
                // 将事件ID添加到已处理完成集合中，防止重复处理
                completedEvents.add(event.id);
                
                // 立即禁用按钮，防止重复点击
                deleteButton.disabled = true;
                deleteButton.textContent = '...';
                
                // 立即从界面上移除该事件（视觉反馈）
                eventItem.style.opacity = '0.3';
                eventItem.style.pointerEvents = 'none';
                eventItem.style.transition = 'all 0.5s ease';
                eventItem.style.transform = 'translateX(100%)';
                
                // 删除事件
                deleteCompletedTask(event.id);
            });
            
            eventItem.appendChild(deleteButton);
        } else {
            // 未完成事件 - 添加完成按钮
            const completeButton = document.createElement('button');
            completeButton.className = 'complete-button';
            completeButton.textContent = '○';
            completeButton.title = '标记为已完成';
            
            // 阻止事件冒泡，避免点击按钮时触发事件详情
            completeButton.addEventListener('click', function(e) {
                e.stopPropagation();
                
                // 检查事件是否已经处理完成
                if (completedEvents.has(event.id)) {
                    console.log(`事件 ${event.id} 已经处理完成，忽略请求`);
                    return;
                }
                
                // 调用标记为已完成函数
                markEventCompleted(event.id, true);
            });
            
            eventItem.appendChild(completeButton);
        }
    }
    
    // 应用自定义样式
    if (options.style) {
        Object.assign(eventItem.style, options.style);
    }
    
    // 添加到容器
    container.appendChild(eventItem);
    
    return eventItem;
}

// 解析时间字符串为小时和分钟
function parseTimeString(timeStr) {
    const parts = timeStr.trim().split(':');
    const hour = parseInt(parts[0]);
    const minute = parseInt(parts[1] || 0);
    return { hour, minute };
}

// 检查事件是否跨天
function isOvernightEvent(timeRange) {
    if (!timeRange || timeRange.length === 0) return false;
    
    const parts = timeRange.split('-');
    if (parts.length !== 2) return false;
    
    const startTime = parseTimeString(parts[0]);
    const endTime = parseTimeString(parts[1]);
    
    // 如果结束时间小于开始时间，则认为是跨天事件
    return endTime.hour < startTime.hour || (endTime.hour === startTime.hour && endTime.minute < startTime.minute);
}

// 获取事件在次日的时间范围
function getNextDayTimeRange(timeRange) {
    if (!isOvernightEvent(timeRange)) return null;
    
    const parts = timeRange.split('-');
    return `00:00-${parts[1]}`;
}

// 获取事件在当天的时间范围
function getCurrentDayTimeRange(timeRange) {
    if (!isOvernightEvent(timeRange)) return timeRange;
    
    const parts = timeRange.split('-');
    return `${parts[0]}-24:00`;
}

// 计算事件在时间轴上的位置
function calculateEventPosition(timeRange) {
    if (!timeRange || timeRange.length === 0) return null;
    
    const parts = timeRange.split('-');
    if (parts.length !== 2) return null;
    
    const startTime = parseTimeString(parts[0]);
    const endTime = parseTimeString(parts[1]);
    
    // 计算开始位置（相对于时间轴顶部）
    const top = (startTime.hour + startTime.minute / 60) * 40 + 30; // 30px是头部高度
    
    // 计算事件持续时间（小时）
    let durationHours = endTime.hour - startTime.hour + (endTime.minute - startTime.minute) / 60;
    
    // 处理跨天事件（结束时间小于开始时间，表示跨越到第二天）
    if (durationHours <= 0) {
        // 计算到午夜的时间 + 从午夜到结束时间的时间
        durationHours = (24 - startTime.hour - startTime.minute / 60) + (endTime.hour + endTime.minute / 60);
    }
    
    // 计算事件高度
    const height = durationHours * 40;
    
    return { top, height };
}

// 渲染周视图
function renderWeekView() {
    const weekGrid = document.getElementById('week-grid');
    weekGrid.innerHTML = ''; // 清空内容
    
    // 创建时间轴标签列
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    
    // 添加空白头部单元格
    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'week-day-header';
    timeColumn.appendChild(emptyHeader);
    
    // 添加时间标签
    for (let hour = 0; hour < 24; hour++) {
        const timeLabel = document.createElement('div');
        timeLabel.className = 'time-label';
        timeLabel.textContent = `${hour}:00`;
        timeLabel.style.position = 'absolute';
        timeLabel.style.top = `${hour * 40 + 30}px`;
        timeColumn.appendChild(timeLabel);
    }
    
    weekGrid.appendChild(timeColumn);
    
    // 获取当前周的起始日期（周日）
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    
    // 创建每一天的列
    const dayColumns = [];
    const dayDates = [];
    
    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(startOfWeek);
        dayDate.setDate(startOfWeek.getDate() + i);
        const dateStr = formatDate(dayDate);
        dayDates.push(dateStr);
        
        const dayColumn = document.createElement('div');
        dayColumn.className = 'day-column';
        
        // 添加日期标题
        const dayHeader = document.createElement('div');
        dayHeader.className = 'week-day-header';
        dayHeader.textContent = `${dayDate.getMonth() + 1}/${dayDate.getDate()} ${['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dayDate.getDay()]}`;
        dayColumn.appendChild(dayHeader);
        
        // 添加时间背景网格线
        for (let hour = 0; hour < 24; hour++) {
            const hourLine = document.createElement('div');
            hourLine.className = 'hour-line';
            hourLine.style.position = 'absolute';
            hourLine.style.left = '0';
            hourLine.style.right = '0';
            hourLine.style.top = `${hour * 40 + 30}px`;
            hourLine.style.height = '1px';
            hourLine.style.backgroundColor = '#eee';
            hourLine.style.zIndex = '1';
            dayColumn.appendChild(hourLine);
        }
        
        dayColumns.push(dayColumn);
        weekGrid.appendChild(dayColumn);
    }
    
    // 分两步处理事件：
    // 1. 处理当前周内的事件
    // 2. 处理前一天的跨天事件
    
    // 第一步：处理当前周内的事件
    console.log("处理当前周内的事件");
    events.forEach(event => {
        // 检查事件日期是否在当前周内
        const dateIndex = dayDates.indexOf(event.date);
        if (dateIndex === -1) return; // 如果不在当前周内，跳过
        
        // 检查是否是跨天事件
        const isOvernight = isOvernightEvent(event.time_range);
        
        // 在当天显示事件
        const currentDayTimeRange = isOvernight ? getCurrentDayTimeRange(event.time_range) : event.time_range;
        const currentDayPosition = calculateEventPosition(currentDayTimeRange);
        
        if (currentDayPosition) {
            // 使用renderEventItem函数创建事件元素
            const eventStyle = {
                position: 'absolute',
                top: `${currentDayPosition.top}px`,
                left: '5px',
                right: '5px',
                height: `${currentDayPosition.height}px`,
                zIndex: '2'
            };
            
            // 设置事件显示内容
            const eventOptions = {
                style: eventStyle,
                customContent: `${event.time_range}: ${event.title}`
            };
            
            renderEventItem(event, dayColumns[dateIndex], eventOptions);
        }
        
        // 如果是跨天事件，且次日也在当前周内，则在次日也显示事件
        if (isOvernight && dateIndex < 6) {
            const nextDayTimeRange = getNextDayTimeRange(event.time_range);
            const nextDayPosition = calculateEventPosition(nextDayTimeRange);
            
            if (nextDayPosition) {
                // 使用renderEventItem函数创建次日事件元素
                const nextDayStyle = {
                    position: 'absolute',
                    top: `${nextDayPosition.top}px`,
                    left: '5px',
                    right: '5px',
                    height: `${nextDayPosition.height}px`,
                    zIndex: '2'
                };
                
                // 设置次日事件显示内容
                const nextDayOptions = {
                    style: nextDayStyle,
                    customContent: `(续) ${event.title}`
                };
                
                renderEventItem(event, dayColumns[dateIndex + 1], nextDayOptions);
            }
        }
    });
    
    // 第二步：处理前一天的跨天事件（特别是周六到周日的跨天事件）
    console.log("处理前一天的跨天事件");
    events.forEach(event => {
        // 检查是否是跨天事件
        if (!isOvernightEvent(event.time_range)) return;
        
        // 计算事件的次日
        const eventDate = new Date(event.date);
        eventDate.setDate(eventDate.getDate() + 1);
        const nextDateStr = formatDate(eventDate);
        
        // 检查次日是否在当前周内
        const nextDateIndex = dayDates.indexOf(nextDateStr);
        if (nextDateIndex === -1) return; // 如果次日不在当前周内，跳过
        
        // 获取次日的时间范围
        const nextDayTimeRange = getNextDayTimeRange(event.time_range);
        const position = calculateEventPosition(nextDayTimeRange);
        
        if (position) {
            // 使用renderEventItem函数创建次日事件元素
            const nextDayStyle = {
                position: 'absolute',
                top: `${position.top}px`,
                left: '5px',
                right: '5px',
                height: `${position.height}px`,
                zIndex: '2'
            };
            
            // 设置次日事件显示内容
            const nextDayOptions = {
                style: nextDayStyle,
                customContent: `(续) ${event.title}`
            };
            
            renderEventItem(event, dayColumns[nextDateIndex], nextDayOptions);
        }
    });
    
    // 添加当前时间指示线
    addCurrentTimeIndicator();
}

// 渲染日视图
function renderDayView() {
    const dayGrid = document.getElementById('day-grid');
    dayGrid.innerHTML = ''; // 清空内容
    
    // 创建时间轴标签列
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    
    // 添加空白头部单元格
    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'day-header';
    timeColumn.appendChild(emptyHeader);
    
    // 添加时间标签
    for (let hour = 0; hour < 24; hour++) {
        const timeLabel = document.createElement('div');
        timeLabel.className = 'time-label';
        timeLabel.textContent = `${hour}:00`;
        timeLabel.style.position = 'absolute';
        timeLabel.style.top = `${hour * 40 + 30}px`;
        timeColumn.appendChild(timeLabel);
    }
    
    dayGrid.appendChild(timeColumn);
    
    // 创建当天的列
    const dayColumn = document.createElement('div');
    dayColumn.className = 'day-column';
    
    // 添加日期标题
    const dayHeader = document.createElement('div');
    dayHeader.className = 'day-header';
    dayHeader.textContent = `${currentDate.getFullYear()}年${currentDate.getMonth() + 1}月${currentDate.getDate()}日 ${['周日', '周一', '周二', '周三', '周四', '周五', '周六'][currentDate.getDay()]}`;
    dayColumn.appendChild(dayHeader);
    
    // 添加时间背景网格线
    for (let hour = 0; hour < 24; hour++) {
        const hourLine = document.createElement('div');
        hourLine.className = 'hour-line';
        hourLine.style.position = 'absolute';
        hourLine.style.left = '0';
        hourLine.style.right = '0';
        hourLine.style.top = `${hour * 40 + 30}px`;
        hourLine.style.height = '1px';
        hourLine.style.backgroundColor = '#eee';
        hourLine.style.zIndex = '1';
        dayColumn.appendChild(hourLine);
    }
    
    dayGrid.appendChild(dayColumn);
    
    // 获取当前日期的格式化字符串
    const currentDateStr = formatDate(currentDate);
    
    // 获取当前日期的事件
    const dayEvents = events.filter(event => event.date === currentDateStr);
    
    // 添加当天的事件
    dayEvents.forEach(event => {
        // 检查是否是跨天事件
        const isOvernight = isOvernightEvent(event.time_range);
        
        // 获取当天的时间范围
        const currentDayTimeRange = isOvernight ? getCurrentDayTimeRange(event.time_range) : event.time_range;
        const position = calculateEventPosition(currentDayTimeRange);
        
        if (position) {
            // 使用renderEventItem函数创建事件元素
            const eventStyle = {
                position: 'absolute',
                top: `${position.top}px`,
                left: '5px',
                right: '5px',
                height: `${position.height}px`,
                zIndex: '2'
            };
            
            // 设置事件显示内容
            const eventOptions = {
                style: eventStyle,
                customContent: `${event.time_range}: ${event.title}`
            };
            
            renderEventItem(event, dayColumn, eventOptions);
        }
    });
    
    // 获取前一天的日期
    const prevDate = new Date(currentDate);
    prevDate.setDate(currentDate.getDate() - 1);
    const prevDateStr = formatDate(prevDate);
    
    // 获取前一天的事件
    const prevDayEvents = events.filter(event => event.date === prevDateStr);
    
    // 添加前一天跨天的事件
    prevDayEvents.forEach(event => {
        // 检查是否是跨天事件
        const isOvernight = isOvernightEvent(event.time_range);
        
        if (isOvernight) {
            // 获取次日的时间范围
            const nextDayTimeRange = getNextDayTimeRange(event.time_range);
            const position = calculateEventPosition(nextDayTimeRange);
            
            if (position) {
                // 使用renderEventItem函数创建次日事件元素
                const nextDayStyle = {
                    position: 'absolute',
                    top: `${position.top}px`,
                    left: '5px',
                    right: '5px',
                    height: `${position.height}px`,
                    zIndex: '2'
                };
                
                // 设置次日事件显示内容
                const nextDayOptions = {
                    style: nextDayStyle,
                    customContent: `(续) ${event.title}`
                };
                
                renderEventItem(event, dayColumn, nextDayOptions);
            }
        }
    });
    
    // 添加当前时间指示线
    addCurrentTimeIndicator();
}

// 渲染列表视图
function renderListView() {
    const listGrid = document.getElementById('list-grid');
    listGrid.innerHTML = ''; // 清空内容
    
    // 创建标题
    const header = document.createElement('h2');
    header.textContent = '事件列表';
    listGrid.appendChild(header);
    
    // 如果没有事件，显示提示信息
    if (events.length === 0) {
        const emptyMessage = document.createElement('p');
        emptyMessage.className = 'empty-message';
        emptyMessage.textContent = '暂无事件';
        listGrid.appendChild(emptyMessage);
        return;
    }
    
    // 按日期分组
    const eventsByDate = {};
    events.forEach(event => {
        if (!eventsByDate[event.date]) {
            eventsByDate[event.date] = [];
        }
        eventsByDate[event.date].push(event);
    });
    
    // 按日期排序
    const sortedDates = Object.keys(eventsByDate).sort();
    
    // 创建日期分组列表
    sortedDates.forEach(date => {
        const dateGroup = document.createElement('div');
        dateGroup.className = 'date-group';
        
        // 创建日期标题
        const dateHeader = document.createElement('h3');
        const dateObj = new Date(date);
        dateHeader.textContent = `${date} ${['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()]}`;
        dateGroup.appendChild(dateHeader);
        
        // 创建事件列表
        const eventsList = document.createElement('div');
        eventsList.className = 'events-list';
        
        // 按时间排序
        eventsByDate[date].sort((a, b) => {
            // 提取开始时间
            const getStartTime = (timeRange) => {
                const parts = timeRange.split('-');
                return parts[0].trim();
            };
            
            const aStart = getStartTime(a.time_range);
            const bStart = getStartTime(b.time_range);
            
            return aStart.localeCompare(bStart);
        });
        
        // 添加事件
        eventsByDate[date].forEach(event => {
            renderEventItem(event, eventsList, { showTimeRange: true });
        });
        
        dateGroup.appendChild(eventsList);
        listGrid.appendChild(dateGroup);
    });
}

// 显示事件详情
function showEventDetails(event) {
    const detailsContainer = document.getElementById('event-details');
    const detailsContent = document.getElementById('event-details-content');
    
    // 清空内容
    detailsContent.innerHTML = '';
    
    // 创建详情内容
    const details = [
        `<strong>事项:</strong> ${event.title}`,
        `<strong>日期:</strong> ${event.date}`,
        `<strong>时间段:</strong> ${event.time_range}`,
        `<strong>类型:</strong> ${event.event_type}`
    ];
    
    // 添加可选字段
    if (event.deadline) {
        details.push(`<strong>截止日期:</strong> ${event.deadline}`);
    }
    
    if (event.importance) {
        details.push(`<strong>重要程度:</strong> ${event.importance}`);
    }
    
    if (event.description) {
        details.push(`<strong>描述:</strong> ${event.description}`);
    }
    
    // 添加完成状态
    const isCompleted = event.is_completed === true;
    details.push(`<strong>状态:</strong> ${isCompleted ? '已完成' : '未完成'}`);
    
    // 如果是已完成事件，显示完成时间和备注
    if (isCompleted && event.completion_date) {
        details.push(`<strong>完成时间:</strong> ${event.completion_date}`);
    }
    
    if (isCompleted && event.completion_notes) {
        details.push(`<strong>完成备注:</strong> ${event.completion_notes}`);
    }
    
    if (isCompleted && event.reflection_notes) {
        details.push(`<strong>复盘笔记:</strong> ${event.reflection_notes}`);
    }
    
    // 设置内容
    detailsContent.innerHTML = details.join('<br>');
    
    // 根据事件来源添加不同的按钮
    if (isCompleted) {
        // 已完成事件 - 添加删除按钮
        const deleteButton = document.createElement('button');
        deleteButton.className = 'action-button delete-button';
        deleteButton.textContent = '删除事件';
        deleteButton.addEventListener('click', function() {
            // 直接调用删除函数，不显示确认对话框
            deleteCompletedTask(event.id);
        });
        detailsContent.appendChild(document.createElement('br'));
        detailsContent.appendChild(deleteButton);
    } else {
        // 未完成事件 - 添加标记为已完成按钮
        const completeButton = document.createElement('button');
        completeButton.className = 'action-button complete-button';
        completeButton.textContent = '标记为已完成';
        completeButton.addEventListener('click', function() {
            markEventCompleted(event.id, true);
        });
        detailsContent.appendChild(document.createElement('br'));
        detailsContent.appendChild(completeButton);
    }
    
    // 显示详情面板
    detailsContainer.classList.remove('hidden');
}

// 删除已完成任务
function deleteCompletedTask(taskId) {
    // 如果该任务正在处理中，则忽略请求
    if (processingEvents.has(taskId)) {
        console.log(`事件 ${taskId} 正在处理中，忽略删除请求`);
        return;
    }
    
    // 将任务ID添加到处理集合中
    processingEvents.add(taskId);
    console.log(`开始处理事件 ${taskId} 的删除操作`);
    
    // 立即从界面上移除该事件（视觉反馈）
    const eventElements = document.querySelectorAll(`.event-item[data-event-id="${taskId}"]`);
    eventElements.forEach(element => {
        element.style.opacity = '0.3';
        element.style.pointerEvents = 'none';
        element.style.transition = 'all 0.5s ease';
        element.style.transform = 'translateX(100%)';
        
        // 禁用所有按钮
        const buttons = element.querySelectorAll('button');
        buttons.forEach(button => {
            button.disabled = true;
            button.textContent = '...';
        });
        
        // 500ms后完全移除事件元素
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 500);
    });
    
    // 关闭详情面板
    document.getElementById('event-details').classList.add('hidden');
    
    fetch(`/api/completed-tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => {
        console.log(`事件 ${taskId} 的删除请求已发送，状态码: ${response.status}`);
        return response.json();
    })
    .then(data => {
        // 从处理集合中移除任务ID
        processingEvents.delete(taskId);
        console.log(`事件 ${taskId} 的删除操作已完成，结果: ${data.status}`);
        
        if (data.status === 'success') {
            // 显示成功消息
            showNotification('任务已成功删除');
            
            // 延迟一段时间后重新加载事件，确保后端处理完成
            setTimeout(() => {
                // 重新加载事件
                loadEvents();
                // 刷新已完成任务列表
                renderCompletedView();
            }, 500);
        } else {
            // 处理失败，从已处理完成集合中移除事件ID
            completedEvents.delete(taskId);
            alert('删除任务失败: ' + data.message);
        }
    })
    .catch(error => {
        // 从处理集合中移除任务ID
        processingEvents.delete(taskId);
        // 处理失败，从已处理完成集合中移除事件ID
        completedEvents.delete(taskId);
        
        console.error(`事件 ${taskId} 删除出错:`, error);
        alert('删除任务时发生错误');
    });
}

// 显示通知消息
function showNotification(message, type = 'success') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // 自动隐藏通知
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 标记事件为已完成或未完成
function markEventCompleted(eventId, completed) {
    // 如果该事件已经处理完成，则忽略请求
    if (completedEvents.has(eventId)) {
        console.log(`事件 ${eventId} 已经处理完成，忽略重复请求`);
        return;
    }
    
    // 如果该事件正在处理中，则忽略请求
    if (processingEvents.has(eventId)) {
        console.log(`事件 ${eventId} 正在处理中，忽略重复请求`);
        return;
    }
    
    // 将事件ID添加到处理集合中
    processingEvents.add(eventId);
    console.log(`开始处理事件 ${eventId} 的完成状态变更`);
    
    // 立即从界面上标记该事件（视觉反馈）
    const eventElements = document.querySelectorAll(`.event-item[data-event-id="${eventId}"]`);
    eventElements.forEach(element => {
        // 获取日期，用于区分周期性事件的特定实例
        const eventDate = element.dataset.date;
        
        // 如果是今天标记为已完成的事件，则添加特殊效果
        element.classList.add('completing');
        element.style.opacity = '0.3';
        element.style.pointerEvents = 'none';
        element.style.transition = 'all 0.5s ease';
        element.style.transform = 'translateX(100%)';
        
        // 禁用所有按钮
        const buttons = element.querySelectorAll('button');
        buttons.forEach(button => {
            button.disabled = true;
            button.textContent = '...';
        });
        
        // 500ms后完全移除事件元素
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 500);
    });
    
    // 关闭详情面板
    document.getElementById('event-details').classList.add('hidden');
    
    // 将事件ID添加到已处理完成集合中，防止重复处理
    completedEvents.add(eventId);
    
    // 添加当前日期信息到请求中，用于处理周期性事件
    const currentDateStr = formatDate(new Date());
    const eventDate = document.querySelector(`.event-item[data-event-id="${eventId}"]`)?.dataset.date || currentDateStr;
    
    fetch(`/api/events/${eventId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            completed: completed,
            date: eventDate // 添加日期信息
        })
    })
    .then(response => {
        console.log(`事件 ${eventId} 的请求已发送，状态码: ${response.status}`);
        return response.json();
    })
    .then(data => {
        // 从处理集合中移除事件ID
        processingEvents.delete(eventId);
        console.log(`事件 ${eventId} 的处理已完成，结果: ${data.status}`);
        
        if (data.status === 'success') {
            // 显示成功消息
            showNotification('事件已标记为已完成');
            
            // 延迟一段时间后重新加载事件，确保后端处理完成
            setTimeout(() => {
                // 重新加载事件
                loadEvents();
                // 刷新已完成任务列表
                renderCompletedView();
            }, 700);
        } else {
            // 处理失败，从已处理完成集合中移除事件ID
            completedEvents.delete(eventId);
            alert('更新事件状态失败: ' + data.message);
            
            // 恢复界面上的事件元素
            const eventElements = document.querySelectorAll(`.event-item.completing`);
            eventElements.forEach(element => {
                element.classList.remove('completing');
                element.style.opacity = '1';
                element.style.pointerEvents = 'auto';
                element.style.transform = 'translateX(0)';
                
                // 恢复按钮状态
                const completeButton = element.querySelector('.complete-button');
                if (completeButton) {
                    completeButton.disabled = false;
                    completeButton.textContent = '○';
                }
            });
        }
    })
    .catch(error => {
        // 从处理集合中移除事件ID
        processingEvents.delete(eventId);
        // 处理失败，从已处理完成集合中移除事件ID
        completedEvents.delete(eventId);
        
        console.error(`事件 ${eventId} 处理出错:`, error);
        alert('更新事件状态时发生错误');
        
        // 恢复界面上的事件元素
        const eventElements = document.querySelectorAll(`.event-item.completing`);
        eventElements.forEach(element => {
            element.classList.remove('completing');
            element.style.opacity = '1';
            element.style.pointerEvents = 'auto';
            element.style.transform = 'translateX(0)';
            
            // 恢复按钮状态
            const completeButton = element.querySelector('.complete-button');
            if (completeButton) {
                completeButton.disabled = false;
                completeButton.textContent = '○';
            }
        });
    });
}

// LLM查询相关功能
document.addEventListener('DOMContentLoaded', function() {
    // 绑定LLM视图按钮
    document.getElementById('llm-view').addEventListener('click', function() {
        switchView('llm');
    });
    
    // 重复设置下拉框变化事件
    document.getElementById('recurrence').addEventListener('change', function() {
        const endDateContainer = document.getElementById('end-date-container');
        if (this.value) {
            endDateContainer.classList.remove('hidden');
        } else {
            endDateContainer.classList.add('hidden');
        }
    });
    
    // 确保加载指示器初始状态为隐藏
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.classList.add('hidden');
    }
    
    // 提交LLM查询
    document.getElementById('submit-llm').addEventListener('click', submitLLMQuery);
    
    // 新的查询按钮
    document.getElementById('new-query').addEventListener('click', function() {
        document.querySelector('.llm-form').classList.remove('hidden');
        document.getElementById('llm-results').classList.add('hidden');
        document.getElementById('llm-prompt').value = '';
    });
});

// 提交LLM查询
function submitLLMQuery() {
    // 获取用户输入
    const prompt = document.getElementById('llm-prompt').value.trim();
    if (!prompt) {
        alert('请输入日程安排需求');
        return;
    }
    
    // 获取选项
    const model = document.querySelector('input[name="model"]:checked').value;
    const recurrence = document.getElementById('recurrence').value;
    const endDate = document.getElementById('end-date').value;
    const showSummary = document.getElementById('show-summary').checked;
    const showChanges = document.getElementById('show-changes').checked;
    const showEvents = document.getElementById('show-events').checked;
    const showUnchanged = document.getElementById('show-unchanged').checked;
    
    // 显示加载指示器
    document.getElementById('loading-indicator').classList.remove('hidden');
    document.getElementById('submit-llm').disabled = true;
    
    // 准备请求数据
    const requestData = {
        prompt: prompt,
        model: model,
        recurrence: recurrence,
        end_date: endDate,
        show_summary: showSummary,
        show_changes: showChanges,
        show_events: showEvents,
        show_unchanged: showUnchanged,
        query_type: document.querySelector('input[name="query_type"]:checked').value
    };
    
    // 发送API请求
    fetch('/api/llm-query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏加载指示器
        document.getElementById('loading-indicator').classList.add('hidden');
        document.getElementById('submit-llm').disabled = false;
        
        // 显示结果区域
        document.querySelector('.llm-form').classList.add('hidden');
        document.getElementById('llm-results').classList.remove('hidden');
        
        // 显示模型回复
        document.getElementById('llm-response').textContent = data.response || '';
        
        // 显示处理摘要（如果有）
        if (data.summary && showSummary) {
            document.getElementById('summary-section').classList.remove('hidden');
            document.getElementById('summary-content').textContent = data.summary;
        } else {
            document.getElementById('summary-section').classList.add('hidden');
        }
        
        // 显示变更详情（如果有）
        if (data.changes && showChanges) {
            document.getElementById('changes-section').classList.remove('hidden');
            document.getElementById('changes-content').textContent = data.changes;
        } else {
            document.getElementById('changes-section').classList.add('hidden');
        }
        
        // 显示所有事件（如果需要）
        if (data.events && showEvents) {
            document.getElementById('events-section').classList.remove('hidden');
            document.getElementById('events-content').textContent = data.events;
        } else {
            document.getElementById('events-section').classList.add('hidden');
        }
        
        // 显示错误信息（如果有）
        if (data.error) {
            document.getElementById('error-section').classList.remove('hidden');
            document.getElementById('error-content').textContent = data.error;
        } else {
            document.getElementById('error-section').classList.add('hidden');
        }
        
        // 刷新事件数据
        loadEvents();
    })
    .catch(error => {
        // 隐藏加载指示器
        document.getElementById('loading-indicator').classList.add('hidden');
        document.getElementById('submit-llm').disabled = false;
        
        // 显示错误信息
        document.getElementById('error-section').classList.remove('hidden');
        document.getElementById('error-content').textContent = '请求失败: ' + error.message;
        
        console.error('LLM查询失败:', error);
    });
}

// 添加已完成任务列表视图
function renderCompletedView() {
    const completedGrid = document.getElementById('completed-grid');
    completedGrid.innerHTML = ''; // 清空内容
    
    // 创建标题
    const header = document.createElement('h2');
    header.textContent = '已完成任务';
    completedGrid.appendChild(header);
    
    // 加载已完成事件
    fetch('/api/events/completed')
        .then(response => response.json())
        .then(completedEvents => {
            if (completedEvents.length === 0) {
                const emptyMessage = document.createElement('p');
                emptyMessage.className = 'empty-message';
                emptyMessage.textContent = '暂无已完成任务';
                completedGrid.appendChild(emptyMessage);
                return;
            }
            
            // 按日期分组
            const eventsByDate = {};
            completedEvents.forEach(event => {
                if (!eventsByDate[event.date]) {
                    eventsByDate[event.date] = [];
                }
                eventsByDate[event.date].push(event);
            });
            
            // 按日期排序（降序）
            const sortedDates = Object.keys(eventsByDate).sort().reverse();
            
            // 创建日期分组列表
            sortedDates.forEach(date => {
                const dateGroup = document.createElement('div');
                dateGroup.className = 'date-group';
                
                // 创建日期标题
                const dateHeader = document.createElement('h3');
                const dateObj = new Date(date);
                dateHeader.textContent = `${date} ${['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()]}`;
                dateGroup.appendChild(dateHeader);
                
                // 创建事件列表
                const eventsList = document.createElement('div');
                eventsList.className = 'events-list';
                
                // 添加事件
                eventsByDate[date].forEach(event => {
                    // 确保事件有is_completed标志
                    event.is_completed = true;
                    renderEventItem(event, eventsList, { showTimeRange: true });
                });
                
                dateGroup.appendChild(eventsList);
                completedGrid.appendChild(dateGroup);
            });
        })
        .catch(error => {
            console.error('Error loading completed events:', error);
            const errorMessage = document.createElement('p');
            errorMessage.className = 'error-message';
            errorMessage.textContent = '加载已完成任务时发生错误';
            completedGrid.appendChild(errorMessage);
        });
}
    '''
    
    with open('static/js/script.js', 'w', encoding='utf-8') as f:
        f.write(js)

# 主函数
def main():
    ensure_directories()
    create_templates()
    create_css()
    create_js()
    
    print("日程表可视化前端已创建完成！")
    print("请运行以下命令启动应用：")
    print("python schedule_visualizer.py")

if __name__ == "__main__":
    main()
    app.run(debug=True) 