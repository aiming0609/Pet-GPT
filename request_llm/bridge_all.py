"""
    该文件中主要包含2个函数

    不具备多线程能力的函数：
    1. predict: 正常对话时使用，具备完备的交互功能，不可多线程

    具备多线程调用能力的函数
    2. predict_no_ui_long_connection：在实验过程中发现调用predict_no_ui处理长文档时，和openai的连接容易断掉，这个函数用stream的方式解决这个问题，同样支持多线程
"""
import tiktoken
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor

from .bridge_chatgpt import predict_no_ui_long_connection as chatgpt_noui
from .bridge_chatgpt import predict as chatgpt
from toolbox import update_ui

from .bridge_chatglm import predict_no_ui_long_connection as chatglm_noui
from .bridge_chatglm import predict as chatglm_ui

# from .bridge_tgui import predict_no_ui_long_connection as tgui_noui
# from .bridge_tgui import predict as tgui_ui

colors = ['#FF00FF', '#00FFFF', '#FF0000', '#990099', '#009999', '#990044']

class LazyloadTiktoken(object):
    def __init__(self, model):
        self.model = model

    @staticmethod
    @lru_cache(maxsize=128)
    def get_encoder(model):
        print('正在加载tokenizer，如果是第一次运行，可能需要一点时间下载参数')
        tmp = tiktoken.encoding_for_model(model)
        print('加载tokenizer完毕')
        return tmp
    
    def encode(self, *args, **kwargs):
        encoder = self.get_encoder(self.model) 
        return encoder.encode(*args, **kwargs)
    
    def decode(self, *args, **kwargs):
        encoder = self.get_encoder(self.model) 
        return encoder.decode(*args, **kwargs)
    
tokenizer_gpt35 = LazyloadTiktoken("gpt-3.5-turbo")
tokenizer_gpt4 = LazyloadTiktoken("gpt-4")
get_token_num_gpt35 = lambda txt: len(tokenizer_gpt35.encode(txt, disallowed_special=()))
get_token_num_gpt4 = lambda txt: len(tokenizer_gpt4.encode(txt, disallowed_special=()))

model_info = {
    "flowise": {
        "fn_with_ui": chatgpt,
        "fn_without_ui": chatgpt_noui,
        "endpoint": None,  # 使用配置文件中的endpoint
        "max_token": 4096
    }
}

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=None, console_slience=False):
    """
    发送至LLM，等待回复，一次性完成，不显示中间过程。但内部用stream的方法避免中途网线被掐。
    """
    return chatgpt_noui(inputs, llm_kwargs, history, sys_prompt, observe_window, console_slience)

def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream=True, additional_fn=None):
    """
    发送至LLM，流式获取输出。
    用于基础的对话功能。
    inputs：
        是本次问询的输入
    llm_kwargs：
        是LLM的内部调优参数
    plugin_kwargs：
        是插件的内部调优参数
    chatbot：
        聊天显示框的句柄
    history：
        聊天历史
    system_prompt：
        系统提示词
    stream：
        流式输出还是一次性输出
    additional_fn：
        插件的额外功能函数
    """
    yield from chatgpt(inputs, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, stream, additional_fn)

