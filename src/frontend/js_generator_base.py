"""
基本JavaScript生成器模块，负责生成基本的JavaScript功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

class JSGeneratorBase:
    """基本JavaScript生成器，负责生成基本的JavaScript功能"""
    
    def __init__(self, static_dir="static"):
        """
        初始化JavaScript生成器
        
        Args:
            static_dir (str): 静态资源目录路径
        """
        self.static_dir = static_dir
        self.js_dir = os.path.join(static_dir, "js")
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        # 创建JavaScript目录
        if not os.path.exists(self.js_dir):
            os.makedirs(self.js_dir)
    
    def create_base_js(self):
        """创建基本的JavaScript功能"""
        try:
            self.ensure_directories()
            
            js = """// 全局变量
let currentView = 'calendar';
let currentDate = new Date();
let events = [];

// DOM元素
document.addEventListener('DOMContentLoaded', function() {
    // 导航切换
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const view = this.getAttribute('data-view');
            switchView(view);
        });
    });
    
    // 表单提交
    const taskForm = document.getElementById('task-form');
    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitTask();
    });
    
    // 重复规则选择变化
    const recurrenceSelect = document.getElementById('recurrence-select');
    recurrenceSelect.addEventListener('change', function() {
        const endDateGroup = document.querySelector('.end-date-group');
        if (this.value) {
            endDateGroup.style.display = 'block';
        } else {
            endDateGroup.style.display = 'none';
        }
    });
    
    // 日历导航
    document.getElementById('prev-month').addEventListener('click', function() {
        navigateMonth(-1);
    });
    
    document.getElementById('next-month').addEventListener('click', function() {
        navigateMonth(1);
    });
    
    // 列表导航
    document.getElementById('prev-week').addEventListener('click', function() {
        navigateWeek(-1);
    });
    
    document.getElementById('next-week').addEventListener('click', function() {
        navigateWeek(1);
    });
    
    // 时间复盘日期筛选
    document.getElementById('apply-date-filter').addEventListener('click', function() {
        loadTimeReview();
    });
    
    // 关闭模态框
    const closeButtons = document.querySelectorAll('.close-modal');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // 完成任务表单提交
    const completeForm = document.getElementById('complete-form');
    completeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitCompletion();
    });
    
    // 初始化
    loadEvents();
});

// 视图切换
function switchView(view) {
    // 更新导航链接
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-view') === view) {
            link.classList.add('active');
        }
    });
    
    // 隐藏所有视图
    const viewSections = document.querySelectorAll('.view-section');
    viewSections.forEach(section => {
        section.classList.remove('active');
    });
    
    // 显示选中的视图
    const selectedView = document.getElementById(view + '-view');
    if (selectedView) {
        selectedView.classList.add('active');
        currentView = view;
        
        // 根据视图加载数据
        if (view === 'calendar') {
            renderCalendar();
        } else if (view === 'list') {
            renderList();
        } else if (view === 'time-review') {
            loadTimeReview();
        }
    }
}

// 加载事件数据
function loadEvents() {
    // 获取当前月份的第一天和最后一天
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    
    const dateFrom = formatDate(firstDay);
    const dateTo = formatDate(lastDay);
    
    // 显示加载动画
    // ...
    
    // 发送API请求获取事件
    fetch(`/api/events?date_from=${dateFrom}&date_to=${dateTo}`)
        .then(response => response.json())
        .then(data => {
            events = data;
            
            // 根据当前视图渲染数据
            if (currentView === 'calendar') {
                renderCalendar();
            } else if (currentView === 'list') {
                renderList();
            }
            
            // 隐藏加载动画
            // ...
        })
        .catch(error => {
            console.error('Error loading events:', error);
            // 隐藏加载动画
            // ...
        });
}

// 渲染日历视图
function renderCalendar() {
    const calendarGrid = document.getElementById('calendar-grid');
    calendarGrid.innerHTML = '';
    
    // 获取当前月份的第一天
    const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    
    // 获取当前月份的天数
    const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const daysInMonth = lastDay.getDate();
    
    // 获取当前月份第一天是星期几（0-6，0表示星期日）
    const firstDayOfWeek = firstDay.getDay();
    
    // 更新月份标题
    document.getElementById('current-month').textContent = `${currentDate.getFullYear()}年${currentDate.getMonth() + 1}月`;
    
    // 添加星期标题
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    weekdays.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-day-header';
        dayHeader.textContent = day;
        calendarGrid.appendChild(dayHeader);
    });
    
    // 添加上个月的剩余天数
    const prevMonthLastDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate();
    for (let i = 0; i < firstDayOfWeek; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day other-month';
        
        const dayNumber = prevMonthLastDay - firstDayOfWeek + i + 1;
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        dayHeader.innerHTML = `<span class="day-number">${dayNumber}</span>`;
        
        day.appendChild(dayHeader);
        calendarGrid.appendChild(day);
    }
    
    // 添加当前月份的天数
    const today = new Date();
    for (let i = 1; i <= daysInMonth; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day';
        
        // 检查是否是今天
        if (currentDate.getFullYear() === today.getFullYear() && 
            currentDate.getMonth() === today.getMonth() && 
            i === today.getDate()) {
            day.classList.add('today');
        }
        
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        dayHeader.innerHTML = `<span class="day-number">${i}</span>`;
        
        const dayEvents = document.createElement('div');
        dayEvents.className = 'day-events';
        
        // 添加当天的事件
        const dateStr = formatDate(new Date(currentDate.getFullYear(), currentDate.getMonth(), i));
        const dayEventsList = events.filter(event => event.date === dateStr);
        
        dayEventsList.forEach(event => {
            const eventItem = document.createElement('div');
            eventItem.className = `event-item ${event.event_type === '任务事项' ? 'task' : 'fixed'}`;
            if (event.completed) {
                eventItem.classList.add('completed');
            }
            eventItem.textContent = `${event.time_range} ${event.title}`;
            eventItem.setAttribute('data-event-id', event.id);
            
            // 点击事件显示详情
            eventItem.addEventListener('click', function() {
                showEventDetails(event);
            });
            
            dayEvents.appendChild(eventItem);
        });
        
        day.appendChild(dayHeader);
        day.appendChild(dayEvents);
        calendarGrid.appendChild(day);
    }
    
    // 添加下个月的开始天数
    const remainingDays = 42 - (firstDayOfWeek + daysInMonth); // 6行7列 = 42个格子
    for (let i = 1; i <= remainingDays; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day other-month';
        
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        dayHeader.innerHTML = `<span class="day-number">${i}</span>`;
        
        day.appendChild(dayHeader);
        calendarGrid.appendChild(day);
    }
}

// 渲染列表视图
function renderList() {
    const listContainer = document.getElementById('list-container');
    listContainer.innerHTML = '';
    
    // 获取当前周的开始和结束日期
    const weekStart = new Date(currentDate);
    weekStart.setDate(currentDate.getDate() - currentDate.getDay());
    
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    
    // 更新周标题
    const weekNumber = getWeekNumber(currentDate);
    document.getElementById('current-week').textContent = `${currentDate.getFullYear()}年第${weekNumber}周 (${formatDate(weekStart)}-${formatDate(weekEnd)})`;
    
    // 按日期分组事件
    const eventsByDate = {};
    
    // 创建一周的日期范围
    for (let i = 0; i < 7; i++) {
        const date = new Date(weekStart);
        date.setDate(weekStart.getDate() + i);
        const dateStr = formatDate(date);
        eventsByDate[dateStr] = [];
    }
    
    // 将事件分配到对应日期
    events.forEach(event => {
        if (eventsByDate[event.date]) {
            eventsByDate[event.date].push(event);
        }
    });
    
    // 渲染每一天的事件
    Object.keys(eventsByDate).sort().forEach(date => {
        const dayEvents = eventsByDate[date];
        
        // 创建日期组
        const dayGroup = document.createElement('div');
        dayGroup.className = 'day-group';
        
        // 检查是否是今天
        const today = new Date();
        const currentDate = new Date(date);
        if (today.getFullYear() === currentDate.getFullYear() && 
            today.getMonth() === currentDate.getMonth() && 
            today.getDate() === currentDate.getDate()) {
            dayGroup.classList.add('today');
        }
        
        // 创建日期标题
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-group-header';
        
        const dateObj = new Date(date);
        const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()];
        dayHeader.textContent = `${date} ${weekday}`;
        
        dayGroup.appendChild(dayHeader);
        
        // 创建事件列表
        const eventsList = document.createElement('div');
        eventsList.className = 'events-list';
        
        if (dayEvents.length === 0) {
            const noEvents = document.createElement('div');
            noEvents.className = 'no-events';
            noEvents.textContent = '今日无事件';
            eventsList.appendChild(noEvents);
        } else {
            // 按时间排序
            dayEvents.sort((a, b) => {
                return a.time_range.localeCompare(b.time_range);
            });
            
            // 添加事件
            dayEvents.forEach(event => {
                const eventItem = document.createElement('div');
                eventItem.className = 'list-event-item';
                if (event.completed) {
                    eventItem.classList.add('completed');
                }
                
                const eventTime = document.createElement('div');
                eventTime.className = 'event-time';
                eventTime.textContent = event.time_range;
                
                const eventContent = document.createElement('div');
                eventContent.className = 'event-content';
                
                const eventTitle = document.createElement('div');
                eventTitle.className = 'event-title';
                eventTitle.textContent = event.title;
                
                const eventDetails = document.createElement('div');
                eventDetails.className = 'event-details';
                eventDetails.textContent = `类型: ${event.event_type}`;
                if (event.deadline) {
                    eventDetails.textContent += ` | 截止: ${event.deadline}`;
                }
                if (event.importance) {
                    eventDetails.textContent += ` | 重要程度: ${event.importance}`;
                }
                
                eventContent.appendChild(eventTitle);
                eventContent.appendChild(eventDetails);
                
                // 添加操作按钮
                const eventActions = document.createElement('div');
                eventActions.className = 'event-actions';
                
                if (event.event_type === '任务事项' && !event.completed) {
                    const completeBtn = document.createElement('button');
                    completeBtn.className = 'complete-btn';
                    completeBtn.textContent = '完成';
                    completeBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        showCompleteModal(event.id);
                    });
                    eventActions.appendChild(completeBtn);
                }
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'delete-btn';
                deleteBtn.textContent = '删除';
                deleteBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (confirm('确定要删除此事件吗？')) {
                        deleteEvent(event.id);
                    }
                });
                eventActions.appendChild(deleteBtn);
                
                eventContent.appendChild(eventActions);
                
                eventItem.appendChild(eventTime);
                eventItem.appendChild(eventContent);
                
                // 点击事件显示详情
                eventItem.addEventListener('click', function() {
                    showEventDetails(event);
                });
                
                eventsList.appendChild(eventItem);
            });
        }
        
        dayGroup.appendChild(eventsList);
        listContainer.appendChild(dayGroup);
    });
}

// 格式化日期为YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 获取周数
function getWeekNumber(date) {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

// 导航月份
function navigateMonth(direction) {
    currentDate.setMonth(currentDate.getMonth() + direction);
    loadEvents();
}

// 导航周
function navigateWeek(direction) {
    currentDate.setDate(currentDate.getDate() + direction * 7);
    loadEvents();
}

// 显示事件详情
function showEventDetails(event) {
    const modal = document.getElementById('event-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    const modalActions = document.getElementById('modal-actions');
    
    modalTitle.textContent = event.title;
    
    // 构建详情内容
    let content = `
        <p><strong>日期:</strong> ${event.date}</p>
        <p><strong>时间:</strong> ${event.time_range}</p>
        <p><strong>类型:</strong> ${event.event_type}</p>
    `;
    
    if (event.deadline) {
        content += `<p><strong>截止日期:</strong> ${event.deadline}</p>`;
    }
    
    if (event.importance) {
        content += `<p><strong>重要程度:</strong> ${event.importance}</p>`;
    }
    
    if (event.recurrence_rule) {
        const recurrenceText = {
            'daily': '每天',
            'weekly': '每周',
            'weekdays': '工作日',
            'monthly': '每月',
            'yearly': '每年'
        }[event.recurrence_rule] || event.recurrence_rule;
        
        content += `<p><strong>重复规则:</strong> ${recurrenceText}</p>`;
    }
    
    modalContent.innerHTML = content;
    
    // 构建操作按钮
    modalActions.innerHTML = '';
    
    if (event.event_type === '任务事项' && !event.completed) {
        const completeBtn = document.createElement('button');
        completeBtn.className = 'complete-btn';
        completeBtn.textContent = '标记为已完成';
        completeBtn.addEventListener('click', function() {
            closeModal(modal);
            showCompleteModal(event.id);
        });
        modalActions.appendChild(completeBtn);
    }
    
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn';
    deleteBtn.textContent = '删除事件';
    deleteBtn.addEventListener('click', function() {
        if (confirm('确定要删除此事件吗？')) {
            closeModal(modal);
            deleteEvent(event.id);
        }
    });
    modalActions.appendChild(deleteBtn);
    
    // 显示模态框
    modal.style.display = 'flex';
}

// 关闭模态框
function closeModal(modal) {
    modal.style.display = 'none';
}

// 显示完成任务模态框
function showCompleteModal(eventId) {
    const modal = document.getElementById('complete-modal');
    document.getElementById('complete-task-id').value = eventId;
    
    // 重置表单
    document.getElementById('actual-time-range').value = '';
    document.getElementById('completion-notes').value = '';
    document.getElementById('reflection-notes').value = '';
    
    // 显示模态框
    modal.style.display = 'flex';
}

// 提交任务完成
function submitCompletion() {
    const eventId = document.getElementById('complete-task-id').value;
    const actualTimeRange = document.getElementById('actual-time-range').value;
    const completionNotes = document.getElementById('completion-notes').value;
    const reflectionNotes = document.getElementById('reflection-notes').value;
    
    // 发送API请求
    fetch(`/api/events/${eventId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            actual_time_range: actualTimeRange,
            completion_notes: completionNotes,
            reflection_notes: reflectionNotes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 关闭模态框
            closeModal(document.getElementById('complete-modal'));
            
            // 重新加载事件
            loadEvents();
            
            // 显示成功消息
            alert('任务已标记为完成！');
        } else {
            alert(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error completing task:', error);
        alert('标记任务完成时出错，请重试。');
    });
}

// 删除事件
function deleteEvent(eventId) {
    // 发送API请求
    fetch(`/api/events/${eventId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 重新加载事件
            loadEvents();
            
            // 显示成功消息
            alert('事件已删除！');
        } else {
            alert(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error deleting event:', error);
        alert('删除事件时出错，请重试。');
    });
}
"""
            
            # 写入文件
            with open(os.path.join(self.js_dir, 'script_base.js'), 'w', encoding='utf-8') as f:
                f.write(js)
                
            return True
        except Exception as e:
            print(f"创建基本JavaScript文件时出错: {str(e)}")
            return False
    
    def create_all_base_js(self):
        """创建所有基本JavaScript功能"""
        self.ensure_directories()
        result = self.create_base_js()
        
        if result:
            return "基本JavaScript功能已创建完成"
        else:
            return "创建基本JavaScript功能时出错" 