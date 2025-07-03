from zbricks.signals import Signal, subscribe

def test_override_callback():
    class Ding(Signal):
        msg: str

    hits = []

    def original(signal):
        hits.append("original")

    def replacement(signal):
        hits.append("replacement")

    sub_id = subscribe(Ding, original)

    with Ding.override_block(sub_id, replacement):
        Ding(msg="x").emit()

    Ding(msg="x").emit()

    assert hits == ["replacement", "original"]
