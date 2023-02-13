#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/3/31
import inspect
from loguru import logger
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import BaseORMException
from tortoise.transactions import in_transaction
from .imp.const import MsgDoOp, OpCancel, OpCompensate, MsgDoBranch0, OpRollback, MsgDoBarrier1, BarrierTableName
from ...settings import DATABASE_NAME


async def insert_barrier(
    tconn: BaseDBAsyncClient, trans_type: str, gid: str, branch_id: str, op: str, barrier_id: str,
    reason: str
):
    if op == "":
        return 0, False
    sql = f"insert ignore into {DATABASE_NAME}.dtm_barrier (trans_type, gid, branch_id," \
          f" op, barrier_id, reason) values(%s,%s,%s,%s,%s,%s)"

    try:
        affect, result = await tconn.execute_query(sql, [trans_type, gid, branch_id, op, barrier_id, reason, ], )
        return affect, False
    except BaseORMException:
        return 0, True


def barrier_from(trans_type: str, gid: str, branch_id: str, op: str):
    ti = BranchBarrier(trans_type=trans_type, gid=gid, branch_id=branch_id, op=op)
    if ti.trans_type == "" or ti.gid == "" or ti.branch_id == "" or ti.op == "":
        return None, f"invalid trans info {ti}"
    return ti, None


class BranchBarrier:

    def __init__(
        self,
        trans_type: str = None,
        gid: str = None,
        branch_id: str = None,
        op: str = None,
        barrier_id: int = None
    ):
        """

        :param trans_type:
        :param gid:
        :param branch_id:
        :param op:
        :param barrier_id:
        """
        self.trans_type: str = trans_type or ""
        self.gid: str = gid or ""
        self.branch_id: str = branch_id or ""
        self.op: str = op or ""
        self.barrier_id: int = barrier_id or 0

    def new_barrier_id(self):
        self.barrier_id += 1
        return f"{self.barrier_id:02d}"

    async def call(self, tconn: BaseDBAsyncClient, callback: callable, *args, **kwargs):

        bid = self.new_barrier_id()
        origin_op = {
            "cancel": "try",
            "compensate": "action",
        }.get(self.op, "")

        origin_affected, oerr = await insert_barrier(
            tconn=tconn,
            trans_type=self.trans_type,
            gid=self.gid,
            branch_id=self.branch_id,
            op=origin_op,
            barrier_id=bid,
            reason=self.op,
        )
        current_affected, rerr = await insert_barrier(
            tconn=tconn,
            trans_type=self.trans_type,
            gid=self.gid,
            branch_id=self.branch_id,
            op=self.op,
            barrier_id=bid,
            reason=self.op,
        )

        logger.debug(f"origin_barrier_obj: {origin_affected} current_barrier_obj: {current_affected}")

        if (not rerr) and self.op == MsgDoOp and (not current_affected):
            return "DUPLICATED"

        if not rerr:
            rerr = oerr

        if (self.op == OpCancel or self.op == OpCompensate) and origin_affected or not current_affected:
            return rerr
        if not rerr:
            # 执行回调
            if inspect.iscoroutinefunction(callback):
                rerr = await callback(tconn, *args, **kwargs)
            else:
                rerr = callback(tconn, *args, **kwargs)

        return rerr

    async def call_with_db(self, busi_call: callable, *args, **kwargs):
        try:
            async with in_transaction("master") as tconn:
                err = await self.call(tconn, busi_call, *args, **kwargs)
            return err
        except Exception as e:
            # logger.error(e)
            raise e

    async def query_prepared(self, tconn: BaseDBAsyncClient):
        _, err = await insert_barrier(
            tconn, self.trans_type, self.gid, MsgDoBranch0, MsgDoOp, MsgDoBarrier1,
            OpRollback
        )
        reason = None
        if not err:
            sql = f"select reason from {BarrierTableName} where gid=%s and branch_id=%s and op=%s and barrier_id=%s"
            try:
                affect, result = await tconn.execute_query(sql, [self.gid, MsgDoBranch0, MsgDoOp, MsgDoBarrier1, ], )
                reason = result[0].get("reason")
                err = False
            except BaseORMException:
                err = True

        if reason == OpRollback:
            return "FAILURE"
        return err

    def __str__(self):
        return f"transInfo: {self.trans_type} {self.gid} {self.branch_id} {self.op}"
