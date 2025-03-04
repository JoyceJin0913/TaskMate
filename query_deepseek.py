import os
import openai
import datetime

# Set up the OpenAI API key
# Option 1: Set API key directly in the code (quick but not secure for production)
#openai.api_key = "your-api-key-here"

# Option 2: Use environment variable (more secure)
api_key = os.environ.get("DEEPSEEK_API_KEY")

def query_deepseek(prompt, schedule, model="deepseek-chat"):
    """
    Send a query to the DeepSeek API and return the response.
    
    Args:
        prompt (str): The text prompt to send to the API
        model (str): The model to use
        
    Returns:
        str: The model's response text
    """
    try:
        client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        system_prompt = """您是一名专业的时间规划师，精通GTD工作法和敏捷项目管理。请根据用户提供的待办事项和现有时间表，完成以下任务："""
        user_prompt = f"""
【处理规则】

基本规则：
事项：
事项名称为用户输入的代办事项拆分后的小事项名称，尽量减少重复

日期、时间段：
日期与时间段为任务的执行时间，若无要求则根据现有任务以及新增任务的时间来安排

类型：
类型为任务事项或固定日程
任务事项：任务事项为需要用户执行的任务，如作业、工作、运动等
固定日程：固定日程为固定不变的事件，如会议、约会、课程等

截止日期：
截止日期为任务的截止时间，若无要求则与任务执行日期相同

重要程度：
重要程度根据任务的紧急程度和重要性来判断，取值范围为1-5，5为最高
若任务接近截止时间，则重要程度较高，反之较低
若任务可能关系到用户的健康、安全、财产、生涯等，则重要程度较高
若任务是固定日程，则重要程度为5

变动：
输出时变动有三种：新增、更改、删除
新增：任务是新添加的，只要是用户提出的新事件，就需要输出此类以将其添加到时间表中，安排时段优先根据用户要求，若无要求则根据任务重要程度和紧急程度安排
更改：任务是已存在的，但需要修改，可因为用户要求，或是有其他更为紧急的任务，输出的时段为更改后的时段
删除：任务是已存在的，但需要删除，只有在用户要求删除时输出，输出时时间段可保持不变
其余无变动任务无需输出

【特殊规则】

时间分配：
尽量使用每日专注时段（默认 09:00-12:30;14:00-17:30）
单任务最长持续≤120分钟，间隔≥10分钟缓冲
冲突处理原则：截止时间近者优先，重要度相同则用时少者优先

自动预留截止时间前15%时长作为应急缓冲
连续工作>120分钟必须插入15分钟休息
每日保留19:00-21:00作为弹性时段（可调整）
输出时间精度保持±5分钟对齐

【输入示例】
当前时间：2024-03-14 16:00

当前时间表：
事项: 项目会议
日期: 2024-03-15
时间段: 09:00-10:30
类型: 固定日程
截止日期：2024-03-15
重要程度：5

事项: 完成报告
日期: 2024-03-16
时间段: 15:30-16:30
类型: 任务事项
截止日期：2024-03-18
重要程度：3

新增任务：
我后天下午三点要开个会，得准备个PPT


【输出示例】
新任务：开会并准备PPT
开会并准备PPT → 拆分为：
- 准备演讲稿（预计需两小时，时段：2024-03-15 15:00-17:00）
- 进行会议（预计需一小时，时段：2024-03-16 15:00-16:00）


日程建议：
事项: 完成报告
日期: 2024-03-17
时间段: 9:00-10:00
类型: 任务事项
截止日期：2024-03-18
重要程度：4
变动：更改

事项: 准备演讲稿
日期: 2024-03-15
时间段: 15:00-17:00
类型: 任务事项
截止日期：2024-03-16
重要程度：4
变动：新增

事项: 项目会议
日期: 2024-03-16
时间段: 15:00-16:00
类型: 固定日程
截止日期：2024-03-16
重要程度：5
变动：新增


请根据以上指令完成以下任务规划，并严格遵守输出格式，无需进行任何额外说明与解释：

【输入】
当前时间：{current_time}

当前时间表：
{schedule}

新增任务：
{prompt}

【输出】
"""
        #print(prompt)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            max_tokens=1024,
            temperature=0.2
        )

        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error querying DeepSeek API: {str(e)}"

