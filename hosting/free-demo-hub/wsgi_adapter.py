"""Mount an unchanged Flask application below its independent demo URL."""
import importlib
import os
import sys
from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

sys.path.insert(0, os.getcwd())
prefix = os.environ['DEMO_PREFIX']
app = importlib.import_module(os.environ['DEMO_MODULE']).app
app.config['APPLICATION_ROOT'] = prefix
app.config['SESSION_COOKIE_PATH'] = prefix
application = ProxyFix(DispatcherMiddleware(NotFound(), {prefix: app}), x_proto=1, x_host=1)
