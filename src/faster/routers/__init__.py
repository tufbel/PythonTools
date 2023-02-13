# -*- coding: utf-8 -*-
# @Time    : 2023/2/13 16:27
# @Author  : Tuffy
# @Description : 

__all__ = ()

from fastapi import Request
from fastapi.responses import ORJSONResponse
from loguru import logger
from pydantic import BaseModel

# 若需要自动生成外键关联，则需要在模型schema初始化前，调用外键关联
from . import foreign_key_init

from src.settings import HTTP_BASE_URL
from .. import fast_app


class FastAPIStatus(BaseModel):
    message: str = "FastAPI success!"


@fast_app.get(
    f"{HTTP_BASE_URL}",
    summary="验活",
    response_class=ORJSONResponse,
    response_model=FastAPIStatus,
    response_description="验活成功响应",
)
async def home(request: Request):
    logger.debug(f"Request from [{request.client}]")
    return FastAPIStatus()
