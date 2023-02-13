# -*- coding: utf-8 -*-
# @Time    : 2021/12/1 16:48
# @Author  : Tuffy
# @Description : FastAPI的app

from fastapi import FastAPI

from src.my_tools.kafka_tools.clients import KafkaConsumerClient, KafkaProducerClient
from src.my_tools.object_manager_tools import global_om
from src.my_tools.redis_tools.clients import RedisSentinelClient
from src.settings import HTTP_BASE_URL, MQ_CONFIG, REDIS_CONFIG, VERSION

__all__ = (
    "fast_app",
)
fast_app = FastAPI(
    title="Python Tools",
    description="python 工具",
    version=VERSION,
    openapi_url=f"{HTTP_BASE_URL}/openapi.json",
    docs_url=f"{HTTP_BASE_URL}/docs",
    redoc_url=f"{HTTP_BASE_URL}/redoc",
    swagger_ui_oauth2_redirect_url=f"{HTTP_BASE_URL}/docs/oauth2-redirect",
)
global_om.register("fast_app", fast_app)

global_om.register(
    "redis_client",
    RedisSentinelClient(
        sentinels=REDIS_CONFIG["sentinels"]["service"],
        service_name=REDIS_CONFIG["sentinels"]["service_name"],
        db=REDIS_CONFIG["db"],
        user=REDIS_CONFIG["user"],
        password=REDIS_CONFIG["password"],
        retry_interval=REDIS_CONFIG["retry_interval"],
    )
)

global_om.register(
    "web_client",
    RedisSentinelClient(
        sentinels=REDIS_CONFIG["sentinels"]["service"],
        service_name=REDIS_CONFIG["sentinels"]["service_name"],
        db=REDIS_CONFIG["ws_db"],
        user=REDIS_CONFIG["user"],
        password=REDIS_CONFIG["password"],
        retry_interval=REDIS_CONFIG["retry_interval"],
    )
)

global_om.register(
    "kafka_producer_client",
    KafkaProducerClient(
        bootstrap_servers=MQ_CONFIG["bootstrap_servers"],
        user=MQ_CONFIG["user"],
        password=MQ_CONFIG["password"],
    )
)

global_om.register(
    "kafka_consumer_client",
    KafkaConsumerClient(
        bootstrap_servers=MQ_CONFIG["bootstrap_servers"],
        user=MQ_CONFIG["user"],
        password=MQ_CONFIG["password"],
        group=MQ_CONFIG["group"],
        async_callbacks=True,
    )
)
