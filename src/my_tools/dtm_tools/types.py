#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/4/1
import orjson

from .http_client import dtm_client
from .imp.const import StatusOK


async def must_gen_gid() -> str:
    resp_code_, bytes_data_ = await dtm_client.get("/api/dtmsvr/newGid")
    if resp_code_ != StatusOK or not (gid := orjson.loads(bytes_data_).get("gid")):
        raise Exception("newGid error")
    return gid
