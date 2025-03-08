"""
高级JavaScript生成器模块，负责生成高级的JavaScript功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

class JSGeneratorAdvanced:
    """高级JavaScript生成器，负责生成高级的JavaScript功能"""
    
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
    
    def create_advanced_js(self):
        """创建高级的JavaScript功能"""
        try:
            self.ensure_directories()
            
            js = """// 加载时间复盘数据
function loadTimeReview() {
    const timeReviewGrid = document.getElementById('time-review-grid');
    timeReviewGrid.innerHTML = '';
    
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
    
    // 显示加载动画
    timeReviewGrid.innerHTML = '<div class="loading-spinner" style="display: flex; justify-content: center; margin: 50px 0;"><div class="spinner"></div><span>加载中...</span></div>';
    
    // 发送API请求获取已完成事件
    fetch(`/api/events/completed?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            timeReviewGrid.innerHTML = '';
            
            if (data.length === 0) {
                timeReviewGrid.innerHTML = '<p class="no-data">该时间段内没有已完成的任务</p>';
                return;
            }
            
            // 按日期分组事件
            const eventsByDate = {};
            
            data.forEach(event => {
                if (!eventsByDate[event.date]) {
                    eventsByDate[event.date] = [];
                }
                eventsByDate[event.date].push(event);
            });
            
            // 按日期排序（从新到旧）
            const sortedDates = Object.keys(eventsByDate).sort().reverse();
            
            // 渲染每一天的已完成事件
            sortedDates.forEach(date => {
                const dayEvents = eventsByDate[date];
                
                // 创建日期组
                const dayGroup = document.createElement('div');
                dayGroup.className = 'day-group';
                
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
                
                // 按时间排序
                dayEvents.sort((a, b) => {
                    return a.time_range.localeCompare(b.time_range);
                });
                
                // 添加事件
                dayEvents.forEach(event => {
                    const eventItem = document.createElement('div');
                    eventItem.className = 'list-event-item completed';
                    
                    const eventTime = document.createElement('div');
                    eventTime.className = 'event-time';
                    eventTime.textContent = event.time_range;
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'event-content';
                    
                    const titleDiv = document.createElement('div');
                    titleDiv.className = 'event-title';
                    titleDiv.textContent = event.title;
                    
                    const detailsDiv = document.createElement('div');
                    detailsDiv.className = 'event-details';
                    
                    let detailsText = `类型: ${event.event_type}`;
                    if (event.actual_time_range) {
                        detailsText += ` | 实际用时: ${event.actual_time_range}`;
                    }
                    if (event.completion_date) {
                        const completionDate = new Date(event.completion_date);
                        detailsText += ` | 完成于: ${formatDateTime(completionDate)}`;
                    }
                    
                    detailsDiv.textContent = detailsText;
                    
                    contentDiv.appendChild(titleDiv);
                    contentDiv.appendChild(detailsDiv);
                    
                    // 添加完成笔记和反思
                    if (event.completion_notes || event.reflection_notes) {
                        const notesDiv = document.createElement('div');
                        notesDiv.className = 'event-notes';
                        
                        if (event.completion_notes) {
                            const completionNotesDiv = document.createElement('div');
                            completionNotesDiv.className = 'completion-notes';
                            completionNotesDiv.innerHTML = `<strong>完成情况:</strong> ${event.completion_notes}`;
                            notesDiv.appendChild(completionNotesDiv);
                        }
                        
                        if (event.reflection_notes) {
                            const reflectionNotesDiv = document.createElement('div');
                            reflectionNotesDiv.className = 'reflection-notes';
                            reflectionNotesDiv.innerHTML = `<strong>反思与收获:</strong> ${event.reflection_notes}`;
                            notesDiv.appendChild(reflectionNotesDiv);
                        }
                        
                        // 添加删除按钮
                        const actionsDiv = document.createElement('div');
                        actionsDiv.className = 'event-actions';
                        
                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = 'delete-btn';
                        deleteBtn.textContent = '删除记录';
                        deleteBtn.addEventListener('click', function() {
                            if (confirm('确定要删除此完成记录吗？')) {
                                deleteCompletedTask(event.id);
                            }
                        });
                        
                        actionsDiv.appendChild(deleteBtn);
                        notesDiv.appendChild(actionsDiv);
                        
                        contentDiv.appendChild(notesDiv);
                    }
                    
                    eventItem.appendChild(eventTime);
                    eventItem.appendChild(contentDiv);
                    eventsList.appendChild(eventItem);
                });
                
                dayGroup.appendChild(eventsList);
                timeReviewGrid.appendChild(dayGroup);
            });
        })
        .catch(error => {
            console.error('Error loading completed events:', error);
            timeReviewGrid.innerHTML = '<p class="error-message">加载时间复盘数据时发生错误</p>';
        });
}

// 删除已完成任务
function deleteCompletedTask(taskId) {
    // 发送API请求
    fetch(`/api/completed-tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 重新加载时间复盘
            loadTimeReview();
            
            // 显示成功消息
            alert('完成记录已删除！');
        } else {
            alert(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error deleting completed task:', error);
        alert('删除完成记录时出错，请重试。');
    });
}

// 格式化日期时间
function formatDateTime(date) {
    return `${formatDate(date)} ${formatTime(date)}`;
}

// 格式化时间为HH:MM
function formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

// 提交任务
function submitTask() {
    const prompt = document.getElementById('task-prompt').value.trim();
    if (!prompt) {
        alert('请输入任务描述');
        return;
    }
    
    const model = document.getElementById('model-select').value;
    const recurrence = document.getElementById('recurrence-select').value;
    const endDate = document.getElementById('end-date').value;
    
    // 显示加载动画
    document.getElementById('loading-spinner').style.display = 'flex';
    document.getElementById('submit-task').disabled = true;
    
    // 发送API请求
    fetch('/api/llm-query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prompt: prompt,
            model: model,
            recurrence: recurrence,
            end_date: endDate,
            show_summary: true,
            show_changes: true,
            process_events: true
        })
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏加载动画
        document.getElementById('loading-spinner').style.display = 'none';
        document.getElementById('submit-task').disabled = false;
        
        // 显示响应
        showResponse(data);
        
        // 重新加载事件
        loadEvents();
    })
    .catch(error => {
        console.error('Error submitting task:', error);
        
        // 隐藏加载动画
        document.getElementById('loading-spinner').style.display = 'none';
        document.getElementById('submit-task').disabled = false;
        
        // 显示错误消息
        alert('提交任务时出错，请重试。');
    });
}

// 显示响应
function showResponse(data) {
    const responseModal = document.getElementById('response-modal');
    const responseContent = document.getElementById('response-content');
    
    let content = '';
    
    if (data.response) {
        content += `<h3>AI助手回复:</h3><div class="ai-response">${data.response.replace(/\\n/g, '<br>')}</div>`;
    }
    
    if (data.summary) {
        content += `<h3>处理摘要:</h3><div class="summary">${data.summary.replace(/\\n/g, '<br>')}</div>`;
    }
    
    if (data.error) {
        content += `<h3>错误:</h3><div class="error">${data.error}</div>`;
    }
    
    responseContent.innerHTML = content;
    responseModal.style.display = 'flex';
}

// 加载已完成事件与实际时间
function loadCompletedEventsWithActualTime() {
    const timeReviewGrid = document.getElementById('time-review-grid');
    timeReviewGrid.innerHTML = '';
    
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
    
    // 显示加载动画
    timeReviewGrid.innerHTML = '<div class="loading-spinner" style="display: flex; justify-content: center; margin: 50px 0;"><div class="spinner"></div><span>加载中...</span></div>';
    
    // 发送API请求获取任务历史
    fetch(`/api/task-history?date_from=${fromDate}&date_to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            timeReviewGrid.innerHTML = '';
            
            if (data.length === 0) {
                timeReviewGrid.innerHTML = '<p class="no-data">该时间段内没有任务历史记录</p>';
                return;
            }
            
            // 按日期分组事件
            const eventsByDate = {};
            
            data.forEach(event => {
                const completionDate = new Date(event.completion_date);
                const dateStr = formatDate(completionDate);
                
                if (!eventsByDate[dateStr]) {
                    eventsByDate[dateStr] = [];
                }
                eventsByDate[dateStr].push(event);
            });
            
            // 按日期排序（从新到旧）
            const sortedDates = Object.keys(eventsByDate).sort().reverse();
            
            // 渲染每一天的任务历史
            sortedDates.forEach(date => {
                const dayEvents = eventsByDate[date];
                
                // 创建日期组
                const dayGroup = document.createElement('div');
                dayGroup.className = 'day-group';
                
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
                
                // 按时间排序
                dayEvents.sort((a, b) => {
                    const timeA = new Date(a.completion_date).getTime();
                    const timeB = new Date(b.completion_date).getTime();
                    return timeB - timeA;  // 从新到旧
                });
                
                // 添加事件
                dayEvents.forEach(event => {
                    const eventItem = document.createElement('div');
                    eventItem.className = 'list-event-item completed';
                    
                    const eventTime = document.createElement('div');
                    eventTime.className = 'event-time';
                    eventTime.textContent = event.actual_time_range || event.time_range;
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'event-content';
                    
                    const titleDiv = document.createElement('div');
                    titleDiv.className = 'event-title';
                    titleDiv.textContent = event.title;
                    
                    const detailsDiv = document.createElement('div');
                    detailsDiv.className = 'event-details';
                    
                    let detailsText = `原计划: ${event.date} ${event.time_range}`;
                    if (event.actual_time_range && event.actual_time_range !== event.time_range) {
                        detailsText += ` | 实际用时: ${event.actual_time_range}`;
                    }
                    
                    detailsDiv.textContent = detailsText;
                    
                    contentDiv.appendChild(titleDiv);
                    contentDiv.appendChild(detailsDiv);
                    
                    // 添加完成笔记和反思
                    const notesDiv = document.createElement('div');
                    notesDiv.className = 'event-notes';
                    
                    if (event.completion_notes) {
                        const completionNotesDiv = document.createElement('div');
                        completionNotesDiv.className = 'completion-notes';
                        completionNotesDiv.innerHTML = `<strong>完成情况:</strong> ${event.completion_notes}`;
                        notesDiv.appendChild(completionNotesDiv);
                    }
                    
                    if (event.reflection_notes) {
                        const reflectionNotesDiv = document.createElement('div');
                        reflectionNotesDiv.className = 'reflection-notes';
                        reflectionNotesDiv.innerHTML = `<strong>反思与收获:</strong> ${event.reflection_notes}`;
                        notesDiv.appendChild(reflectionNotesDiv);
                    } else {
                        // 如果没有反思，添加反思按钮
                        const addReflectionBtn = document.createElement('button');
                        addReflectionBtn.className = 'add-reflection-btn';
                        addReflectionBtn.textContent = '添加反思';
                        addReflectionBtn.addEventListener('click', function() {
                            const reflection = prompt('请输入你对这个任务的反思与收获:');
                            if (reflection) {
                                addTaskReflection(event.id, reflection);
                            }
                        });
                        notesDiv.appendChild(addReflectionBtn);
                    }
                    
                    contentDiv.appendChild(notesDiv);
                    eventItem.appendChild(eventTime);
                    eventItem.appendChild(contentDiv);
                    eventsList.appendChild(eventItem);
                });
                
                dayGroup.appendChild(eventsList);
                timeReviewGrid.appendChild(dayGroup);
            });
        })
        .catch(error => {
            console.error('Error loading completed events with actual time:', error);
            timeReviewGrid.innerHTML = '<p class="error-message">加载时间复盘数据时发生错误</p>';
        });
}

// 添加任务反思
function addTaskReflection(taskId, reflection) {
    // 发送API请求
    fetch('/api/task-reflection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task_id: taskId,
            reflection_notes: reflection
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 重新加载时间复盘
            loadTimeReview();
            
            // 显示成功消息
            alert('反思已添加！');
        } else {
            alert(`错误: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error adding reflection:', error);
        alert('添加反思时出错，请重试。');
    });
}
"""
            
            # 写入文件
            with open(os.path.join(self.js_dir, 'script_advanced.js'), 'w', encoding='utf-8') as f:
                f.write(js)
                
            return True
        except Exception as e:
            print(f"创建高级JavaScript文件时出错: {str(e)}")
            return False
    
    def create_all_advanced_js(self):
        """创建所有高级JavaScript功能"""
        self.ensure_directories()
        result = self.create_advanced_js()
        
        if result:
            return "高级JavaScript功能已创建完成"
        else:
            return "创建高级JavaScript功能时出错" 