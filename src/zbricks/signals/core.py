from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import BaseModel

from zbricks.signals.dispatchers.fire_and_forget import FireAndForgetDispatcher
from zbricks.signals.replies.ignore import IgnoreReplies


class BaseSignal(BaseModel):
    """
    Base class for all signals. Only data, no emission logic.
    """

class Signal(BaseSignal, FireAndForgetDispatcher, IgnoreReplies):
    """
    Default signal: fire-and-forget, no reply aggregation.
    """
    zbricks_handlers: ClassVar[list[Callable]] = []

    @classmethod
    def subscribe(cls, handler: Callable):
        cls.zbricks_handlers.append(handler)
        return handler

    def emit(self, **kwargs: Any) -> None:
        handlers = self.__class__.zbricks_handlers
        self.dispatch(self, handlers, kwargs)
        self.handle_replies(None)
