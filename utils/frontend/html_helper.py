def create_templates():
    """Create HTML templates"""
    index_html = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskMate</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>TaskMate</h1>
            <div class="date-controls">
                <!-- Month view navigation -->
                <div id="month-navigation" class="navigation-controls active">
                    <button id="prev-month">上个月</button>
                    <span id="current-month"></span>
                    <button id="next-month">下个月</button>
                </div>
                
                <!-- Week view navigation -->
                <div id="week-navigation" class="navigation-controls">
                    <button id="prev-week">上一周</button>
                    <span id="current-week"></span>
                    <button id="next-week">下一周</button>
                </div>
                
                <!-- Day view navigation -->
                <div id="day-navigation" class="navigation-controls">
                    <button id="prev-day">前一天</button>
                    <span id="current-day"></span>
                    <button id="next-day">后一天</button>
                </div>
            </div>
        </header>
        
        <div class="main-content">
            <!-- 左侧菜单 -->
            <div class="sidebar">
                <div class="sidebar-section">
                    <button id="planning-view" class="section-button">Planning</button>
                </div>
                
                <div class="sidebar-section">
                    <button id="schedule-section-btn" class="section-button active">Schedule</button>
                    <div id="schedule-menu" class="sidebar-menu active">
                        <button id="month-view" class="sidebar-button active">月视图</button>
                        <button id="week-view" class="sidebar-button">周视图</button>
                        <button id="day-view" class="sidebar-button">日视图</button>
                        <!-- 暂时隐藏列表视图和已完成按钮 
                        <button id="list-view" class="sidebar-button">列表视图</button>
                        <button id="completed-view" class="sidebar-button">已完成</button>
                        -->
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <button id="reviewing-view" class="section-button">Reviewing</button>
                </div>
            </div>
            
            <!-- 主内容区域 -->
            <div class="content-area">
                <!-- View containers -->
                <div id="calendar-container">
                    <!-- Month view -->
                    <div id="month-grid" class="view active"></div>
                    
                    <!-- Week view -->
                    <div id="week-grid" class="view"></div>
                    
                    <!-- Day view -->
                    <div id="day-grid" class="view"></div>
                    
                    <!-- List view -->
                    <div id="list-grid" class="view"></div>
                    
                    <!-- Completed view -->
                    <div id="completed-grid" class="view"></div>
                    
                    <!-- Time review view -->
                    <div id="time-review-grid" class="view"></div>
                    
                    <!-- LLM query view -->
                    <div id="llm-grid" class="view">
                        <div class="llm-container">
                            <h2>LLM日程规划助手</h2>
                            <div class="llm-form">
                                <!-- 隐藏选择操作模式选项 -->
                                <div class="hidden">
                                    <input type="radio" id="mode-future-planning" name="query_type" value="future_planning" checked>
                                    <input type="radio" id="mode-historical-review" name="query_type" value="historical_review">
                                </div>

                                <div class="form-group">
                                    <label for="llm-prompt">请输入您的需求：</label>
                                    <textarea id="llm-prompt" rows="4" placeholder="请输入您的日程规划需求，例如：明天下午三点要开会，需要提前准备一个小时"></textarea>
                                </div>
                                
                                <div class="form-group">
                                    <label>选择模型：</label>
                                    <div class="radio-group">
                                        <input type="radio" id="model-deepseek-chat" name="model" value="deepseek-chat" checked>
                                        <label for="model-deepseek-chat">DeepSeek V3</label>

                                        <input type="radio" id="model-deepseek-reasoner" name="model" value="deepseek-reasoner">
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
            </div>
        </div>
        
        <div id="event-details" class="hidden">
            <div class="event-details-header">
                <h2>事件详情</h2>
                <button id="close-details">×</button>
            </div>
            <div id="event-details-content"></div>
        </div>

        <!-- Complete task dialog -->
        <div id="complete-task-dialog" class="hidden">
            <div class="dialog-header">
                <h2>完成任务</h2>
                <button id="close-complete-dialog">×</button>
            </div>
            <div class="dialog-content">
                <div class="form-group">
                    <label>实际发生时间范围（可选）：</label>
                    <div class="time-picker-container">
                        <div class="time-picker-group">
                            <label for="actual-start-time">开始时间：</label>
                            <input type="time" id="actual-start-time">
                        </div>
                        <div class="time-picker-separator">至</div>
                        <div class="time-picker-group">
                            <label for="actual-end-time">结束时间：</label>
                            <input type="time" id="actual-end-time">
                        </div>
                    </div>
                    <div class="overnight-checkbox">
                        <input type="checkbox" id="is-overnight-event">
                        <label for="is-overnight-event">跨天事件（结束时间在次日）</label>
                    </div>
                </div>
                <div class="form-group">
                    <label for="completion-notes">完成情况备注（可选）：</label>
                    <textarea id="completion-notes" rows="3" placeholder="请输入完成情况备注..."></textarea>
                </div>
                <div class="form-group">
                    <label for="reflection-notes">复盘笔记（可选）：</label>
                    <textarea id="reflection-notes" rows="3" placeholder="请输入复盘笔记..."></textarea>
                </div>
                <div class="dialog-buttons">
                    <button id="submit-complete" class="primary-button">确认完成</button>
                    <button id="cancel-complete" class="secondary-button">取消</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
