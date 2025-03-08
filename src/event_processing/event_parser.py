"""
事件解析器模块，负责从LLM输出中提取事件
"""

import re
from datetime import datetime, timedelta, date

class EventParser:
    """事件解析器，负责从LLM输出中提取事件"""
    
    def __init__(self):
        """初始化事件解析器"""
        pass
    
    def extract_events(self, llm_output):
        """
        从LLM输出中提取事件
        
        Args:
            llm_output (str): LLM的输出文本
            
        Returns:
            list: 提取的事件列表
        """
        events = []
        
        # 查找事件块
        event_blocks = re.findall(r'事项:.*?(?=事项:|$)', llm_output, re.DOTALL)
        
        if not event_blocks:
            # 尝试使用不同的格式查找
            event_blocks = re.findall(r'事项：.*?(?=事项：|$)', llm_output, re.DOTALL)
            
        for block in event_blocks:
            event = {}
            
            # 提取事项
            title_match = re.search(r'事项:[ \t]*(.*?)[\r\n]', block) or re.search(r'事项：[ \t]*(.*?)[\r\n]', block)
            if title_match:
                event['title'] = title_match.group(1).strip()
            
            # 提取日期
            date_match = re.search(r'日期:[ \t]*(.*?)[\r\n]', block) or re.search(r'日期：[ \t]*(.*?)[\r\n]', block)
            if date_match:
                event['date'] = date_match.group(1).strip()
            
            # 提取时间段
            time_range_match = re.search(r'时间段:[ \t]*(.*?)[\r\n]', block) or re.search(r'时间段：[ \t]*(.*?)[\r\n]', block)
            if time_range_match:
                event['time_range'] = time_range_match.group(1).strip()
            
            # 提取类型
            event_type_match = re.search(r'类型:[ \t]*(.*?)[\r\n]', block) or re.search(r'类型：[ \t]*(.*?)[\r\n]', block)
            if event_type_match:
                event['event_type'] = event_type_match.group(1).strip()
            
            # 提取截止日期
            deadline_match = re.search(r'截止日期:[ \t]*(.*?)[\r\n]', block) or re.search(r'截止日期：[ \t]*(.*?)[\r\n]', block)
            if deadline_match:
                event['deadline'] = deadline_match.group(1).strip()
            
            # 提取重要程度
            importance_match = re.search(r'重要程度:[ \t]*(.*?)[\r\n]', block) or re.search(r'重要程度：[ \t]*(.*?)[\r\n]', block)
            if importance_match:
                try:
                    event['importance'] = int(importance_match.group(1).strip())
                except ValueError:
                    event['importance'] = 3  # 默认中等重要程度
            
            # 提取变动类型
            change_match = re.search(r'变动:[ \t]*(.*?)[\r\n]', block) or re.search(r'变动：[ \t]*(.*?)[\r\n]', block)
            if change_match:
                event['change_type'] = change_match.group(1).strip()
            
            # 检查是否有足够的信息构成一个有效事件
            if 'title' in event and 'date' in event and 'time_range' in event and 'event_type' in event:
                events.append(event)
        
        return events
    
    def parse_time_range(self, time_range):
        """
        解析时间范围字符串
        
        Args:
            time_range (str): 时间范围字符串，格式为"HH:MM-HH:MM"
            
        Returns:
            tuple: (开始时间, 结束时间)，格式为(datetime.time, datetime.time)
        """
        if not time_range:
            return None, None
            
        parts = time_range.split('-')
        if len(parts) != 2:
            return None, None
            
        try:
            start_time_str, end_time_str = parts
            
            # 解析开始时间
            start_hour, start_minute = map(int, start_time_str.strip().split(':'))
            start_time = datetime.strptime(f"{start_hour:02d}:{start_minute:02d}", "%H:%M").time()
            
            # 解析结束时间
            end_hour, end_minute = map(int, end_time_str.strip().split(':'))
            end_time = datetime.strptime(f"{end_hour:02d}:{end_minute:02d}", "%H:%M").time()
            
            return start_time, end_time
        except (ValueError, IndexError):
            return None, None
    
    def generate_occurrences(self, start_date, recurrence_rule, end_date=None):
        """
        根据重复规则生成事件发生日期
        
        Args:
            start_date (str): 开始日期，格式为"YYYY-MM-DD"
            recurrence_rule (str): 重复规则，可以是"daily", "weekly", "weekdays", "monthly", "yearly"
            end_date (str, optional): 结束日期，格式为"YYYY-MM-DD"
            
        Returns:
            list: 事件发生日期列表，格式为["YYYY-MM-DD", ...]
        """
        if not recurrence_rule:
            return [start_date]
            
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
            else:
                # 默认生成未来30天的事件
                end = start + timedelta(days=30)
                
            dates = []
            current = start
            
            while current <= end:
                if recurrence_rule == "daily":
                    dates.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)
                elif recurrence_rule == "weekly":
                    dates.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=7)
                elif recurrence_rule == "weekdays":
                    # 只包括工作日（周一至周五）
                    if current.weekday() < 5:  # 0-4 表示周一至周五
                        dates.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)
                elif recurrence_rule == "monthly":
                    dates.append(current.strftime("%Y-%m-%d"))
                    # 移动到下个月的同一天
                    month = current.month + 1
                    year = current.year
                    if month > 12:
                        month = 1
                        year += 1
                    # 处理月末日期问题（例如1月31日 -> 2月28/29日）
                    day = min(current.day, self._get_days_in_month(year, month))
                    current = date(year, month, day)
                elif recurrence_rule == "yearly":
                    dates.append(current.strftime("%Y-%m-%d"))
                    # 移动到下一年的同一天
                    try:
                        current = date(current.year + 1, current.month, current.day)
                    except ValueError:
                        # 处理闰年问题（2月29日）
                        if current.month == 2 and current.day == 29:
                            current = date(current.year + 1, 3, 1)
                else:
                    # 不支持的重复规则
                    return [start_date]
            
            return dates
        except ValueError:
            return [start_date]
    
    def _get_days_in_month(self, year, month):
        """
        获取指定月份的天数
        
        Args:
            year (int): 年份
            month (int): 月份
            
        Returns:
            int: 天数
        """
        if month == 2:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            else:
                return 28
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            return 31 