
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
    
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    
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
    // 关闭事件详情弹窗
    document.getElementById('event-details').classList.add('hidden');
    
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
    