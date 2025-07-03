from collections.abc import Callable
from typing import Any


class FireAndForgetDispatcher:
    """
    Dispatcher that calls all handlers, ignores their return values.
    """
    def dispatch(
        self,
        signal: Any,
        handlers: list[Callable],
        payload: dict[str, Any] | None = None,
    ) -> None:
        for handler in handlers:
            handler(signal, payload)
