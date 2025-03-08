#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import argparse
from query_api import query_api
from schedule_parser import TimetableProcessor

def query_llm():
    """
    主函数：提示用户输入待办事项，查询LLM，处理事件并更新数据库
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='查询LLM并处理日程安排')
    parser.add_argument('--model', type=str, default='deepseek-chat', 
                        help='使用的LLM模型 (deepseek-chat 或 gpt-4o)')
    parser.add_argument('--db-type', type=str, default='sqlite', 
                        choices=['sqlite', 'csv'], help='数据库类型')
    parser.add_argument('--show-summary', action='store_true', 
                        help='显示处理摘要')
    parser.add_argument('--show-changes', action='store_true', 
                        help='显示变更详情')
    parser.add_argument('--show-events', action='store_true', 
                        help='显示当前所有事件')
    parser.add_argument('--show-unchanged', action='store_true',
                        help='显示未变化的事件')
    parser.add_argument('--recurrence', type=str, 
                        choices=['daily', 'weekly', 'weekdays', 'monthly', 'yearly'],
                        help='设置事件的重复模式')
    parser.add_argument('--end-date', type=str, 
                        help='设置重复事件的结束日期，格式为YYYY-MM-DD')
    parser.add_argument('--limit', type=int, default=20, 
                        help='显示事件的最大数量')
    args = parser.parse_args()

    # 初始化时间表处理器
    processor = TimetableProcessor(database_type=args.db_type)
    
    # 获取当前事件列表
    current_events = processor.format_events_as_llm_output(include_header=False, limit=args.limit)
    
    # 提示用户输入
    user_prompt = input("你有什么想放进计划表的东西吗？")
    print(f"你的输入：{user_prompt}")
    
    # 如果用户输入为空，则退出
    if not user_prompt.strip():
        print("输入为空，程序退出")
        return
    
    # 查询LLM
    print(f"正在使用 {args.model} 模型处理...")
    start_time = time.time()
    response = query_api(user_prompt, current_events, model=args.model)
    end_time = time.time()
    
    # 显示LLM响应
    print(f"模型推理时间：{end_time - start_time:.2f}秒")
    print("\n模型回复：")
    print(response)
    
    # 获取修改前的所有事件（如果需要显示变更）
    if args.show_changes:
        old_events = processor.get_all_events(limit=args.limit)
    
    # 处理事件并更新数据库
    try:
        if args.recurrence:
            # 如果设置了重复模式，使用 process_recurring_events 方法
            summary = processor.process_recurring_events(
                response, 
                recurrence_rule=args.recurrence,
                end_date=args.end_date,
                handle_conflicts='error'
            )
        else:
            # 否则使用普通的 process_events 方法
            summary = processor.process_events(response)
        
        if args.show_summary:
            print("\n处理摘要：")
            print(summary)
            
        # 显示变更（如果需要）
        if args.show_changes:
            new_events = processor.get_all_events(limit=args.limit)
            changes = processor.format_events_with_changes(old_events, new_events, include_header=True, show_unchanged=args.show_unchanged)
            print("\n事件变更：")
            print(changes)
        
        # 显示当前所有事件（如果需要）
        if args.show_events:
            formatted_output = processor.format_events_as_llm_output(limit=args.limit)
            print("\n当前所有事件：")
            print(formatted_output)
            
    except ValueError as e:
        print(f"\n错误：{str(e)}")
        if "conflict" in str(e).lower():
            print("提示：事件时间冲突。您可以修改事件时间或删除冲突的事件。")
        if "date" in str(e).lower() or "time" in str(e).lower():
            print("提示：日期或时间格式错误。请确保日期格式为YYYY-MM-DD，时间格式为HH:MM。")
        return

if __name__ == "__main__":
    query_llm()
