import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    """Загружает конфигурацию из JSON-файла, если он существует."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Сохраняет конфигурацию в JSON-файл."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
