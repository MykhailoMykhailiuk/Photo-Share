from contextlib import asynccontextmanager
from ipaddress import ip_address
import os
from pathlib import Path
from typing import Callable

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from src.repository.images import get_all_images
from src.conf.config import config
from src.database.db import get_db
from src.routes import auth, comments, images, tags, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Підключення до Redis
    """The lifespan function is a FastAPI lifecycle hook that runs before the app starts and after it stops.

    Args:
        app (FastAPI): FastAPI: Pass the fastapi instance to the function.
    """
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(r)
    app.state.redis = r

    # Yield управління життєвим циклом
    yield

    # Закриття підключення до Redis
    await r.close()
    app.state.redis = None


# Ініціалізація FastAPI з контекстним менеджером lifespan
app = FastAPI(lifespan=lifespan)


banned_ips = [
    ip_address("192.168.1.1"),
    ip_address("192.168.1.2"),
]

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ban_ips(request: Request, call_next: Callable):
    ip = request.headers.get("X-Forwarded-For", request.client.host)
    ip = ip_address(ip)
    if ip in banned_ips:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"}
        )
    response = await call_next(request)
    return response


BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("static")

app.mount("/static", StaticFiles(directory=directory), name="static")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(comments.router, prefix="/api")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    images = await get_all_images(limit, offset, db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "images": images}
    )


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """The healthchecker function is a simple function that checks if the database connection is working.
    It does this by making a request to the database and checking if it returns any results.
    If there are no results, then we know something went wrong with our connection.

    Args:
        db (AsyncSession, optional): Pass the database session to the function.

    Returns:
        Dict: A dictionary with the message key.
    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=int(os.environ.get("PORT", 8000)),
#         log_level="info",
#     )
