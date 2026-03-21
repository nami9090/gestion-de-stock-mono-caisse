import os
import sys
import webbrowser
import threading
from wsgiref.simple_server import make_server

os.environ.setdefault("DJANGO_SETTINGS_MODULE","smartshop.settings")

import django
django.setup()

from django.core.wsgi import get_wsgi_application

def open_browser():
	webbrowser.open("http://127.0.0.1:8000/auth/")

if __name__ == "__main__":
	application = get_wsgi_application()
	threading.Timer(2, open_browser).start()

	with make_server('127.0.0.1', 8000, application) as httpd:
		print("Smart Stock en cours d'execution...")
		httpd.serve_forever()