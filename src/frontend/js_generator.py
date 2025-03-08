"""
JavaScript生成器模块，负责组合基本和高级JavaScript功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.frontend.js_generator_base import JSGeneratorBase
from src.frontend.js_generator_advanced import JSGeneratorAdvanced

class JSGenerator:
    """JavaScript生成器，负责组合基本和高级JavaScript功能"""
    
    def __init__(self, static_dir="static"):
        """
        初始化JavaScript生成器
        
        Args:
            static_dir (str): 静态资源目录路径
        """
        self.static_dir = static_dir
        self.js_dir = os.path.join(static_dir, "js")
        self.base_generator = JSGeneratorBase(static_dir)
        self.advanced_generator = JSGeneratorAdvanced(static_dir)
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        # 创建JavaScript目录
        if not os.path.exists(self.js_dir):
            os.makedirs(self.js_dir)
    
    def create_combined_js(self):
        """创建组合的JavaScript文件"""
        try:
            # 生成基本和高级JavaScript文件
            self.base_generator.create_base_js()
            self.advanced_generator.create_advanced_js()
            
            # 读取基本JavaScript文件
            with open(os.path.join(self.js_dir, 'script_base.js'), 'r', encoding='utf-8') as f:
                base_js = f.read()
            
            # 读取高级JavaScript文件
            with open(os.path.join(self.js_dir, 'script_advanced.js'), 'r', encoding='utf-8') as f:
                advanced_js = f.read()
            
            # 组合JavaScript文件
            combined_js = base_js + "\n\n" + advanced_js
            
            # 写入组合的JavaScript文件
            with open(os.path.join(self.js_dir, 'script.js'), 'w', encoding='utf-8') as f:
                f.write(combined_js)
            
            # 删除临时文件
            try:
                os.remove(os.path.join(self.js_dir, 'script_base.js'))
                os.remove(os.path.join(self.js_dir, 'script_advanced.js'))
            except:
                pass  # 忽略删除临时文件时的错误
                
            return True
        except Exception as e:
            print(f"创建组合JavaScript文件时出错: {str(e)}")
            return False
    
    def create_all_js(self):
        """创建所有JavaScript功能"""
        self.ensure_directories()
        result = self.create_combined_js()
        
        if result:
            return "JavaScript功能已创建完成"
        else:
            return "创建JavaScript功能时出错" 