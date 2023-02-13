# -*- coding: utf-8 -*-
# @Time    : 2021/12/1 16:09
# @Author  : Tuffy
# @Description : FastAPI 启动与关闭事件
import asyncio
import contextlib

import async_timeout
from tortoise import Tortoise

from src.my_tools.kafka_tools.clients import KafkaConsumerClient, KafkaProducerClient
from src.my_tools.redis_tools.clients import RedisSentinelClient
from src.settings import DATABASE_CONFIG, MQ_CONFIG
from src.my_tools.logging_handler import *
from src.my_tools.object_manager_tools import global_om
from .apps import fast_app

__all__ = ()


@fast_app.on_event("startup")
async def startup() -> None:
    logger.info("Startup: Message")


@fast_app.on_event("startup")
async def logger_startup() -> None:
    logging.root.handlers = [LoguruHandler()]

    for name in logging.root.manager.loggerDict.keys():
        logger_ = logging.getLogger(name)
        if "uvicorn" in name or "tortoise" in name:
            logger_.handlers = [AccessHandler()]
        elif "aiokafka" in name:
            logger_.handlers = []
        else:
            logger_.handlers = [LoguruHandler()]
        logger_.propagate = False


@fast_app.on_event("startup")
async def init_orm() -> None:
    await Tortoise.init(config=DATABASE_CONFIG)
    logger.info(f"Tortoise-ORM started: {Tortoise.apps}")


@fast_app.on_event("startup")
async def init_redis() -> None:
    redis_sentinel_: RedisSentinelClient = global_om["redis_client"]
    redis_sentinel_.start()
    async with async_timeout.timeout(10) as cm:
        await redis_sentinel_.wait_connect()
    web_sentinel_: RedisSentinelClient = global_om["web_client"]
    web_sentinel_.start()
    async with async_timeout.timeout(10) as cm:
        await web_sentinel_.wait_connect()


@fast_app.on_event("startup")
async def init_kafka():
    kafka_producer_client_: KafkaProducerClient = global_om["kafka_producer_client"]
    kafka_producer_client_.start()
    async with async_timeout.timeout(10) as cm:
        await kafka_producer_client_.wait_connect()
        await kafka_producer_client_.create_topics([{"name": topic_name_} for _, topic_name_ in MQ_CONFIG["topics"]["producer"].items()])

    topics_ = await kafka_producer_client_.get_topics()
    logger.success(f"Kafka exist topics:{topics_}")

    # kafka消费者
    kafka_consumer_client_: KafkaConsumerClient = global_om["kafka_consumer_client"]
    kafka_consumer_client_.register_callbacks()
    kafka_consumer_client_.start()
    async with async_timeout.timeout(10) as cm:
        await kafka_consumer_client_.wait_connect()


@fast_app.on_event("shutdown")
async def close_kafka():
    from src.my_tools.kafka_tools.clients import KafkaProducerClient, KafkaConsumerClient
    kafka_producer_client_: KafkaProducerClient = global_om["kafka_producer_client"]
    kafka_producer_client_.stop()
    with contextlib.suppress(asyncio.TimeoutError):
        async with async_timeout.timeout(1) as cm:
            await kafka_producer_client_.wait_stop()

    kafka_consumer_client_: KafkaConsumerClient = global_om["kafka_consumer_client"]
    kafka_consumer_client_.stop()
    with contextlib.suppress(asyncio.TimeoutError):
        async with async_timeout.timeout(1) as cm:
            await kafka_consumer_client_.wait_stop()


@fast_app.on_event("shutdown")
async def close_redis():
    redis_client_: RedisSentinelClient = global_om["redis_client"]
    redis_client_.stop()
    with contextlib.suppress(asyncio.TimeoutError):
        async with async_timeout.timeout(1) as cm:
            await redis_client_.wait_stop()


@fast_app.on_event("shutdown")
async def close_orm() -> None:
    with contextlib.suppress(asyncio.TimeoutError):
        async with async_timeout.timeout(1) as cm:
            await Tortoise.close_connections()
    logger.info("Tortoise-ORM shutdown")


@fast_app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("Shutdown: Message")
