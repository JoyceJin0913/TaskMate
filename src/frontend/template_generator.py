"""
模板生成器模块，负责组合HTML、CSS和JavaScript生成器
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.frontend.html_generator import HTMLGenerator
from src.frontend.css_generator import CSSGenerator
from src.frontend.js_generator import JSGenerator

class TemplateGenerator:
    """模板生成器，负责组合HTML、CSS和JavaScript生成器"""
    
    def __init__(self, templates_dir="templates", static_dir="static"):
        """
        初始化模板生成器
        
        Args:
            templates_dir (str): 模板目录路径
            static_dir (str): 静态资源目录路径
        """
        self.templates_dir = templates_dir
        self.static_dir = static_dir
        self.html_generator = HTMLGenerator(templates_dir)
        self.css_generator = CSSGenerator(static_dir)
        self.js_generator = JSGenerator(static_dir)
    
    def ensure_directories(self):
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
    
    def create_all_templates(self):
        """创建所有模板和静态资源"""
        self.ensure_directories()
        
        try:
            # 创建HTML模板
            self.html_generator.create_all_templates()
            
            # 创建CSS样式
            self.css_generator.create_all_css()
            
            # 创建JavaScript功能
            self.js_generator.create_all_js()
            
            print("所有模板和静态资源已创建完成")
            return "所有模板和静态资源已创建完成"
        except Exception as e:
            print(f"创建模板和静态资源时出错: {str(e)}")
            return f"创建模板和静态资源时出错: {str(e)}" 