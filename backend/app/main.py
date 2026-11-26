import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 从环境变量读取允许跨域访问的前端地址。
# 如果没有设置环境变量，则使用三套本地开发环境的默认地址。
_default_cors_origins = "http://localhost:3000,http://localhost:3001,http://localhost:3002"

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_cors_origins).split(",")
    if origin.strip()
]

# 不允许空来源配置，也不允许使用通配符。
if not cors_origins or "*" in cors_origins:
    raise ValueError("CORS_ORIGINS must contain explicit allowed origins")


app = FastAPI(
    title="HanboweiOJ API",
    version="0.1.0",
    description="面向青少年信息学奥赛学习的教学型 OJ API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "hanbowei-oj-api"}


@app.get("/api/v1", tags=["meta"])
async def api_root() -> dict[str, str]:
    return {"name": "HanboweiOJ API", "version": "0.1.0"}
