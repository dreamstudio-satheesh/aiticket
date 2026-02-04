from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.kb import router as kb_router
from app.api.v1.search import router as search_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.whmcs import router as whmcs_router
from app.api.v1.replies import router as replies_router
from app.api.v1.ui import router as ui_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.examples import router as examples_router
from app.api.v1.corrections import router as corrections_router
from app.api.v1.weights import router as weights_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(kb_router)
router.include_router(search_router)
router.include_router(prompts_router)
router.include_router(whmcs_router)
router.include_router(replies_router)
router.include_router(ui_router)
router.include_router(analytics_router)
router.include_router(examples_router)
router.include_router(corrections_router)
router.include_router(weights_router)


@router.get("/")
async def root():
    return {"message": "AI Support Assistant API v1"}
