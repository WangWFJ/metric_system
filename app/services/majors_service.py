# =============================
# app/services/majors_service.py
# =============================
from sqlalchemy import select, func, asc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import Optional, Tuple, List

from models.metrics import Major
from models.metrics_schemas import MajorOut, MajorBase


async def list_majors(
    session: AsyncSession,
    q: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> Tuple[List[MajorOut], int]:
    stmt = select(Major)
    if q:
        stmt = stmt.where(Major.major_name.like(f"%{q}%") | Major.major_code.like(f"%{q}%"))
    count = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(asc(Major.major_id)).offset((page - 1) * size).limit(size)
    rows = (await session.execute(stmt)).scalars().all()
    return ([MajorOut.model_validate(r) for r in rows], count)


async def create_major(session: AsyncSession, payload: MajorBase) -> MajorOut:
    obj = Major(major_name=payload.major_name, major_code=payload.major_code)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return MajorOut.model_validate(obj)


async def update_major(session: AsyncSession, major_id: int, payload: MajorBase) -> MajorOut:
    obj = await session.get(Major, major_id)
    if not obj:
        raise HTTPException(404, "Major not found")
    obj.major_name = payload.major_name
    obj.major_code = payload.major_code
    await session.commit()
    await session.refresh(obj)
    return MajorOut.model_validate(obj)


async def delete_major(session: AsyncSession, major_id: int) -> dict:
    obj = await session.get(Major, major_id)
    if not obj:
        raise HTTPException(404, "Major not found")
    await session.delete(obj)
    await session.commit()
    return {"deleted": 1}

