# -*- coding: utf-8 -*-
# @Time    : 2021/11/22 16:51
# @Author  : Tuffy
# @Description : 配置文件
import json
import os
import sys
from pathlib import Path
from typing import Dict

import dotenv
import tomlkit
from loguru import logger as __logger

# 项目根目录
PROJECT_DIR: Path = Path(__file__).parents[1]
if PROJECT_DIR.name == "lib":  # 适配cx_Freeze打包项目后根目录的变化
    PROJECT_DIR = PROJECT_DIR.parent

# 加载环境变量
dotenv.load_dotenv(PROJECT_DIR.joinpath("project_env"))
# 加载项目配置
__toml_config = json.loads(
    json.dumps(
        tomlkit.loads(PROJECT_DIR.joinpath("pyproject.toml").read_bytes())
    )
)  # 转换包装类型为Python默认类型

VERSION = __toml_config["tool"]["commitizen"]["version"]
VERSION_FORMAT = __toml_config["tool"]["commitizen"]["tag_format"].replace("$version", VERSION)
PROJECT_CONFIG = __toml_config["myproject"]

# DEBUG控制
DEV = PROJECT_CONFIG.get("dev", False)
# 生产环境控制
PROD = not DEV and PROJECT_CONFIG.get("prod", True)

DEV and __logger.info(f"[DEV] Server - Version:{VERSION_FORMAT}")
PROD and __logger.info(f"[PROD] Server - Version:{VERSION_FORMAT}")

# 服务监听
HTTP_API_LISTEN_HOST = PROJECT_CONFIG.get("http_api_listen_host", "0.0.0.0")
HTTP_API_LISTEN_PORT = int(os.getenv("HTTP_API_LISTEN_PORT", PROJECT_CONFIG.get("http_api_listen_port", 8080)))
HTTP_BASE_URL = PROJECT_CONFIG.get("http_base_url", "/api/python_tools")

# 配置日志
LOG_LEVEL = PROJECT_CONFIG["log"]["level"].upper()
LOGGER_CONFIG: Dict = {
    "handlers": {
        "console": {
            "sink": sys.stdout,
            "level": LOG_LEVEL,
            "enqueue": True,
            "backtrace": False,
            "diagnose": True,
            "catch": True,
            "filter": lambda record: "name" not in record["extra"],
        },
        "project": {
            "sink": PROJECT_DIR.joinpath(PROJECT_CONFIG["log"]["file_path"], "project.log"),
            "rotation": "10 MB",
            "retention": PROJECT_CONFIG["log"].get("retention", 10),
            "level": PROJECT_CONFIG["log"]["file_level"].upper(),
            "enqueue": True,
            "backtrace": False,
            "diagnose": True,
            "encoding": "utf-8",
            "catch": True,
            "filter": lambda record: "name" not in record["extra"],
        },
        "access_console": {
            "sink": sys.stdout,
            "level": PROJECT_CONFIG["log"]["access_console_log"].upper() if PROJECT_CONFIG["log"]["access_console_log"] else None,
            "enqueue": True,
            "backtrace": False,
            "diagnose": True,
            "catch": True,
            "filter": lambda record: record["extra"].get("name", None) == "access",
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>ACCESS</cyan> - <level>{message}</level>"
        },
        "access_file": {
            "sink": PROJECT_DIR.joinpath(PROJECT_CONFIG["log"]["file_path"], "access.log"),
            "rotation": "3 MB",
            "retention": PROJECT_CONFIG["log"].get("retention", 10),
            "level": PROJECT_CONFIG["log"]["access_file_log"].upper() if PROJECT_CONFIG["log"]["access_file_log"] else None,
            "enqueue": True,
            "backtrace": False,
            "diagnose": True,
            "encoding": "utf-8",
            "catch": True,
            "filter": lambda record: record["extra"].get("name", None) == "access",
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>ACCESS</cyan> - <level>{message}</level>"
        },
    }
}
__logger.remove()
LOGGERS_ID = {
    key: __logger.add(**handler_)
    for key, handler_ in LOGGER_CONFIG["handlers"].items()
    if handler_["level"]
}
__logger.success(f"Loggers: {LOGGERS_ID}")

DEFAULT_TIMEZONE = "UTC"
LOCAL_TIMEZONE = "Asia/Shanghai"

DATABASE_NAME = os.getenv("DATABASE_NAME", PROJECT_CONFIG["database"]["db_name"])
DATABASE_CONFIG = {
    "connections": {
        "master": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": os.getenv("MASTER_DATABASE_HOST", PROJECT_CONFIG["database"]["master"]["host"]),  # DATABASE_HOST 数据库名称环境变量根据需求修改
                "port": int(os.getenv("MASTER_DATABASE_PORT", PROJECT_CONFIG["database"]["master"]["port"])),
                "user": os.getenv("MASTER_DATABASE_USER", PROJECT_CONFIG["database"]["master"]["user"]),
                "password": os.getenv("MASTER_DATABASE_PASSWORD", PROJECT_CONFIG["database"]["master"]["password"]),
                "database": os.getenv("DATABASE_NAME", PROJECT_CONFIG["database"]["db_name"]),
                "minsize": PROJECT_CONFIG["database"]["minsize"],
                "maxsize": PROJECT_CONFIG["database"]["maxsize"],
                "charset": "utf8mb4",
                "pool_recycle": PROJECT_CONFIG["database"]["pool_recycle"],
            }
        },
        "slave": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": os.getenv("SLAVE_DATABASE_HOST", PROJECT_CONFIG["database"]["slave"]["host"]),  # DATABASE_HOST 数据库名称环境变量根据需求修改
                "port": int(os.getenv("SLAVE_DATABASE_PORT", PROJECT_CONFIG["database"]["slave"]["port"])),
                "user": os.getenv("SLAVE_DATABASE_USER", PROJECT_CONFIG["database"]["slave"]["user"]),
                "password": os.getenv("SLAVE_DATABASE_PASSWORD", PROJECT_CONFIG["database"]["slave"]["password"]),
                "database": os.getenv("DATABASE_NAME", PROJECT_CONFIG["database"]["db_name"]),
                "minsize": PROJECT_CONFIG["database"]["minsize"],
                "maxsize": PROJECT_CONFIG["database"]["maxsize"],
                "charset": "utf8mb4",
                "pool_recycle": PROJECT_CONFIG["database"]["pool_recycle"],
            }
        },
    },
    "apps": {
        "app_name": {
            "models": [
                "src.faster.routers.route_name.models",
            ],
            "default_connection": "master",
        },
    },
    "routers": ["src.my_tools.tortoise_tools.routers.WriteOrReadRouter"],
    "use_tz": True,  # 设置数据库总是存储utc时间
    "timezone": DEFAULT_TIMEZONE,  # 设置时区，数据库存储的时间时区与此设置一致，如果use_tz设置为True，那么此值应该设置为UTC
}
# DTM支持 按需开启
DATABASE_CONFIG["apps"].update(
    {
        "dtm": {
            "models": ["src.my_tools.dtm_tools.models"],
            "default_connection": "master",
        },
    }
)

# 仅开发时需要记录迁移情况
DEV and DATABASE_CONFIG["apps"].update(
    {
        "aerich": {
            "models": ["aerich.models"],
            "default_connection": "master",
        }
    }
)

# 消息队列配置
MQ_CONFIG = PROJECT_CONFIG["mq"]
if __kafka_service := os.getenv("KAFKA_SERVICE"):
    MQ_CONFIG["bootstrap_servers"] = [item_.strip() for item_ in __kafka_service.split(",")]
if __rcu_kafka_service := os.getenv("RCU_KAFKA_SERVICE"):
    MQ_CONFIG["rcu_bootstrap_servers"] = [item_.strip() for item_ in __rcu_kafka_service.split(",")]

REDIS_CONFIG = PROJECT_CONFIG["redis"]
__redis_service = os.getenv("REDIS_SENTINEL_SERVICE")
__redis_service = [(item_[0].strip(), int(item_[1])) for item_ in REDIS_CONFIG["sentinels"]["service"]] \
    if __redis_service is None \
    else [(item_[0].strip(), int(item_[1])) for item_ in (_.split(":") for _ in __redis_service.split(","))]

REDIS_CONFIG.update(
    {
        "host": os.getenv("REDIS_HOST", REDIS_CONFIG["host"]),
        "port": int(os.getenv("REDIS_PORT", REDIS_CONFIG["port"])),
        "sentinels": {
            "service": __redis_service,
            "service_name": os.getenv("REDIS_SENTINEL_SERVICE_NAME", REDIS_CONFIG["sentinels"]["service_name"]),
        }
    }
)

CACHE_CONFIG = PROJECT_CONFIG["cache_config"]

DTM_CONFIG = PROJECT_CONFIG["dtm"]
DTM_CONFIG.update(
    {
        "host": os.getenv("DTM_HOST", DTM_CONFIG["host"]),
        "port": os.getenv("DTM_PORT", DTM_CONFIG["port"]),
    }
)

HTTP_REQUEST_JSON_HEADER = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
