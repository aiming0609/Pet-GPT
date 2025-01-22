import json
import traceback
import requests
from queue import Queue
import time
from PyQt5.QtCore import QThread, pyqtSignal

class Flowise_request(QThread):
    response_received = pyqtSignal(str)
    tools_received = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.prompt_queue = Queue()

        # 基本参数
        self.flowise_url = self.config["Flowise"]["flowise_url"]
        self.api_key = self.config["Flowise"]["flowise_api_key"]
        self.bolt_id = self.config["Flowise"]["flowise_bolt_id"]
        self.timeout_seconds = int(self.config["Flowise"]["timeout_seconds"])
        self.max_retry = int(self.config["Flowise"]["max_retry"])

        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def run(self):
        while True:
            prompt, context, sys_prompt, tools = self.prompt_queue.get()
            self.get_response_from_flowise(inputs=prompt, history=context, sys_prompt=sys_prompt, tools=tools)

    def get_response_from_flowise(self, inputs, history, sys_prompt='', tools=False):
        retry_op = self.max_retry
        while retry_op > 0:
            try:
                # 构建请求数据
                payload = {
                    "question": inputs,
                    "history": history,
                    "systemPrompt": sys_prompt
                }

                # 发送请求到Flowise
                response = requests.post(
                    f"{self.flowise_url}/api/v1/prediction/{self.bolt_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout_seconds
                )

                if response.status_code == 200:
                    result = response.json().get("text", "")
                    if tools:
                        self.tools_received.emit(result)
                    else:
                        self.response_received.emit(result)
                    return

                else:
                    raise Exception(f"请求失败: {response.status_code} - {response.text}")

            except Exception as e:
                retry_op -= 1
                if retry_op > 0:
                    time.sleep(5)
                    continue
                else:
                    error_msg = f"[Local Message] 错误: {str(e)}"
                    if tools:
                        self.tools_received.emit(error_msg)
                    else:
                        self.response_received.emit(error_msg)
                    return 