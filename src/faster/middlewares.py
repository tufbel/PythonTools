# -*- coding: utf-8 -*-
# @Time    : 2021/12/1 16:10
# @Author  : Tuffy
# @Description : FastAPI中间件
import asyncio
import contextlib
import random

import aioredis
import async_timeout
from aioredis.lock import Lock as RedisLock
from fastapi import Request
from starlette.concurrency import iterate_in_threadpool
from starlette.responses import Response, StreamingResponse

from .apps import fast_app

__all__ = ()

from src.my_tools.object_manager_tools import global_om
from src.my_tools.redis_tools.clients import RedisNamespace, RedisSentinelClient, SentinelNodeEnum
from src.settings import CACHE_CONFIG

sentinel_client: RedisSentinelClient = global_om["redis_client"]


async def wait_cache_lock_release(client: aioredis.Redis, key: bytes, sleep: float = CACHE_CONFIG["wait_lock_time"], blocking: bool = True) -> bool:
    while locked := await client.get(key) is not None and blocking:
        await asyncio.sleep(sleep)
    return locked is None


async def wait_cache_response(client: aioredis.Redis, cache_key: bytes) -> bytes:
    with contextlib.suppress(asyncio.TimeoutError):
        async with async_timeout.timeout(CACHE_CONFIG["lock_timeout"]) as cm:
            await wait_cache_lock_release(client, b"cache_locked:" + cache_key)
    return await client.get(cache_key)


@fast_app.middleware("http")
async def api_cache_response(request: Request, call_next):
    if request.method not in {"GET"}:
        return await call_next(request)

    # 如果是GET请求，则进行缓存逻辑
    http_cache_key = RedisNamespace.key(f"http_cache:{request.url.path}?{request.url.query}") \
        if request.url.query \
        else RedisNamespace.key(f"http_cache:{request.url.path}")

    with sentinel_client.get_client(SentinelNodeEnum.slave) as read_client:
        assert isinstance(read_client, aioredis.Redis)
        bytes_ = await read_client.get(http_cache_key)

        if bytes_ == b"no_cache":
            return await call_next(request)
        elif bytes_ is not None:
            return Response(content=bytes_, headers={"Content-Type": "application/json"})

    with sentinel_client.get_client(SentinelNodeEnum.master) as write_client:
        assert isinstance(write_client, aioredis.Redis)
        lock_ = RedisLock(write_client, b"cache_locked:" + http_cache_key, timeout=20, blocking=False)
        if not await lock_.acquire():
            # 加锁失败,说明已经有一个请求穿透进数据库，所以等待锁释放
            bytes_ = await wait_cache_response(read_client, http_cache_key)
            if bytes_ == b"no_cache":
                return await call_next(request)
            elif bytes_ is not None:
                return Response(content=bytes_, headers={"Content-Type": "application/json"})

        response: StreamingResponse = await call_next(request)
        if response.status_code >= 300 or response.headers["content-type"] != "application/json" or "no-cache" in response.headers:
            await write_client.set(http_cache_key, b"no_cache", ex=60)
            with contextlib.suppress(Exception):
                await lock_.release()
            return response

        response_body_bytes_ = b""
        body_iterator_ = []
        async for chunk in response.body_iterator:
            response_body_bytes_ += chunk
            body_iterator_.append(chunk)

        await write_client.set(http_cache_key, response_body_bytes_, px=random.randint(CACHE_CONFIG["min_cache_time"], CACHE_CONFIG["max_cache_time"]))
        response.body_iterator = iterate_in_threadpool(iter(body_iterator_))
        with contextlib.suppress(Exception):
            await lock_.release()
        return response
