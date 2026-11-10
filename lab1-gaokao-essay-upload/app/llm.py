from __future__ import annotations

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .config import settings


class LLMError(RuntimeError):
    pass


def new_client() -> AsyncOpenAI:
    if not settings.has_api_key:
        raise LLMError("未配置 DEEPSEEK_API_KEY，请在 .env 中填写，或开启 DEMO_MODE。")
    return AsyncOpenAI(api_key=settings.api_key, base_url=settings.base_url)


async def complete(
    messages: list[dict],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    client = new_client()
    try:
        response = await client.chat.completions.create(
            model=settings.model,
            messages=messages,
            temperature=settings.temperature if temperature is None else temperature,
            max_tokens=settings.max_tokens if max_tokens is None else max_tokens,
        )
    except Exception as exc:  # noqa: BLE001 - 统一转为用户可读错误
        raise LLMError(f"调用大模型失败：{exc}") from exc
    finally:
        await client.close()

    content = response.choices[0].message.content
    if not content:
        raise LLMError("大模型返回了空内容，请重试。")
    return content.strip()


async def stream(
    messages: list[dict],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[str]:
    client = new_client()
    try:
        try:
            response = await client.chat.completions.create(
                model=settings.model,
                messages=messages,
                temperature=settings.temperature if temperature is None else temperature,
                max_tokens=settings.max_tokens if max_tokens is None else max_tokens,
                stream=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"调用大模型失败：{exc}") from exc

        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    finally:
        await client.close()
