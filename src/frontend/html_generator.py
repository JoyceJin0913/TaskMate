"""
HTML模板生成器模块，负责生成HTML模板
"""

import os

class HTMLGenerator:
    """HTML模板生成器，负责生成HTML模板"""
    
    def __init__(self, templates_dir="templates"):
        """
        初始化HTML模板生成器
        
        Args:
            templates_dir (str): 模板目录路径
        """
        self.templates_dir = templates_dir
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        # 创建模板目录
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def create_index_template(self):
        """创建主页模板"""
        index_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskMate - 智能日程管理</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>TaskMate <span class="subtitle">智能日程管理</span></h1>
            <nav>
                <ul>
                    <li><a href="#calendar-view" class="active" data-view="calendar">日历视图</a></li>
                    <li><a href="#list-view" data-view="list">列表视图</a></li>
                    <li><a href="#time-review" data-view="time-review">时间复盘</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <!-- 添加任务表单 -->
            <section class="task-input">
                <h2>添加新任务</h2>
                <form id="task-form">
                    <div class="form-group">
                        <label for="task-prompt">描述你的任务：</label>
                        <textarea id="task-prompt" placeholder="例如：明天下午3点开会，需要准备PPT"></textarea>
                    </div>
                    
                    <div class="form-options">
                        <div class="form-group">
                            <label for="model-select">选择模型：</label>
                            <select id="model-select">
                                <option value="deepseek-chat">DeepSeek Chat</option>
                                <option value="gpt-4o">GPT-4o</option>
                                <option value="gpt-4-mini">GPT-4 Mini</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="recurrence-select">重复规则：</label>
                            <select id="recurrence-select">
                                <option value="">不重复</option>
                                <option value="daily">每天</option>
                                <option value="weekly">每周</option>
                                <option value="weekdays">工作日</option>
                                <option value="monthly">每月</option>
                                <option value="yearly">每年</option>
                            </select>
                        </div>
                        
                        <div class="form-group end-date-group" style="display: none;">
                            <label for="end-date">结束日期：</label>
                            <input type="date" id="end-date">
                        </div>
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" id="submit-task">添加任务</button>
                        <div class="loading-spinner" id="loading-spinner" style="display: none;">
                            <div class="spinner"></div>
                            <span>处理中...</span>
                        </div>
                    </div>
                </form>
            </section>
            
            <!-- 日历视图 -->
            <section id="calendar-view" class="view-section active">
                <div class="calendar-header">
                    <button id="prev-month"><i class="fas fa-chevron-left"></i></button>
                    <h2 id="current-month">2024年3月</h2>
                    <button id="next-month"><i class="fas fa-chevron-right"></i></button>
                </div>
                <div class="calendar-grid" id="calendar-grid">
                    <!-- 日历内容将通过JavaScript动态生成 -->
                </div>
            </section>
            
            <!-- 列表视图 -->
            <section id="list-view" class="view-section">
                <div class="list-header">
                    <div class="date-navigation">
                        <button id="prev-week"><i class="fas fa-chevron-left"></i> 上一周</button>
                        <h2 id="current-week">2024年第10周 (3月4日-3月10日)</h2>
                        <button id="next-week">下一周 <i class="fas fa-chevron-right"></i></button>
                    </div>
                </div>
                <div class="list-container" id="list-container">
                    <!-- 列表内容将通过JavaScript动态生成 -->
                </div>
            </section>
            
            <!-- 时间复盘 -->
            <section id="time-review" class="view-section">
                <div class="review-header">
                    <h2>时间复盘</h2>
                    <div class="date-filter">
                        <label for="review-date-from">从：</label>
                        <input type="date" id="review-date-from">
                        <label for="review-date-to">至：</label>
                        <input type="date" id="review-date-to">
                        <button id="apply-date-filter">应用</button>
                    </div>
                </div>
                <div class="time-review-grid" id="time-review-grid">
                    <!-- 时间复盘内容将通过JavaScript动态生成 -->
                </div>
            </section>
        </main>
        
        <!-- 事件详情模态框 -->
        <div class="modal" id="event-modal">
            <div class="modal-content">
                <span class="close-modal">&times;</span>
                <h2 id="modal-title">事件详情</h2>
                <div id="modal-content">
                    <!-- 事件详情将通过JavaScript动态生成 -->
                </div>
                <div class="modal-actions" id="modal-actions">
                    <!-- 操作按钮将通过JavaScript动态生成 -->
                </div>
            </div>
        </div>
        
        <!-- 完成任务模态框 -->
        <div class="modal" id="complete-modal">
            <div class="modal-content">
                <span class="close-modal">&times;</span>
                <h2>完成任务</h2>
                <form id="complete-form">
                    <input type="hidden" id="complete-task-id">
                    <div class="form-group">
                        <label for="actual-time-range">实际用时：</label>
                        <input type="text" id="actual-time-range" placeholder="例如：14:00-15:30">
                    </div>
                    <div class="form-group">
                        <label for="completion-notes">完成情况：</label>
                        <textarea id="completion-notes" placeholder="描述任务完成情况..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="reflection-notes">反思与收获：</label>
                        <textarea id="reflection-notes" placeholder="记录你的反思与收获..."></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="submit" id="submit-completion">提交</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- 响应模态框 -->
        <div class="modal" id="response-modal">
            <div class="modal-content">
                <span class="close-modal">&times;</span>
                <h2>AI助手回复</h2>
                <div id="response-content" class="response-content">
                    <!-- AI响应内容将通过JavaScript动态生成 -->
                </div>
            </div>
        </div>
        
        <footer>
            <p>&copy; 2024 TaskMate - 智能日程管理系统</p>
        </footer>
    </div>
    
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
"""
        
        # 写入文件
        with open(os.path.join(self.templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    def create_all_templates(self):
        """创建所有HTML模板"""
        self.ensure_directories()
        self.create_index_template()
        
        return "HTML模板已创建完成" 