# -*- coding: utf-8 -*-
# @Time    : 2021/12/1 16:11
# @Author  : Tuffy
# @Description : FastAPI 的异常捕获
from fastapi import Request
from fastapi.responses import ORJSONResponse

from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import BaseModel, ValidationError as PydanticValidationError
from tortoise.exceptions import DoesNotExist, IntegrityError, ValidationError as TortoiseValidationError

from .apps import fast_app

__all__ = ("HTTPError",)


class HTTPError(BaseModel):
    detail: str


@fast_app.exception_handler(HTTPException)
async def fast_http_exception_handler(request: Request, exc: HTTPException):
    """
    覆盖fastapi默认的HTTPException
    """
    return ORJSONResponse(status_code=exc.status_code, content=exc.detail)


@fast_app.exception_handler(DoesNotExist)
async def doesnotexist_exception_handler(request: Request, exc: DoesNotExist):
    """
    捕获获取数据库获取数据失败的异常
    """
    return ORJSONResponse(
        status_code=404,
        content={"detail": [{"loc": [], "msg": str(exc)}]},
    )


@fast_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    捕获请求体数据的验证错误（FastAPI封装的验证错误）
    """
    return ORJSONResponse(
        status_code=422,
        content={"detail": [{"loc": [], "msg": exc.errors()}]},
    )


@fast_app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    """
    捕获请求体数据的验证错误（FastAPI未封装的验证错误）
    """
    return ORJSONResponse(
        status_code=422,
        content={"detail": [{"loc": [], "msg": exc.errors()}]},
    )


@fast_app.exception_handler(TortoiseValidationError)
async def tortoise_validation_exception_handler(request: Request, exc: TortoiseValidationError):
    """
    捕获数据库更新数据时的验证错误（model中验证器抛出）
    """
    return ORJSONResponse(
        status_code=422,
        content={"detail": [{"loc": [], "msg": "Attributes of the added object conflicted", "type": "ValidationError"}]},
    )


@fast_app.exception_handler(IntegrityError)
async def integrityerror_exception_handler(request: Request, exc: IntegrityError):
    """
    捕获数据库更新数据时的完整性错误（model的数据不完整）
    包括插入数据时数据重复
    """
    return ORJSONResponse(
        status_code=422,
        content={"detail": [{"loc": [], "msg": "Required attributes are missing", "type": "IntegrityError"}]},
    )


@fast_app.exception_handler(ValueError)
async def database_validation_exception_handler(request: Request, exc: ValueError):
    """
    捕获数据库更新数据时的验证错误（数据库写入错误抛出）
    """
    return ORJSONResponse(
        status_code=422,
        content={"detail": [{"loc": [], "msg": str(exc), "type": "ValueError"}]},
    )
