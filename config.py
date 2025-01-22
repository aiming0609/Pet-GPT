import configparser
import os

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'pet_config.ini')
    config.read(config_path, encoding='utf-8')

    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(config_path):
        config['Pet'] = {
            'nickname': 'Bell',
            'pet_icon': 'pet_image\\yuansheng\\七七.gif',
            'random_walk': 'False',
            'random_chat': 'False',
            'width': '300',
            'height': '300',
            'shortcuts_chat_window': 'Ctrl+Alt+2',
            'shortcuts_chat_web': 'Ctrl+Alt+1'
        }
        
        config['Flowise'] = {
            'flowise_url': 'http://your-flowise-url',
            'flowise_api_key': 'your-api-key',
            'flowise_bolt_id': 'your-bolt-id',
            'timeout_seconds': '100',
            'max_retry': '3'
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)

    return config

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'pet_config.ini')
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
