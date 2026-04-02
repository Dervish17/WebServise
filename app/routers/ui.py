from fastapi import APIRouter

from app.routers.ui_auth import router as auth_router
from app.routers.ui_clients_equipment import router as clients_equipment_router
from app.routers.ui_orders import router as orders_router
from app.routers.ui_users import router as users_router

router = APIRouter(tags=["ui"])
router.include_router(auth_router)
router.include_router(clients_equipment_router)
router.include_router(orders_router)
router.include_router(users_router)
