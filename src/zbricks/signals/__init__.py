import inspect
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

from pydantic import BaseModel

from zbricks.introspection import (
    build_call_kwargs as _build_call_kwargs,
)
from zbricks.introspection import (
    call_single_param as _call_single_param,
)
from zbricks.introspection import (
    get_params as _get_params,
)
from zbricks.introspection import (
    is_single_payload_param as _is_single_payload_param,
)

__all__ = ["BaseSignal", "Signal", "subscribe"]

# --- Type Definitions ---
S = TypeVar("S", bound="BaseSignal")

Payload = dict[str, Any] | None

def default_filter(signal: Any, payload: Payload = None) -> bool:
    return True

# --- Unpacked handler helpers (moved out of class for clarity and to avoid staticmethod misuse) ---
class Registry:
    class Subscription:
        def __init__(
            self,
            sub_id: str,
            handler: Callable[..., Any],
            filter_func: Callable[[Any, Any], bool],
            user_handler: Callable[..., Any],
            signal_cls: type["BaseSignal"],
            once: bool = False,
        ):
            self.sub_id = sub_id
            self.handler = handler
            self.filter_func = filter_func
            self.user_handler = user_handler
            self.signal_cls = signal_cls
            self.once = once

        def call(self, signal: Any, payload: Payload = None) -> Any:
            result = self._call_handler(signal, payload)
            if self.once:
                get_registry().remove_sub(self.signal_cls, self.sub_id)
            return result

        def _call_handler(self, signal: Any, payload: Payload = None) -> Any:
            return self.handler(signal, payload)

        def passes_filter(self, signal: Any, payload: Payload) -> bool:
            return self.filter_func(signal, payload)

    class BaldSubscription(Subscription):
        def _call_handler(self, signal: Any, payload: Payload = None) -> Any:
            return self.handler(signal)

    class LoadedSubscription(Subscription):
        def _call_handler(self, signal: Any, payload: Payload = None) -> Any:
            return self.handler(signal, payload)

    class UnpackedSubscription(Subscription):
        def _call_handler(self, signal: Any, payload: Payload = None) -> Any:
            return self._call_with_signature(self.handler, signal, payload)

        @staticmethod
        def _call_with_signature(
            cb: Callable[..., Any],
            signal: Any,
            payload: Payload,
        ) -> Any:
            sig = inspect.signature(cb)
            params = _get_params(sig)
            if not params:
                return cb(signal)
            if _is_single_payload_param(params):
                return _call_single_param(cb, signal, payload, params[0])
            call_kwargs = _build_call_kwargs(cb, params, payload)
            return cb(signal, **call_kwargs)

    def __init__(self):
        self.subscriptions: dict[type, list[Registry.Subscription]] = {}
        self.overrides: dict[type, list[tuple[str, Callable[..., Any]]]] = {}

    def ensure(self, cls: type) -> None:
        self.subscriptions.setdefault(cls, [])
        self.overrides.setdefault(cls, [])

    def get_subs(self, cls: type) -> list["Registry.Subscription"]:
        return self.subscriptions.get(cls, [])

    def get_overrides(self, cls: type) -> list[tuple[str, Callable[..., Any]]]:
        return self.overrides.get(cls, [])

    def add_sub(self, cls: type, sub: "Registry.Subscription") -> None:
        self.ensure(cls)
        self.subscriptions[cls].append(sub)

    def remove_sub(self, cls: type, sub_id: str) -> None:
        subs = self.get_subs(cls)
        for i, sub in enumerate(subs):
            if sub.sub_id == sub_id:
                subs.pop(i)
                break

    def add_override(self, cls: type, sub_id: str, handler: Callable[..., Any]) -> None:
        self.ensure(cls)
        self.overrides[cls].append((sub_id, handler))

    def pop_override(self, cls: type) -> tuple[str, Callable[..., Any]] | None:
        if self.overrides.get(cls):
            return self.overrides[cls].pop()
        return None

# Module-level singleton
_registry: Registry | None = None

def get_registry() -> Registry:
    global _registry
    if _registry is None:
        _registry = Registry()
    return _registry

# --- BaseSignal ---
class BaseSignal(BaseModel):
    # Use global registry for subscriptions and overrides
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.get_registry().ensure(cls)

    @classmethod
    def get_registry(cls) -> Registry:
        from zbricks.signals import get_registry
        return get_registry()

    def emit(self, **kwargs: Any) -> None:
        seen: set[Callable] = set()
        for cls in self.__class__.mro():
            for subscription in self.get_registry().get_subs(cls):
                if subscription.handler in seen:
                    continue
                if not subscription.passes_filter(self, kwargs):
                    continue
                seen.add(subscription.handler)
                subscription.call(self, kwargs)

    @classmethod
    def subscribe(
        cls: type[S],
        *,
        fn: Callable[[Any, Any], bool] = default_filter,
        once: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator-friendly API for subscribing a handler to a Signal class.
        Usage:
            @SomeSignal.subscribe(fn=...)
            def handler(...): ...
        Returns the handler (not an id).
        """
        def decorator(cb: Callable[..., Any]) -> Callable[..., Any]:
            _subscribe_internal(cls, cb, filter_func=fn, once=once)
            return cb
        return decorator

    @classmethod
    def unsubscribe(cls, sub_id: str) -> None:
        cls.get_registry().remove_sub(cls, sub_id)

    @classmethod
    def override(cls, sub_id: str, new: Callable[..., Any]):
        subs = cls.get_registry().get_subs(cls)
        for i, sub in enumerate(subs):
            if sub.sub_id == sub_id:
                cls.get_registry().add_override(cls, sub_id, sub.handler)
                sig = inspect.signature(new)
                params = list(sig.parameters.values())
                if params and params[0].name in ("self", "cls"):
                    params = params[1:]
                if params:
                    params = params[1:]
                sub_cls: type[Registry.Subscription]
                if not params:
                    sub_cls = Registry.BaldSubscription
                elif len(params) == 1 and params[0].kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                ):
                    if params[0].name == "payload":
                        sub_cls = Registry.LoadedSubscription
                    else:
                        sub_cls = Registry.UnpackedSubscription
                else:
                    sub_cls = Registry.UnpackedSubscription
                subs[i] = sub_cls(
                    sub_id, new, sub.filter_func, new, cls, sub.once
                )
                return

    @classmethod
    def revert_last_override(cls):
        popped = cls.get_registry().pop_override(cls)
        if not popped:
            return
        sub_id, old = popped
        subs = cls.get_registry().get_subs(cls)
        for i, sub in enumerate(subs):
            if sub.sub_id == sub_id:
                sig = inspect.signature(old)
                params = list(sig.parameters.values())
                if params and params[0].name in ("self", "cls"):
                    params = params[1:]
                if params:
                    params = params[1:]
                sub_cls: type[Registry.Subscription]
                if not params:
                    sub_cls = Registry.BaldSubscription
                elif len(params) == 1 and params[0].kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                ):
                    if params[0].name == "payload":
                        sub_cls = Registry.LoadedSubscription
                    else:
                        sub_cls = Registry.UnpackedSubscription
                else:
                    sub_cls = Registry.UnpackedSubscription
                subs[i] = sub_cls(
                    sub_id, old, sub.filter_func, old, cls, sub.once
                )
                return

    @classmethod
    @contextmanager
    def override_block(cls, old, new):
        cls.override(old, new)
        try:
            yield
        finally:
            cls.revert_last_override()

# --- Global imperative subscribe function ---
def _subscribe_internal(
    signal_cls: type[BaseSignal],
    callback: Callable[..., Any],
    *,
    filter_func: Callable[[Any, Any], bool] = default_filter,
    once: bool = False,
) -> str:
    sig = inspect.signature(callback)
    params = list(sig.parameters.values())
    if params and params[0].name in ("self", "cls"):
        params = params[1:]
    if params:
        params = params[1:]
    sub_cls: type[Registry.Subscription]
    if not params:
        sub_cls = Registry.BaldSubscription
    elif len(params) == 1 and params[0].kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    ):
        if params[0].name == "payload":
            sub_cls = Registry.LoadedSubscription
        else:
            sub_cls = Registry.UnpackedSubscription
    else:
        sub_cls = Registry.UnpackedSubscription
    sub_id = str(uuid.uuid4())
    sub = sub_cls(sub_id, callback, filter_func, callback, signal_cls, once=once)
    get_registry().add_sub(signal_cls, sub)
    return sub_id

def subscribe(
    signal_cls: type[BaseSignal],
    callback: Callable[..., Any],
    *,
    filter_func: Callable[[Any, Any], bool] = default_filter,
    once: bool = False,
) -> str:
    return _subscribe_internal(signal_cls, callback, filter_func=filter_func, once=once)

# Alias: all user-defined signals should subclass this
class Signal(BaseSignal):
    pass
