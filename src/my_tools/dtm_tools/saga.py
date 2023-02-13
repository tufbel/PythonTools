#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/3/31
from typing import Dict, List

import orjson

from .imp.trans_base import TransBase, trans_call_dtm


class Saga(TransBase):

    def __init__(self, orders: Dict[int, List[int]] = None, **kwargs):
        """

        :param orders:
        """
        kwargs.update(trans_type="saga")
        super(Saga, self).__init__(**kwargs)
        self.orders: Dict[int, List[int]] = orders

    def add(self, action: str, compensate: str, post_data: dict):
        self.steps.append({"action": action, "compensate": compensate})
        self.payloads.append(orjson.dumps(post_data).decode("utf-8"))
        return self

    def add_branch_order(self, branch: int, pre_branches: List[int]):
        self.orders[branch] = pre_branches

    def set_concurrent(self):
        self.concurrent = True

    async def submit(self):
        self.build_custom_options()
        return await trans_call_dtm(self, self, operation="submit")

    def build_custom_options(self):
        if self.concurrent:
            self.custom_data = orjson.dumps({"orders": self.orders, "concurrent": self.concurrent})
