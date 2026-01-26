# # =============================
# # app/api/endpoints/users.py —— 路由改为使用 id
# # =============================
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession

# from models.schemas import UserCreate, UserUpdate, UserOut, UserLogin, Token
# from models.database import get_session
# from services.user_service import (
#     create_user,
#     authenticate_user,
#     get_user_by_id,
#     get_user_by_username,
#     update_user as svc_update_user,
#     delete_user as svc_delete_user,
# )
# from core.security import get_current_user

# router = APIRouter(prefix="/api/v1/users", tags=["users"])

# @router.post("/register", response_model=UserOut, status_code=201)
# async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
#     return await create_user(user_in, session)

# @router.post("/login", response_model=Token)
# async def login(form_data: UserLogin, session: AsyncSession = Depends(get_session)):
#     token = await authenticate_user(form_data.username, form_data.password, session)
#     return {"access_token": token, "token_type": "bearer"}

# # ✅ 查询（GET）按 username
# @router.get("/{username}", response_model=UserOut)
# async def get_user(username: str, session: AsyncSession = Depends(get_session)):
#     user = await get_user_by_username(username, session)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# # ✅ 更新（PATCH）按 username
# @router.patch("/{username}", response_model=UserOut)
# async def update_user(username: str, user_in: UserUpdate, session: AsyncSession = Depends(get_session)):
#     return await svc_update_user(username, user_in, session)

# @router.delete("/{username}", status_code=204)
# async def delete_user(username: str, session: AsyncSession = Depends(get_session)):
#     await svc_delete_user(username, session)
#     return None

# app/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_schemas import UserCreate, UserUpdate, UserOut, UserLogin, Token, ChangePassword, UpdateMyProfile
from models.database import get_session, User
from services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_id,
    get_user_by_username,
    update_user as svc_update_user,
    update_user_by_id,
    delete_user as svc_delete_user,
    delete_user_by_id,
)
from core.security import get_current_user, verify_password, get_password_hash
from core.security import require_permission
from models.database import RolePermission, Permission
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("/register", response_model=UserOut, status_code=201)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    return await create_user(user_in, session)

# @router.post("/login", response_model=Token)
# async def login(form_data: UserLogin, session: AsyncSession = Depends(get_session)):
#     token = await authenticate_user(form_data.username, form_data.password, session)
#     return {"access_token": token, "token_type": "bearer"}
@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, session: AsyncSession = Depends(get_session)):
    token = await authenticate_user(form_data.username, form_data.password, session)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# GET 按 user_id 查询（优先使用 id）
@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# PATCH 按 user_id 更新（需登录）
@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_in: UserUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    # 这里可添加权限判定，例如只有本人或管理员可修改
    # 简单示例：允许本人或 role_id == 1 (假设 1 是 admin)
    if current_user.id != user_id and (current_user.role_id or 0) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to update this user")
    return await update_user_by_id(user_id, user_in, session)

# DELETE 按 user_id 删除（需登录）
@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and (current_user.role_id or 0) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to delete this user")
    await delete_user_by_id(user_id, session)
    return None

@router.post("/me/password")
async def change_my_password(
    payload: ChangePassword,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(payload.current_password, db_user.password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    if len(payload.new_password) < 8 or (payload.new_password.isdigit() or payload.new_password.isalpha()):
        raise HTTPException(status_code=400, detail="新密码需至少8位并包含字母与数字")
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")
    db_user.password = get_password_hash(payload.new_password)
    await session.commit()
    return {"message": "密码已更新"}

@router.patch("/me/profile", response_model=UserOut)
async def update_my_profile(
    payload: UpdateMyProfile,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.phone is not None:
        db_user.phone = payload.phone
    await session.commit()
    await session.refresh(db_user)
    return UserOut.model_validate(db_user)

@router.get("/me/permissions")
async def my_permissions(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    stmt = select(Permission.permission_code).join(RolePermission, Permission.permission_id == RolePermission.permission_id).where(RolePermission.role_id == current_user.role_id, Permission.status == 1)
    rows = (await session.execute(stmt)).all()
    return [r[0] for r in rows]
