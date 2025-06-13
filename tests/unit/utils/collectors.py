"""Module collectors contains dummy collectors for testing purposes."""

import pytest
from monitor.collectors.collector import Collector


class DummyCollector(Collector):
    @classmethod
    def get_name(cls):
        return "dummy"

    async def init(self):
        pass

    async def collect(self):
        return {}


class AnotherCollector(DummyCollector):
    @classmethod
    def get_name(cls):
        return "another_dummy"


class ThirdCollector(DummyCollector):
    @classmethod
    def get_name(cls):
        return "third_dummy"


COLLECTORS = [DummyCollector, AnotherCollector, ThirdCollector]
