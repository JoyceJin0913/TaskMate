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
    
    # 从数据库获取事件
    events = timetable_processor.get_all_events(
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    return jsonify(events)

@app.route('/api/events/<date>')
def get_events_for_date(date):
    """获取特定日期的事件"""
    events = timetable_processor.get_events_for_date(date)
    return jsonify(events)

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
        limit = data.get('limit', 20)
        
        # 获取当前事件列表
        current_events = timetable_processor.format_events_as_llm_output(include_header=False, limit=limit)
        
        # 查询LLM
        response = query_api(prompt, current_events, model=model)
        
        # 准备返回结果
        result = {
            'response': response,
            'error': None
        }
        
        # 获取修改前的所有事件（如果需要显示变更）
        if show_changes:
            old_events = timetable_processor.get_all_events(limit=limit)
        
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
                result['summary'] = summary
            
            # 添加变更详情到结果
            if show_changes:
                new_events = timetable_processor.get_all_events(limit=limit)
                changes = timetable_processor.format_events_with_changes(
                    old_events, 
                    new_events, 
                    include_header=True, 
                    show_unchanged=show_unchanged
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
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'response': None,
            'error': f"处理请求时发生错误: {str(e)}"
        })

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
    <title>日程表可视化</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>日程表可视化</h1>
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
            
            <!-- LLM查询视图 -->
            <div id="llm-grid" class="view">
                <div class="llm-container">
                    <h2>LLM日程规划助手</h2>
                    <div class="llm-form">
                        <div class="form-group">
                            <label for="llm-prompt">请输入您的日程安排需求：</label>
                            <textarea id="llm-prompt" rows="4" placeholder="例如：明天下午三点要开会，需要提前准备一个小时"></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>选择模型：</label>
                            <div class="radio-group">
                                <input type="radio" id="model-deepseek" name="model" value="deepseek-chat" checked>
                                <label for="model-deepseek">DeepSeek Chat</label>
                                
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
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Microsoft YaHei', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ddd;
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
    margin-bottom: 5px;
    padding: 5px;
    border-radius: 3px;
    font-size: 12px;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
}

.radio-group label, .checkbox-group label {
    font-weight: normal;
    margin-bottom: 0;
    cursor: pointer;
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
    display: none;
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
    
    // 移除所有按钮的active类
    document.querySelectorAll('.view-controls button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 添加当前按钮的active类
    document.getElementById(viewType + '-view').classList.add('active');
    
    // 隐藏所有视图
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    // 显示对应的视图
    document.getElementById(viewType + '-grid').classList.add('active');
    
    // 隐藏所有导航控件
    document.querySelectorAll('.navigation-controls').forEach(nav => {
        nav.classList.remove('active');
    });
    
    // 显示对应的导航控件
    if (viewType === 'list') {
        // 列表视图使用月份导航
        document.getElementById('month-navigation').classList.add('active');
    } else {
        document.getElementById(viewType + '-navigation').classList.add('active');
    }
    
    // 更新日期显示
    updateDateDisplay();
    
    // 重新加载事件数据
    loadEvents();
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
function loadEvents() {
    let dateFrom, dateTo;
    
    // 根据当前视图类型确定日期范围
    switch(currentView) {
        case 'month':
            // 计算当前月份的起始日期和结束日期
            const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            dateFrom = formatDate(firstDay);
            dateTo = formatDate(lastDay);
            break;
            
        case 'week':
            // 计算当前周的起始日期和结束日期
            const startOfWeek = new Date(currentDate);
            startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
            const endOfWeek = new Date(startOfWeek);
            endOfWeek.setDate(startOfWeek.getDate() + 6);
            dateFrom = formatDate(startOfWeek);
            dateTo = formatDate(endOfWeek);
            break;
            
        case 'day':
            // 当前日期
            dateFrom = formatDate(currentDate);
            dateTo = dateFrom;
            break;
            
        case 'list':
            // 默认显示当前月
            const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            dateFrom = formatDate(firstDayOfMonth);
            dateTo = formatDate(lastDayOfMonth);
            break;
    }
    
    console.log("加载事件数据:", dateFrom, "到", dateTo);
    
    // 发送API请求获取事件
    fetch(`/api/events?date_from=${dateFrom}&date_to=${dateTo}`)
        .then(response => response.json())
        .then(data => {
            events = data;
            renderCurrentView();
        })
        .catch(error => {
            console.error('获取事件数据失败:', error);
        });
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
    updateDateDisplay();
    loadEvents();
}

// 下个月
function nextMonth() {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
    updateDateDisplay();
    loadEvents();
}

// 上一周
function previousWeek() {
    currentDate.setDate(currentDate.getDate() - 7);
    updateDateDisplay();
    loadEvents();
}

// 下一周
function nextWeek() {
    currentDate.setDate(currentDate.getDate() + 7);
    updateDateDisplay();
    loadEvents();
}

// 前一天
function previousDay() {
    currentDate.setDate(currentDate.getDate() - 1);
    updateDateDisplay();
    loadEvents();
}

// 后一天
function nextDay() {
    currentDate.setDate(currentDate.getDate() + 1);
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
            const eventItem = document.createElement('div');
            eventItem.className = `event-item type-${event.event_type.toLowerCase()}`;
            eventItem.textContent = event.title;
            eventItem.dataset.eventId = event.id;
            
            // 添加点击事件显示详情
            eventItem.addEventListener('click', function() {
                showEventDetails(event);
            });
            
            dayCell.appendChild(eventItem);
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

// 解析时间字符串为小时和分钟
function parseTimeString(timeStr) {
    const parts = timeStr.trim().split(':');
    const hour = parseInt(parts[0]);
    const minute = parseInt(parts[1] || 0);
    return { hour, minute };
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
    if (durationHours <= 0) durationHours = 0.5; // 最小持续时间30分钟
    
    // 计算事件高度
    const height = durationHours * 40;
    
    return { top, height };
}

// 渲染周视图
function renderWeekView() {
    const weekGrid = document.getElementById('week-grid');
    
    // 计算当前周的起始日期
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    
    // 添加时间列
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    
    // 添加空白头部单元格
    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'week-day-header empty';
    timeColumn.appendChild(emptyHeader);
    
    // 添加时间单元格
    for (let hour = 0; hour < 24; hour++) {
        const timeCell = document.createElement('div');
        timeCell.className = 'time-cell';
        timeCell.textContent = `${hour.toString().padStart(2, '0')}:00`;
        timeColumn.appendChild(timeCell);
    }
    
    weekGrid.appendChild(timeColumn);
    
    // 添加每天的列
    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(startOfWeek);
        dayDate.setDate(startOfWeek.getDate() + i);
        
        const dayColumn = document.createElement('div');
        dayColumn.className = 'week-day-column';
        
        // 添加日期头部
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
            
            // 添加小时标签（可选，在每个小时处显示时间）
            if (i === 0) { // 只在第一列添加
                const hourLabel = document.createElement('div');
                hourLabel.className = 'hour-label';
                hourLabel.style.position = 'absolute';
                hourLabel.style.left = '5px';
                hourLabel.style.top = `${hour * 40 + 30 - 10}px`;
                hourLabel.style.fontSize = '10px';
                hourLabel.style.color = '#999';
                hourLabel.style.zIndex = '2';
                hourLabel.textContent = `${hour.toString().padStart(2, '0')}:00`;
                // 不添加到DOM，因为已经有时间列了
            }
        }
        
        // 获取当天的事件
        const currentDateStr = formatDate(dayDate);
        const dayEvents = events.filter(event => event.date === currentDateStr);
        
        // 添加事件到日期列
        dayEvents.forEach(event => {
            const eventItem = document.createElement('div');
            eventItem.className = `event-item type-${event.event_type.toLowerCase()}`;
            eventItem.textContent = `${event.time_range}: ${event.title}`;
            eventItem.dataset.eventId = event.id;
            
            // 解析时间范围，计算位置
            const position = calculateEventPosition(event.time_range);
            if (position) {
                eventItem.style.position = 'absolute';
                eventItem.style.top = `${position.top}px`;
                eventItem.style.left = '5px';
                eventItem.style.right = '5px';
                eventItem.style.height = `${position.height}px`;
            }
            
            // 添加点击事件显示详情
            eventItem.addEventListener('click', function() {
                showEventDetails(event);
            });
            
            dayColumn.appendChild(eventItem);
        });
        
        weekGrid.appendChild(dayColumn);
    }
}

// 渲染日视图
function renderDayView() {
    const dayGrid = document.getElementById('day-grid');
    
    // 添加时间列
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    
    // 添加空白头部单元格
    const emptyHeader = document.createElement('div');
    emptyHeader.className = 'week-day-header empty';
    timeColumn.appendChild(emptyHeader);
    
    // 添加时间单元格
    for (let hour = 0; hour < 24; hour++) {
        const timeCell = document.createElement('div');
        timeCell.className = 'time-cell';
        timeCell.textContent = `${hour.toString().padStart(2, '0')}:00`;
        timeColumn.appendChild(timeCell);
    }
    
    dayGrid.appendChild(timeColumn);
    
    // 添加当天的列
    const dayColumn = document.createElement('div');
    dayColumn.className = 'day-column';
    
    // 添加日期头部
    const dayHeader = document.createElement('div');
    dayHeader.className = 'week-day-header';
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
    
    // 获取当天的事件
    const currentDateStr = formatDate(currentDate);
    const dayEvents = events.filter(event => event.date === currentDateStr);
    
    // 添加事件到日期列
    dayEvents.forEach(event => {
        const eventItem = document.createElement('div');
        eventItem.className = `event-item type-${event.event_type.toLowerCase()}`;
        eventItem.textContent = `${event.time_range}: ${event.title}`;
        eventItem.dataset.eventId = event.id;
        
        // 解析时间范围，计算位置
        const position = calculateEventPosition(event.time_range);
        if (position) {
            eventItem.style.position = 'absolute';
            eventItem.style.top = `${position.top}px`;
            eventItem.style.left = '5px';
            eventItem.style.right = '5px';
            eventItem.style.height = `${position.height}px`;
        }
        
        // 添加点击事件显示详情
        eventItem.addEventListener('click', function() {
            showEventDetails(event);
        });
        
        dayColumn.appendChild(eventItem);
    });
    
    dayGrid.appendChild(dayColumn);
}

// 渲染列表视图
function renderListView() {
    const listGrid = document.getElementById('list-grid');
    
    // 按日期分组事件
    const eventsByDate = {};
    events.forEach(event => {
        if (!eventsByDate[event.date]) {
            eventsByDate[event.date] = [];
        }
        eventsByDate[event.date].push(event);
    });
    
    // 按日期排序
    const sortedDates = Object.keys(eventsByDate).sort();
    
    // 遍历日期
    sortedDates.forEach(date => {
        // 添加日期标题
        const dateHeader = document.createElement('div');
        dateHeader.className = 'list-date-header';
        
        // 格式化日期显示
        const dateParts = date.split('-');
        const dateObj = new Date(dateParts[0], dateParts[1] - 1, dateParts[2]);
        dateHeader.textContent = `${dateObj.getFullYear()}年${dateObj.getMonth() + 1}月${dateObj.getDate()}日 ${['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()]}`;
        
        listGrid.appendChild(dateHeader);
        
        // 添加当天的事件
        eventsByDate[date].forEach(event => {
            const eventItem = document.createElement('div');
            eventItem.className = `list-event-item type-${event.event_type.toLowerCase()}`;
            
            // 创建事件内容
            const eventTitle = document.createElement('div');
            eventTitle.className = 'event-title';
            eventTitle.textContent = event.title;
            
            const eventTime = document.createElement('div');
            eventTime.className = 'event-time';
            eventTime.textContent = `时间: ${event.time_range}`;
            
            const eventType = document.createElement('div');
            eventType.className = 'event-type';
            eventType.textContent = `类型: ${event.event_type}`;
            
            eventItem.appendChild(eventTitle);
            eventItem.appendChild(eventTime);
            eventItem.appendChild(eventType);
            
            // 添加点击事件显示详情
            eventItem.addEventListener('click', function() {
                showEventDetails(event);
            });
            
            listGrid.appendChild(eventItem);
        });
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
    
    // 设置内容
    detailsContent.innerHTML = details.join('<br>');
    
    // 显示详情面板
    detailsContainer.classList.remove('hidden');
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
        show_unchanged: showUnchanged
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