from volcenginesdkarkruntime import Ark
from openai import OpenAI
import json, os, re
import chardet
# 加载设置
settings_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(settings_path, "r", encoding="utf-8") as f:
    settings = json.load(f)

# 从设置中获取 API 配置
API_KEYS = settings["api_keys"]
BASE_URLS = settings["base_urls"]

# 豆包的服务
client = Ark(
    base_url=BASE_URLS["doubao"],
    api_key=API_KEYS["doubao"]
)

# 移动的服务
yidong_client = OpenAI(  
    api_key=API_KEYS["yidong"],
    base_url=BASE_URLS["yidong"]
)

openai_client = OpenAI(
    api_key=API_KEYS["openai"],
    base_url=BASE_URLS["openai"]
)

google_client = OpenAI(
    api_key=API_KEYS["google"],
    base_url=BASE_URLS["google"]
)

client_list = {"doubao":client,
               "qwen3":yidong_client,
               "dsv3":yidong_client,
               "gpt-4.1":openai_client,
               "dsr1":yidong_client,
               "gemini-2.0-flash":google_client,
               "gemini-2.5-pro":google_client
               }

model_name_list = {"doubao":"ep-20241031214346-9xd5h",
               "qwen3":"qwen3-32b",
               "dsv3":"deepseek-v3",
               "gpt-4.1":"gpt-4.1",
               "dsr1":"deepseek-r1",
               "gemini-2.0-flash":"gemini-2.0-flash",
               "gemini-2.5-pro":"gemini-2.5-pro"
               }

def query_llm(input_data, model='dsv3'):
    """
    根据输入类型（list 或 str）调用相应的 LLM 接口并返回结果。
    
    参数:
        input_data (list or str): 输入数据，可以是消息列表或单个提示字符串。
    
    返回:
        str: LLM 的响应结果。
    """
    if isinstance(input_data, list):
        # 如果输入是列表，使用 query_doubao_w_messages
        try:

            # 标准请求
            #print("----- standard request -----")
            completion = client_list[model].chat.completions.create(
                model=model_name_list[model],
                messages=input_data
            )
            return completion.choices[0].message.content

        except Exception as e:
            print(f"调用API时发生错误: {str(e)}")
            return ""
    elif isinstance(input_data, str):
        # 如果输入是字符串，使用 query_doubao
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": input_data
                }
            ]

            # 标准请求
            #print("----- standard request -----")
            completion = client_list[model].chat.completions.create(
                model=model_name_list[model],
                messages=messages,
            )
            return completion.choices[0].message.content

        except Exception as e:
            print(model+"-----调用错误")
            print(f"调用API时发生错误: {str(e)}")
    else:
        raise ValueError("输入类型必须是 list 或 str")

def load_prompt(file_path='./prompts/sys_prompt1.txt'):
    """
    加载提示词文件内容。

    参数：
        file_path (str): 提示词文件路径。

    返回：
        str: 提示词内容。
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        detected_encoding = chardet.detect(raw_data)['encoding']

    with open(file_path, 'r', encoding=detected_encoding) as f:
        return f.read()

def save_to_file(content, file_path="data/thesis/draft.tex"):
    """
    将内容保存到指定文件。

    参数：
        content (str): 要保存的内容。
        file_path (str): 保存路径。
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def remove_think_chain(response):
    """
    从模型的响应中移除 <think>xxx</think> 格式的思维链内容。

    参数：
        response (str): 模型的完整响应。

    返回：
        str: 移除思维链后的正式回答部分。
    """
    # 使用正则表达式移除 <think> 标签及其内容
    cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    return cleaned_response.strip()


def parse_llm_json(text, save_failed_path=None):
    """从 LLM 的返回文本中提取并解析 JSON 内容。

    支持如下常见情形：
    - 纯 JSON 文本
    - 包含代码块 ```json ... ``` 的情形
    - 响应中包含前后说明文字，函数会在第一个 JSON 对象/数组的起止处尝试提取

    返回解析后的 Python 对象（dict 或 list）。若无法解析则抛出 ValueError。
    """
    if not isinstance(text, str):
        raise ValueError('输入必须是字符串')

    s = text.strip()

    # 优先查找 ```json 或 ``` 包裹的代码块
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```", s, flags=re.IGNORECASE)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception as e:
            # 保存原始响应以便离线检查
            if save_failed_path:
                os.makedirs(os.path.dirname(save_failed_path), exist_ok=True)
                with open(save_failed_path, 'w', encoding='utf-8') as f:
                    f.write(s)
            raise ValueError(f'解析代码块内 JSON 失败: {e}') from e

    # 否则，尝试找到第一个 JSON 对象或数组并做配对查找
    s_len = len(s)
    for start_char in ['{', '[']:
        start_idx = s.find(start_char)
        if start_idx == -1:
            continue
        stack = []
        for i in range(start_idx, s_len):
            ch = s[i]
            if ch == '{' or ch == '[':
                stack.append(ch)
            elif ch == '}' or ch == ']':
                if not stack:
                    break
                opening = stack.pop()
                # 简单配对，不严格检查类型一致性
                if not stack:
                    candidate = s[start_idx:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception as e:
                        if save_failed_path:
                            os.makedirs(os.path.dirname(save_failed_path), exist_ok=True)
                            with open(save_failed_path, 'w', encoding='utf-8') as f:
                                f.write(s)
                        raise ValueError(f'解析提取到的 JSON 失败: {e}') from e

    # 最后尝试直接 json.loads（如果字符串就是 JSON）
    try:
        return json.loads(s)
    except Exception as e:
        if save_failed_path:
            os.makedirs(os.path.dirname(save_failed_path), exist_ok=True)
            with open(save_failed_path, 'w', encoding='utf-8') as f:
                f.write(s)
        raise ValueError(f'无法从模型响应中解析 JSON: {e}') from e