import sys
import os
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.insert(0, '/var/www/nothard/nothard_website')

# Загрузка переменных окружения
load_dotenv()

from app import app as application
