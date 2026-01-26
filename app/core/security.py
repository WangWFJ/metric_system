# # app/core/security.py
# from datetime import datetime, timedelta, timezone
# from typing import Optional

# from jose import jwt, JWTError
# from passlib.context import CryptContext
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from models.schemas import TokenData
# from core.config import settings
# from models.database import get_session, User

# pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
# # 使用相对路径 tokenUrl（不以 / 开头），与登录接口一致
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login")


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)


# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     to_encode = data.copy()
#     expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     session: AsyncSession = Depends(get_session),
# ) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
#         username: Optional[str] = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception

#     stmt = select(User).where(User.username == token_data.username)
#     result = await session.execute(stmt)
#     user = result.scalar_one_or_none()
#     if not user or user.status != 1:
#         # status != 1 表示被锁定/禁用
#         raise credentials_exception

#     # 返回 ORM 实体（User），这样依赖方可以读 user.id、user.role_id 等
#     return user

# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_schemas import TokenData, UserOut
from core.config import settings
from models.database import get_session, User
from models.database import Role, RolePermission, Permission

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
#     """
#     JWT 的 sub 改为 user.id
#     """
#     to_encode = {"sub": str(user_id)}  # 必须是字符串
#     expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
from typing import Optional

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 的 sub 改为 user.id，exp 使用 UNIX 时间戳
    """
    to_encode: dict[str, object] = {"sub": str(user_id)}  # value 可以是 str 或 int
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = int(expire.timestamp())  # UNIX 时间戳
    from jose import jwt
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)



async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or user.status != 1:
        raise credentials_exception

    return UserOut.model_validate(user)

async def require_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or user.status != 1:
        raise credentials_exception
    if user.role_id == 1:
        return user
    role = None
    if user.role_id:
        r = await session.execute(select(Role).where(Role.role_id == user.role_id))
        role = r.scalar_one_or_none()
    if role and role.role_code == "admin":
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

_perm_cache: dict[int, tuple[set[str], int, int]] = {}
_PERM_VERSION: int = 1

def bump_perm_version():
    global _PERM_VERSION
    _PERM_VERSION += 1

def require_permission(permission_code: str):
    async def _dep(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
    ):
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or user.status != 1:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        if user.role_id == 1:
            return
        now_ts = int(datetime.now(timezone.utc).timestamp())
        codes: set[str] | None = None
        cached = _perm_cache.get(user.id)
        if cached and cached[1] > now_ts and cached[2] == _PERM_VERSION:
            codes = cached[0]
        if codes is None:
            stmt = select(Permission.permission_code).join(RolePermission, Permission.permission_id == RolePermission.permission_id).where(RolePermission.role_id == user.role_id, Permission.status == 1)
            rows = (await session.execute(stmt)).all()
            codes = {r[0] for r in rows}
            _perm_cache[user.id] = (codes, now_ts + 300, _PERM_VERSION)
        if permission_code not in codes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return _dep
