from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, asc
from typing import Optional
from models.database import get_session, User, Role
from models.user_schemas import UserOut, UserUpdate, AdminUserCreate
from models.common import PageResponse
from core.security import require_permission, get_password_hash, bump_perm_version

router = APIRouter(prefix="/api/v1/admin/users", tags=["user-manage"])

@router.get("/", response_model=PageResponse[UserOut])
async def list_users(
    q: Optional[str] = Query(None),
    role_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _perm = Depends(require_permission("user:manage")),
):
    stmt = select(User)
    if q:
        stmt = stmt.where(or_(User.username.like(f"%{q}%"), User.phone.like(f"%{q}%")))
    if role_id is not None:
        stmt = stmt.where(User.role_id == role_id)
    if status is not None:
        stmt = stmt.where(User.status == status)
    count = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(asc(User.id)).offset((page - 1) * size).limit(size)
    rows = (await session.execute(stmt)).scalars().all()
    data = [UserOut.model_validate(u) for u in rows]
    return PageResponse(data=data, total=count, page=page, size=size)

@router.post("/", response_model=UserOut, status_code=201)
async def create_user_admin(payload: AdminUserCreate, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    if not payload.role_id:
        raise HTTPException(status_code=400, detail="role_id is required")
    raw_pwd = payload.password if (payload.password and payload.password.strip()) else "cmcc123456"
    u = User(
        username=payload.username,
        password=get_password_hash(raw_pwd),
        phone=payload.phone,
        role_id=payload.role_id,
        status=1 if (payload.status is None) else payload.status,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return UserOut.model_validate(u)

@router.patch("/{user_id}", response_model=UserOut)
async def update_user_admin(user_id: int, payload: UserUpdate, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    u = await session.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.password is not None:
        u.password = get_password_hash(payload.password)
    if payload.phone is not None:
        u.phone = payload.phone
    if payload.role_id is not None:
        u.role_id = payload.role_id
        bump_perm_version()
    if payload.status is not None:
        u.status = payload.status
    await session.commit()
    await session.refresh(u)
    return UserOut.model_validate(u)

@router.delete("/{user_id}")
async def delete_user_admin(user_id: int, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    u = await session.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(u)
    await session.commit()
    return {"deleted": 1}

@router.get("/roles")
async def list_roles(session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    rows = (await session.execute(select(Role).where(Role.status == 1).order_by(asc(Role.role_id)))).scalars().all()
    return [{"role_id": r.role_id, "role_name": r.role_name, "role_code": r.role_code} for r in rows]
