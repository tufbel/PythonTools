#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/3/31
from typing import ByteString, Dict, List, Union

from ..http_client import dtm_client
from ..imp.const import StatusOK


class TransOptions:

    def __init__(
        self,
        wait_result: bool = None,
        timeout_to_fail: int = None,
        request_timeout: int = None,
        retry_interval: int = None,
        passthrough_headers: list[str] = None,
        branch_headers: Dict[str, str] = None,
        concurrent: bool = False,
        **kwargs
    ):
        """

        :param wait_result:
        :param timeout_to_fail: for trans type: xa, tcc
        :param request_timeout:  for global trans resets request timeout
        :param retry_interval:  for trans type: msg saga xa tcc
        :param passthrough_headers:
        :param branch_headers:
        :param concurrent:   for trans type: saga msg
        """
        super(TransOptions, self).__init__(**kwargs)
        self.wait_result: bool = wait_result
        self.timeout_to_fail: int = timeout_to_fail
        self.request_timeout: int = request_timeout
        self.retry_interval: int = retry_interval
        self.passthrough_headers: list = passthrough_headers
        self.branch_headers: Dict[str, str] = branch_headers
        self.concurrent: bool = concurrent


class BranchIDGen:

    def __init__(
        self,
        branch_id: str = None,
        sub_branch_id: int = None,
        **kwargs
    ):
        """

        :param branch_id:
        :param sub_branch_id:
        """
        super(BranchIDGen, self).__init__(**kwargs)
        self.branch_id: str = branch_id or ""
        self.sub_branch_id: int = sub_branch_id or 0

    def new_sub_branch_id(self):
        if self.sub_branch_id >= 99:
            raise Exception("branch id is larger than 99")
        if len(self.branch_id) >= 20:
            raise Exception("total branch id is longer than 20")
        self.sub_branch_id += 1
        return self.current_sub_branch_id()

    def current_sub_branch_id(self):
        return f"{self.branch_id}{self.sub_branch_id:02d}"


class TransBase(TransOptions, BranchIDGen):

    def __init__(
        self,
        gid: str = None,
        trans_type: str = None,
        dtm: str = "/api/dtmsvr",
        custom_data: str = None,
        steps: List[Dict[str, str]] = None,
        payloads: List[Union[str, ByteString]] = None,
        bin_payloads: List[bytes] = None,
        op: str = None,
        query_prepared: str = None,
        protocol: str = None,
        **kwargs
    ):
        """

        :param gid:
        :param trans_type:
        :param dtm:
        :param custom_data:
        :param steps:  use in MSG/SAGA
        :param payloads:  use in MSG/SAGA
        :param bin_payloads:
        :param op: used in XA/TCC
        :param query_prepared: used in MSG
        :param protocol:
        :param kwargs:
        """
        super(TransBase, self).__init__(**kwargs)
        payloads = payloads or []
        steps = steps or []
        self.gid: str = gid
        self.trans_type: str = trans_type
        self.dtm: str = dtm
        self.custom_data: Union[str, ByteString] = custom_data
        self.steps: List[Dict[str, str]] = steps
        self.payloads: List[Union[str, ByteString]] = payloads
        self.bin_payloads: List[bytes] = bin_payloads
        self.op: str = op
        self.query_prepared: str = query_prepared
        self.protocol: str = protocol

    def with_global_trans_request_timeout(self, timeout: int):
        self.request_timeout = timeout

    def to_dict(self):
        exclude_field = ["dtm", "bin_payloads", "branch_id", "sub_branch_id", "op"]
        return {k: v for k, v in self.__dict__.items() if not (k in exclude_field or v is None)}


async def trans_call_dtm(tb: TransBase, body: Union[dict, TransBase], operation: str):
    # if tb.protocol == Jrpc:
    #     body = {
    #         "jsonrpc": "2.0",
    #         "id": "no-use",
    #         "method": operation,
    #         "params": body,
    #     }
    #     resp_code_, bytes_data_ = await dtm_client.post(url="/api/dtmsvr/submit" if tb.dtm else tb.dtm, headers=HTTP_REQUEST_JSON_HEADER, data=body)
    #     return f"{resp_code_} {bytes_data_}" if resp_code_ != StatusOK else None

    resp_code_, bytes_data_ = await dtm_client.post(
        url=f"{tb.dtm}/{operation}",
        json=body if isinstance(body, dict) else body.to_dict()
    )
    if resp_code_ != StatusOK or b"FAILURE" in bytes_data_:
        return f"{resp_code_} {bytes_data_}"


async def trans_register_branch(tb: TransBase, added: Dict[str, str], operation: str):
    m = {
        "gid": tb.gid,
        "trans_type": tb.trans_type,
    }
    m.update(**added)
    return await trans_call_dtm(tb, m, operation)


async def trans_request_branch(
    t: TransBase, method: str, body: Union[dict, TransBase], branch_id: str, op: str,
    url: str
):
    if not url:
        return None, None
    params = {
        "dtm": t.dtm,
        "gid": t.gid,
        "branch_id": branch_id,
        "trans_type": t.trans_type,
        "op": op,
    }

    if t.trans_type == "xa":
        params["phase2_url"] = url

    resp_code_, bytes_data_ = await dtm_client.request(
        method, f"{url}", data=body if isinstance(body, dict) else body.to_dict(),
        params=params, headers=t.branch_headers
    )
    return bytes_data_, "" if resp_code_ == StatusOK else "", bytes_data_
