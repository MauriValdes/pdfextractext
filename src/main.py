from fastapi import FastAPI
from src.api import docs_api

app = FastAPI(title="PDF Extract Text API")

app.include_router(docs_api.router)