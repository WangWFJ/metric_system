from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, asc, delete
from typing import Optional, List
from models.database import get_session, Permission, RolePermission, Role
from core.security import require_permission, bump_perm_version
from models.common import PageResponse

router = APIRouter(prefix="/api/v1/admin/permissions", tags=["permissions"])

@router.get("/list", response_model=PageResponse[dict])
async def list_permissions(
    q: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    role_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
    _perm = Depends(require_permission("user:manage")),
):
    stmt = select(Permission)
    if q:
        stmt = stmt.where(or_(Permission.permission_name.like(f"%{q}%"), Permission.permission_code.like(f"%{q}%")))
    if resource:
        stmt = stmt.where(Permission.resource == resource)
    if action:
        stmt = stmt.where(Permission.action == action)
    if status is not None:
        stmt = stmt.where(Permission.status == status)
    if role_id is not None:
        subq = select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        stmt = stmt.where(Permission.permission_id.in_(subq))
    count = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(asc(Permission.permission_id)).offset((page - 1) * size).limit(size)
    rows = (await session.execute(stmt)).scalars().all()
    data = [
        {
            "permission_id": p.permission_id,
            "permission_code": p.permission_code,
            "permission_name": p.permission_name,
            "resource": p.resource,
            "action": p.action,
            "status": p.status,
            "create_time": str(p.create_time),
        } for p in rows
    ]
    return PageResponse(data=data, total=count, page=page, size=size)

@router.post("/", status_code=201)
async def create_permission(
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _perm = Depends(require_permission("user:manage")),
):
    required = ["permission_code", "permission_name", "resource", "action"]
    for k in required:
        if not payload.get(k):
            raise HTTPException(status_code=400, detail=f"{k} is required")
    obj = Permission(
        permission_code=payload["permission_code"],
        permission_name=payload["permission_name"],
        resource=payload["resource"],
        action=payload["action"],
        status=int(payload.get("status", 1)),
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    bump_perm_version()
    return {"permission_id": obj.permission_id}

@router.patch("/{permission_id}")
async def update_permission(
    permission_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _perm = Depends(require_permission("user:manage")),
):
    obj = await session.get(Permission, permission_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Permission not found")
    for k in ["permission_name", "resource", "action", "status"]:
        if k in payload and payload[k] is not None:
            setattr(obj, k, payload[k] if k != "status" else int(payload[k]))
    await session.commit()
    bump_perm_version()
    return {"ok": True}

@router.delete("/{permission_id}")
async def delete_permission_endpoint(permission_id: int, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    obj = await session.get(Permission, permission_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Permission not found")
    await session.delete(obj)
    await session.commit()
    bump_perm_version()
    return {"deleted": 1}

@router.get("/roles")
async def list_roles(session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    rows = (await session.execute(select(Role).where(Role.status == 1).order_by(asc(Role.role_id)))).scalars().all()
    return [{"role_id": r.role_id, "role_name": r.role_name, "role_code": r.role_code} for r in rows]

@router.post("/roles", status_code=201)
async def create_role(payload: dict, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    code = (payload.get("role_code") or "").strip()
    name = (payload.get("role_name") or "").strip()
    status_val = int(payload.get("status", 1))
    if not code or not name:
        raise HTTPException(status_code=400, detail="role_code and role_name are required")
    exists = (await session.execute(select(Role).where(Role.role_code == code))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="role_code exists")
    obj = Role(role_code=code, role_name=name, status=status_val)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    bump_perm_version()
    return {"role_id": obj.role_id}

@router.patch("/roles/{role_id}")
async def update_role(role_id: int, payload: dict, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    obj = await session.get(Role, role_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Role not found")
    if "role_name" in payload and payload["role_name"]:
        obj.role_name = payload["role_name"]
    if "status" in payload and payload["status"] is not None:
        obj.status = int(payload["status"])
    await session.commit()
    bump_perm_version()
    return {"ok": True}

@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    obj = await session.get(Role, role_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Role not found")
    await session.delete(obj)
    await session.commit()
    bump_perm_version()
    return {"deleted": 1}

@router.get("/role_permissions")
async def get_role_permissions(role_id: int, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    rows = (await session.execute(select(RolePermission).where(RolePermission.role_id == role_id))).scalars().all()
    return [rp.permission_id for rp in rows]

@router.post("/role_permissions/assign")
async def assign_role_permissions(payload: dict, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    role_id = payload.get("role_id")
    ids: List[int] = payload.get("permission_ids") or []
    if not role_id or not ids:
        raise HTTPException(status_code=400, detail="role_id and permission_ids required")
    # 清理重复后插入缺失项
    existing = (await session.execute(select(RolePermission).where(RolePermission.role_id == role_id))).scalars().all()
    existing_ids = {e.permission_id for e in existing}
    for pid in ids:
        if pid not in existing_ids:
            session.add(RolePermission(role_id=role_id, permission_id=pid))
    await session.commit()
    bump_perm_version()
    return {"assigned": len(ids)}

@router.post("/role_permissions/revoke")
async def revoke_role_permissions(payload: dict, session: AsyncSession = Depends(get_session), _perm = Depends(require_permission("user:manage"))):
    role_id = payload.get("role_id")
    ids: List[int] = payload.get("permission_ids") or []
    if not role_id or not ids:
        raise HTTPException(status_code=400, detail="role_id and permission_ids required")
    await session.execute(delete(RolePermission).where(RolePermission.role_id == role_id, RolePermission.permission_id.in_(ids)))
    await session.commit()
    bump_perm_version()
    return {"revoked": len(ids)}
