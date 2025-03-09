"""
CSS生成器模块，负责生成CSS样式文件
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

class CSSGenerator:
    """CSS生成器，负责生成CSS样式文件"""
    
    def __init__(self, static_dir="static"):
        """
        初始化CSS生成器
        
        Args:
            static_dir (str): 静态资源目录路径
        """
        self.static_dir = static_dir
        self.css_dir = os.path.join(static_dir, "css")
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        # 创建CSS目录
        if not os.path.exists(self.css_dir):
            os.makedirs(self.css_dir)
    
    def create_css(self):
        """创建CSS样式文件"""
        css = """/* 全局样式 */
:root {
    --primary-color: #4a6fa5;
    --secondary-color: #6b8cae;
    --accent-color: #ff6b6b;
    --background-color: #f8f9fa;
    --card-color: #ffffff;
    --text-color: #333333;
    --border-color: #e0e0e0;
    --shadow-color: rgba(0, 0, 0, 0.1);
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --info-color: #17a2b8;
    --timeline-bg: #f5f5f5;
    --timeline-line: #ddd;
    --timeline-hour: #888;
    --timeline-now: #ff6b6b;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* 头部样式 */
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
}

header h1 {
    color: var(--primary-color);
    font-size: 2.5rem;
}

header .subtitle {
    font-size: 1.2rem;
    font-weight: normal;
    color: var(--secondary-color);
}

nav ul {
    display: flex;
    list-style: none;
}

nav ul li {
    margin-left: 20px;
}

nav ul li a {
    text-decoration: none;
    color: var(--text-color);
    font-weight: 500;
    padding: 8px 12px;
    border-radius: 4px;
    transition: all 0.3s ease;
}

nav ul li a:hover {
    background-color: var(--secondary-color);
    color: white;
}

nav ul li a.active {
    background-color: var(--primary-color);
    color: white;
}

/* 主要内容区域 */
main {
    margin-bottom: 40px;
}

/* 任务输入表单 */
.task-input {
    background-color: var(--card-color);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px var(--shadow-color);
    margin-bottom: 30px;
}

.task-input h2 {
    margin-bottom: 20px;
    color: var(--primary-color);
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}

.form-group textarea,
.form-group input,
.form-group select {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-family: inherit;
    font-size: 1rem;
}

.form-group textarea {
    height: 100px;
    resize: vertical;
}

.form-options {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 20px;
}

.form-options .form-group {
    flex: 1;
    min-width: 200px;
}

.form-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.3s ease;
}

button:hover {
    background-color: var(--secondary-color);
}

/* 加载动画 */
.loading-spinner {
    display: flex;
    align-items: center;
}

.spinner {
    border: 3px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top: 3px solid var(--primary-color);
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
    margin-right: 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 视图部分 */
.view-section {
    display: none;
    background-color: var(--card-color);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px var(--shadow-color);
}

.view-section.active {
    display: block;
}

/* 日历视图 */
.calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.calendar-header h2 {
    color: var(--primary-color);
}

.calendar-header button {
    background-color: transparent;
    color: var(--primary-color);
    border: 1px solid var(--primary-color);
    padding: 5px 10px;
}

.calendar-header button:hover {
    background-color: var(--primary-color);
    color: white;
}

.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 10px;
}

.calendar-day-header {
    text-align: center;
    font-weight: bold;
    padding: 10px;
    background-color: var(--primary-color);
    color: white;
    border-radius: 4px;
}

.calendar-day {
    min-height: 120px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 10px;
    position: relative;
}

.calendar-day.today {
    background-color: rgba(74, 111, 165, 0.1);
    border-color: var(--primary-color);
}

.calendar-day.other-month {
    background-color: #f0f0f0;
    color: #999;
}

.day-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}

.day-number {
    font-weight: bold;
}

.day-events {
    overflow-y: auto;
    max-height: 80px;
}

.event-item {
    background-color: var(--primary-color);
    color: white;
    padding: 5px;
    border-radius: 3px;
    margin-bottom: 5px;
    font-size: 0.8rem;
    cursor: pointer;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.event-item.task {
    background-color: var(--secondary-color);
}

.event-item.fixed {
    background-color: var(--accent-color);
}

.event-item.completed {
    background-color: var(--success-color);
    text-decoration: line-through;
}

/* 列表视图 */
.list-header,
.week-header,
.day-header {
    margin-bottom: 20px;
}

.date-navigation {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.date-navigation h2 {
    color: var(--primary-color);
}

.list-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.day-group {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
}

.day-group-header {
    background-color: var(--primary-color);
    color: white;
    padding: 10px 15px;
    font-weight: bold;
}

.day-group.today .day-group-header {
    background-color: var(--accent-color);
}

.events-list {
    padding: 10px;
}

.list-event-item {
    display: flex;
    padding: 10px;
    border-bottom: 1px solid var(--border-color);
    transition: background-color 0.2s ease;
}

.list-event-item:last-child {
    border-bottom: none;
}

.list-event-item:hover {
    background-color: rgba(74, 111, 165, 0.05);
}

.event-time {
    width: 100px;
    font-weight: bold;
    color: var(--primary-color);
}

.event-content {
    flex: 1;
}

.event-title {
    font-weight: bold;
    margin-bottom: 5px;
}

.event-details {
    font-size: 0.9rem;
    color: #666;
}

.event-actions {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}

.event-actions button {
    padding: 5px 10px;
    font-size: 0.8rem;
}

.complete-btn {
    background-color: var(--success-color);
}

.complete-btn:hover {
    background-color: #218838;
}

.delete-btn {
    background-color: var(--danger-color);
}

.delete-btn:hover {
    background-color: #c82333;
}

/* 周视图和日视图 */
.week-timeline,
.day-timeline {
    display: flex;
    flex-direction: column;
    background-color: var(--timeline-bg);
    border-radius: 8px;
    overflow: hidden;
}

.timeline-header {
    display: flex;
    border-bottom: 1px solid var(--timeline-line);
}

.timeline-header .time-column {
    width: 60px;
    border-right: 1px solid var(--timeline-line);
}

.timeline-header .day-column {
    flex: 1;
    text-align: center;
    padding: 10px;
    font-weight: bold;
    border-right: 1px solid var(--timeline-line);
}

.timeline-header .day-column:last-child {
    border-right: none;
}

.timeline-header .day-column.today {
    background-color: rgba(74, 111, 165, 0.1);
}

.timeline-body {
    display: flex;
    position: relative;
}

.timeline-hours {
    width: 60px;
    border-right: 1px solid var(--timeline-line);
}

.timeline-hour {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--timeline-line);
    color: var(--timeline-hour);
    font-size: 0.8rem;
}

.timeline-days {
    display: flex;
    flex: 1;
}

.timeline-day {
    flex: 1;
    border-right: 1px solid var(--timeline-line);
    position: relative;
}

.timeline-day:last-child {
    border-right: none;
}

.timeline-day.today {
    background-color: rgba(74, 111, 165, 0.05);
}

.timeline-event {
    position: absolute;
    left: 5px;
    right: 5px;
    padding: 5px;
    border-radius: 4px;
    font-size: 0.8rem;
    overflow: hidden;
    cursor: pointer;
    z-index: 1;
}

.timeline-event.task {
    background-color: var(--secondary-color);
    color: white;
}

.timeline-event.fixed {
    background-color: var(--accent-color);
    color: white;
}

.timeline-event.completed {
    background-color: var(--success-color);
    color: white;
    text-decoration: line-through;
}

.timeline-now-line {
    position: absolute;
    left: 0;
    right: 0;
    border-top: 2px dashed var(--timeline-now);
    z-index: 2;
}

.timeline-now-label {
    position: absolute;
    left: 5px;
    background-color: var(--timeline-now);
    color: white;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 0.7rem;
    z-index: 3;
}

/* 时间复盘 */
.review-header {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-bottom: 20px;
}

.review-header h2 {
    color: var(--primary-color);
}

.date-filter {
    display: flex;
    align-items: center;
    gap: 10px;
}

.date-filter input {
    padding: 5px 10px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
}

.review-tabs {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}

.review-tabs button {
    background-color: transparent;
    color: var(--text-color);
    border: 1px solid var(--border-color);
    padding: 8px 15px;
}

.review-tabs button.active {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.time-review-grid {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.event-notes {
    margin-top: 10px;
    padding: 10px;
    background-color: #f9f9f9;
    border-radius: 4px;
}

.completion-notes,
.reflection-notes {
    margin-bottom: 10px;
}

.add-reflection-btn {
    background-color: var(--info-color);
    color: white;
    padding: 5px 10px;
    font-size: 0.8rem;
}

.add-reflection-btn:hover {
    background-color: #138496;
}

/* 时间分析 */
.analysis-charts {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-top: 20px;
}

.chart-container {
    flex: 1;
    min-width: 300px;
    background-color: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.chart-container h3 {
    margin-bottom: 15px;
    color: var(--primary-color);
    text-align: center;
}

/* 生产力报告 */
.productivity-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    flex: 1;
    min-width: 200px;
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    text-align: center;
}

.stat-card h3 {
    margin-bottom: 10px;
    color: var(--primary-color);
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--secondary-color);
}

.productivity-trends {
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.productivity-trends h3 {
    margin-bottom: 15px;
    color: var(--primary-color);
    text-align: center;
}

/* 模态框 */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.modal-content {
    background-color: var(--card-color);
    padding: 20px;
    border-radius: 8px;
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    position: relative;
}

.close-modal {
    position: absolute;
    top: 10px;
    right: 15px;
    font-size: 1.5rem;
    cursor: pointer;
    color: #999;
}

.close-modal:hover {
    color: var(--danger-color);
}

.modal h2 {
    margin-bottom: 20px;
    color: var(--primary-color);
    padding-right: 30px;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
}

/* 响应内容 */
.response-content {
    white-space: pre-wrap;
    font-family: monospace;
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    max-height: 60vh;
    overflow-y: auto;
}

/* 页脚 */
footer {
    text-align: center;
    padding: 20px 0;
    color: #666;
    border-top: 1px solid var(--border-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
    header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    nav ul {
        margin-top: 15px;
        flex-wrap: wrap;
    }
    
    nav ul li {
        margin-left: 0;
        margin-right: 15px;
        margin-bottom: 10px;
    }
    
    .form-options {
        flex-direction: column;
        gap: 10px;
    }
    
    .calendar-grid {
        grid-template-columns: repeat(1, 1fr);
    }
    
    .calendar-day {
        min-height: auto;
    }
    
    .date-navigation {
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
    }
    
    .date-filter {
        flex-wrap: wrap;
    }
    
    .timeline-header .day-column {
        padding: 5px;
        font-size: 0.8rem;
    }
    
    .timeline-event {
        font-size: 0.7rem;
    }
    
    .analysis-charts,
    .productivity-stats {
        flex-direction: column;
    }
}
"""
        
        # 写入文件
        with open(os.path.join(self.css_dir, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(css)
    
    def create_all_css(self):
        """创建所有CSS样式文件"""
        self.ensure_directories()
        self.create_css()
        
        return "CSS样式文件已创建完成" 