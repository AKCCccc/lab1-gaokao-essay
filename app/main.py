from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .demo import DEMO_ESSAY, DEMO_REVIEW, demo_outline
from .llm import LLMError, complete, stream
from .models import GenerateRequest, ReviewRequest
from .prompts import (
    build_direct_messages,
    build_essay_messages,
    build_outline_messages,
    build_review_messages,
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title=settings.app_name,
    description="基于 FastAPI + OpenAI SDK + 提示工程的高考满分作文生成应用",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _is_demo() -> bool:
    return settings.demo_mode or not settings.has_api_key


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _word_count(text: str) -> int:
    return len(re.sub(r"\s", "", text))


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "model": settings.model,
        "base_url": settings.base_url,
        "demo_mode": _is_demo(),
    }


@app.post("/api/outline")
async def create_outline(req: GenerateRequest) -> dict:
    if _is_demo():
        await asyncio.sleep(0.6)
        return {
            "outline": demo_outline(req.title, req.genre, req.word_count),
            "demo": True,
        }

    messages = build_outline_messages(
        req.title, req.material, req.genre, req.word_count, req.style, req.extra
    )
    try:
        outline = await complete(messages, temperature=0.7, max_tokens=1500)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"outline": outline, "demo": False}


@app.post("/api/essay")
async def create_essay(req: GenerateRequest) -> StreamingResponse:
    async def event_stream():
        try:
            if _is_demo():
                yield _sse({"type": "start", "demo": True})
                for i in range(0, len(DEMO_ESSAY), 18):
                    yield _sse({"type": "delta", "content": DEMO_ESSAY[i : i + 18]})
                    await asyncio.sleep(0.012)
                yield _sse(
                    {
                        "type": "done",
                        "word_count": _word_count(DEMO_ESSAY),
                        "demo": True,
                    }
                )
                return

            yield _sse({"type": "start", "demo": False})

            outline = req.outline.strip()
            if req.mode == "standard" and not outline:
                outline_messages = build_outline_messages(
                    req.title,
                    req.material,
                    req.genre,
                    req.word_count,
                    req.style,
                    req.extra,
                )
                outline = await complete(
                    outline_messages, temperature=0.7, max_tokens=1500
                )

            if req.mode == "fast":
                messages = build_direct_messages(
                    req.title,
                    req.material,
                    req.genre,
                    req.word_count,
                    req.style,
                    req.extra,
                )
            else:
                messages = build_essay_messages(
                    req.title,
                    req.material,
                    req.genre,
                    req.word_count,
                    req.style,
                    req.extra,
                    outline,
                )

            pieces: list[str] = []
            async for delta in stream(messages, temperature=settings.temperature):
                pieces.append(delta)
                yield _sse({"type": "delta", "content": delta})

            full_text = "".join(pieces)
            yield _sse(
                {
                    "type": "done",
                    "word_count": _word_count(full_text),
                    "demo": False,
                }
            )
        except LLMError as exc:
            yield _sse({"type": "error", "message": str(exc)})
        except Exception as exc:  # noqa: BLE001
            yield _sse({"type": "error", "message": f"生成失败：{exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/review")
async def review_essay(req: ReviewRequest) -> dict:
    if _is_demo():
        await asyncio.sleep(0.5)
        return {"review": DEMO_REVIEW, "demo": True}

    messages = build_review_messages(req.title, req.essay)
    try:
        review = await complete(messages, temperature=0.3, max_tokens=1800)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"review": review, "demo": False}
