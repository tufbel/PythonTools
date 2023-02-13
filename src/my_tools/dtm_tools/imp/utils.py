#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author : Austin Stone
# Date    : 2022/6/6

def or_string(*args):
    for s in args:
        if s != "":
            return s
    return ""
