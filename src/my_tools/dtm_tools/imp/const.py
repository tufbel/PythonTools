#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Stone
# Date    : 2022/3/31
Jrpc = "json-rpc"
JrpcCodeFailure = -32901

DefaultHTTPServer = "http://localhost:36789/api/dtmsvr"
DefaultJrpcServer = "http://localhost:36789/api/json-rpc"
DefaultGrpcServer = "localhost:36790"
BarrierTableName: str = "dtm_barrier.barrier"

StatusOK = 200

ResultFailure = "FAILURE"

ResultSuccess = "SUCCESS"

ResultOngoing = "ONGOING"

OpTry = "try"

OpConfirm = "confirm"

OpCancel = "cancel"

OpAction = "action"

OpCompensate = "compensate"

OpCommit = "commit"

OpRollback = "rollback"

DBTypeMysql = "mysql"

DBTypePostgres = "postgres"

DBTypeRedis = "redis"

JrpcCodeOngoing = -32902

MsgDoBranch0 = "00"

MsgDoBarrier1 = "01"

MsgDoOp = "msg"

XaBarrier1 = "01"

ProtocolGRPC = "grpc"

ProtocolHTTP = "http"
