# # =============================
# # app/main.py
# # =============================
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from api.routers import api_router
# from core.config import settings
# from sqlalchemy import text
# from models.database import engine

# app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[settings.CORS_ALLOW_ORIGINS],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/health")
# async def health_check():
#     return {"status": "ok"}

# @app.get("/db/ping")
# async def db_ping():
#     async with engine.begin() as conn:
#         res = await conn.execute(text("SELECT 1"))
#         _ = res.scalar_one()
#     return {"db": "ok"}


# app.include_router(api_router)

# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routers import api_router
from core.config import settings
from sqlalchemy import text
from sqlalchemy.engine import make_url
from models.database import engine

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # <-- 使用 config 中的解析列表
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/db/ping")
async def db_ping():
    try:
        url = make_url(settings.DATABASE_URL)
        host = url.host or ""
        port = url.port or ""
        database = url.database or ""
        if host and port:
            db_addr = f"{host}:{port}/{database}" if database else f"{host}:{port}"
        else:
            db_addr = database or host or ""
    except Exception:
        db_addr = ""

    try:
        async with engine.begin() as conn:
            res = await conn.execute(text("SELECT 1"))
            _ = res.scalar_one()
        return {"db": "ok", "db_addr": db_addr}
    except Exception as e:
        # 更明确的错误信息，便于运维告警与排查
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Database connection error: {e}",
                "db_addr": db_addr,
            },
        )

app.include_router(api_router)

