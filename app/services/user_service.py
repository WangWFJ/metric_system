# # =============================
# # app/services/user_service.py —— 全量改为使用 id
# # =============================
# from sqlalchemy import select
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import HTTPException, status
# from typing import Optional

# from models.database import User
# from models.schemas import UserCreate, UserUpdate, UserOut
# from core.security import get_password_hash, verify_password, create_access_token


# async def get_user_by_id(user_id: int, session: AsyncSession) -> UserOut | None:
#     result = await session.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()
#     return UserOut.model_validate(user) if user else None

# # ✅ 查询用户：按 username
# async def get_user_by_username(username: str, session: AsyncSession) -> UserOut | None:
#     result = await session.execute(select(User).where(User.username == username))
#     user = result.scalar_one_or_none()
#     return UserOut.model_validate(user) if user else None


# # ✅ 认证用：返回 ORM 实体（包含 password）
# async def get_user_entity_by_username(username: str, session: AsyncSession) -> Optional[User]:
#     result = await session.execute(select(User).where(User.username == username))
#     return result.scalar_one_or_none()


# async def create_user(user_in: UserCreate, session: AsyncSession) -> UserOut:
#     db_obj = User(
#         username=user_in.username,
#         password=get_password_hash(user_in.password),
#         name=user_in.name,
#         phone=user_in.phone,
#         role_id=user_in.role_id,
#         status=1,
#     )
#     session.add(db_obj)
#     try:
#         await session.commit()
#         await session.refresh(db_obj)
#     except IntegrityError:
#         await session.rollback()
#         raise HTTPException(status_code=400, detail="Username already exists")
#     return UserOut.model_validate(db_obj)


# # ✅ 更新用户：按 username
# async def update_user(username: str, user_in: UserUpdate, session: AsyncSession) -> UserOut:
#     result = await session.execute(select(User).where(User.username == username))
#     db_user: User | None = result.scalar_one_or_none()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")

#     if user_in.username is not None:
#         db_user.username = user_in.username
#     if user_in.password is not None:
#         db_user.password = get_password_hash(user_in.password)
#     if user_in.name is not None:
#         db_user.name = user_in.name
#     if user_in.phone is not None:
#         db_user.phone = user_in.phone
#     if user_in.role_id is not None:
#         db_user.role_id = user_in.role_id
#     if user_in.status is not None:
#         db_user.status = user_in.status

#     try:
#         await session.commit()
#         await session.refresh(db_user)
#     except IntegrityError:
#         await session.rollback()
#         raise HTTPException(status_code=400, detail="Username already exists")

#     return UserOut.model_validate(db_user)


# async def delete_user(username: str, session: AsyncSession) -> None:
#     result = await session.execute(select(User).where(User.username == username))
#     db_user: User | None = result.scalar_one_or_none()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")

#     await session.delete(db_user)
#     await session.commit()


# async def authenticate_user(username: str, password: str, session: AsyncSession) -> str:
#     user: User | None = await get_user_entity_by_username(username, session)
#     if not user or user.status != 1 or not verify_password(password, user.password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     token = create_access_token({"sub": user.username})
#     return token


# app/services/user_service.py
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional

from models.database import User
from models.user_schemas import UserCreate, UserUpdate, UserOut
from core.security import get_password_hash, verify_password, create_access_token


async def get_user_by_id(user_id: int, session: AsyncSession) -> UserOut | None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return UserOut.model_validate(user) if user else None

# 查询用户：按 username（保留兼容）
async def get_user_by_username(username: str, session: AsyncSession) -> UserOut | None:
    # 允许使用用户名或手机号查询
    result = await session.execute(select(User).where(or_(User.username == username, User.phone == username)))
    user = result.scalar_one_or_none()
    return UserOut.model_validate(user) if user else None


# 认证用：返回 ORM 实体（包含 password）
async def get_user_entity_by_username(username: str, session: AsyncSession) -> Optional[User]:
    # 登录时，支持用户名或手机号
    result = await session.execute(select(User).where(or_(User.username == username, User.phone == username)))
    return result.scalar_one_or_none()


async def create_user(user_in: UserCreate, session: AsyncSession) -> UserOut:
    db_obj = User(
        username=user_in.username,
        password=get_password_hash(user_in.password),
        phone=user_in.phone,
        role_id=user_in.role_id,
        status=1,
    )
    session.add(db_obj)
    try:
        await session.commit()
        await session.refresh(db_obj)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    return UserOut.model_validate(db_obj)


# 旧版：按 username 更新（保留兼容）
async def update_user(username: str, user_in: UserUpdate, session: AsyncSession) -> UserOut:
    result = await session.execute(select(User).where(User.username == username))
    db_user: User | None = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.username is not None:
        db_user.username = user_in.username
    if user_in.password is not None:
        db_user.password = get_password_hash(user_in.password)
    if user_in.phone is not None:
        db_user.phone = user_in.phone
    if user_in.role_id is not None:
        db_user.role_id = user_in.role_id
    if user_in.status is not None:
        db_user.status = user_in.status

    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    return UserOut.model_validate(db_user)


# ✅ 新增：按 id 更新（推荐）
async def update_user_by_id(user_id: int, user_in: UserUpdate, session: AsyncSession) -> UserOut:
    result = await session.execute(select(User).where(User.id == user_id))
    db_user: User | None = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 为避免 token 或身份混乱，禁止通过此接口修改 username
    if user_in.username is not None and user_in.username != db_user.username:
        raise HTTPException(status_code=400, detail="Changing username is not allowed via this endpoint")

    if user_in.password is not None:
        db_user.password = get_password_hash(user_in.password)
    if user_in.phone is not None:
        db_user.phone = user_in.phone
    if user_in.role_id is not None:
        db_user.role_id = user_in.role_id
    if user_in.status is not None:
        db_user.status = user_in.status

    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to constraint error")

    return UserOut.model_validate(db_user)


# 旧版：按 username 删除（保留兼容）
async def delete_user(username: str, session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.username == username))
    db_user: User | None = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(db_user)
    await session.commit()


# ✅ 新增：按 id 删除（推荐）
async def delete_user_by_id(user_id: int, session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    db_user: User | None = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(db_user)
    await session.commit()


# async def authenticate_user(username: str, password: str, session: AsyncSession) -> str:
#     user: User | None = await get_user_entity_by_username(username, session)
#     if not user or user.status != 1 or not verify_password(password, user.password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
#     token = create_access_token({"sub": user.username})
#     return token
async def authenticate_user(username: str, password: str, session: AsyncSession) -> str:
    user: User | None = await get_user_entity_by_username(username, session)
    if not user or user.status != 1 or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    # 返回 token 使用 user.id
    token = create_access_token(user.id)
    return token

