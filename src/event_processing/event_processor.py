"""
事件处理器模块，负责处理LLM输出并更新数据库
"""

from datetime import datetime
from src.event_processing.event_parser import EventParser
from src.event_processing.event_manager import EventManager

class EventProcessor:
    """事件处理器，负责处理LLM输出并更新数据库"""
    
    def __init__(self, database_type="sqlite", db_path="timetable.db", csv_path="timetable.csv"):
        """
        初始化事件处理器
        
        Args:
            database_type (str): 'sqlite' 或 'csv'
            db_path (str): SQLite数据库路径
            csv_path (str): CSV文件路径
        """
        self.event_parser = EventParser()
        self.event_manager = EventManager(database_type, db_path, csv_path)
    
    def process_events(self, llm_output, handle_conflicts='error'):
        """
        处理LLM输出并更新数据库
        
        Args:
            llm_output (str): LLM的输出文本
            handle_conflicts (str, optional): 处理冲突的方式，可以是'error'（报错）或'force'（强制添加）
            
        Returns:
            str: 处理结果摘要
        """
        # 提取事件
        events = self.event_parser.extract_events(llm_output)
        
        if not events:
            return "未找到有效事件"
        
        # 处理事件
        added = []
        modified = []
        deleted = []
        errors = []
        
        for event in events:
            if 'change_type' in event:
                change_type = event['change_type'].lower()
                
                if change_type == '新增':
                    # 添加事件
                    result = self.event_manager.add_event(event)
                    if result['success']:
                        added.append(f"{event['title']} ({event['date']} {event['time_range']})")
                    else:
                        if handle_conflicts == 'force':
                            # 强制添加
                            result = self.event_manager._add_event_no_check(event)
                            if result['success']:
                                added.append(f"{event['title']} ({event['date']} {event['time_range']}) [强制添加]")
                            else:
                                errors.append(f"{event['title']}: {result['message']}")
                        else:
                            errors.append(f"{event['title']}: {result['message']}")
                
                elif change_type == '更改':
                    # 查找要修改的事件
                    existing_events = self.event_manager.get_all_events()
                    found = False
                    
                    for existing_event in existing_events:
                        if existing_event['title'] == event['title']:
                            # 找到匹配的事件，更新它
                            event['id'] = existing_event['id']
                            result = self.event_manager.modify_event(event)
                            
                            if result['success']:
                                modified.append(f"{event['title']} ({event['date']} {event['time_range']})")
                            else:
                                errors.append(f"{event['title']}: {result['message']}")
                            
                            found = True
                            break
                    
                    if not found:
                        errors.append(f"{event['title']}: 未找到要修改的事件")
                
                elif change_type == '删除':
                    # 查找要删除的事件
                    existing_events = self.event_manager.get_all_events()
                    found = False
                    
                    for existing_event in existing_events:
                        if existing_event['title'] == event['title']:
                            # 找到匹配的事件，删除它
                            result = self.event_manager.delete_event(existing_event['id'])
                            
                            if result['success']:
                                deleted.append(f"{event['title']} ({existing_event['date']} {existing_event['time_range']})")
                            else:
                                errors.append(f"{event['title']}: {result['message']}")
                            
                            found = True
                            break
                    
                    if not found:
                        errors.append(f"{event['title']}: 未找到要删除的事件")
            else:
                # 默认为新增
                result = self.event_manager.add_event(event)
                if result['success']:
                    added.append(f"{event['title']} ({event['date']} {event['time_range']})")
                else:
                    if handle_conflicts == 'force':
                        # 强制添加
                        result = self.event_manager._add_event_no_check(event)
                        if result['success']:
                            added.append(f"{event['title']} ({event['date']} {event['time_range']}) [强制添加]")
                        else:
                            errors.append(f"{event['title']}: {result['message']}")
                    else:
                        errors.append(f"{event['title']}: {result['message']}")
        
        # 生成摘要
        summary = []
        
        if added:
            summary.append(f"已添加 {len(added)} 个事件:")
            for item in added:
                summary.append(f"- {item}")
        
        if modified:
            summary.append(f"\n已修改 {len(modified)} 个事件:")
            for item in modified:
                summary.append(f"- {item}")
        
        if deleted:
            summary.append(f"\n已删除 {len(deleted)} 个事件:")
            for item in deleted:
                summary.append(f"- {item}")
        
        if errors:
            summary.append(f"\n处理过程中出现 {len(errors)} 个错误:")
            for item in errors:
                summary.append(f"- {item}")
        
        if not summary:
            return "未处理任何事件"
        
        return "\n".join(summary)
    
    def process_recurring_events(self, llm_output, recurrence_rule, end_date=None, handle_conflicts='error'):
        """
        处理周期性事件
        
        Args:
            llm_output (str): LLM的输出文本
            recurrence_rule (str): 重复规则，可以是"daily", "weekly", "weekdays", "monthly", "yearly"
            end_date (str, optional): 结束日期，格式为"YYYY-MM-DD"
            handle_conflicts (str, optional): 处理冲突的方式，可以是'error'（报错）或'force'（强制添加）
            
        Returns:
            str: 处理结果摘要
        """
        # 提取事件
        events = self.event_parser.extract_events(llm_output)
        
        if not events:
            return "未找到有效事件"
        
        # 处理事件
        added = []
        modified = []
        deleted = []
        errors = []
        
        for event in events:
            if 'change_type' in event and event['change_type'].lower() == '删除':
                # 查找要删除的事件
                existing_events = self.event_manager.get_all_events()
                found = False
                
                for existing_event in existing_events:
                    if existing_event['title'] == event['title']:
                        # 找到匹配的事件，删除它
                        result = self.event_manager.delete_event(existing_event['id'])
                        
                        if result['success']:
                            deleted.append(f"{event['title']} ({existing_event['date']} {existing_event['time_range']})")
                        else:
                            errors.append(f"{event['title']}: {result['message']}")
                        
                        found = True
                        break
                
                if not found:
                    errors.append(f"{event['title']}: 未找到要删除的事件")
            else:
                # 添加周期性事件
                event['recurrence_rule'] = recurrence_rule
                
                # 生成所有发生日期
                start_date = event['date']
                dates = self.event_parser.generate_occurrences(start_date, recurrence_rule, end_date)
                
                # 添加每个发生日期的事件
                for date in dates:
                    event_copy = event.copy()
                    event_copy['date'] = date
                    
                    result = self.event_manager.add_event(event_copy)
                    if result['success']:
                        added.append(f"{event_copy['title']} ({date} {event_copy['time_range']})")
                    else:
                        if handle_conflicts == 'force':
                            # 强制添加
                            result = self.event_manager._add_event_no_check(event_copy)
                            if result['success']:
                                added.append(f"{event_copy['title']} ({date} {event_copy['time_range']}) [强制添加]")
                            else:
                                errors.append(f"{event_copy['title']} ({date}): {result['message']}")
                        else:
                            errors.append(f"{event_copy['title']} ({date}): {result['message']}")
        
        # 生成摘要
        summary = []
        
        if added:
            summary.append(f"已添加 {len(added)} 个周期性事件:")
            for item in added:
                summary.append(f"- {item}")
        
        if modified:
            summary.append(f"\n已修改 {len(modified)} 个事件:")
            for item in modified:
                summary.append(f"- {item}")
        
        if deleted:
            summary.append(f"\n已删除 {len(deleted)} 个事件:")
            for item in deleted:
                summary.append(f"- {item}")
        
        if errors:
            summary.append(f"\n处理过程中出现 {len(errors)} 个错误:")
            for item in errors:
                summary.append(f"- {item}")
        
        if not summary:
            return "未处理任何事件"
        
        return "\n".join(summary)
    
    def format_events_as_llm_output(self, events=None, include_header=False, date_from=None, date_to=None, limit=None, offset=0):
        """
        将事件格式化为LLM输出格式
        
        Args:
            events (list, optional): 事件列表，如果为None则获取所有事件
            include_header (bool, optional): 是否包含头部信息
            date_from (str, optional): 开始日期，格式为"YYYY-MM-DD"
            date_to (str, optional): 结束日期，格式为"YYYY-MM-DD"
            limit (int, optional): 返回的最大事件数
            offset (int, optional): 偏移量
            
        Returns:
            str: 格式化后的文本
        """
        if events is None:
            events = self.event_manager.get_all_events(date_from, date_to, limit, offset)
        
        if not events:
            return "当前时间表为空"
        
        lines = []
        
        if include_header:
            lines.append("当前时间表：")
        
        for event in events:
            lines.append(f"事项: {event['title']}")
            lines.append(f"日期: {event['date']}")
            lines.append(f"时间段: {event['time_range']}")
            lines.append(f"类型: {event['event_type']}")
            
            if 'deadline' in event and event['deadline']:
                lines.append(f"截止日期：{event['deadline']}")
            
            if 'importance' in event and event['importance']:
                lines.append(f"重要程度：{event['importance']}")
            
            if 'recurrence_rule' in event and event['recurrence_rule']:
                lines.append(f"重复规则：{event['recurrence_rule']}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def format_events_with_changes(self, old_events=None, new_events=None, include_header=False, date_from=None, date_to=None, limit=None, offset=0, show_unchanged=True):
        """
        将事件变更格式化为文本
        
        Args:
            old_events (list, optional): 旧事件列表
            new_events (list, optional): 新事件列表
            include_header (bool, optional): 是否包含头部信息
            date_from (str, optional): 开始日期，格式为"YYYY-MM-DD"
            date_to (str, optional): 结束日期，格式为"YYYY-MM-DD"
            limit (int, optional): 返回的最大事件数
            offset (int, optional): 偏移量
            show_unchanged (bool, optional): 是否显示未变化的事件
            
        Returns:
            str: 格式化后的文本
        """
        if old_events is None:
            old_events = []
        
        if new_events is None:
            new_events = self.event_manager.get_all_events(date_from, date_to, limit, offset)
        
        # 将事件转换为字典，以便于比较
        old_dict = {self._event_key(event): event for event in old_events}
        new_dict = {self._event_key(event): event for event in new_events}
        
        # 找出添加、修改和删除的事件
        added_keys = set(new_dict.keys()) - set(old_dict.keys())
        deleted_keys = set(old_dict.keys()) - set(new_dict.keys())
        common_keys = set(old_dict.keys()) & set(new_dict.keys())
        
        # 找出修改的事件
        modified_keys = set()
        for key in common_keys:
            old_event = old_dict[key]
            new_event = new_dict[key]
            
            # 比较事件的各个字段
            for field in ['title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule']:
                if field in old_event and field in new_event and old_event[field] != new_event[field]:
                    modified_keys.add(key)
                    break
        
        # 未修改的事件
        unchanged_keys = common_keys - modified_keys
        
        # 生成输出
        lines = []
        
        if include_header:
            lines.append("事件变更：")
        
        # 添加的事件
        for key in added_keys:
            event = new_dict[key]
            lines.append(f"事项: {event['title']}")
            lines.append(f"日期: {event['date']}")
            lines.append(f"时间段: {event['time_range']}")
            lines.append(f"类型: {event['event_type']}")
            
            if 'deadline' in event and event['deadline']:
                lines.append(f"截止日期：{event['deadline']}")
            
            if 'importance' in event and event['importance']:
                lines.append(f"重要程度：{event['importance']}")
            
            if 'recurrence_rule' in event and event['recurrence_rule']:
                lines.append(f"重复规则：{event['recurrence_rule']}")
            
            lines.append("变动：新增")
            lines.append("")
        
        # 修改的事件
        for key in modified_keys:
            old_event = old_dict[key]
            new_event = new_dict[key]
            
            lines.append(f"事项: {new_event['title']}")
            lines.append(f"日期: {new_event['date']}")
            lines.append(f"时间段: {new_event['time_range']}")
            lines.append(f"类型: {new_event['event_type']}")
            
            if 'deadline' in new_event and new_event['deadline']:
                lines.append(f"截止日期：{new_event['deadline']}")
            
            if 'importance' in new_event and new_event['importance']:
                lines.append(f"重要程度：{new_event['importance']}")
            
            if 'recurrence_rule' in new_event and new_event['recurrence_rule']:
                lines.append(f"重复规则：{new_event['recurrence_rule']}")
            
            lines.append("变动：更改")
            
            # 显示变更详情
            changes = []
            for field in ['title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule']:
                if field in old_event and field in new_event and old_event[field] != new_event[field]:
                    field_name = {
                        'title': '事项',
                        'date': '日期',
                        'time_range': '时间段',
                        'event_type': '类型',
                        'deadline': '截止日期',
                        'importance': '重要程度',
                        'recurrence_rule': '重复规则'
                    }.get(field, field)
                    
                    changes.append(f"{field_name}: {old_event[field]} -> {new_event[field]}")
            
            if changes:
                lines.append("变更详情：")
                for change in changes:
                    lines.append(f"- {change}")
            
            lines.append("")
        
        # 删除的事件
        for key in deleted_keys:
            event = old_dict[key]
            lines.append(f"事项: {event['title']}")
            lines.append(f"日期: {event['date']}")
            lines.append(f"时间段: {event['time_range']}")
            lines.append(f"类型: {event['event_type']}")
            
            if 'deadline' in event and event['deadline']:
                lines.append(f"截止日期：{event['deadline']}")
            
            if 'importance' in event and event['importance']:
                lines.append(f"重要程度：{event['importance']}")
            
            if 'recurrence_rule' in event and event['recurrence_rule']:
                lines.append(f"重复规则：{event['recurrence_rule']}")
            
            lines.append("变动：删除")
            lines.append("")
        
        # 未修改的事件
        if show_unchanged:
            for key in unchanged_keys:
                event = new_dict[key]
                lines.append(f"事项: {event['title']}")
                lines.append(f"日期: {event['date']}")
                lines.append(f"时间段: {event['time_range']}")
                lines.append(f"类型: {event['event_type']}")
                
                if 'deadline' in event and event['deadline']:
                    lines.append(f"截止日期：{event['deadline']}")
                
                if 'importance' in event and event['importance']:
                    lines.append(f"重要程度：{event['importance']}")
                
                if 'recurrence_rule' in event and event['recurrence_rule']:
                    lines.append(f"重复规则：{event['recurrence_rule']}")
                
                lines.append("变动：无")
                lines.append("")
        
        if not lines:
            return "没有事件变更"
        
        return "\n".join(lines)
    
    def _event_key(self, event):
        """
        生成事件的唯一键
        
        Args:
            event (dict): 事件信息
            
        Returns:
            str: 事件的唯一键
        """
        if 'id' in event:
            return str(event['id'])
        else:
            return f"{event['title']}_{event['date']}_{event['time_range']}" 