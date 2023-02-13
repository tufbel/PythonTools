#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/3/31
import inspect

from .imp.const import OpCancel, OpConfirm, OpTry
from .imp.trans_base import TransBase, trans_register_branch, trans_request_branch, trans_call_dtm


def tcc_global_transaction(dtm: str, gid: str, tcc_func):
    return tcc_global_transaction2(dtm, gid, my_custom, tcc_func)


async def tcc_global_transaction2(dtm: str, gid: str, custom, tcc_func):
    tcc = Tcc(gid=gid, trans_type="tcc", dtm=dtm, branch_id="")
    try:
        _ = await custom(tcc) if inspect.iscoroutinefunction(custom) else custom(tcc)
        res = await trans_call_dtm(tcc, tcc, "prepare")
        if res:
            return res

        resp, err = await tcc_func(tcc) if inspect.iscoroutinefunction(tcc_func) else tcc_func(tcc)
        _ = await trans_call_dtm(tcc, tcc, "abort") if err else await trans_call_dtm(tcc, tcc, "submit")

    except Exception as e:
        await trans_call_dtm(tcc, tcc, "abort")
        raise e
    return


class Tcc(TransBase):

    def __init__(self,**kwargs):
        """

        :param orders:
        """
        kwargs.update(trans_type="tcc")
        super(Tcc, self).__init__(**kwargs)

    async def call_branch(self, body: dict, try_url: str, confirm_url: str, cancel_url: str):
        branch_id = self.new_sub_branch_id()
        added = {
            "data": body,
            "branch_id": branch_id,
            OpConfirm: confirm_url,
            OpCancel: cancel_url,
        }
        error = await trans_register_branch(self, added, operation="registerBranch")
        if not error:
            return None, error
        return await trans_request_branch(self, "POST", body, branch_id, OpTry, try_url)


async def my_custom(t: Tcc):
    ...
