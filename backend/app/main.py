from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HanboweiOJ API", version="0.1.0", description="面向青少年信息学奥赛学习的教学型 OJ API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["GET","POST","PUT","PATCH","DELETE"], allow_headers=["Authorization","Content-Type"])

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status":"ok","service":"hanbowei-oj-api"}

@app.get("/api/v1", tags=["meta"])
async def api_root() -> dict[str, str]:
    return {"name":"HanboweiOJ API","version":"0.1.0"}
