# -*- coding: utf-8 -*-
# @Time    : 2022/7/8 11:00
# @Author  : Tuffy
# @Description :
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.my_tools.singleton_tools import SingletonMeta


@dataclass
class BaseTask(metaclass=SingletonMeta):
    """
    基础定时任务
    """
    alive_flag: bool = False
    job_config: Dict = None
    job: Job = None

    __scheduler: AsyncIOScheduler = None

    def __init__(self, **kwargs):
        super().__init__()
        self.alive_flag = False
        self.job_config = kwargs
        self.job_config["id"] = self.__class__.__name__

    @classmethod
    def scheduler(cls) -> AsyncIOScheduler:
        if not isinstance(BaseTask.__scheduler, AsyncIOScheduler):
            BaseTask.__scheduler = AsyncIOScheduler()
        return cls.__scheduler

    @classmethod
    async def start_scheduler(cls):
        logger.success(f"Start BaseForwardTask scheduler")
        cls.scheduler().start()

    @classmethod
    def shutdown_scheduler(cls, wait=True):
        logger.warning(f"Shutdown BaseForwardTask scheduler ...")
        cls.scheduler().shutdown(wait=wait)

    async def job_func(self):
        pass

    def start(self):
        if self.alive_flag:
            logger.info(f"{self} is started")
            return
        self.alive_flag = True
        self.job = self.scheduler().add_job(self.job_func, **self.job_config)
        logger.success(f"Start {self}")

    def resume(self):
        if self.alive_flag:
            logger.info(f"{self} is resumed")
            return
        self.alive_flag = True
        self.job.resume()
        logger.success(f"Resume {self}")

    def stop(self):
        if not self.alive_flag:
            logger.info(f"{self} is stopped")
            return
        if isinstance(self.job, Job):
            self.job.remove()
        self.job = None
        logger.warning(f"{self} stop")
        self.alive_flag = False

    def pause(self):
        if not self.alive_flag:
            logger.info(f"{self} is pause")
            return
        self.alive_flag = False
        self.job.pause()
        logger.info(f"Pause {self}")


class DeltaIntervalTrigger(IntervalTrigger):
    def __init__(self, interval=None, **kwargs):
        super().__init__(**kwargs)
        if self.interval:
            self.interval = interval
            self.interval_length = self.interval.days * 24 * 60 * 60 + self.interval.seconds + self.interval.microseconds / 1000000.0
            if self.interval_length == 0:
                self.interval = timedelta(seconds=1)
                self.interval_length = 1
