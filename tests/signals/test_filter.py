from zbricks.signals import Signal


def test_filtered_subscription():
    class Note(Signal):
        level: str

    levels = []

    @Note.subscribe(filter=lambda s, _: s.level == "warn")
    def handler(signal):
        levels.append(signal.level)

    Note(level="info").emit()
    Note(level="warn").emit()

    assert levels == ["warn"]
