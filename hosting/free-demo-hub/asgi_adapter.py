"""Mount the unchanged password API with correct OpenAPI and static-file paths."""
import os
import sys
from fastapi import FastAPI

sys.path.insert(0, os.getcwd())
from app.main import app

application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
application.mount('/demos/password', app)
