import sys
import os

# Asegurar que el directorio del proyecto está en sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Adaptador ASGI a WSGI para ejecutar FastAPI en PythonAnywhere
from a2wsgi import ASGIMiddleware
from api import app

_asgi_app = None

def application(environ, start_response):
    global _asgi_app
    if _asgi_app is None:
        _asgi_app = ASGIMiddleware(app)
    return _asgi_app(environ, start_response)
