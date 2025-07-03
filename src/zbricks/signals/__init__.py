import inspect
import uuid
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from typing import Any, TypeVar, ClassVar
from pydantic import BaseModel

__all__ = ["BaseSignal", "Signal", "subscribe"]

# --- Type Definitions ---
S = TypeVar("S", bound="BaseSignal")

Payload = dict[str, Any] | None

def default_filter(signal: Any, payload: Payload = None) -> bool:
    return True

class Registry:
    class Subscription:
        def __init__(
            self,
            sub_id: str,
            handler: Callable[..., Any],
            call_style: str,
            filter_func: Callable[[Any, Any], bool],
            user_handler: Callable[..., Any],
        ):
            self.sub_id = sub_id
            self.handler = handler
            self.call_style = call_style
            self.filter_func = filter_func
            self.user_handler = user_handler

        def call(self, signal: Any, payload: Payload = None) -> Any:
            if self.call_style == "bald":
                return self.handler(signal)
            elif self.call_style == "loaded":
                return self.handler(signal, payload)
            elif self.call_style == "unpacked":
                return self._call_with_signature(self.handler, signal, payload)
            else:
                raise RuntimeError(f"Unknown call style: {self.call_style}")

        def passes_filter(self, signal: Any, payload: Payload) -> bool:
            return self.filter_func(signal, payload)

        @staticmethod
        def _call_with_signature(
            cb: Callable[..., Any],
            signal: Any,
            payload: Payload,
        ) -> Any:
            sig = inspect.signature(cb)
            params = list(sig.parameters.values())
            if params and params[0].name in ("self", "cls"):
                params = params[1:]
            if params:
                params = params[1:]
            if not params:
                return cb(signal)
            if (
                len(params) == 1
                and params[0].kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
            ):
                if params[0].name == "payload":
                    return cb(signal, payload)
                else:
                    if payload is None or params[0].name not in payload:
                        if params[0].default is not inspect.Parameter.empty:
                            return cb(signal, params[0].default)
                        raise TypeError(
                            f"Missing required payload key '{params[0].name}' "
                            f"for handler '{cb.__name__}'"
                        )
                    return cb(signal, payload[params[0].name])
            payload = payload or {}
            call_kwargs = {}
            for p in params:
                if p.name in payload:
                    call_kwargs[p.name] = payload[p.name]
                elif p.default is not inspect.Parameter.empty:
                    call_kwargs[p.name] = p.default
                elif (
                    p.annotation is not inspect.Parameter.empty
                    and getattr(p.annotation, "__origin__", None) is type(None)
                ):
                    call_kwargs[p.name] = None
                else:
                    raise TypeError(
                        f"Missing required payload key '{p.name}' for handler '{cb.__name__}'"
                    )
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
                if not params:
                    new_call_style = "bald"
                elif len(params) == 1 and params[0].kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                ):
                    new_call_style = (
                        "loaded" if params[0].name == "payload" else "unpacked"
                    )
                else:
                    new_call_style = "unpacked"
                subs[i] = Registry.Subscription(
                    sub_id, new, new_call_style, sub.filter_func, new
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
                if not params:
                    old_call_style = "bald"
                elif len(params) == 1 and params[0].kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                ):
                    old_call_style = (
                        "loaded" if params[0].name == "payload" else "unpacked"
                    )
                else:
                    old_call_style = "unpacked"
                subs[i] = Registry.Subscription(
                    sub_id, old, old_call_style, sub.filter_func, old
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
    if not params:
        call_style = "bald"
    elif len(params) == 1 and params[0].kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    ):
        call_style = (
            "loaded" if params[0].name == "payload" else "unpacked"
        )
    else:
        call_style = "unpacked"
    sub_id = str(uuid.uuid4())
    def unsubscribe():
        subs = get_registry().get_subs(signal_cls)
        for i, sub in enumerate(subs):
            if sub.sub_id == sub_id:
                subs.pop(i)
                break
    if once:
        def wrapped_once(sig: Any, payload: Payload = None):
            unsubscribe()
            if call_style == "bald":
                return callback(sig)
            elif call_style == "loaded":
                return callback(sig, payload)
            elif call_style == "unpacked":
                return Registry.Subscription._call_with_signature(
                    callback, sig, dict(payload) if payload else None
                )
        handler = wrapped_once
    else:
        def wrapped_cb(sig: Any, payload: Payload = None):
            if call_style == "bald":
                return callback(sig)
            elif call_style == "loaded":
                return callback(sig, payload)
            elif call_style == "unpacked":
                return Registry.Subscription._call_with_signature(
                    callback, sig, dict(payload) if payload else None
                )
        handler = wrapped_cb
    sub = Registry.Subscription(sub_id, handler, call_style, filter_func, callback)
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
