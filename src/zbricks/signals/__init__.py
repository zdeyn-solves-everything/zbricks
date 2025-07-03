from typing import Callable, Any, Dict, Type, Set, Optional, Mapping, TypeVar
from contextlib import contextmanager
from pydantic import BaseModel
import inspect
import uuid

__all__ = ["BaseSignal", "Signal", "subscribe"]

# --- Type Definitions ---
S = TypeVar("S", bound="BaseSignal")

Payload = Optional[Mapping[str, Any]]

def DEFAULT_FILTER(s: Any, p: Any = None) -> bool:
    return True

class Subscription:
    def __init__(
        self,
        sub_id: str,
        handler: Callable[..., Any],
        call_style: str,
        filter: Callable[[Any, Any], bool],
        user_handler: Callable[..., Any],
    ):
        self.sub_id = sub_id
        self.handler = handler
        self.call_style = call_style
        self.filter = filter
        self.user_handler = user_handler

    def call(self, signal: Any, payload: Optional[Dict[str, Any]] = None) -> Any:
        if self.call_style == 'bald':
            return self.handler(signal)
        elif self.call_style == 'loaded':
            return self.handler(signal, payload)
        elif self.call_style == 'unpacked':
            return self._call_with_signature(self.handler, signal, payload)
        else:
            raise RuntimeError(f"Unknown call style: {self.call_style}")

    def passes_filter(self, signal: Any, payload: Optional[Dict[str, Any]]) -> bool:
        return self.filter(signal, payload)

    @staticmethod
    def _call_with_signature(cb: Callable[..., Any], signal: Any, payload: Optional[Dict[str, Any]]) -> Any:
        sig = inspect.signature(cb)
        params = list(sig.parameters.values())
        if params and params[0].name in ("self", "cls"):
            params = params[1:]
        if params:
            params = params[1:]
        if not params:
            return cb(signal)
        if len(params) == 1 and params[0].kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            if params[0].name == 'payload':
                return cb(signal, payload)
            else:
                if payload is None or params[0].name not in payload:
                    if params[0].default is not inspect.Parameter.empty:
                        return cb(signal, params[0].default)
                    else:
                        raise TypeError(f"Missing required payload key '{params[0].name}' for handler '{cb.__name__}'")
                return cb(signal, payload[params[0].name])
        payload = payload or {}
        call_kwargs = {}
        for p in params:
            if p.name in payload:
                call_kwargs[p.name] = payload[p.name]
            elif p.default is not inspect.Parameter.empty:
                call_kwargs[p.name] = p.default
            elif (p.annotation is not inspect.Parameter.empty and getattr(p.annotation, '__origin__', None) is Optional):
                call_kwargs[p.name] = None
            else:
                raise TypeError(f"Missing required payload key '{p.name}' for handler '{cb.__name__}'")
        return cb(signal, **call_kwargs)

# --- BaseSignal ---
class BaseSignal(BaseModel):
    # Use per-class storage for subscriptions and overrides
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        setattr(cls, '_subscriptions', {})
        setattr(cls, '_overrides', [])

    def emit(self, **kwargs: Any) -> None:
        seen: Set[Callable] = set()
        for cls in self.__class__.mro():
            for subscription in getattr(cls, '_subscriptions', {}).get(cls, []):
                if subscription.handler in seen:
                    continue
                if not subscription.passes_filter(self, kwargs):
                    continue
                seen.add(subscription.handler)
                subscription.call(self, kwargs)

    @classmethod
    def subscribe(
        cls: Type[S],
        *,
        filter: Callable[[Any, Any], bool] = DEFAULT_FILTER,
        once: bool = False
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator-friendly API for subscribing a handler to a Signal class.
        Usage:
            @SomeSignal.subscribe(filter=...)
            def handler(...): ...
        Returns the handler (not an id).
        """
        def decorator(cb: Callable[..., Any]) -> Callable[..., Any]:
            _subscribe_internal(cls, cb, filter=filter, once=once)
            return cb
        return decorator

    @classmethod
    def unsubscribe(cls, sub_id: str) -> None:
        for subs in getattr(cls, '_subscriptions').values():
            for i, sub in enumerate(subs):
                if sub.sub_id == sub_id:
                    subs.pop(i)
                    return

    @classmethod
    def override(cls, sub_id: str, new: Callable[..., Any]):
        for subs in getattr(cls, '_subscriptions').values():
            for i, sub in enumerate(subs):
                if sub.sub_id == sub_id:
                    getattr(cls, '_overrides').append((sub_id, sub.handler))
                    sig = inspect.signature(new)
                    params = list(sig.parameters.values())
                    if params and params[0].name in ("self", "cls"):
                        params = params[1:]
                    if params:
                        params = params[1:]
                    if not params:
                        new_call_style = 'bald'
                    elif len(params) == 1 and params[0].kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                        if params[0].name == 'payload':
                            new_call_style = 'loaded'
                        else:
                            new_call_style = 'unpacked'
                    else:
                        new_call_style = 'unpacked'
                    subs[i] = Subscription(sub_id, new, new_call_style, sub.filter, new)
                    return

    @classmethod
    def revert_last_override(cls):
        if not getattr(cls, '_overrides'):
            return
        sub_id, old = getattr(cls, '_overrides').pop()
        for subs in getattr(cls, '_subscriptions').values():
            for i, sub in enumerate(subs):
                if sub.sub_id == sub_id:
                    sig = inspect.signature(old)
                    params = list(sig.parameters.values())
                    if params and params[0].name in ("self", "cls"):
                        params = params[1:]
                    if params:
                        params = params[1:]
                    if not params:
                        old_call_style = 'bald'
                    elif len(params) == 1 and params[0].kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                        if params[0].name == 'payload':
                            old_call_style = 'loaded'
                        else:
                            old_call_style = 'unpacked'
                    else:
                        old_call_style = 'unpacked'
                    subs[i] = Subscription(sub_id, old, old_call_style, sub.filter, old)
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
    signal_cls: Type[BaseSignal],
    callback: Callable[..., Any],
    *,
    filter: Callable[[Any, Any], bool] = DEFAULT_FILTER,
    once: bool = False
) -> str:
    sig = inspect.signature(callback)
    params = list(sig.parameters.values())
    if params and params[0].name in ("self", "cls"):
        params = params[1:]
    if params:
        params = params[1:]
    if not params:
        call_style = 'bald'
    elif len(params) == 1 and params[0].kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
        if params[0].name == 'payload':
            call_style = 'loaded'
        else:
            call_style = 'unpacked'
    else:
        call_style = 'unpacked'
    sub_id = str(uuid.uuid4())
    def unsubscribe():
        subs = getattr(signal_cls, '_subscriptions').get(signal_cls, [])
        for i, sub in enumerate(subs):
            if sub.sub_id == sub_id:
                subs.pop(i)
                break
    if once:
        def wrapped_once(sig: Any, payload: Payload = None):
            unsubscribe()
            if call_style == 'bald':
                return callback(sig)
            elif call_style == 'loaded':
                return callback(sig, payload)
            elif call_style == 'unpacked':
                return Subscription._call_with_signature(callback, sig, dict(payload) if payload else None)
        handler = wrapped_once
    else:
        def wrapped_cb(sig: Any, payload: Payload = None):
            if call_style == 'bald':
                return callback(sig)
            elif call_style == 'loaded':
                return callback(sig, payload)
            elif call_style == 'unpacked':
                return Subscription._call_with_signature(callback, sig, dict(payload) if payload else None)
        handler = wrapped_cb
    sub = Subscription(sub_id, handler, call_style, filter, callback)
    getattr(signal_cls, '_subscriptions').setdefault(signal_cls, []).append(sub)
    return sub_id

def subscribe(
    signal_cls: Type[BaseSignal],
    callback: Callable[..., Any],
    *,
    filter: Callable[[Any, Any], bool] = DEFAULT_FILTER,
    once: bool = False
) -> str:
    return _subscribe_internal(signal_cls, callback, filter=filter, once=once)

# Alias: all user-defined signals should subclass this
class Signal(BaseSignal):
    pass
