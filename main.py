"""
入口文件，用于启动应用
"""

import argparse
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.app import create_app

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='TaskMate - 智能日程管理系统')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='主机地址')
    parser.add_argument('--port', type=int, default=5000, help='端口号')
    parser.add_argument('--debug', action='store_true', help='是否开启调试模式')
    parser.add_argument('--db-type', type=str, default='sqlite', choices=['sqlite', 'csv'], help='数据库类型')
    parser.add_argument('--db-path', type=str, default='timetable.db', help='SQLite数据库路径')
    parser.add_argument('--csv-path', type=str, default='timetable.csv', help='CSV文件路径')
    parser.add_argument('--templates-dir', type=str, default='templates', help='模板目录路径')
    parser.add_argument('--static-dir', type=str, default='static', help='静态资源目录路径')
    
    args = parser.parse_args()
    
    # 创建应用
    app = create_app(
        templates_dir=args.templates_dir,
        static_dir=args.static_dir,
        database_type=args.db_type,
        db_path=args.db_path,
        csv_path=args.csv_path
    )
    
    # 运行应用
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main() 