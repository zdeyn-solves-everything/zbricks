from zbricks.signals import Signal


def test_once_subscription():
    class Boom(Signal):
        key: int

    count = 0

    @Boom.subscribe(once=True)
    def handler(signal):
        nonlocal count
        count += 1

    Boom(key=1).emit()
    Boom(key=2).emit()

    assert count == 1
