"""
主应用模块，负责整合所有功能
"""

import os
import sys
from flask import Flask

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.api.routes import APIRoutes
from src.event_processing.event_processor import EventProcessor
from src.frontend.template_generator import TemplateGenerator

class App:
    """主应用类，负责整合所有功能"""
    
    def __init__(self, templates_dir="templates", static_dir="static", 
                 database_type="sqlite", db_path="timetable.db", csv_path="timetable.csv"):
        """
        初始化应用
        
        Args:
            templates_dir (str): 模板目录路径
            static_dir (str): 静态资源目录路径
            database_type (str): 数据库类型，'sqlite'或'csv'
            db_path (str): SQLite数据库路径
            csv_path (str): CSV文件路径
        """
        self.templates_dir = templates_dir
        self.static_dir = static_dir
        self.database_type = database_type
        self.db_path = db_path
        self.csv_path = csv_path
        
        # 确保目录存在
        self._ensure_directories()
        
        # 创建Flask应用
        self.flask_app = Flask("TaskMate", 
                              template_folder=os.path.abspath(templates_dir),
                              static_folder=os.path.abspath(static_dir))
        self.flask_app.config['TEMPLATES_AUTO_RELOAD'] = True
        
        # 创建事件处理器
        self.event_processor = EventProcessor(database_type, db_path, csv_path)
        
        # 创建API路由
        self.api_routes = APIRoutes(self.flask_app, self.event_processor)
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        # 创建模板目录
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # 创建静态资源目录
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)
        
        # 创建CSS目录
        css_dir = os.path.join(self.static_dir, "css")
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)
        
        # 创建JS目录
        js_dir = os.path.join(self.static_dir, "js")
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
    
    def setup(self):
        """设置应用"""
        # 生成前端模板和静态资源
        template_generator = TemplateGenerator(self.templates_dir, self.static_dir)
        template_generator.create_all_templates()
    
    def run(self, host='127.0.0.1', port=5000, debug=True):
        """
        运行应用
        
        Args:
            host (str): 主机地址
            port (int): 端口号
            debug (bool): 是否开启调试模式
        """
        print(f"启动服务器: http://{host}:{port}/")
        self.flask_app.run(host=host, port=port, debug=debug)

def create_app(templates_dir="templates", static_dir="static", 
               database_type="sqlite", db_path="timetable.db", csv_path="timetable.csv"):
    """
    创建应用实例
    
    Args:
        templates_dir (str): 模板目录路径
        static_dir (str): 静态资源目录路径
        database_type (str): 数据库类型，'sqlite'或'csv'
        db_path (str): SQLite数据库路径
        csv_path (str): CSV文件路径
        
    Returns:
        App: 应用实例
    """
    app = App(templates_dir, static_dir, database_type, db_path, csv_path)
    app.setup()
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True) 