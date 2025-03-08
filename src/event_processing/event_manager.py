"""
事件管理器模块，负责事件的增删改查
"""

import sqlite3
import csv
import os
import json
from datetime import datetime, timedelta
from src.database.db_manager import DatabaseManager
from src.event_processing.event_parser import EventParser

class EventManager:
    """事件管理器，负责事件的增删改查"""
    
    def __init__(self, database_type="sqlite", db_path="timetable.db", csv_path="timetable.csv"):
        """
        初始化事件管理器
        
        Args:
            database_type (str): 'sqlite' 或 'csv'
            db_path (str): SQLite数据库路径
            csv_path (str): CSV文件路径
        """
        self.database_type = database_type.lower()
        self.db_path = db_path
        self.csv_path = csv_path
        self.db_manager = DatabaseManager(database_type, db_path, csv_path)
        self.event_parser = EventParser()
    
    def add_event(self, event):
        """
        添加事件
        
        Args:
            event (dict): 事件信息
            
        Returns:
            dict: 添加结果
        """
        # 检查事件是否有必要的字段
        required_fields = ['title', 'date', 'time_range', 'event_type']
        for field in required_fields:
            if field not in event:
                return {
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }
        
        # 检查是否有重复事件
        duplicate = self._check_duplicate_event(event)
        if duplicate:
            return {
                'success': False,
                'message': f'事件已存在: {event["title"]} ({event["date"]} {event["time_range"]})'
            }
        
        # 检查是否有时间冲突
        conflict = self._check_time_conflict(event)
        if conflict:
            return {
                'success': False,
                'message': f'时间冲突: {conflict["title"]} ({conflict["date"]} {conflict["time_range"]})'
            }
        
        # 添加事件
        return self._add_event_no_check(event)
    
    def _add_event_no_check(self, event):
        """
        添加事件（不检查重复和冲突）
        
        Args:
            event (dict): 事件信息
            
        Returns:
            dict: 添加结果
        """
        try:
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 准备SQL语句
                fields = ['title', 'date', 'time_range', 'event_type']
                values = [event['title'], event['date'], event['time_range'], event['event_type']]
                
                # 添加可选字段
                if 'deadline' in event:
                    fields.append('deadline')
                    values.append(event['deadline'])
                
                if 'importance' in event:
                    fields.append('importance')
                    values.append(event['importance'])
                
                if 'recurrence_rule' in event:
                    fields.append('recurrence_rule')
                    values.append(event['recurrence_rule'])
                
                # 构建SQL语句
                sql = f"INSERT INTO timetable ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})"
                
                # 执行SQL语句
                cursor.execute(sql, values)
                event_id = cursor.lastrowid
                
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'message': f'事件已添加: {event["title"]} ({event["date"]} {event["time_range"]})',
                    'event_id': event_id
                }
            elif self.database_type == "csv":
                # 读取现有事件
                events = []
                max_id = 0
                
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            events.append(row)
                            if int(row['id']) > max_id:
                                max_id = int(row['id'])
                
                # 添加新事件
                event_id = max_id + 1
                event['id'] = event_id
                event['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 确保所有必要字段都存在
                if 'deadline' not in event:
                    event['deadline'] = ''
                if 'importance' not in event:
                    event['importance'] = ''
                if 'recurrence_rule' not in event:
                    event['recurrence_rule'] = ''
                
                events.append(event)
                
                # 写入CSV文件
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule', 'last_updated']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for e in events:
                        writer.writerow(e)
                
                return {
                    'success': True,
                    'message': f'事件已添加: {event["title"]} ({event["date"]} {event["time_range"]})',
                    'event_id': event_id
                }
            else:
                return {
                    'success': False,
                    'message': f'不支持的数据库类型: {self.database_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'添加事件时出错: {str(e)}'
            }
    
    def _check_duplicate_event(self, event):
        """
        检查是否有重复事件
        
        Args:
            event (dict): 事件信息
            
        Returns:
            dict: 重复的事件，如果没有则返回None
        """
        try:
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 查询是否有相同标题、日期和时间段的事件
                cursor.execute("""
                SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule
                FROM timetable
                WHERE title = ? AND date = ? AND time_range = ?
                """, (event['title'], event['date'], event['time_range']))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        'id': row[0],
                        'title': row[1],
                        'date': row[2],
                        'time_range': row[3],
                        'event_type': row[4],
                        'deadline': row[5],
                        'importance': row[6],
                        'recurrence_rule': row[7]
                    }
                else:
                    return None
            elif self.database_type == "csv":
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if (row['title'] == event['title'] and 
                                row['date'] == event['date'] and 
                                row['time_range'] == event['time_range']):
                                return row
                
                return None
            else:
                return None
        except Exception:
            return None
    
    def _check_time_conflict(self, event):
        """
        检查是否有时间冲突
        
        Args:
            event (dict): 事件信息
            
        Returns:
            dict: 冲突的事件，如果没有则返回None
        """
        try:
            # 解析事件的时间范围
            event_date = event['date']
            event_time_range = event['time_range']
            start_time, end_time = self.event_parser.parse_time_range(event_time_range)
            
            if not start_time or not end_time:
                return None
            
            # 获取同一天的所有事件
            events = self.get_events_for_date(event_date)
            
            for existing_event in events:
                # 跳过与自己的比较（如果有ID）
                if 'id' in event and 'id' in existing_event and event['id'] == existing_event['id']:
                    continue
                
                # 解析现有事件的时间范围
                existing_time_range = existing_event['time_range']
                existing_start_time, existing_end_time = self.event_parser.parse_time_range(existing_time_range)
                
                if not existing_start_time or not existing_end_time:
                    continue
                
                # 检查时间是否重叠
                if ((start_time <= existing_start_time and end_time > existing_start_time) or
                    (start_time < existing_end_time and end_time >= existing_end_time) or
                    (start_time >= existing_start_time and end_time <= existing_end_time)):
                    return existing_event
            
            return None
        except Exception:
            return None
    
    def modify_event(self, event):
        """
        修改事件
        
        Args:
            event (dict): 事件信息，必须包含id字段
            
        Returns:
            dict: 修改结果
        """
        # 检查是否有ID
        if 'id' not in event:
            return {
                'success': False,
                'message': '缺少事件ID'
            }
        
        # 检查事件是否存在
        existing_event = self.get_event_by_id(event['id'])
        if not existing_event:
            return {
                'success': False,
                'message': f'事件不存在: ID {event["id"]}'
            }
        
        # 检查是否有时间冲突（排除自己）
        conflict = self._check_time_conflict(event)
        if conflict:
            return {
                'success': False,
                'message': f'时间冲突: {conflict["title"]} ({conflict["date"]} {conflict["time_range"]})'
            }
        
        # 修改事件
        try:
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 准备SQL语句
                update_fields = []
                values = []
                
                # 添加要更新的字段
                for field in ['title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule']:
                    if field in event:
                        update_fields.append(f"{field} = ?")
                        values.append(event[field])
                
                # 添加最后更新时间
                update_fields.append("last_updated = ?")
                values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                # 添加ID
                values.append(event['id'])
                
                # 构建SQL语句
                sql = f"UPDATE timetable SET {', '.join(update_fields)} WHERE id = ?"
                
                # 执行SQL语句
                cursor.execute(sql, values)
                
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'message': f'事件已修改: {event.get("title", existing_event["title"])} ({event.get("date", existing_event["date"])} {event.get("time_range", existing_event["time_range"])})'
                }
            elif self.database_type == "csv":
                # 读取现有事件
                events = []
                
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row['id'] == str(event['id']):
                                # 更新事件
                                for field in ['title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule']:
                                    if field in event:
                                        row[field] = event[field]
                                
                                # 更新最后更新时间
                                row['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            events.append(row)
                
                # 写入CSV文件
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule', 'last_updated']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for e in events:
                        writer.writerow(e)
                
                return {
                    'success': True,
                    'message': f'事件已修改: {event.get("title", existing_event["title"])} ({event.get("date", existing_event["date"])} {event.get("time_range", existing_event["time_range"])})'
                }
            else:
                return {
                    'success': False,
                    'message': f'不支持的数据库类型: {self.database_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'修改事件时出错: {str(e)}'
            }
    
    def delete_event(self, event_id):
        """
        删除事件
        
        Args:
            event_id (int): 事件ID
            
        Returns:
            dict: 删除结果
        """
        # 检查事件是否存在
        existing_event = self.get_event_by_id(event_id)
        if not existing_event:
            return {
                'success': False,
                'message': f'事件不存在: ID {event_id}'
            }
        
        # 删除事件
        try:
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 删除事件
                cursor.execute("DELETE FROM timetable WHERE id = ?", (event_id,))
                
                # 删除相关的已完成周期性事件日期
                cursor.execute("DELETE FROM completed_recurring_dates WHERE event_id = ?", (event_id,))
                
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'message': f'事件已删除: {existing_event["title"]} ({existing_event["date"]} {existing_event["time_range"]})'
                }
            elif self.database_type == "csv":
                # 读取现有事件
                events = []
                
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row['id'] != str(event_id):
                                events.append(row)
                
                # 写入CSV文件
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule', 'last_updated']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for e in events:
                        writer.writerow(e)
                
                # 删除相关的已完成周期性事件日期
                recurring_completed_csv_path = self.csv_path.replace('.csv', '_recurring_completed.csv')
                if os.path.exists(recurring_completed_csv_path):
                    recurring_completed_events = []
                    
                    with open(recurring_completed_csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row['event_id'] != str(event_id):
                                recurring_completed_events.append(row)
                    
                    with open(recurring_completed_csv_path, 'w', newline='', encoding='utf-8') as f:
                        fieldnames = ['id', 'event_id', 'date', 'completion_date']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for e in recurring_completed_events:
                            writer.writerow(e)
                
                return {
                    'success': True,
                    'message': f'事件已删除: {existing_event["title"]} ({existing_event["date"]} {existing_event["time_range"]})'
                }
            else:
                return {
                    'success': False,
                    'message': f'不支持的数据库类型: {self.database_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'删除事件时出错: {str(e)}'
            }
    
    def get_event_by_id(self, event_id):
        """
        根据ID获取事件
        
        Args:
            event_id (int): 事件ID
            
        Returns:
            dict: 事件信息，如果不存在则返回None
        """
        try:
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 查询事件
                cursor.execute("""
                SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated
                FROM timetable
                WHERE id = ?
                """, (event_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        'id': row[0],
                        'title': row[1],
                        'date': row[2],
                        'time_range': row[3],
                        'event_type': row[4],
                        'deadline': row[5],
                        'importance': row[6],
                        'recurrence_rule': row[7],
                        'last_updated': row[8]
                    }
                else:
                    return None
            elif self.database_type == "csv":
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row['id'] == str(event_id):
                                return row
                
                return None
            else:
                return None
        except Exception:
            return None
    
    def get_events_for_date(self, date, limit=None, offset=0):
        """
        获取指定日期的事件
        
        Args:
            date (str): 日期，格式为"YYYY-MM-DD"
            limit (int, optional): 返回的最大事件数
            offset (int, optional): 偏移量
            
        Returns:
            list: 事件列表
        """
        try:
            events = []
            
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 构建SQL语句
                sql = """
                SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated
                FROM timetable
                WHERE date = ?
                ORDER BY time_range
                """
                
                # 添加分页
                if limit is not None:
                    sql += f" LIMIT {limit}"
                    if offset > 0:
                        sql += f" OFFSET {offset}"
                
                # 查询事件
                cursor.execute(sql, (date,))
                
                for row in cursor.fetchall():
                    events.append({
                        'id': row[0],
                        'title': row[1],
                        'date': row[2],
                        'time_range': row[3],
                        'event_type': row[4],
                        'deadline': row[5],
                        'importance': row[6],
                        'recurrence_rule': row[7],
                        'last_updated': row[8]
                    })
                
                conn.close()
            elif self.database_type == "csv":
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row['date'] == date:
                                events.append(row)
                    
                    # 按时间段排序
                    events.sort(key=lambda x: x['time_range'])
                    
                    # 应用分页
                    if limit is not None:
                        events = events[offset:offset+limit]
            
            return events
        except Exception:
            return []
    
    def get_all_events(self, date_from=None, date_to=None, limit=None, offset=0):
        """
        获取所有事件
        
        Args:
            date_from (str, optional): 开始日期，格式为"YYYY-MM-DD"
            date_to (str, optional): 结束日期，格式为"YYYY-MM-DD"
            limit (int, optional): 返回的最大事件数
            offset (int, optional): 偏移量
            
        Returns:
            list: 事件列表
        """
        try:
            events = []
            
            if self.database_type == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 构建SQL语句
                sql = """
                SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated
                FROM timetable
                """
                
                # 添加日期范围
                conditions = []
                params = []
                
                if date_from:
                    conditions.append("date >= ?")
                    params.append(date_from)
                
                if date_to:
                    conditions.append("date <= ?")
                    params.append(date_to)
                
                if conditions:
                    sql += f" WHERE {' AND '.join(conditions)}"
                
                # 添加排序
                sql += " ORDER BY date, time_range"
                
                # 添加分页
                if limit is not None:
                    sql += f" LIMIT {limit}"
                    if offset > 0:
                        sql += f" OFFSET {offset}"
                
                # 查询事件
                cursor.execute(sql, params)
                
                for row in cursor.fetchall():
                    events.append({
                        'id': row[0],
                        'title': row[1],
                        'date': row[2],
                        'time_range': row[3],
                        'event_type': row[4],
                        'deadline': row[5],
                        'importance': row[6],
                        'recurrence_rule': row[7],
                        'last_updated': row[8]
                    })
                
                conn.close()
            elif self.database_type == "csv":
                if os.path.exists(self.csv_path):
                    with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # 应用日期范围过滤
                            if date_from and row['date'] < date_from:
                                continue
                            if date_to and row['date'] > date_to:
                                continue
                            
                            events.append(row)
                    
                    # 按日期和时间段排序
                    events.sort(key=lambda x: (x['date'], x['time_range']))
                    
                    # 应用分页
                    if limit is not None:
                        events = events[offset:offset+limit]
            
            return events
        except Exception:
            return [] 