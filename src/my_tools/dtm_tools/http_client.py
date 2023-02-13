#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/3/31


from src.my_tools.aiohttp_tools import BaseHTTPClient
from src.settings import DTM_CONFIG


class DTMHttpClient(BaseHTTPClient):
    pass


DTMHttpClient.set_base_url(f"http://{DTM_CONFIG['host']}:{DTM_CONFIG['port']}")

dtm_client = DTMHttpClient()
