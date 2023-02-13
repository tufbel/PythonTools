#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Austin Stone
# Date    : 2022/6/6
from .imp.const import OpAction
from .imp.trans_base import TransBase, trans_request_branch


class Xa(TransBase):

    def __init__(self, phase_2_url: str, **kwargs):
        """

        @param phase_2_url:
        @param kwargs:
        """
        self.phase_2_url = phase_2_url
        super(Xa, self).__init__(**kwargs)

    async def call_branch(self, body: dict, url: str):
        branch_id = self.new_sub_branch_id()
        return await trans_request_branch(self, method="POST", body=body, branch_id=branch_id, op=OpAction, url=url)
