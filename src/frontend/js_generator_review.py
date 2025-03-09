"""
时间复盘功能JavaScript生成器模块，负责生成时间复盘相关的JavaScript功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

class JSGeneratorReview:
    """时间复盘功能JavaScript生成器，负责生成时间复盘相关的JavaScript功能"""
    
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
    
    def create_review_js(self):
        """创建时间复盘功能的JavaScript代码"""
        try:
            self.ensure_directories()
            
            js = """// 时间复盘相关功能
// 初始化时间复盘
document.addEventListener('DOMContentLoaded', function() {
    // 时间复盘标签切换
    const tabCompletedEvents = document.getElementById('tab-completed-events');
    const tabTimeAnalysis = document.getElementById('tab-time-analysis');
    const tabProductivity = document.getElementById('tab-productivity');
    
    const timeReviewGrid = document.getElementById('time-review-grid');
    const timeAnalysis = document.getElementById('time-analysis');
    const productivityReport = document.getElementById('productivity-report');
    
    tabCompletedEvents.addEventListener('click', function() {
        tabCompletedEvents.classList.add('active');
        tabTimeAnalysis.classList.remove('active');
        tabProductivity.classList.remove('active');
        
        timeReviewGrid.style.display = 'flex';
        timeAnalysis.style.display = 'none';
        productivityReport.style.display = 'none';
        
        loadTimeReview();
    });
    
    tabTimeAnalysis.addEventListener('click', function() {
        tabCompletedEvents.classList.remove('active');
        tabTimeAnalysis.classList.add('active');
        tabProductivity.classList.remove('active');
        
        timeReviewGrid.style.display = 'none';
        timeAnalysis.style.display = 'block';
        productivityReport.style.display = 'none';
        
        loadTimeAnalysis();
    });
    
    tabProductivity.addEventListener('click', function() {
        tabCompletedEvents.classList.remove('active');
        tabTimeAnalysis.classList.remove('active');
        tabProductivity.classList.add('active');
        
        timeReviewGrid.style.display = 'none';
        timeAnalysis.style.display = 'none';
        productivityReport.style.display = 'block';
        
        loadProductivityReport();
    });
    
    // 视图切换时加载时间复盘
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const view = this.getAttribute('data-view');
            if (view === 'time-review') {
                loadTimeReview();
            }
        });
    });
});

// 加载时间分析
function loadTimeAnalysis() {
    // 获取日期范围
    const dateFrom = document.getElementById('review-date-from').value;
    const dateTo = document.getElementById('review-date-to').value;
    
    // 如果没有提供日期范围，默认显示过去30天
    let fromDate = dateFrom;
    let toDate = dateTo;
    
    if (!fromDate) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        fromDate = formatDate(thirtyDaysAgo);
    }
    
    if (!toDate) {
        toDate = formatDate(new Date());
    }
    
    // 发送API请求获取已完成事件
    fetch(`/api/events/completed?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                document.getElementById('time-analysis').innerHTML = '<p class="no-data">该时间段内没有已完成的任务</p>';
                return;
            }
            
            // 准备图表数据
            const dailyTimeData = prepareDailyTimeData(data);
            const taskTypeData = prepareTaskTypeData(data);
            
            // 渲染图表
            renderDailyTimeChart(dailyTimeData);
            renderTaskTypeChart(taskTypeData);
        })
        .catch(error => {
            console.error('Error loading time analysis data:', error);
            document.getElementById('time-analysis').innerHTML = '<p class="error-message">加载时间分析数据时发生错误</p>';
        });
}

// 准备每日时间分配数据
function prepareDailyTimeData(events) {
    // 按日期分组事件
    const eventsByDate = {};
    
    events.forEach(event => {
        if (!eventsByDate[event.date]) {
            eventsByDate[event.date] = [];
        }
        eventsByDate[event.date].push(event);
    });
    
    // 计算每天的时间分配
    const dates = Object.keys(eventsByDate).sort();
    const taskTime = [];
    const fixedTime = [];
    
    dates.forEach(date => {
        const dayEvents = eventsByDate[date];
        let taskMinutes = 0;
        let fixedMinutes = 0;
        
        dayEvents.forEach(event => {
            // 解析时间范围
            const timeRange = event.actual_time_range || event.time_range;
            const [startTime, endTime] = timeRange.split('-');
            
            // 计算开始和结束分钟数
            const [startHour, startMinute] = startTime.split(':').map(Number);
            const [endHour, endMinute] = endTime.split(':').map(Number);
            
            const startMinutes = startHour * 60 + startMinute;
            const endMinutes = endHour * 60 + endMinute;
            const durationMinutes = endMinutes - startMinutes;
            
            if (event.event_type === '任务事项') {
                taskMinutes += durationMinutes;
            } else {
                fixedMinutes += durationMinutes;
            }
        });
        
        // 转换为小时
        taskTime.push(Math.round(taskMinutes / 60 * 10) / 10);
        fixedTime.push(Math.round(fixedMinutes / 60 * 10) / 10);
    });
    
    return {
        dates: dates,
        taskTime: taskTime,
        fixedTime: fixedTime
    };
}

// 准备任务类型分布数据
function prepareTaskTypeData(events) {
    // 统计不同类型的事件数量
    const taskCount = events.filter(event => event.event_type === '任务事项').length;
    const fixedCount = events.filter(event => event.event_type === '固定日程').length;
    
    return {
        labels: ['任务事项', '固定日程'],
        data: [taskCount, fixedCount]
    };
}

// 渲染每日时间分配图表
function renderDailyTimeChart(data) {
    const ctx = document.getElementById('daily-time-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: '任务事项',
                    data: data.taskTime,
                    backgroundColor: 'rgba(107, 140, 174, 0.7)',
                    borderColor: 'rgba(107, 140, 174, 1)',
                    borderWidth: 1
                },
                {
                    label: '固定日程',
                    data: data.fixedTime,
                    backgroundColor: 'rgba(255, 107, 107, 0.7)',
                    borderColor: 'rgba(255, 107, 107, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: '小时'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '每日时间分配'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw} 小时`;
                        }
                    }
                }
            }
        }
    });
}

// 渲染任务类型分布图表
function renderTaskTypeChart(data) {
    const ctx = document.getElementById('task-type-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [
                {
                    data: data.data,
                    backgroundColor: [
                        'rgba(107, 140, 174, 0.7)',
                        'rgba(255, 107, 107, 0.7)'
                    ],
                    borderColor: [
                        'rgba(107, 140, 174, 1)',
                        'rgba(255, 107, 107, 1)'
                    ],
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '任务类型分布'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 加载生产力报告
function loadProductivityReport() {
    // 获取日期范围
    const dateFrom = document.getElementById('review-date-from').value;
    const dateTo = document.getElementById('review-date-to').value;
    
    // 如果没有提供日期范围，默认显示过去30天
    let fromDate = dateFrom;
    let toDate = dateTo;
    
    if (!fromDate) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        fromDate = formatDate(thirtyDaysAgo);
    }
    
    if (!toDate) {
        toDate = formatDate(new Date());
    }
    
    // 发送API请求获取任务历史
    fetch(`/api/task-history?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                document.getElementById('productivity-report').innerHTML = '<p class="no-data">该时间段内没有任务历史记录</p>';
                return;
            }
            
            // 计算生产力统计数据
            const stats = calculateProductivityStats(data);
            
            // 更新统计卡片
            document.getElementById('completion-rate').textContent = `${stats.completionRate}%`;
            document.getElementById('on-time-rate').textContent = `${stats.onTimeRate}%`;
            document.getElementById('focus-time').textContent = `${stats.focusTime}小时`;
            
            // 渲染生产力趋势图表
            renderProductivityTrendChart(stats.trendData);
        })
        .catch(error => {
            console.error('Error loading productivity report data:', error);
            document.getElementById('productivity-report').innerHTML = '<p class="error-message">加载生产力报告数据时发生错误</p>';
        });
}

// 计算生产力统计数据
function calculateProductivityStats(tasks) {
    // 计算完成率
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.completion_notes).length;
    const completionRate = Math.round((completedTasks / totalTasks) * 100);
    
    // 计算准时率
    let onTimeCount = 0;
    tasks.forEach(task => {
        if (task.actual_time_range && task.time_range) {
            const [actualStartTime, actualEndTime] = task.actual_time_range.split('-');
            const [plannedStartTime, plannedEndTime] = task.time_range.split('-');
            
            // 简单判断：如果实际结束时间不晚于计划结束时间，则视为准时
            if (actualEndTime <= plannedEndTime) {
                onTimeCount++;
            }
        }
    });
    const onTimeRate = Math.round((onTimeCount / totalTasks) * 100);
    
    // 计算专注时间
    let totalFocusMinutes = 0;
    tasks.forEach(task => {
        if (task.actual_time_range) {
            const [startTime, endTime] = task.actual_time_range.split('-');
            
            // 计算开始和结束分钟数
            const [startHour, startMinute] = startTime.split(':').map(Number);
            const [endHour, endMinute] = endTime.split(':').map(Number);
            
            const startMinutes = startHour * 60 + startMinute;
            const endMinutes = endHour * 60 + endMinute;
            const durationMinutes = endMinutes - startMinutes;
            
            totalFocusMinutes += durationMinutes;
        }
    });
    const focusTime = Math.round(totalFocusMinutes / 60 * 10) / 10;
    
    // 准备趋势数据
    const trendData = prepareProductivityTrendData(tasks);
    
    return {
        completionRate,
        onTimeRate,
        focusTime,
        trendData
    };
}

// 准备生产力趋势数据
function prepareProductivityTrendData(tasks) {
    // 按日期分组任务
    const tasksByDate = {};
    
    tasks.forEach(task => {
        const completionDate = new Date(task.completion_date);
        const dateStr = formatDate(completionDate);
        
        if (!tasksByDate[dateStr]) {
            tasksByDate[dateStr] = [];
        }
        tasksByDate[dateStr].push(task);
    });
    
    // 计算每天的完成率和专注时间
    const dates = Object.keys(tasksByDate).sort();
    const completionRates = [];
    const focusTimes = [];
    
    dates.forEach(date => {
        const dayTasks = tasksByDate[date];
        const totalTasks = dayTasks.length;
        const completedTasks = dayTasks.filter(task => task.completion_notes).length;
        const completionRate = Math.round((completedTasks / totalTasks) * 100);
        
        let totalFocusMinutes = 0;
        dayTasks.forEach(task => {
            if (task.actual_time_range) {
                const [startTime, endTime] = task.actual_time_range.split('-');
                
                // 计算开始和结束分钟数
                const [startHour, startMinute] = startTime.split(':').map(Number);
                const [endHour, endMinute] = endTime.split(':').map(Number);
                
                const startMinutes = startHour * 60 + startMinute;
                const endMinutes = endHour * 60 + endMinute;
                const durationMinutes = endMinutes - startMinutes;
                
                totalFocusMinutes += durationMinutes;
            }
        });
        const focusTime = Math.round(totalFocusMinutes / 60 * 10) / 10;
        
        completionRates.push(completionRate);
        focusTimes.push(focusTime);
    });
    
    return {
        dates,
        completionRates,
        focusTimes
    };
}

// 渲染生产力趋势图表
function renderProductivityTrendChart(data) {
    const ctx = document.getElementById('productivity-trend-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: '完成率 (%)',
                    data: data.completionRates,
                    borderColor: 'rgba(74, 111, 165, 1)',
                    backgroundColor: 'rgba(74, 111, 165, 0.1)',
                    yAxisID: 'y',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '专注时间 (小时)',
                    data: data.focusTimes,
                    borderColor: 'rgba(255, 107, 107, 1)',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    yAxisID: 'y1',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '完成率 (%)'
                    },
                    min: 0,
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '专注时间 (小时)'
                    },
                    min: 0,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '生产力趋势'
                }
            }
        }
    });
}

// 标记事件完成
function markEventCompleted(eventId) {
    // 获取实际完成时间和备注
    const actualTimeRange = prompt('请输入实际完成时间（格式：HH:MM-HH:MM）：');
    if (!actualTimeRange) return;
    
    const completionNotes = prompt('请输入完成备注：');
    const reflectionNotes = prompt('请输入反思笔记：');
    
    // 发送API请求标记事件完成
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
        if (data.status === 'success') {
            alert('事件已标记为完成！');
            closeEventModal();
            
            // 根据当前视图刷新页面
            const currentView = document.querySelector('nav a.active').getAttribute('data-view');
            if (currentView === 'week') {
                renderWeekTimeline();
            } else if (currentView === 'day') {
                renderDayView();
            } else if (currentView === 'time-review') {
                loadTimeReview();
            }
        } else {
            alert('标记事件完成时出错：' + data.message);
        }
    })
    .catch(error => {
        console.error('Error marking event as completed:', error);
        alert('标记事件完成时发生错误');
    });
}

// 删除已完成事件
function deleteCompletedTask(taskId) {
    if (!confirm('确定要删除这条完成记录吗？')) {
        return;
    }
    
    // 发送API请求删除已完成事件
    fetch(`/api/events/${taskId}/completed`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('完成记录已删除！');
            loadTimeReview();
        } else {
            alert('删除完成记录时出错：' + data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting completed task:', error);
        alert('删除完成记录时发生错误');
    });
}

// 显示事件详情
function showEventDetails(event) {
    const modal = document.getElementById('event-modal');
    const title = document.getElementById('event-modal-title');
    const content = document.getElementById('event-modal-content');
    const actions = document.getElementById('event-modal-actions');
    
    title.textContent = event.title;
    
    let contentHtml = `
        <div class="event-info">
            <p><strong>日期：</strong>${event.date}</p>
            <p><strong>时间：</strong>${event.time_range}</p>
            <p><strong>类型：</strong>${event.event_type}</p>
    `;
    
    if (event.deadline) {
        contentHtml += `<p><strong>截止日期：</strong>${event.deadline}</p>`;
    }
    
    if (event.importance) {
        contentHtml += `<p><strong>重要程度：</strong>${event.importance}</p>`;
    }
    
    if (event.actual_time_range) {
        contentHtml += `<p><strong>实际用时：</strong>${event.actual_time_range}</p>`;
    }
    
    if (event.completion_notes) {
        contentHtml += `<p><strong>完成备注：</strong>${event.completion_notes}</p>`;
    }
    
    if (event.reflection_notes) {
        contentHtml += `<p><strong>反思笔记：</strong>${event.reflection_notes}</p>`;
    }
    
    content.innerHTML = contentHtml;
    
    // 添加操作按钮
    let actionsHtml = '';
    
    if (!event.is_completed) {
        actionsHtml += `
            <button class="btn btn-primary" onclick="markEventCompleted(${event.id})">
                标记完成
            </button>
        `;
    }
    
    if (event.can_delete) {
        actionsHtml += `
            <button class="btn btn-danger" onclick="deleteCompletedTask(${event.id})">
                删除
            </button>
        `;
    }
    
    actionsHtml += `
        <button class="btn btn-secondary" onclick="closeEventModal()">
            关闭
        </button>
    `;
    
    actions.innerHTML = actionsHtml;
    
    modal.style.display = 'flex';
}

// 关闭事件详情模态框
function closeEventModal() {
    const modal = document.getElementById('event-modal');
    modal.style.display = 'none';
}

// 加载时间复盘
function loadTimeReview() {
    // 获取日期范围
    const dateFrom = document.getElementById('review-date-from').value;
    const dateTo = document.getElementById('review-date-to').value;
    
    // 如果没有提供日期范围，默认显示过去30天
    let fromDate = dateFrom;
    let toDate = dateTo;
    
    if (!fromDate) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        fromDate = formatDate(thirtyDaysAgo);
    }
    
    if (!toDate) {
        toDate = formatDate(new Date());
    }
    
    // 发送API请求获取已完成事件
    fetch(`/api/events/completed?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(events => {
            const timeReviewGrid = document.getElementById('time-review-grid');
            
            if (events.length === 0) {
                timeReviewGrid.innerHTML = '<p class="no-data">该时间段内没有已完成的事件</p>';
                return;
            }
            
            // 按日期分组事件
            const eventsByDate = {};
            events.forEach(event => {
                const date = event.date;
                if (!eventsByDate[date]) {
                    eventsByDate[date] = [];
                }
                eventsByDate[date].push(event);
            });
            
            // 按日期排序（从新到旧）
            const sortedDates = Object.keys(eventsByDate).sort().reverse();
            
            // 构建事件列表
            let html = '';
            
            sortedDates.forEach(date => {
                const dayEvents = eventsByDate[date];
                const dateObj = new Date(date);
                const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()];
                
                html += `
                    <div class="day-group">
                        <div class="day-header">
                            <h3>${date} ${weekday}</h3>
                        </div>
                        <div class="events-list">
                `;
                
                dayEvents.forEach(event => {
                    html += `
                        <div class="event-card ${event.event_type === '任务事项' ? 'task' : 'fixed'} completed"
                             onclick="showEventDetails(${JSON.stringify(event).replace(/"/g, '&quot;')})">
                            <div class="event-header">
                                <h4>${event.title}</h4>
                                <span class="event-type">${event.event_type}</span>
                            </div>
                            <div class="event-body">
                                <p><strong>计划时间：</strong>${event.time_range}</p>
                                ${event.actual_time_range ? `<p><strong>实际用时：</strong>${event.actual_time_range}</p>` : ''}
                                ${event.completion_notes ? `<p><strong>完成备注：</strong>${event.completion_notes}</p>` : ''}
                                ${event.reflection_notes ? `<p><strong>反思笔记：</strong>${event.reflection_notes}</p>` : ''}
                            </div>
                            <div class="event-footer">
                                <button class="btn btn-danger" onclick="event.stopPropagation(); deleteCompletedTask(${event.id})">
                                    删除
                                </button>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            });
            
            timeReviewGrid.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading completed events:', error);
            timeReviewGrid.innerHTML = '<p class="error-message">加载已完成事件时发生错误</p>';
        });
}

// 加载时间分析
function loadTimeAnalysis() {
    // 获取日期范围
    const dateFrom = document.getElementById('review-date-from').value;
    const dateTo = document.getElementById('review-date-to').value;
    
    // 如果没有提供日期范围，默认显示过去30天
    let fromDate = dateFrom;
    let toDate = dateTo;
    
    if (!fromDate) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        fromDate = formatDate(thirtyDaysAgo);
    }
    
    if (!toDate) {
        toDate = formatDate(new Date());
    }
    
    // 发送API请求获取已完成事件
    fetch(`/api/events/completed?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                document.getElementById('time-analysis').innerHTML = '<p class="no-data">该时间段内没有已完成的任务</p>';
                return;
            }
            
            // 准备图表数据
            const dailyTimeData = prepareDailyTimeData(data);
            const taskTypeData = prepareTaskTypeData(data);
            
            // 渲染图表
            renderDailyTimeChart(dailyTimeData);
            renderTaskTypeChart(taskTypeData);
        })
        .catch(error => {
            console.error('Error loading time analysis data:', error);
            document.getElementById('time-analysis').innerHTML = '<p class="error-message">加载时间分析数据时发生错误</p>';
        });
}

// 准备每日时间分配数据
function prepareDailyTimeData(events) {
    // 按日期分组事件
    const eventsByDate = {};
    
    events.forEach(event => {
        if (!eventsByDate[event.date]) {
            eventsByDate[event.date] = [];
        }
        eventsByDate[event.date].push(event);
    });
    
    // 计算每天的时间分配
    const dates = Object.keys(eventsByDate).sort();
    const taskTime = [];
    const fixedTime = [];
    
    dates.forEach(date => {
        const dayEvents = eventsByDate[date];
        let taskMinutes = 0;
        let fixedMinutes = 0;
        
        dayEvents.forEach(event => {
            // 解析时间范围
            const timeRange = event.actual_time_range || event.time_range;
            const [startTime, endTime] = timeRange.split('-');
            
            // 计算开始和结束分钟数
            const [startHour, startMinute] = startTime.split(':').map(Number);
            const [endHour, endMinute] = endTime.split(':').map(Number);
            
            const startMinutes = startHour * 60 + startMinute;
            const endMinutes = endHour * 60 + endMinute;
            const durationMinutes = endMinutes - startMinutes;
            
            if (event.event_type === '任务事项') {
                taskMinutes += durationMinutes;
            } else {
                fixedMinutes += durationMinutes;
            }
        });
        
        // 转换为小时
        taskTime.push(Math.round(taskMinutes / 60 * 10) / 10);
        fixedTime.push(Math.round(fixedMinutes / 60 * 10) / 10);
    });
    
    return {
        dates: dates,
        taskTime: taskTime,
        fixedTime: fixedTime
    };
}

// 准备任务类型分布数据
function prepareTaskTypeData(events) {
    // 统计不同类型的事件数量
    const taskCount = events.filter(event => event.event_type === '任务事项').length;
    const fixedCount = events.filter(event => event.event_type === '固定日程').length;
    
    return {
        labels: ['任务事项', '固定日程'],
        data: [taskCount, fixedCount]
    };
}

// 渲染每日时间分配图表
function renderDailyTimeChart(data) {
    const ctx = document.getElementById('daily-time-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: '任务事项',
                    data: data.taskTime,
                    backgroundColor: 'rgba(107, 140, 174, 0.7)',
                    borderColor: 'rgba(107, 140, 174, 1)',
                    borderWidth: 1
                },
                {
                    label: '固定日程',
                    data: data.fixedTime,
                    backgroundColor: 'rgba(255, 107, 107, 0.7)',
                    borderColor: 'rgba(255, 107, 107, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: '小时'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '每日时间分配'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw} 小时`;
                        }
                    }
                }
            }
        }
    });
}

// 渲染任务类型分布图表
function renderTaskTypeChart(data) {
    const ctx = document.getElementById('task-type-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [
                {
                    data: data.data,
                    backgroundColor: [
                        'rgba(107, 140, 174, 0.7)',
                        'rgba(255, 107, 107, 0.7)'
                    ],
                    borderColor: [
                        'rgba(107, 140, 174, 1)',
                        'rgba(255, 107, 107, 1)'
                    ],
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '任务类型分布'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 加载生产力报告
function loadProductivityReport() {
    // 获取日期范围
    const dateFrom = document.getElementById('review-date-from').value;
    const dateTo = document.getElementById('review-date-to').value;
    
    // 如果没有提供日期范围，默认显示过去30天
    let fromDate = dateFrom;
    let toDate = dateTo;
    
    if (!fromDate) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        fromDate = formatDate(thirtyDaysAgo);
    }
    
    if (!toDate) {
        toDate = formatDate(new Date());
    }
    
    // 发送API请求获取任务历史
    fetch(`/api/task-history?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                document.getElementById('productivity-report').innerHTML = '<p class="no-data">该时间段内没有任务历史记录</p>';
                return;
            }
            
            // 计算生产力统计数据
            const stats = calculateProductivityStats(data);
            
            // 更新统计卡片
            document.getElementById('completion-rate').textContent = `${stats.completionRate}%`;
            document.getElementById('on-time-rate').textContent = `${stats.onTimeRate}%`;
            document.getElementById('focus-time').textContent = `${stats.focusTime}小时`;
            
            // 渲染生产力趋势图表
            renderProductivityTrendChart(stats.trendData);
        })
        .catch(error => {
            console.error('Error loading productivity report data:', error);
            document.getElementById('productivity-report').innerHTML = '<p class="error-message">加载生产力报告数据时发生错误</p>';
        });
}

// 计算生产力统计数据
function calculateProductivityStats(tasks) {
    // 计算完成率
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.completion_notes).length;
    const completionRate = Math.round((completedTasks / totalTasks) * 100);
    
    // 计算准时率
    let onTimeCount = 0;
    tasks.forEach(task => {
        if (task.actual_time_range && task.time_range) {
            const [actualStartTime, actualEndTime] = task.actual_time_range.split('-');
            const [plannedStartTime, plannedEndTime] = task.time_range.split('-');
            
            // 简单判断：如果实际结束时间不晚于计划结束时间，则视为准时
            if (actualEndTime <= plannedEndTime) {
                onTimeCount++;
            }
        }
    });
    const onTimeRate = Math.round((onTimeCount / totalTasks) * 100);
    
    // 计算专注时间
    let totalFocusMinutes = 0;
    tasks.forEach(task => {
        if (task.actual_time_range) {
            const [startTime, endTime] = task.actual_time_range.split('-');
            
            // 计算开始和结束分钟数
            const [startHour, startMinute] = startTime.split(':').map(Number);
            const [endHour, endMinute] = endTime.split(':').map(Number);
            
            const startMinutes = startHour * 60 + startMinute;
            const endMinutes = endHour * 60 + endMinute;
            const durationMinutes = endMinutes - startMinutes;
            
            totalFocusMinutes += durationMinutes;
        }
    });
    const focusTime = Math.round(totalFocusMinutes / 60 * 10) / 10;
    
    // 准备趋势数据
    const trendData = prepareProductivityTrendData(tasks);
    
    return {
        completionRate,
        onTimeRate,
        focusTime,
        trendData
    };
}

// 准备生产力趋势数据
function prepareProductivityTrendData(tasks) {
    // 按日期分组任务
    const tasksByDate = {};
    
    tasks.forEach(task => {
        const completionDate = new Date(task.completion_date);
        const dateStr = formatDate(completionDate);
        
        if (!tasksByDate[dateStr]) {
            tasksByDate[dateStr] = [];
        }
        tasksByDate[dateStr].push(task);
    });
    
    // 计算每天的完成率和专注时间
    const dates = Object.keys(tasksByDate).sort();
    const completionRates = [];
    const focusTimes = [];
    
    dates.forEach(date => {
        const dayTasks = tasksByDate[date];
        const totalTasks = dayTasks.length;
        const completedTasks = dayTasks.filter(task => task.completion_notes).length;
        const completionRate = Math.round((completedTasks / totalTasks) * 100);
        
        let totalFocusMinutes = 0;
        dayTasks.forEach(task => {
            if (task.actual_time_range) {
                const [startTime, endTime] = task.actual_time_range.split('-');
                
                // 计算开始和结束分钟数
                const [startHour, startMinute] = startTime.split(':').map(Number);
                const [endHour, endMinute] = endTime.split(':').map(Number);
                
                const startMinutes = startHour * 60 + startMinute;
                const endMinutes = endHour * 60 + endMinute;
                const durationMinutes = endMinutes - startMinutes;
                
                totalFocusMinutes += durationMinutes;
            }
        });
        const focusTime = Math.round(totalFocusMinutes / 60 * 10) / 10;
        
        completionRates.push(completionRate);
        focusTimes.push(focusTime);
    });
    
    return {
        dates,
        completionRates,
        focusTimes
    };
}

// 渲染生产力趋势图表
function renderProductivityTrendChart(data) {
    const ctx = document.getElementById('productivity-trend-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: '完成率 (%)',
                    data: data.completionRates,
                    borderColor: 'rgba(74, 111, 165, 1)',
                    backgroundColor: 'rgba(74, 111, 165, 0.1)',
                    yAxisID: 'y',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '专注时间 (小时)',
                    data: data.focusTimes,
                    borderColor: 'rgba(255, 107, 107, 1)',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    yAxisID: 'y1',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '完成率 (%)'
                    },
                    min: 0,
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '专注时间 (小时)'
                    },
                    min: 0,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '生产力趋势'
                }
            }
        }
    });
}
"""
            
            # 写入文件
            with open(os.path.join(self.js_dir, 'script_review.js'), 'w', encoding='utf-8') as f:
                f.write(js)
                
            return True
        except Exception as e:
            print(f"创建时间复盘功能JavaScript文件时出错: {str(e)}")
            return False
    
    def create_all_review_js(self):
        """创建所有时间复盘功能JavaScript代码"""
        self.ensure_directories()
        result = self.create_review_js()
        
        if result:
            return "时间复盘功能JavaScript代码已创建完成"
        else:
            return "创建时间复盘功能JavaScript代码时出错" 