#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/4/1

from tortoise import models, fields


class Barrier(models.Model):
    id = fields.IntField(pk=True, description="自增主键")
    trans_type = fields.CharField(max_length=20, null=True, description="事务模式， 一般为saga")
    gid = fields.CharField(max_length=50, null=True, description="全局事务gid")
    branch_id = fields.CharField(max_length=20, null=True, description="子事务id")
    op = fields.CharField(max_length=50, null=True, description="操作 operation")
    barrier_id = fields.CharField(max_length=20, null=True, description="屏障id， 自动生成")
    reason = fields.CharField(max_length=100, null=True, description="描述")
    update_time = fields.DatetimeField(auto_now=True)
    create_time = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = f"dtm_barrier"
        unique_together = ("gid", "branch_id", "op", "barrier_id")
