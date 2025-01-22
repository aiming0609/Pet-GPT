# 借鉴了 https://github.com/GaiZhenbiao/ChuanhuChatGPT 项目

"""
    该文件中主要包含三个函数

    不具备多线程能力的函数：
    1. predict: 正常对话时使用，具备完备的交互功能，不可多线程

    具备多线程调用能力的函数
    2. predict_no_ui：高级实验性功能模块调用，不会实时显示在界面上，参数简单，可以多线程并行，方便实现复杂的功能逻辑
    3. predict_no_ui_long_connection：在实验过程中发现调用predict_no_ui处理长文档时，和openai的连接容易断掉，这个函数用stream的方式解决这个问题，同样支持多线程
"""

import json
import time
import gradio as gr
import logging
import traceback
import requests
import importlib
from config import load_config

config = load_config()
timeout_bot_msg = '[Local Message] Request timeout. Network error.' + \
                  '网络错误，请检查网络连接。'

def update_ui(chatbot=None, history=None, msg='正常', **kwargs):
    """刷新界面的函数"""
    if chatbot is not None and history is not None:
        yield chatbot, history, msg
    elif chatbot is not None:
        yield chatbot, msg
    elif history is not None:
        yield history, msg
    else:
        yield msg

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=None, console_slience=False):
    """
    发送至Flowise，等待回复，一次性完成，不显示中间过程。
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['Flowise']['flowise_api_key']}"
    }

    payload = {
        "question": inputs,
        "history": history,
        "systemPrompt": sys_prompt
    }

    retry = 0
    max_retry = int(config['Flowise']['max_retry'])
    while True:
        try:
            response = requests.post(
                f"{config['Flowise']['flowise_url']}/api/v1/prediction/{config['Flowise']['flowise_bolt_id']}",
                headers=headers,
                json=payload,
                timeout=int(config['Flowise']['timeout_seconds'])
            )
            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                raise Exception(f"请求失败: {response.status_code} - {response.text}")
        except requests.exceptions.ReadTimeout:
            retry += 1
            if retry > max_retry:
                raise TimeoutError
            print(f'请求超时，正在重试 ({retry}/{max_retry}) ……')

def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream=True, additional_fn=None):
    """
    发送至Flowise，流式获取输出。
    用于基础的对话功能。
    """
    if additional_fn is not None:
        import core_functional
        importlib.reload(core_functional)    # 热更新prompt
        core_functional = core_functional.get_core_functions()
        if "PreProcess" in core_functional[additional_fn]:
            inputs = core_functional[additional_fn]["PreProcess"](inputs)
        inputs = core_functional[additional_fn]["Prefix"] + inputs + core_functional[additional_fn]["Suffix"]

    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="等待响应")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['Flowise']['flowise_api_key']}"
    }

    payload = {
        "question": inputs,
        "history": history,
        "systemPrompt": system_prompt
    }

    retry = 0
    max_retry = int(config['Flowise']['max_retry'])
    while True:
        try:
            response = requests.post(
                f"{config['Flowise']['flowise_url']}/api/v1/prediction/{config['Flowise']['flowise_bolt_id']}",
                headers=headers,
                json=payload,
                timeout=int(config['Flowise']['timeout_seconds'])
            )
            break
        except:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
            retry_msg = f"，正在重试 ({retry}/{max_retry}) ……" if max_retry > 0 else ""
            yield from update_ui(chatbot=chatbot, history=history, msg="请求超时"+retry_msg)
            if retry > max_retry:
                raise TimeoutError

    if response.status_code == 200:
        result = response.json().get("text", "")
        history.append(inputs)
        history.append(result)
        chatbot[-1] = (history[-2], history[-1])
        yield from update_ui(chatbot=chatbot, history=history, msg="完成")
    else:
        error_msg = f"请求失败: {response.status_code} - {response.text}"
        chatbot[-1] = (chatbot[-1][0], error_msg)
        yield from update_ui(chatbot=chatbot, history=history, msg="请求失败")


