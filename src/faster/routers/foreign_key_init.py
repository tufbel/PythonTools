# -*- coding: utf-8 -*-
# @Time    : 2022/7/25 16:04
# @Author  : Tuffy
# @Description : 

from src.settings import DATABASE_CONFIG
from tortoise import Tortoise

# 在模型schema初始化前，调用外键关联
# 1.这将调用Tortoise子带的外键关联，如果想自定义外键关联的字段，需要自己写Pydantic
# 2.如果想偷懒只要能返回外键关联信息，则使用此方法
# 在模型schema初始化前，调用外键关联
# 1.这将调用Tortoise子带的外键关联，如果想自定义外键关联的字段，需要自己写Pydantic
# 2.如果想偷懒只要能返回外键关联信息，则使用此方法
Tortoise.init_models(DATABASE_CONFIG["apps"]["db_name"]["models"], "db_name")
