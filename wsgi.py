import sys
import os

# Путь к приложению
path = '/home/moongohard271/mysite'
if path not in sys.path:
    sys.path.append(path)

# Импортируем приложение
from bot_app import app as application