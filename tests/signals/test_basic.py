from zbricks.signals import Signal, subscribe

def test_basic_subscription_and_emit():
    class SomethingHappened(Signal):
        who: str
        what: str

    events = []

    def listener(signal, payload=None):
        events.append((signal.who, signal.what))
    sub_id = subscribe(SomethingHappened, listener)

    s = SomethingHappened(who="zdeyn", what="conquered")
    s.emit()

    assert events == [("zdeyn", "conquered")]
    SomethingHappened.unsubscribe(sub_id)

def test_imperative_global_subscribe():
    class SomethingHappened(Signal):
        who: str
        what: str

    events = []

    def listener(signal, payload=None):
        events.append((signal.who, signal.what))
    sub_id = subscribe(SomethingHappened, listener)

    s = SomethingHappened(who="zdeyn", what="conquered")
    s.emit()

    assert events == [("zdeyn", "conquered")]
    SomethingHappened.unsubscribe(sub_id)
