#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Austin Stone
# Date    : 2022/6/6
import orjson
from typing import Any

from .barrier import barrier_from, BranchBarrier
from .imp.const import MsgDoBranch0, MsgDoOp
from .imp.trans_base import TransBase, trans_call_dtm, trans_request_branch
from .imp.utils import or_string


class Msg(TransBase):

    def __init__(self, delay: int, **kwargs):
        """

        @param delay: call branch, unit second
        @param kwargs:
        """
        super(Msg, self).__init__(**kwargs)
        self.delay = delay

    def add(self, action: str, post_data: Any):
        self.steps.append({"action": action})
        self.payloads.append(orjson.dumps(post_data))
        return self

    def set_delay(self, delay: int):
        self.delay = delay
        return self

    async def prepare(self, query_prepared: str):
        self.query_prepared = or_string(query_prepared, self.query_prepared)
        return await trans_call_dtm(self, self, operation="prepare")

    async def submit(self):
        self.build_custom_options()
        return await trans_call_dtm(self, self, operation="submit")

    def do_and_submit_db(self, query_prepared: str, busi_call: callable):

        async def func_busi_call(bb: BranchBarrier):
            return await bb.call_with_db(busi_call)

        return self.do_and_submit(query_prepared, func_busi_call)

    async def do_and_submit(self, query_prepared: str, busi_call: callable):
        bb, err = barrier_from(self.trans_type, self.gid, MsgDoBranch0, MsgDoOp)
        if not err:
            err = self.prepare(query_prepared)

        if not err:
            errb = await busi_call(bb)
            if errb and errb.find("FAILURE") == -1:
                _, err = await trans_request_branch(
                    self, method="GET", body={}, branch_id=self.branch_id, op=self.op,
                    url=query_prepared
                )
            if errb.find("FAILURE") != -1 or b"FAILURE" in err:
                await trans_call_dtm(self, self, operation="abort")
            elif not err:
                err = await self.submit()

            if errb:
                return errb

        return err

    def build_custom_options(self):
        if self.delay > 0:
            self.custom_data = orjson.dumps({"delay": self.delay})
