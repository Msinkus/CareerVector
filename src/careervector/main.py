from fastapi import FastAPI

from careervector.api.v1.router import api_router
from careervector.config import get_settings

settings = get_settings()

app = FastAPI(title="CareerVector", version="0.1.0")
app.include_router(api_router, prefix=settings.api_v1_prefix)
