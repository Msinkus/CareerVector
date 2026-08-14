from fastapi import APIRouter

from careervector.api.v1.candidates import router as candidates_router

api_router = APIRouter()
api_router.include_router(candidates_router)
