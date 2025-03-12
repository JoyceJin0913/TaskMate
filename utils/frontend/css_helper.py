def create_css():
    css = '''
/* 全局样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-color: #4361ee;
    --primary-light: #4895ef;
    --primary-dark: #3f37c9;
    --primary-light-transparent: rgba(72, 149, 239, 0.2);
    --secondary-color: #4cc9f0;
    --text-color: #2b2d42;
    --text-light: #8d99ae;
    --background-color: #f8f9fa;
    --card-color: #ffffff;
    --border-color: #e9ecef;
    --success-color: #4ade80;
    --warning-color: #fbbf24;
    --error-color: #f87171;
    --error-light: #fecaca;
    --info-color: #60a5fa;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
    --border-radius-sm: 4px;
    --border-radius-md: 8px;
    --border-radius-lg: 12px;
    --transition-speed: 0.3s;
    --heading-color: #2c3e50;
    --text-color-light: #8d99ae;
    --today-highlight: rgba(67, 97, 238, 0.1);
}

body {
    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}

.container {
    max-width: 1500px;
    margin: 0 auto;
    padding: 20px;
}

/* 主内容布局 */
.main-content {
    display: flex;
    gap: 20px;
    min-height: calc(100vh - 100px);
}

/* 左侧边栏样式 */
.sidebar {
    width: 220px;
    background-color: var(--card-color);
    border-radius: var(--border-radius-md);
    box-shadow: var(--shadow-md);
    padding: 20px;
    flex-shrink: 0;
}

.sidebar-section {
    margin-bottom: 20px;
}

/* 分类按钮样式 */
.section-button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 12px 15px;
    background-color: var(--background-color);
    color: var(--text-color);
    border: none;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    transition: all var(--transition-speed);
    font-weight: 600;
    font-size: 15px;
}

.section-button:hover {
    background-color: var(--border-color);
    transform: translateY(-2px);
}

.section-button.active {
    background-color: var(--primary-color);
    color: white;
    box-shadow: var(--shadow-sm);
}

/* Schedule按钮特殊样式 */
#schedule-section-btn {
    position: relative;
}

#schedule-section-btn::after {
    content: '▼';
    position: absolute;
    right: 15px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 12px;
    transition: transform var(--transition-speed);
}

#schedule-section-btn.active::after {
    transform: translateY(-50%) rotate(180deg);
}

/* 侧边栏菜单样式 */
.sidebar-menu {
    display: none;
    flex-direction: column;
    gap: 10px;
    padding: 12px 0 0 12px;
}

.sidebar-menu.active {
    display: flex;
}

.sidebar-button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 10px 12px;
    background-color: var(--background-color);
    color: var(--text-color);
    border: none;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    transition: all var(--transition-speed);
    font-size: 14px;
}

.sidebar-button:hover {
    background-color: var(--border-color);
    transform: translateX(3px);
}

.sidebar-button.active {
    background-color: var(--primary-light);
    color: white;
}

/* 主内容区域样式 */
.content-area {
    flex-grow: 1;
    background-color: var(--card-color);
    border-radius: var(--border-radius-md);
    box-shadow: var(--shadow-md);
    padding: 25px;
    overflow: auto;
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
    font-size: 28px;
    color: var(--heading-color);
    font-weight: 700;
    margin-bottom: 20px;
}

.date-controls {
    display: flex;
    align-items: center;
    gap: 12px;
}

.navigation-controls {
    display: none;
    align-items: center;
    gap: 12px;
}

.navigation-controls.active {
    display: flex;
}

button {
    padding: 10px 16px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    transition: all var(--transition-speed);
    font-weight: 500;
    box-shadow: var(--shadow-sm);
}

button:hover {
    background-color: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

button:active {
    transform: translateY(0);
}

.view-controls {
    display: flex;
    gap: 12px;
    margin-bottom: 25px;
}

.view-controls button {
    background-color: var(--background-color);
    color: var(--text-color);
    border: 1px solid var(--border-color);
}

.view-controls button:hover {
    background-color: var(--border-color);
    border-color: var(--text-color-light);
}

.view-controls button.active {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

/* 视图容器 */
#calendar-container {
    position: relative;
    height: 700px; /* 固定高度 */
    width: 100%;
    overflow-y: auto; /* 添加垂直滚动条 */
    overflow-x: hidden; /* 隐藏水平滚动条 */
    scroll-behavior: smooth; /* 平滑滚动 */
    border-radius: var(--border-radius-md);
    background-color: var(--background-color);
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
    width: 100%;
}

#month-grid.active {
    display: grid;
}

.day-cell {
    min-height: 100px;
    background-color: var(--card-color);
    border-radius: var(--border-radius-sm);
    padding: 5px;
    border: 1px solid var(--border-color);
    transition: all var(--transition-speed);
    position: relative;
    overflow: visible;
    width: 100%; /* 固定宽度 */
}

.day-cell:hover {
    box-shadow: var(--shadow-sm);
    border-color: var(--primary-light);
}

.day-header {
    text-align: center;
    font-weight: 600;
    padding: 8px;
    background-color: var(--background-color);
    border-radius: var(--border-radius-sm) var(--border-radius-sm) 0 0;
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
    transition: all var(--transition-speed);
    border-left-width: 3px;
    border-left-style: solid;
}

/* 月视图中的事件悬停效果 */
.day-cell .event-item:hover {
    z-index: 100;
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
    min-height: auto;
    position: relative;
    border-radius: var(--border-radius-sm);
    padding: 4px 25px 4px 5px;
    width: auto;
    word-wrap: break-word;
    overflow: visible;
    margin-right: -10px;
}

/* 已完成事件样式 */
.event-item.completed {
    text-decoration: line-through;
    opacity: 0.7;
    background: #f0f0f0 !important;
    color: #666 !important;
    border-left: 3px solid #999 !important;
}

/* 周视图和日视图中的已完成事件样式 */
.day-column .event-item.completed {
    text-decoration: line-through;
    opacity: 0.7;
    background: rgba(240, 240, 240, 0.9) !important;
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
    transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    transform-style: preserve-3d;
    backface-visibility: hidden;
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
    background-color: #4CAF50;
    color: white;
    border-color: #4CAF50;
    transform: translateY(-50%); /* 保持原位置 */
}

.day-column .complete-button:hover {
    transform: none; /* 保持原位置 */
}

/* 覆盖任何可能的继承变换 */
button.complete-button:hover {
    transform: translateY(-50%);
    box-shadow: none;
}

.day-column button.complete-button:hover {
    transform: none;
}

/* 已完成视图样式 */
#completed-grid {
    padding: 20px;
    background-color: var(--card-color);
    border-radius: var(--border-radius-md);
}

#completed-grid h2 {
    margin-bottom: 25px;
    color: var(--heading-color);
    font-size: 22px;
    font-weight: 600;
}

.date-group {
    margin-bottom: 25px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 15px;
}

.date-group h3 {
    margin-bottom: 15px;
    color: var(--text-color);
    font-size: 18px;
    font-weight: 500;
}

.events-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* 列表视图中的事件项样式 */
.events-list .event-item {
    padding: 12px 15px;
    border-radius: var(--border-radius-sm);
    margin: 0;
    position: relative;
    display: flex;
    align-items: center;
    transition: all var(--transition-speed);
    box-shadow: var(--shadow-sm);
}

.events-list .event-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.events-list .event-item .complete-button {
    position: absolute;
    right: 15px;
}

.empty-message, .error-message {
    padding: 30px;
    text-align: center;
    color: var(--text-color-light);
    background-color: var(--background-color);
    border-radius: var(--border-radius-md);
    margin: 20px 0;
}

.error-message {
    color: var(--error-color);
    border: 1px solid var(--error-light);
}

/* 操作按钮样式 */
.action-button {
    margin-top: 15px;
    padding: 8px 14px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    transition: all var(--transition-speed);
    font-weight: 500;
    box-shadow: var(--shadow-sm);
}

.action-button:hover {
    background-color: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.action-button:active {
    transform: translateY(0);
}

/* 时间轴样式 */
.time-column {
    background-color: var(--background-color);
    border-right: 1px solid var(--border-color);
    min-height: 990px; /* 与日期列保持一致 */
    position: sticky; /* 使时间列固定 */
    left: 0; /* 固定在左侧 */
    z-index: 50; /* 确保在最上层 */
    width: 60px; /* 固定宽度 */
    box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05); /* 添加轻微阴影效果 */
}

.time-cell {
    text-align: right;
    padding: 5px 10px 5px 5px;
    font-size: 12px;
    height: 40px; /* 固定高度，与事件位置计算匹配 */
    line-height: 30px; /* 垂直居中 */
    border-bottom: 1px dashed var(--border-color); /* 添加分隔线 */
    color: var(--text-light);
}

/* 时间标签样式 */
.time-label {
    position: absolute;
    right: 10px;
    font-size: 12px;
    color: var(--text-light);
    font-weight: 500;
    background-color: var(--background-color);
    padding: 2px 4px;
    border-radius: 3px;
    transform: translateY(-50%);
    z-index: 5;
}

/* 小时线样式 */
.hour-line {
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background-color: var(--border-color);
    z-index: 1;
}

/* 半小时线样式 */
.hour-line.half-hour {
    border-top: 1px dotted var(--border-color);
    opacity: 0.7;
}

.week-day-column, .day-column {
    background-color: var(--card-color);
    border: 1px solid var(--border-color);
    min-height: 990px; /* 24小时 * 40px + 30px头部 = 990px */
    position: relative;
    height: 100%; /* 确保列高度填满容器 */
}

.week-day-header {
    text-align: center;
    padding: 10px 8px;
    font-weight: 600;
    background-color: var(--background-color);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 16;
}

/* 日期名称样式 */
.day-name {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 3px;
}

/* 日期数字样式 */
.day-date {
    font-size: 12px;
    color: var(--text-light);
}

.week-day-header.today {
    background-color: var(--today-highlight);
    color: var(--primary-color);
    font-weight: 700;
}

.week-day-header.today .day-date {
    color: var(--primary-color);
    font-weight: 600;
}

/* 当前时间指示线 */
.current-time-indicator {
    position: absolute;
    left: 0;
    right: 0;
    height: 2px;
    background-color: var(--error-color);
    z-index: 20;
    box-shadow: 0 0 5px var(--error-light); /* 使用变量 */
}

.current-time-indicator::before {
    content: '';
    position: absolute;
    left: -5px;
    top: -4px;
    width: 10px;
    height: 10px;
    background-color: var(--error-color);
    border-radius: 50%;
}

/* 周视图和日视图中的事件样式 */
.week-day-column .event-item,
.day-column .event-item {
    position: absolute;
    left: 5px;
    right: 5px;
    padding: 8px 10px;
    z-index: 5; /* 基础层级 */
    min-height: 28px;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    border-radius: var(--border-radius-sm);
    transition: all var(--transition-speed);
    font-size: 13px;
    line-height: 1.3;
    display: flex;
    flex-direction: column;
    border-left-width: 4px;
    border-left-style: solid;
}

/* 未完成事件的层级更高 */
.week-day-column .event-item:not(.completed),
.day-column .event-item:not(.completed) {
    z-index: 15; /* 比已完成事件高很多层 */
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15); /* 更明显的阴影 */
}

/* 已完成事件的层级较低 */
.week-day-column .event-item.completed,
.day-column .event-item.completed {
    z-index: 3; /* 比未完成事件低很多层 */
    opacity: 0.65; /* 降低不透明度 */
    filter: grayscale(30%); /* 添加灰度效果 */
}

.week-day-column .event-item:hover,
.day-column .event-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    z-index: 20; /* 悬停时层级最高 */
    min-height: auto;
    height: auto !important;
    max-height: none !important;
    white-space: normal;
}

/* 周视图和日视图中的已完成事件样式 */
.day-column .event-item.completed,
.week-day-column .event-item.completed {
    text-decoration: line-through;
    opacity: 0.65;
    background: rgba(240, 240, 240, 0.9) !important;
    color: #666 !important;
    border-left: 3px solid #999 !important;
}

.week-day-column .event-item .event-time,
.day-column .event-item .event-time {
    font-size: 11px;
    font-weight: 600;
    opacity: 0.9;
    margin-bottom: 2px;
}

.week-day-column .event-item .event-title,
.day-column .event-item .event-title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.week-day-column .event-item:hover .event-title,
.day-column .event-item:hover .event-title {
    white-space: normal;
    overflow: visible;
}

/* 事件类型样式 */
.event-item.type-meeting {
    background: linear-gradient(135deg, #4361ee, #3a0ca3);
    color: white;
    border-left: 4px solid #3a0ca3;
}

.event-item.type-task {
    background: linear-gradient(135deg, #4cc9f0, #4895ef);
    color: white;
    border-left: 4px solid #4895ef;
}

.event-item.type-deadline {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: white;
    border-left: 4px solid #f59e0b;
}

.event-item.type-other {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    color: white;
    border-left: 4px solid #3b82f6;
}

/* 添加更多事件类型样式 */
.event-item.type-personal {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border-left: 4px solid #059669;
}

.event-item.type-important {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
    border-left: 4px solid #dc2626;
}

.event-item.type-reminder {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    color: white;
    border-left: 4px solid #7c3aed;
}

.event-item.type-appointment {
    background: linear-gradient(135deg, #ec4899, #db2777);
    color: white;
    border-left: 4px solid #db2777;
}

/* 添加事件类型的悬停效果 */
.event-item.type-meeting:hover {
    background: linear-gradient(135deg, #4361ee, #3a0ca3);
    filter: brightness(1.1);
}

.event-item.type-task:hover {
    background: linear-gradient(135deg, #4cc9f0, #4895ef);
    filter: brightness(1.1);
}

.event-item.type-deadline:hover {
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    filter: brightness(1.1);
}

.event-item.type-other:hover {
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    filter: brightness(1.1);
}

.event-item.type-personal:hover {
    background: linear-gradient(135deg, #10b981, #059669);
    filter: brightness(1.1);
}

.event-item.type-important:hover {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    filter: brightness(1.1);
}

.event-item.type-reminder:hover {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    filter: brightness(1.1);
}

.event-item.type-appointment:hover {
    background: linear-gradient(135deg, #ec4899, #db2777);
    filter: brightness(1.1);
}

/* 周视图样式 */
#week-grid {
    display: none;
    grid-template-columns: 60px repeat(7, 1fr);
    gap: 8px;
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
    background-color: var(--card-color);
    border-radius: var(--border-radius-md);
    padding: 25px;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-md);
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
    margin-bottom: 25px;
}

.form-group label {
    display: block;
    margin-bottom: 10px;
    font-weight: 600;
    color: var(--text-color);
}

.form-group textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    font-family: inherit;
    font-size: 15px;
    resize: vertical;
    transition: border-color var(--transition-speed);
    background-color: var(--background-color);
    color: var(--text-color);
}

.form-group textarea:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 2px var(--primary-light-transparent);
}

.radio-group, .checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-top: 8px;
    padding: 15px;
    background-color: var(--background-color);
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--border-color);
}

.radio-group input[type="radio"] {
    margin-right: 5px;
}

.radio-group label {
    font-weight: normal;
    margin-bottom: 0;
    cursor: pointer;
    padding: 8px 12px;
    border-radius: var(--border-radius-sm);
    transition: all var(--transition-speed);
}

.radio-group label:hover {
    background-color: var(--border-color);
}

.radio-group input[type="radio"]:checked + label {
    background-color: var(--primary-color);
    color: white;
}

select {
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    background-color: var(--background-color);
    color: var(--text-color);
    min-width: 150px;
    transition: border-color var(--transition-speed);
}

select:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 2px var(--primary-light-transparent);
}

#end-date-container {
    margin-top: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
}

#end-date-container label {
    margin-bottom: 0;
}

#end-date-container input[type="date"] {
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    background-color: var(--background-color);
    color: var(--text-color);
    transition: border-color var(--transition-speed);
}

#end-date-container input[type="date"]:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 2px var(--primary-light-transparent);
}

.form-actions {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-top: 30px;
}

.primary-button {
    padding: 12px 24px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all var(--transition-speed);
    box-shadow: var(--shadow-sm);
}

.secondary-button {
    padding: 12px 24px;
    background-color: var(--background-color);
    color: var(--text-color);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: all var(--transition-speed);
}

.primary-button:hover {
    background-color: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.primary-button:active {
    transform: translateY(0);
}

.secondary-button:hover {
    background-color: var(--border-color);
    border-color: var(--text-color-light);
}

#loading-indicator {
    display: flex;
    align-items: center;
    gap: 12px;
}

.spinner {
    width: 22px;
    height: 22px;
    border: 3px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s ease-in-out infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

#llm-results {
    margin-top: 35px;
    padding-top: 25px;
    border-top: 1px solid var(--border-color);
}

.result-section {
    margin-bottom: 25px;
}

.result-section h4 {
    margin-bottom: 15px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);
    color: var(--heading-color);
    font-weight: 600;
}

.result-section pre {
    background-color: var(--background-color);
    padding: 18px;
    border-radius: var(--border-radius-sm);
    overflow-x: auto;
    border: 1px solid var(--border-color);
    font-family: 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.5;
}

#error-section pre {
    background-color: #fff0f0;
    border-left: 3px solid #f44336;
}

/* 事件详情样式 */
#event-details, #complete-task-dialog {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 450px;
    background-color: var(--card-color);
    border-radius: var(--border-radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 1000;
    padding: 25px;
    border: 1px solid var(--border-color);
}

.event-details-header, .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--border-color);
}

.event-details-header h3, .dialog-header h3 {
    font-size: 20px;
    font-weight: 600;
    color: var(--heading-color);
    margin: 0;
}

.close-button {
    background: none;
    border: none;
    font-size: 22px;
    color: var(--text-color-light);
    cursor: pointer;
    padding: 5px;
    transition: all var(--transition-speed);
    box-shadow: none;
}

.close-button:hover {
    color: var(--text-color);
    transform: scale(1.1);
    box-shadow: none;
}

#event-details-content, .dialog-content {
    line-height: 1.8;
    color: var(--text-color);
}

.dialog-content .form-group {
    margin-bottom: 20px;
}

.dialog-content label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--text-color);
}

.dialog-content input[type="text"],
.dialog-content textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    font-size: 15px;
    background-color: var(--background-color);
    color: var(--text-color);
    transition: border-color var(--transition-speed);
}

.dialog-content input[type="text"]:focus,
.dialog-content textarea:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 2px var(--primary-light-transparent);
}

.dialog-content textarea {
    resize: vertical;
    min-height: 80px;
}

.dialog-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 25px;
}

.dialog-buttons button {
    padding: 10px 18px;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    font-size: 15px;
    transition: all var(--transition-speed);
}

.dialog-buttons .primary-button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
}

.dialog-buttons .secondary-button {
    background-color: var(--background-color);
    color: var(--text-color);
    border: 1px solid var(--border-color);
}

.dialog-buttons .primary-button:hover {
    background-color: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.dialog-buttons .primary-button:active {
    transform: translateY(0);
}

.dialog-buttons .secondary-button:hover {
    background-color: var(--border-color);
    border-color: var(--text-color-light);
}

.hidden {
    display: none !important;
}

/* 媒体查询 - 响应式设计 */
@media (max-width: 768px) {
    .main-content {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
        margin-bottom: 25px;
    }
    
    .section-button {
        padding: 12px;
        font-size: 15px;
    }
    
    .sidebar-menu {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
        padding: 12px 0 8px 0;
    }
    
    .sidebar-button {
        width: auto;
        font-size: 14px;
        padding: 10px 14px;
    }
    
    .content-area {
        padding: 20px;
    }
    
    #month-grid {
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
    }
    
    .day-cell {
        min-height: 80px;
        padding: 5px;
    }
    
    #week-grid {
        overflow-x: auto;
    }
    
    #event-details, #complete-task-dialog {
        width: 90%;
        max-width: 450px;
        padding: 20px;
    }
    
    .view-controls {
        flex-wrap: wrap;
    }
    
    .view-controls button {
        font-size: 14px;
        padding: 8px 12px;
    }
    
    .date-controls {
        flex-wrap: wrap;
    }
}

@media (max-width: 480px) {
    .container {
        padding: 10px;
    }
    
    header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    
    .date-controls {
        width: 100%;
        justify-content: space-between;
    }
    
    .navigation-controls {
        width: 100%;
        justify-content: space-between;
    }
    
    .sidebar-section {
        margin-bottom: 10px;
    }
    
    .section-button {
        font-size: 14px;
        padding: 8px 10px;
    }
    
    .sidebar-button {
        font-size: 12px;
        padding: 6px 8px;
        margin: 2px;
    }
    
    .sidebar-menu {
        padding: 8px 0 5px 0;
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

/* 时间选择器样式 */
.time-picker-container {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 5px;
}

.time-picker-group {
    flex: 1;
}

.time-picker-group label {
    display: block;
    margin-bottom: 5px;
    font-size: 14px;
    color: #555;
}

.time-picker-separator {
    margin: 0 5px;
    padding-top: 20px;
    color: #666;
}

input[type="time"] {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    color: #333;
}

input[type="time"]:focus {
    border-color: #4CAF50;
    outline: none;
    box-shadow: 0 0 3px rgba(76, 175, 80, 0.3);
}

.dialog-content .form-group {
    margin-bottom: 15px;
}

.dialog-content label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #333;
}

.dialog-content input[type="text"],
.dialog-content textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.dialog-content textarea {
    resize: vertical;
    min-height: 60px;
}

.dialog-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
}

/* 时间复盘视图样式 */
#time-review-grid {
    padding: 20px;
    background-color: white;
    border-radius: 4px;
    border: 1px solid #ddd;
}

.time-review-header {
    margin-bottom: 20px;
    color: #333;
    font-size: 20px;
    font-weight: bold;
    text-align: center;
}

.time-review-day {
    margin-bottom: 30px;
    border-bottom: 1px solid #eee;
    padding-bottom: 20px;
}

.time-review-day-header {
    margin-bottom: 15px;
    padding: 10px;
    background-color: #f5f5f5;
    border-radius: 4px;
    font-weight: bold;
    color: #333;
    font-size: 16px;
}

.time-review-events {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.time-review-event {
    display: flex;
    flex-direction: column;
    border: 1px solid #ddd;
    border-radius: 4px;
    overflow: hidden;
}

.time-review-event-title {
    padding: 10px;
    background-color: #f9f9f9;
    font-weight: bold;
    border-bottom: 1px solid #ddd;
}

.time-review-event-content {
    display: flex;
    flex-direction: column;
}

.time-review-timeline-container {
    position: relative;
    padding: 40px 10px 60px;
    margin-bottom: 10px;
    background-color: #f9f9f9;
    border-bottom: 1px solid #ddd;
}

.time-review-timeline {
    position: relative;
    height: 60px;
    background-color: #f0f0f0;
    border-radius: 4px;
}

.time-review-hour-marker {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background-color: #ccc;
}

.time-review-hour-label {
    position: absolute;
    bottom: -25px;
    transform: translateX(-50%);
    font-size: 12px;
    color: #666;
    white-space: nowrap;
    min-width: 40px;
    text-align: center;
}

.time-review-time-bar {
    position: absolute;
    height: 20px;
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.planned-time-bar {
    top: 10px;
    background-color: #e8f5e9;
    border: 1px solid #81c784;
    z-index: 2;
}

.actual-time-bar {
    top: 35px;
    background-color: #e3f2fd;
    border: 1px solid #64b5f6;
    z-index: 2;
}

/* 跨天事件的时间条样式 */
.time-review-time-bar.overnight-event {
    background-image: linear-gradient(45deg, rgba(255, 255, 255, 0.3) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, 0.3) 50%, rgba(255, 255, 255, 0.3) 75%, transparent 75%, transparent);
    background-size: 20px 20px;
    animation: overnight-stripe 1s linear infinite;
}

.planned-time-bar.overnight-event {
    background-color: #c8e6c9;
    border: 1px solid #66bb6a;
}

.actual-time-bar.overnight-event {
    background-color: #bbdefb;
    border: 1px solid #42a5f5;
}

@keyframes overnight-stripe {
    0% { background-position: 0 0; }
    100% { background-position: 20px 0; }
}

.time-review-bar-label {
    position: absolute;
    top: -20px;
    left: 0;
    white-space: nowrap;
    font-size: 12px;
    color: #333;
    background-color: rgba(255, 255, 255, 0.8);
    padding: 2px 5px;
    border-radius: 2px;
}

.time-review-diff-info {
    position: absolute;
    bottom: -45px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 13px;
    color: #555;
    padding: 5px;
    background-color: rgba(255, 255, 255, 0.8);
    border-radius: 3px;
}

/* 跨天事件差异信息的样式 */
.time-review-diff-info.overnight-diff {
    background-color: rgba(255, 236, 179, 0.9);
    border-left: 3px solid #ffc107;
    font-weight: 500;
    color: #5d4037;
}

.time-review-event-notes {
    flex: 1;
    padding: 10px;
    background-color: #f5f5f5;
    border-top: 1px solid #ddd;
}

.time-review-notes-section {
    margin-bottom: 10px;
}

.time-review-notes-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
    font-weight: bold;
}

.time-review-notes-value {
    color: #333;
    white-space: pre-line;
    font-size: 14px;
    line-height: 1.4;
}

.time-review-no-notes {
    color: #999;
    font-style: italic;
    text-align: center;
    padding: 20px 0;
}

.time-review-planned-time, 
.time-review-actual-time {
    flex: 1;
    padding: 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.time-review-planned-time {
    background-color: #e8f5e9;
    border-right: 1px solid #ddd;
}

.time-review-actual-time {
    background-color: #e3f2fd;
}

.time-review-time-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}

.time-review-time-value {
    font-weight: bold;
    color: #333;
}

.time-review-empty {
    text-align: center;
    padding: 30px;
    color: #666;
    font-style: italic;
}

/* 遮罩层样式 */
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(3px);
    z-index: 999;
    display: none;
}

.overlay.active {
    display: block;
}

.hidden {
    display: none !important;
}

/* 媒体查询 - 响应式设计 */
@media (max-width: 768px) {
    .main-content {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
        margin-bottom: 25px;
    }
    
    .section-button {
        padding: 12px;
        font-size: 15px;
    }
    
    .sidebar-menu {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
        padding: 12px 0 8px 0;
    }
    
    .sidebar-button {
        width: auto;
        font-size: 14px;
        padding: 10px 14px;
    }
    
    .content-area {
        padding: 20px;
    }
    
    #month-grid {
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
    }
    
    .day-cell {
        min-height: 80px;
        padding: 5px;
    }
    
    #week-grid {
        overflow-x: auto;
    }
    
    #event-details, #complete-task-dialog {
        width: 90%;
        max-width: 450px;
        padding: 20px;
    }
    
    .view-controls {
        flex-wrap: wrap;
    }
    
    .view-controls button {
        font-size: 14px;
        padding: 8px 12px;
    }
    
    .date-controls {
        flex-wrap: wrap;
    }
}

/* 月视图中的事件项悬停效果 */
.day-cell .event-item:hover {
    z-index: 100;
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
    min-height: auto;
    position: relative;
    border-radius: var(--border-radius-sm);
    padding: 4px 25px 4px 5px;
    width: auto;
    word-wrap: break-word;
    overflow: visible;
    margin-right: -10px;
}

/* 禁用功能样式 */
.disabled-feature {
    position: relative;
    opacity: 0.7;
    background-color: #f8f8f8;
    border-radius: var(--border-radius-sm);
    padding: 15px;
    border: 1px dashed #ccc;
    margin-bottom: 20px;
}

.feature-badge {
    position: absolute;
    top: -10px;
    right: 10px;
    background-color: #f0ad4e;
    color: white;
    font-size: 12px;
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 600;
    box-shadow: var(--shadow-sm);
}

.disabled-text {
    color: #999;
}

input[disabled] {
    cursor: not-allowed;
    opacity: 0.6;
}

input[disabled] + label {
    cursor: not-allowed;
}

.overnight-checkbox {
    margin-top: 10px;
    display: flex;
    align-items: center;
}

.overnight-checkbox input[type="checkbox"] {
    margin-right: 8px;
}

.overnight-checkbox label {
    font-size: 14px;
    color: #555;
}
    '''
    
    with open('static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

