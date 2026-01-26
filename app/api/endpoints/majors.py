# =============================
# app/api/endpoints/majors.py
# =============================
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from models.common import PageResponse
from models.database import get_session
from core.security import require_permission
from models.metrics_schemas import MajorOut, MajorBase
from services.majors_service import list_majors, create_major, update_major, delete_major

router = APIRouter(prefix="/api/v1/majors", tags=["majors"])


@router.get("/", response_model=PageResponse[MajorOut], dependencies=[Depends(require_permission("indicator:edit"))])
async def majors_list(
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session)
):
    items, total = await list_majors(session, q=q, page=page, size=size)
    return PageResponse(data=items, total=total, page=page, size=size)


@router.post("/", response_model=MajorOut, status_code=201, dependencies=[Depends(require_permission("indicator:edit"))])
async def majors_create(payload: MajorBase, session: AsyncSession = Depends(get_session)):
    return await create_major(session, payload)


@router.put("/{major_id}", response_model=MajorOut, dependencies=[Depends(require_permission("indicator:edit"))])
async def majors_update(major_id: int, payload: MajorBase, session: AsyncSession = Depends(get_session)):
    return await update_major(session, major_id, payload)


@router.delete("/{major_id}", dependencies=[Depends(require_permission("indicator:edit"))])
async def majors_delete(major_id: int, session: AsyncSession = Depends(get_session)):
    return await delete_major(session, major_id)

