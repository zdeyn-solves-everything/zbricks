from zbricks.signals.core import Signal


def test_basic_signal_fire_and_forget():
    class SomethingHappened(Signal):
        who: str
        what: str

    events = []

    @SomethingHappened.subscribe
    def listener(signal, payload=None):
        events.append((signal.who, signal.what))

    s = SomethingHappened(who="zdeyn", what="conquered")
    s.emit()

    assert events == [("zdeyn", "conquered")]

    # Unsubscribe logic not yet implemented in new system
    # SomethingHappened.unsubscribe(sub_id)
