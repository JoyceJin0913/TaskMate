
// 全局变量
let currentDate = new Date();
let currentView = 'month'; // 当前视图类型：month, week, day, list
let events = [];

// 用于跟踪正在处理的事件ID
let processingEvents = new Set();
// 用于跟踪已处理完成的事件ID，防止重复处理
let completedEvents = new Set();

// 用于存储当前正在完成的事件信息
let currentCompletingEvent = null;

// 用于跟踪加载状态
let isLoadingEvents = false;
let loadEventsRetryCount = 0;
const MAX_RETRY_COUNT = 3;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM加载完成");
    
    // 初始化视图
    initializeView();
    
    // 绑定视图切换按钮
    document.getElementById('month-view').addEventListener('click', function() {
        switchView('month');
    });
    
    document.getElementById('week-view').addEventListener('click', function() {
        switchView('week');
    });
    
    document.getElementById('day-view').addEventListener('click', function() {
        switchView('day');
    });
    
    document.getElementById('list-view').addEventListener('click', function() {
        switchView('list');
    });
    
    document.getElementById('completed-view').addEventListener('click', function() {
        switchView('completed');
    });
    
    document.getElementById('time-review-view').addEventListener('click', function() {
        switchView('time-review');
    });
    
    document.getElementById('llm-view').addEventListener('click', function() {
        switchView('llm');
    });
    
    // 绑定日期导航按钮
    document.getElementById('prev-month').addEventListener('click', previousMonth);
    document.getElementById('next-month').addEventListener('click', nextMonth);
    document.getElementById('prev-week').addEventListener('click', previousWeek);
    document.getElementById('next-week').addEventListener('click', nextWeek);
    document.getElementById('prev-day').addEventListener('click', previousDay);
    document.getElementById('next-day').addEventListener('click', nextDay);
    
    // 绑定事件详情关闭按钮
    document.getElementById('close-details').addEventListener('click', function() {
        document.getElementById('event-details').classList.add('hidden');
    });
    
    // 绑定完成任务对话框事件
    document.getElementById('close-complete-dialog').addEventListener('click', function() {
        document.getElementById('complete-task-dialog').classList.add('hidden');
        // 清空当前正在完成的事件
        currentCompletingEvent = null;
        // 清空表单
        clearCompleteTaskForm();
    });

    document.getElementById('cancel-complete').addEventListener('click', function() {
        document.getElementById('complete-task-dialog').classList.add('hidden');
        // 从处理集合中移除事件ID
        if (currentCompletingEvent) {
            processingEvents.delete(currentCompletingEvent.id);
        }
        // 清空当前正在完成的事件
        currentCompletingEvent = null;
        // 清空表单
        clearCompleteTaskForm();
    });

    document.getElementById('submit-complete').addEventListener('click', submitCompleteTask);

    // 初始化时间选择器
    const now = new Date();
    const currentHour = now.getHours().toString().padStart(2, '0');
    const currentMinute = now.getMinutes().toString().padStart(2, '0');
    const currentTime = `${currentHour}:${currentMinute}`;
    
    // 当用户打开对话框时，默认设置开始时间为当前时间
    document.getElementById('actual-start-time').value = currentTime;
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
    } else if (viewType === 'time-review') {
        renderTimeReviewView();
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
    // 如果当前视图是已完成或时间复盘视图，则不加载事件
    if (currentView === 'completed' || currentView === 'time-review') {
        console.log(`当前视图是 ${currentView}，不需要加载普通事件数据`);
        return;
    }
    
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
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
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
        // 注意：completed 和 time-review 视图在 switchView 函数中处理
    }
    
    // 添加当前时间指示线
    if (currentView === 'week' || currentView === 'day') {
        addCurrentTimeIndicator();
    }
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
        } else if (event.can_complete !== false) {
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
                
                // 调用标记为已完成函数，传递事件ID和日期
                markEventCompleted(event.id, event.date);
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
    
    // 如果是已完成事件，显示实际发生时间范围
    if (isCompleted && event.actual_time_range) {
        details.push(`<strong>实际发生时间:</strong> ${event.actual_time_range}`);
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
            markEventCompleted(event.id, event.date);
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
                // 根据当前视图刷新数据
                if (currentView === 'completed') {
                    renderCompletedView();
                } else if (currentView === 'time-review') {
                    renderTimeReviewView();
                } else {
                    loadEvents();
                }
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

// 清空完成任务表单
function clearCompleteTaskForm() {
    document.getElementById('actual-start-time').value = '';
    document.getElementById('actual-end-time').value = '';
    document.getElementById('completion-notes').value = '';
    document.getElementById('reflection-notes').value = '';
}

// 标记事件为已完成
function markEventCompleted(eventId, eventDate) {
    // 如果该事件正在处理中，则忽略请求
    if (processingEvents.has(eventId)) {
        console.log(`事件 ${eventId} 正在处理中，忽略重复请求`);
        return;
    }

    // 将事件ID添加到处理集合中
    processingEvents.add(eventId);

    // 保存当前正在完成的事件信息
    currentCompletingEvent = {
        id: eventId,
        date: eventDate
    };

    // 设置默认的开始时间为当前时间
    const now = new Date();
    const currentHour = now.getHours().toString().padStart(2, '0');
    const currentMinute = now.getMinutes().toString().padStart(2, '0');
    const currentTime = `${currentHour}:${currentMinute}`;
    
    document.getElementById('actual-start-time').value = currentTime;
    document.getElementById('actual-end-time').value = '';

    // 显示完成任务对话框
    document.getElementById('complete-task-dialog').classList.remove('hidden');
}

// 提交完成任务
function submitCompleteTask() {
    if (!currentCompletingEvent) {
        console.error('没有正在完成的事件');
        return;
    }

    const startTime = document.getElementById('actual-start-time').value;
    const endTime = document.getElementById('actual-end-time').value;
    const completionNotes = document.getElementById('completion-notes').value.trim();
    const reflectionNotes = document.getElementById('reflection-notes').value.trim();

    // 构建时间范围字符串
    let actualTimeRange = '';
    if (startTime && endTime) {
        // 验证开始时间是否小于结束时间
        if (startTime >= endTime) {
            alert('开始时间必须早于结束时间');
            return;
        }
        actualTimeRange = `${startTime}-${endTime}`;
    } else if (startTime || endTime) {
        // 如果只填写了一个时间，提示用户
        alert('请同时填写开始时间和结束时间，或者都不填写');
        return;
    }

    // 注意：我们不再需要 isValidTimeRange 函数，因为我们现在使用 HTML5 的 time 输入类型来验证时间格式

    // 准备请求数据
    const requestData = {
        completion_notes: completionNotes,
        reflection_notes: reflectionNotes,
        event_date: currentCompletingEvent.date,
        actual_time_range: actualTimeRange
    };

    // 发送完成请求
    fetch(`/api/events/${currentCompletingEvent.id}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log(`事件 ${currentCompletingEvent.id} 的完成请求已发送，状态码: ${response.status}`);
        return response.json();
    })
    .then(data => {
        // 从处理集合中移除事件ID
        processingEvents.delete(currentCompletingEvent.id);

        if (data.status === 'success') {
            // 显示成功消息
            showNotification('任务已标记为完成');

            // 将事件ID添加到已完成集合中
            completedEvents.add(currentCompletingEvent.id);

            // 隐藏对话框
            document.getElementById('complete-task-dialog').classList.add('hidden');

            // 清空表单
            clearCompleteTaskForm();

            // 延迟一段时间后重新加载事件，确保后端处理完成
            setTimeout(() => {
                // 根据当前视图刷新数据
                if (currentView === 'completed') {
                    renderCompletedView();
                } else if (currentView === 'time-review') {
                    renderTimeReviewView();
                } else {
                    loadEvents();
                }
            }, 500);
        } else {
            // 处理失败，从已处理完成集合中移除事件ID
            completedEvents.delete(currentCompletingEvent.id);
            alert('标记任务完成失败: ' + data.message);
        }
    })
    .catch(error => {
        // 从处理集合中移除事件ID
        processingEvents.delete(currentCompletingEvent.id);
        // 处理失败，从已处理完成集合中移除事件ID
        completedEvents.delete(currentCompletingEvent.id);

        console.error(`事件 ${currentCompletingEvent.id} 标记完成出错:`, error);
        alert('标记任务完成时发生错误');
    })
    .finally(() => {
        // 清空当前正在完成的事件
        currentCompletingEvent = null;
    });
}

// 验证时间范围格式
function isValidTimeRange(timeRange) {
    if (!timeRange) return true;
    const pattern = /^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
    if (!pattern.test(timeRange)) return false;
    const [start, end] = timeRange.split('-');
    const [startHour, startMin] = start.split(':').map(Number);
    const [endHour, endMin] = end.split(':').map(Number);
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    return startMinutes < endMinutes;
}

// 渲染时间复盘视图
function renderTimeReviewView() {
    const timeReviewGrid = document.getElementById('time-review-grid');
    timeReviewGrid.innerHTML = ''; // 清空内容
    
    // 创建标题
    const header = document.createElement('h2');
    header.className = 'time-review-header';
    header.textContent = '时间复盘';
    timeReviewGrid.appendChild(header);
    
    // 加载已完成事件
    fetch('/api/events/completed')
        .then(response => response.json())
        .then(completedEvents => {
            // 过滤出有实际时间范围的事件
            const eventsWithActualTime = completedEvents.filter(event => event.actual_time_range);
            
            if (eventsWithActualTime.length === 0) {
                const emptyMessage = document.createElement('p');
                emptyMessage.className = 'time-review-empty';
                emptyMessage.textContent = '暂无带有实际时间记录的已完成任务';
                timeReviewGrid.appendChild(emptyMessage);
                return;
            }
            
            // 按日期分组
            const eventsByDate = {};
            eventsWithActualTime.forEach(event => {
                if (!eventsByDate[event.date]) {
                    eventsByDate[event.date] = [];
                }
                eventsByDate[event.date].push(event);
            });
            
            // 按日期排序（降序）
            const sortedDates = Object.keys(eventsByDate).sort().reverse();
            
            // 创建日期分组列表
            sortedDates.forEach(date => {
                const dayGroup = document.createElement('div');
                dayGroup.className = 'time-review-day';
                
                // 创建日期标题
                const dateHeader = document.createElement('div');
                dateHeader.className = 'time-review-day-header';
                const dateObj = new Date(date);
                dateHeader.textContent = `${date} ${['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()]}`;
                dayGroup.appendChild(dateHeader);
                
                // 创建事件列表
                const eventsList = document.createElement('div');
                eventsList.className = 'time-review-events';
                
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
                    const eventItem = document.createElement('div');
                    eventItem.className = 'time-review-event';
                    
                    // 事件标题
                    const titleDiv = document.createElement('div');
                    titleDiv.className = 'time-review-event-title';
                    titleDiv.textContent = event.title;
                    eventItem.appendChild(titleDiv);
                    
                    // 时间对比区域
                    const timesDiv = document.createElement('div');
                    timesDiv.className = 'time-review-event-times';
                    
                    // 计划时间
                    const plannedTimeDiv = document.createElement('div');
                    plannedTimeDiv.className = 'time-review-planned-time';
                    
                    const plannedLabel = document.createElement('div');
                    plannedLabel.className = 'time-review-time-label';
                    plannedLabel.textContent = '计划时间';
                    plannedTimeDiv.appendChild(plannedLabel);
                    
                    const plannedValue = document.createElement('div');
                    plannedValue.className = 'time-review-time-value';
                    plannedValue.textContent = event.time_range;
                    plannedTimeDiv.appendChild(plannedValue);
                    
                    timesDiv.appendChild(plannedTimeDiv);
                    
                    // 实际时间
                    const actualTimeDiv = document.createElement('div');
                    actualTimeDiv.className = 'time-review-actual-time';
                    
                    const actualLabel = document.createElement('div');
                    actualLabel.className = 'time-review-time-label';
                    actualLabel.textContent = '实际时间';
                    actualTimeDiv.appendChild(actualLabel);
                    
                    const actualValue = document.createElement('div');
                    actualValue.className = 'time-review-time-value';
                    actualValue.textContent = event.actual_time_range;
                    actualTimeDiv.appendChild(actualValue);
                    
                    timesDiv.appendChild(actualTimeDiv);
                    
                    eventItem.appendChild(timesDiv);
                    eventsList.appendChild(eventItem);
                });
                
                dayGroup.appendChild(eventsList);
                timeReviewGrid.appendChild(dayGroup);
            });
        })
        .catch(error => {
            console.error('Error loading completed events with actual time:', error);
            const errorMessage = document.createElement('p');
            errorMessage.className = 'error-message';
            errorMessage.textContent = '加载时间复盘数据时发生错误';
            timeReviewGrid.appendChild(errorMessage);
        });
}
    