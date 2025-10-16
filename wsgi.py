#!/usr/bin/env python3
"""
WSGI entry point для деплоя Flask приложения
"""

import sys
import os

# Добавляем путь к проекту в PYTHONPATH
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import app

if __name__ == "__main__":
    app.run()
