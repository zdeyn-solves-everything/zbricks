import inspect
from collections.abc import Callable
from typing import Any

Payload = dict[str, Any] | None

def get_params(sig: inspect.Signature) -> list[inspect.Parameter]:
    params = list(sig.parameters.values())
    if params and params[0].name in ("self", "cls"):
        params = params[1:]
    if params:
        params = params[1:]
    return params

def is_single_payload_param(params: list[inspect.Parameter]) -> bool:
    return (
        len(params) == 1
        and params[0].kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    )

def call_single_param(
    cb: Callable[..., Any],
    signal: Any,
    payload: Payload,
    param: inspect.Parameter,
) -> Any:
    if param.name == "payload":
        return cb(signal, payload)
    else:
        if payload is None or param.name not in payload:
            if param.default is not inspect.Parameter.empty:
                return cb(signal, param.default)
            raise TypeError(
                f"Missing required payload key '{param.name}' "
                f"for handler '{cb.__name__}'"
            )
        return cb(signal, payload[param.name])

def build_call_kwargs(
    cb: Callable[..., Any],
    params: list[inspect.Parameter],
    payload: Payload,
) -> dict[str, Any]:
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
    return call_kwargs
