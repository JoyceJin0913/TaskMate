"""
数据库管理器模块，负责数据库初始化和表结构管理
"""

import sqlite3
import os
import csv
from datetime import datetime

class DatabaseManager:
    """数据库管理器，负责数据库初始化和表结构管理"""
    
    def __init__(self, database_type="sqlite", db_path="timetable.db", csv_path="timetable.csv"):
        """
        初始化数据库管理器
        
        Args:
            database_type (str): 'sqlite' 或 'csv'
            db_path (str): SQLite数据库路径
            csv_path (str): CSV文件路径
        """
        self.database_type = database_type.lower()
        self.db_path = db_path
        self.csv_path = csv_path
        
        if self.database_type == "sqlite":
            self.init_sqlite()
            # 确保数据库结构是最新的
            self.check_and_update_table_structure()
        elif self.database_type == "csv":
            self.init_csv()
        else:
            raise ValueError("不支持的数据库类型。请使用 'sqlite' 或 'csv'。")
    
    def init_sqlite(self):
        """初始化SQLite数据库并创建表（如果不存在）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建事件表（如果不存在）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time_range TEXT NOT NULL,
            event_type TEXT NOT NULL,
            deadline TEXT,
            importance INTEGER,
            recurrence_rule TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建completed_task表用于存储历史复盘任务
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time_range TEXT NOT NULL,
            actual_time_range TEXT,
            event_type TEXT NOT NULL,
            deadline TEXT,
            importance INTEGER,
            completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_notes TEXT,
            reflection_notes TEXT,
            FOREIGN KEY (task_id) REFERENCES timetable(id)
        )
        ''')
        
        # 创建completed_recurring_dates表用于存储已完成的周期性事件日期
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_recurring_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, date),
            FOREIGN KEY (event_id) REFERENCES timetable(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_and_update_table_structure(self, conn=None):
        """
        检查并更新数据库表结构，确保所有必要的列都存在。
        
        Args:
            conn (sqlite3.Connection, optional): 现有的数据库连接。如果为None，将创建新连接。
        """
        if self.database_type != "sqlite":
            return
            
        close_conn = False
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            close_conn = True
            
        cursor = conn.cursor()
        
        # 检查timetable表中是否存在recurrence_rule列
        cursor.execute("PRAGMA table_info(timetable)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "recurrence_rule" not in columns:
            cursor.execute("ALTER TABLE timetable ADD COLUMN recurrence_rule TEXT")
            
        # 检查completed_task表中是否存在reflection_notes列
        cursor.execute("PRAGMA table_info(completed_task)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "reflection_notes" not in columns:
            cursor.execute("ALTER TABLE completed_task ADD COLUMN reflection_notes TEXT")
            
        if "actual_time_range" not in columns:
            cursor.execute("ALTER TABLE completed_task ADD COLUMN actual_time_range TEXT")
        
        # 检查是否存在completed_recurring_dates表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completed_recurring_dates'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE completed_recurring_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, date),
                FOREIGN KEY (event_id) REFERENCES timetable(id)
            )
            ''')
        
        # 迁移已完成的事件到历史记录表
        self.migrate_completed_events(conn)
            
        conn.commit()
        
        if close_conn:
            conn.close()
    
    def migrate_completed_events(self, conn):
        """
        迁移已完成的事件到历史记录表
        
        Args:
            conn (sqlite3.Connection): 数据库连接
        """
        cursor = conn.cursor()
        
        # 检查timetable表中是否存在completed列
        cursor.execute("PRAGMA table_info(timetable)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "completed" in columns:
            # 获取所有已完成的事件
            cursor.execute("""
            SELECT id, title, date, time_range, event_type, deadline, importance
            FROM timetable
            WHERE completed = 1
            """)
            completed_events = cursor.fetchall()
            
            # 将已完成的事件插入到completed_task表
            for event in completed_events:
                event_id, title, date, time_range, event_type, deadline, importance = event
                
                # 检查事件是否已经在completed_task表中
                cursor.execute("""
                SELECT id FROM completed_task WHERE task_id = ?
                """, (event_id,))
                
                if not cursor.fetchone():
                    cursor.execute("""
                    INSERT INTO completed_task (task_id, title, date, time_range, event_type, deadline, importance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (event_id, title, date, time_range, event_type, deadline, importance))
            
            # 从timetable表中删除completed列
            cursor.execute("""
            CREATE TABLE timetable_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time_range TEXT NOT NULL,
                event_type TEXT NOT NULL,
                deadline TEXT,
                importance INTEGER,
                recurrence_rule TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cursor.execute("""
            INSERT INTO timetable_new (id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated)
            SELECT id, title, date, time_range, event_type, deadline, importance, recurrence_rule, last_updated
            FROM timetable
            """)
            
            cursor.execute("DROP TABLE timetable")
            cursor.execute("ALTER TABLE timetable_new RENAME TO timetable")
            
            conn.commit()
    
    def init_csv(self):
        """初始化CSV文件（如果不存在）"""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'title', 'date', 'time_range', 'event_type', 'deadline', 'importance', 'recurrence_rule', 'last_updated'])
                
        # 检查是否存在已完成任务的CSV文件
        completed_csv_path = self.csv_path.replace('.csv', '_completed.csv')
        if not os.path.exists(completed_csv_path):
            with open(completed_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'task_id', 'title', 'date', 'time_range', 'actual_time_range', 'event_type', 'deadline', 'importance', 'completion_date', 'completion_notes', 'reflection_notes'])
                
        # 检查是否存在已完成周期性事件日期的CSV文件
        recurring_completed_csv_path = self.csv_path.replace('.csv', '_recurring_completed.csv')
        if not os.path.exists(recurring_completed_csv_path):
            with open(recurring_completed_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'event_id', 'date', 'completion_date']) 