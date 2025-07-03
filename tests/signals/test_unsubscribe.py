from zbricks.signals import Signal, subscribe


def test_unsubscribe():
    class Ping(Signal):
        id: int

    hits = []

    def handler(signal):
        hits.append(signal.id)

    sub_id = subscribe(Ping, handler)

    Ping(id=1).emit()
    Ping.unsubscribe(sub_id)
    Ping(id=2).emit()

    assert hits == [1]
