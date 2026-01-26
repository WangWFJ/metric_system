from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc
from typing import Optional

from models.common import PageResponse
from models.database import get_session
from models.metrics import EvaluationType
from models.metrics_schemas import EvaluationTypeOut
from core.security import require_permission

router = APIRouter(prefix="/api/v1/evaluation_types", tags=["evaluation-types"])

@router.get("/", response_model=PageResponse[EvaluationTypeOut], dependencies=[Depends(require_permission("indicator:edit"))])
async def types_list(
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(EvaluationType)
    if q:
        stmt = stmt.where(EvaluationType.type_name.like(f"%{q}%"))
    count = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(asc(EvaluationType.type_id)).offset((page - 1) * size).limit(size)
    rows = (await session.execute(stmt)).scalars().all()
    data = [EvaluationTypeOut.model_validate(r) for r in rows]
    return PageResponse(data=data, total=count, page=page, size=size)

@router.post("/", response_model=EvaluationTypeOut, status_code=201, dependencies=[Depends(require_permission("indicator:edit"))])
async def types_create(payload: dict, session: AsyncSession = Depends(get_session)):
    name = (payload.get("type_name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="type_name is required")
    exists = (await session.execute(select(EvaluationType).where(EvaluationType.type_name == name))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="type_name exists")
    obj = EvaluationType(type_name=name)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return EvaluationTypeOut.model_validate(obj)

@router.put("/{type_id}", response_model=EvaluationTypeOut, dependencies=[Depends(require_permission("indicator:edit"))])
async def types_update(type_id: int, payload: dict, session: AsyncSession = Depends(get_session)):
    obj = await session.get(EvaluationType, type_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Type not found")
    if "type_name" in payload and (payload["type_name"] or "").strip():
        obj.type_name = payload["type_name"].strip()
    await session.commit()
    await session.refresh(obj)
    return EvaluationTypeOut.model_validate(obj)

@router.delete("/{type_id}", dependencies=[Depends(require_permission("indicator:edit"))])
async def types_delete(type_id: int, session: AsyncSession = Depends(get_session)):
    obj = await session.get(EvaluationType, type_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Type not found")
    await session.delete(obj)
    await session.commit()
    return {"deleted": 1}

