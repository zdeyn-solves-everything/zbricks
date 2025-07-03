from typing import Any

from zbricks.signals import Signal, subscribe


# --- Basic emission and subscription tests ---
def test_multiple_subscribers() -> None:
    class Multi(Signal):
        x: int
    results: list[tuple[str, int]] = []
    def a(signal, payload=None) -> None:
        results.append(("a", signal.x))
    def b(signal, payload=None) -> None:
        results.append(("b", signal.x))
    sub_id_a = subscribe(Multi, a)
    sub_id_b = subscribe(Multi, b)
    Multi(x=1).emit()
    assert results == [("a", 1), ("b", 1)]
    Multi.unsubscribe(sub_id_a)
    Multi.unsubscribe(sub_id_b)

def test_emit_with_payload() -> None:
    class Payload(Signal):
        x: int
    got: dict[str, Any] = {}
    @Payload.subscribe()
    def handler(signal, extra=None) -> None:
        got["x"] = signal.x
        got["extra"] = extra
    Payload(x=5).emit(extra="foo")
    assert got == {"x": 5, "extra": "foo"}

def test_filter_with_payload() -> None:
    class Filt(Signal):
        y: int
    seen: list[tuple[int, Any]] = []
    @Filt.subscribe(fn=lambda s, p: bool(p and p.get("flag")))
    def handler(signal, flag=None) -> None:
        seen.append((signal.y, flag))
    Filt(y=1).emit(flag=False)
    Filt(y=2).emit(flag=True)
    assert seen == [(2, True)]

# --- Ancestor subscription/observability tests ---
class AncestorSignal(Signal):
    pass

class ChildSignal(AncestorSignal):
    value: int

def test_ancestor_subscription() -> None:
    observed: list[tuple[str, Any]] = []
    def observer(signal, payload=None) -> None:
        observed.append((signal.__class__.__name__, getattr(signal, "value", None)))
    sub_id = subscribe(AncestorSignal, observer)
    ChildSignal(value=42).emit()
    AncestorSignal.unsubscribe(sub_id)
    assert observed == [("ChildSignal", 42)]

def test_signal_observes_itself() -> None:
    # Use the library to observe itself
    observed: list[str] = []
    def logger(signal, payload=None) -> None:
        observed.append(signal.__class__.__name__)
    sub_id = subscribe(Signal, logger)
    class Foo(Signal):
        pass
    Foo().emit()
    Signal.unsubscribe(sub_id)
    assert "Foo" in observed
