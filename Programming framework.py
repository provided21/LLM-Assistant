import requests
import os
from datetime import datetime
import json
import dashscope

# 定义工具列表，模型在选择使用哪个工具时会参考工具的name和description
tools = [
    # 工具1 获取当前时刻的时间
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "当你想知道现在的时间时非常有用。",
            "parameters": {}  # 因为获取当前时间无需输入参数，因此parameters为空字典
        }
    },
    # 工具2 获取指定城市的天气
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市（可同时查询多个城市）的天气预报。",
            "parameters": {  # 查询天气时需要提供位置，因此参数设置为location
                "type": "object",
                "properties": {
                    "locations": {  # 改为复数形式，支持多城市
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "城市列表，如['南京', '扬州']"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期，如 '2025-05-21' 或 '明天'"}
                }
            },
            "required": [
                "location"
            ]
        }
    },
    # 工具3 获取电影数据
    {
        "type": "function",
        "function": {
            "name": "get_douban_movie_reviews",
            "description": "当用户查询某部电影的影评或评价时使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_name": {
                        "type": "string",
                        "description": "电影名称，如'肖申克的救赎'"
                    },
                    "review_count": {
                        "type": "integer",
                        "description": "想要获取的影评数量，默认为60",
                        "default": 60
                    }
                },
                "required": ["movie_name"]
            }
        }
    },
    # 工具4 获取实时股票数据
    {
        "type": "function",
        "function": {
            "name": "get_stock_info",
            "description": "查询股票实时行情信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "股票代码，如'sh000001'（上证指数）或'sh600036'（招商银行）（需要严格的完整股票代码）"
                    }
                },
                "required": ["stock_code"]
            }
        }
    },
    # 工具5 计算器功能
    {
        "type": "function",
        "function": {
            "name": "calculate_expression",
            "description": "计算数学表达式的结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如'3+5*2'或'sqrt(16)'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

import json
import os
import akshare as ak
import math

def calculate_expression(expression):
    """
    计算数学表达式
    """
    app_id = "Your_api"  # 替换为你的 App ID
    url = f"http://api.wolframalpha.com/v1/llm-api?input={expression}&appid={app_id}"
    response = requests.get(url).text  # 返回纯文本或 JSON（根据配置）
    return response

def get_stock_info(stock_code):
    """
    查询股票实时行情
    """
    try:
        # 实时行情数据（支持A股、港股、美股）
        df = ak.stock_zh_a_spot()
        stock_data = df[df["代码"] == stock_code].iloc[0]
        return (
            f"股票名称：{stock_data['名称']}\n"
            f"当前价格：{stock_data['最新价']}\n"
            f"涨跌：{stock_data['涨跌幅']}%\n"
        )
    except Exception as e:
        return f"查询失败：{e}"

def get_douban_movie_reviews(movie_name, review_count=3):
    """
    从指定文件夹的多个 JSON 文件中查询豆瓣影评
    """
    try:
        folder_path = "movie_data"

        # 遍历文件夹查找匹配的电影文件
        matched_files = []

        for filename in os.listdir(folder_path):
            if movie_name in filename and filename.endswith('.json'):
                matched_files.append(filename)

        if not matched_files:
            return f"没有找到关于电影'{movie_name}'的影评文件。"

        # 读取第一个匹配的文件
        file_path = os.path.join(folder_path, matched_files[0])
        with open(file_path, 'r', encoding='utf-8') as f:
            movie_data = json.load(f)

        # 获取影评
        reviews = movie_data.get('评论', [])
        if not reviews:
            return f"电影'{movie_name}'目前没有可用的影评。"


        return reviews

    except Exception as e:
        return f"查询影评时出错：{str(e)}"

# 模拟天气查询工具。返回结果示例：“北京今天是晴天。”
def get_weather(location, date=None):
    params = {
        "key":"Your_api",
        "location":location,
        "language":"zh-Hans",
        "unit":"c",
    }
    url = "https://api.seniverse.com/v3/weather/daily.json"
    r = requests.get(url, params=params)
    data = r.json()["results"][0]

    daily_data = next((d for d in data["daily"] if d["date"] == date), None)
    if not daily_data:
        return f"未找到 {date} 的天气数据"

    # 返回结构化数据（方便模型直接使用）
    return json.dumps({
        "date": date,
        "location": location,
        "weather": daily_data["text_day"],
        "temperature": f"{daily_data['high']}°C ~ {daily_data['low']}°C",
        "precip_prob": daily_data["precip"]
    })


# 查询当前时间的工具。返回结果示例：“当前时间：2024-04-15 17:15:18。“
def get_current_time():
    # 获取当前日期和时间
    current_datetime = datetime.now()
    # 格式化当前日期和时间
    formatted_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    # 返回格式化后的当前时间
    return f"当前时间：{formatted_time}。"


def get_response_q(messages):
    # TODO：你自己的API
    api_key = "Your_api"
    url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Bearer {api_key}'}
    body = {
        'model': 'qwen-plus-latest',
        "input": {
            "messages": messages
        },
        "parameters": {
            "result_format": "message",
            "tools": tools
        }
    }

    response = requests.post(url, headers=headers, json=body)
    return response.json()



def call_with_messages():
    count = 2
    messages = [
        {
            "content": input('请输入：'),  # 示例："肖申克的救赎影评"、"北京天气"、"现在几点"
            "role": "user"
        }
    ]

    # 第一轮模型调用
    first_response = get_response_q(messages)
    print(f"\n第1轮调用结果：{first_response}")

    # 解析模型返回的工具调用信息
    assistant_output = first_response['output']['choices'][0]['message']
    messages.append(assistant_output)
    while True:
        tool_info = []

        # 如果没有工具调用，直接返回回答
        if 'tool_calls' not in assistant_output:
            print(f"最终答案：{assistant_output['content']}")
            return

        # 处理工具调用
        tool_call = assistant_output['tool_calls'][0]
        function_name = tool_call['function']['name']
        function_args = json.loads(tool_call['function']['arguments'])

        # 根据工具类型调用对应函数
        if function_name == 'get_weather':
            locations = function_args.get('locations', [function_args.get('location')])
            date = function_args['date']
            tool_info = []  # 初始化列表
            for city in locations:
                if city:
                    tool_info.append({
                        "role": "tool",
                        "name": "get_weather",
                        "content": get_weather(city, date)
                    })

        elif function_name == 'get_current_time':
            tool_info = [{  # 单结果也包装成列表
                "role": "tool",
                "name": "get_current_time",
                "content": get_current_time()
            }]

        elif function_name == 'get_douban_movie_reviews':
            tool_info = [{
                "role": "tool",
                "name": "get_douban_movie_reviews",
                "content": get_douban_movie_reviews(
                    movie_name=function_args['movie_name'],
                    review_count=function_args.get('review_count', 3)
                )
            }]
        elif function_name == 'get_stock_info':
            stock_code = function_args['stock_code']
            tool_info = [{  # 单结果也包装成列表
                "role": "tool",
                "name": "get_stock_info",
                "content": get_stock_info(stock_code)
            }]
        elif function_name == 'calculate_expression':
            expression = function_args['expression']
            tool_info = [{  # 单结果也包装成列表
                "role": "tool",
                "name": "calculate_expression",
                "content": calculate_expression(expression)
            }]
        else:
            raise ValueError(f"未知的工具调用: {function_name}")

        print("工具输出信息：")
        for tool in tool_info:
            print(f"- {tool['name']}: {tool['content']}")

        # 将全部工具结果加入 messages
        messages.extend(tool_info)

        # 第N轮模型调用（总结工具返回结果）
        response = get_response_q(messages)
        print('response:',response)
        assistant_output = response['output']['choices'][0]['message']
        messages.append(assistant_output)
        print(f"第{count}轮调用结果：{response}")
        count += 1
        print(f"答案：{response['output']['choices'][0]['message']['content']}")


if __name__ == '__main__':
    call_with_messages()