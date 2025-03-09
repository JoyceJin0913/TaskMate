"""
时间轴视图JavaScript生成器模块，负责生成周视图和日视图的JavaScript功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

class JSGeneratorTimeline:
    """时间轴视图JavaScript生成器，负责生成周视图和日视图的JavaScript功能"""
    
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
    
    def create_timeline_js(self):
        """创建时间轴视图的JavaScript功能"""
        try:
            self.ensure_directories()
            
            js = """// 周视图相关功能
let weekViewDate = new Date();

// 初始化周视图
document.addEventListener('DOMContentLoaded', function() {
    // 周视图导航
    document.getElementById('prev-week-timeline').addEventListener('click', function() {
        navigateWeekTimeline(-1);
    });
    
    document.getElementById('next-week-timeline').addEventListener('click', function() {
        navigateWeekTimeline(1);
    });
    
    // 日视图导航
    document.getElementById('prev-day').addEventListener('click', function() {
        navigateDayView(-1);
    });
    
    document.getElementById('next-day').addEventListener('click', function() {
        navigateDayView(1);
    });
    
    // 视图切换时渲染相应视图
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const view = this.getAttribute('data-view');
            if (view === 'week') {
                renderWeekTimeline();
            } else if (view === 'day') {
                renderDayView();
            }
        });
    });
});

// 导航周视图
function navigateWeekTimeline(direction) {
    weekViewDate.setDate(weekViewDate.getDate() + direction * 7);
    renderWeekTimeline();
}

// 导航日视图
function navigateDayView(direction) {
    weekViewDate.setDate(weekViewDate.getDate() + direction);
    renderDayView();
}

// 渲染周视图
function renderWeekTimeline() {
    const weekTimeline = document.getElementById('week-timeline');
    weekTimeline.innerHTML = '';
    
    // 获取当前周的开始和结束日期
    const weekStart = new Date(weekViewDate);
    weekStart.setDate(weekViewDate.getDate() - weekViewDate.getDay());
    
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    
    // 更新周标题
    const weekNumber = getWeekNumber(weekViewDate);
    document.getElementById('current-week-timeline').textContent = `${weekViewDate.getFullYear()}年第${weekNumber}周 (${formatDate(weekStart)}-${formatDate(weekEnd)})`;
    
    // 创建时间轴头部
    const timelineHeader = document.createElement('div');
    timelineHeader.className = 'timeline-header';
    
    // 添加时间列
    const timeColumn = document.createElement('div');
    timeColumn.className = 'time-column';
    timelineHeader.appendChild(timeColumn);
    
    // 添加日期列
    for (let i = 0; i < 7; i++) {
        const date = new Date(weekStart);
        date.setDate(weekStart.getDate() + i);
        
        const dayColumn = document.createElement('div');
        dayColumn.className = 'day-column';
        
        // 检查是否是今天
        const today = new Date();
        if (date.getFullYear() === today.getFullYear() && 
            date.getMonth() === today.getMonth() && 
            date.getDate() === today.getDate()) {
            dayColumn.classList.add('today');
        }
        
        const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()];
        dayColumn.textContent = `${formatDate(date)} ${weekday}`;
        
        timelineHeader.appendChild(dayColumn);
    }
    
    weekTimeline.appendChild(timelineHeader);
    
    // 创建时间轴主体
    const timelineBody = document.createElement('div');
    timelineBody.className = 'timeline-body';
    
    // 添加小时列
    const timelineHours = document.createElement('div');
    timelineHours.className = 'timeline-hours';
    
    for (let hour = 0; hour < 24; hour++) {
        const hourDiv = document.createElement('div');
        hourDiv.className = 'timeline-hour';
        hourDiv.textContent = `${hour}:00`;
        timelineHours.appendChild(hourDiv);
    }
    
    timelineBody.appendChild(timelineHours);
    
    // 添加日期列
    const timelineDays = document.createElement('div');
    timelineDays.className = 'timeline-days';
    
    // 获取当前周的事件
    const dateFrom = formatDate(weekStart);
    const dateTo = formatDate(weekEnd);
    
    // 发送API请求获取事件
    fetch(`/api/events?date_from=${dateFrom}&date_to=${dateTo}`)
        .then(response => response.json())
        .then(events => {
            // 为每一天创建一个列
            for (let i = 0; i < 7; i++) {
                const date = new Date(weekStart);
                date.setDate(weekStart.getDate() + i);
                const dateStr = formatDate(date);
                
                const dayColumn = document.createElement('div');
                dayColumn.className = 'timeline-day';
                dayColumn.style.height = `${24 * 60}px`; // 24小时 * 60像素/小时
                
                // 检查是否是今天
                const today = new Date();
                if (date.getFullYear() === today.getFullYear() && 
                    date.getMonth() === today.getMonth() && 
                    date.getDate() === today.getDate()) {
                    dayColumn.classList.add('today');
                    
                    // 添加"现在"指示线
                    const nowLine = document.createElement('div');
                    nowLine.className = 'timeline-now-line';
                    const nowMinutes = today.getHours() * 60 + today.getMinutes();
                    nowLine.style.top = `${nowMinutes}px`;
                    
                    const nowLabel = document.createElement('div');
                    nowLabel.className = 'timeline-now-label';
                    nowLabel.textContent = '现在';
                    nowLabel.style.top = `${nowMinutes - 10}px`;
                    
                    dayColumn.appendChild(nowLine);
                    dayColumn.appendChild(nowLabel);
                }
                
                // 添加当天的事件
                const dayEvents = events.filter(event => event.date === dateStr);
                
                dayEvents.forEach(event => {
                    // 解析时间范围
                    const timeRange = event.time_range;
                    const [startTime, endTime] = timeRange.split('-');
                    
                    // 计算开始和结束分钟数
                    const [startHour, startMinute] = startTime.split(':').map(Number);
                    const [endHour, endMinute] = endTime.split(':').map(Number);
                    
                    const startMinutes = startHour * 60 + startMinute;
                    const endMinutes = endHour * 60 + endMinute;
                    const durationMinutes = endMinutes - startMinutes;
                    
                    // 创建事件元素
                    const eventElement = document.createElement('div');
                    eventElement.className = `timeline-event ${event.event_type === '任务事项' ? 'task' : 'fixed'}`;
                    if (event.completed) {
                        eventElement.classList.add('completed');
                    }
                    
                    eventElement.textContent = `${timeRange} ${event.title}`;
                    eventElement.style.top = `${startMinutes}px`;
                    eventElement.style.height = `${durationMinutes}px`;
                    
                    // 点击事件显示详情
                    eventElement.addEventListener('click', function() {
                        showEventDetails(event);
                    });
                    
                    dayColumn.appendChild(eventElement);
                });
                
                timelineDays.appendChild(dayColumn);
            }
            
            timelineBody.appendChild(timelineDays);
            weekTimeline.appendChild(timelineBody);
        })
        .catch(error => {
            console.error('Error loading events for week timeline:', error);
            timelineDays.innerHTML = '<p class="error-message">加载事件时发生错误</p>';
        });
}

// 渲染日视图
function renderDayView() {
    const dayTimeline = document.getElementById('day-timeline');
    dayTimeline.innerHTML = '';
    
    // 更新日期标题
    const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][weekViewDate.getDay()];
    document.getElementById('current-day').textContent = `${formatDate(weekViewDate)} ${weekday}`;
    
    // 创建时间轴主体
    const timelineBody = document.createElement('div');
    timelineBody.className = 'timeline-body';
    
    // 添加小时列
    const timelineHours = document.createElement('div');
    timelineHours.className = 'timeline-hours';
    
    for (let hour = 0; hour < 24; hour++) {
        const hourDiv = document.createElement('div');
        hourDiv.className = 'timeline-hour';
        hourDiv.textContent = `${hour}:00`;
        timelineHours.appendChild(hourDiv);
    }
    
    timelineBody.appendChild(timelineHours);
    
    // 添加日期列
    const timelineDays = document.createElement('div');
    timelineDays.className = 'timeline-days';
    
    // 获取当天的事件
    const dateStr = formatDate(weekViewDate);
    
    // 发送API请求获取事件
    fetch(`/api/events/${dateStr}`)
        .then(response => response.json())
        .then(events => {
            // 创建日期列
            const dayColumn = document.createElement('div');
            dayColumn.className = 'timeline-day';
            dayColumn.style.height = `${24 * 60}px`; // 24小时 * 60像素/小时
            dayColumn.style.width = '100%'; // 单日视图占满宽度
            
            // 检查是否是今天
            const today = new Date();
            if (weekViewDate.getFullYear() === today.getFullYear() && 
                weekViewDate.getMonth() === today.getMonth() && 
                weekViewDate.getDate() === today.getDate()) {
                dayColumn.classList.add('today');
                
                // 添加"现在"指示线
                const nowLine = document.createElement('div');
                nowLine.className = 'timeline-now-line';
                const nowMinutes = today.getHours() * 60 + today.getMinutes();
                nowLine.style.top = `${nowMinutes}px`;
                
                const nowLabel = document.createElement('div');
                nowLabel.className = 'timeline-now-label';
                nowLabel.textContent = '现在';
                nowLabel.style.top = `${nowMinutes - 10}px`;
                
                dayColumn.appendChild(nowLine);
                dayColumn.appendChild(nowLabel);
            }
            
            // 添加当天的事件
            events.forEach(event => {
                // 解析时间范围
                const timeRange = event.time_range;
                const [startTime, endTime] = timeRange.split('-');
                
                // 计算开始和结束分钟数
                const [startHour, startMinute] = startTime.split(':').map(Number);
                const [endHour, endMinute] = endTime.split(':').map(Number);
                
                const startMinutes = startHour * 60 + startMinute;
                const endMinutes = endHour * 60 + endMinute;
                const durationMinutes = endMinutes - startMinutes;
                
                // 创建事件元素
                const eventElement = document.createElement('div');
                eventElement.className = `timeline-event ${event.event_type === '任务事项' ? 'task' : 'fixed'}`;
                if (event.completed) {
                    eventElement.classList.add('completed');
                }
                
                eventElement.textContent = `${timeRange} ${event.title}`;
                eventElement.style.top = `${startMinutes}px`;
                eventElement.style.height = `${durationMinutes}px`;
                
                // 点击事件显示详情
                eventElement.addEventListener('click', function() {
                    showEventDetails(event);
                });
                
                dayColumn.appendChild(eventElement);
            });
            
            timelineDays.appendChild(dayColumn);
            timelineBody.appendChild(timelineDays);
            dayTimeline.appendChild(timelineBody);
        })
        .catch(error => {
            console.error('Error loading events for day view:', error);
            timelineDays.innerHTML = '<p class="error-message">加载事件时发生错误</p>';
        });
}
"""
            
            # 写入文件
            with open(os.path.join(self.js_dir, 'script_timeline.js'), 'w', encoding='utf-8') as f:
                f.write(js)
                
            return True
        except Exception as e:
            print(f"创建时间轴视图JavaScript文件时出错: {str(e)}")
            return False
    
    def create_all_timeline_js(self):
        """创建所有时间轴视图JavaScript功能"""
        self.ensure_directories()
        result = self.create_timeline_js()
        
        if result:
            return "时间轴视图JavaScript功能已创建完成"
        else:
            return "创建时间轴视图JavaScript功能时出错" 