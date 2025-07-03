# Signals in zbricks

The `zbricks.signals` module provides a simple, type-safe, and extensible event system for your application. It is inspired by signal/slot patterns and observer patterns, but is designed to be easy to use and integrate with Pydantic models.

## Key Concepts

- **Signal**: A class representing an event. Subclass `Signal` to define your own events with typed fields.
- **Subscription**: Functions (callbacks) that are called when a signal is emitted. You can filter, override, or subscribe for one-time events.
- **Emit**: Trigger a signal, causing all matching subscribers to be called.

## Defining a Signal

Subclass `Signal` and define fields as you would in a Pydantic model:

```python
from zbricks.signals import Signal

class UserRegistered(Signal):
    user_id: int
    email: str
```

## Subscribing to a Signal

You can subscribe to a signal using the `@Signal.subscribe` decorator, or by calling `Signal.subscribe(callback)` directly.

```python
@UserRegistered.subscribe
def on_user_registered(signal: UserRegistered):
    print(f"User registered: {signal.user_id}, {signal.email}")
```

You can also add a filter or make the subscription one-time:

```python
@UserRegistered.subscribe(filter=lambda s, _: s.email.endswith('@example.com'))
def on_example_user(signal: UserRegistered):
    ...

@UserRegistered.subscribe(once=True)
def on_first_user(signal: UserRegistered):
    ...
```

## Emitting a Signal

Create and emit a signal by instantiating it and calling `emit()`:

```python
UserRegistered(user_id=42, email="foo@example.com").emit()
```

All matching subscribers will be called in order of subscription.

### Emitting with Additional Payload

You can pass extra keyword arguments to `emit()`. These are forwarded to the subscriber as additional payload:

```python
@UserRegistered.subscribe
def on_user_registered(signal: UserRegistered, source=None):
    print(f"User {signal.user_id} registered from {source}")

UserRegistered(user_id=1, email="a@b.com").emit(source="web")
```

The `payload` (extra kwargs) is also available to filters:

```python
@UserRegistered.subscribe(filter=lambda s, p: p and p.get('source') == 'web')
def on_web_user(signal: UserRegistered, source=None):
    ...

UserRegistered(user_id=2, email="c@d.com").emit(source="web")  # This will trigger on_web_user
```

## Unsubscribing

The `subscribe` method returns an `unsubscribe` function:

```python
def handler(signal: UserRegistered):
    ...

unsubscribe = UserRegistered.subscribe(handler)
# Later...
unsubscribe()
```

## Overriding Callbacks

You can override a previously subscribed callback:

```python
def original(signal):
    ...
def replacement(signal):
    ...
UserRegistered.override(original, replacement)
```

To temporarily override within a context:

```python
with UserRegistered.override_block(original, replacement):
    ... # replacement is active here
```

## Subscribing to an Ancestor Signal

You can subscribe to the base `Signal` class (or any ancestor), and your handler will be called for all subclasses' emissions. This is useful for logging, debugging, or global observers.

```python
from zbricks.signals import Signal

class SomeEvent(Signal):
    value: int

def log_any_signal(signal: Signal, **kwargs):
    print(f"[LOG] {signal.__class__.__name__} emitted with {signal.dict()}")

@SomeEvent.subscribe
def handle_some_event(signal: SomeEvent):
    print(f"SomeEvent handler: value={signal.value}")

Signal.subscribe(log_any_signal)

SomeEvent(value=123).emit()
# Output:
# [LOG] SomeEvent emitted with {'value': 123}
# SomeEvent handler: value=123
```

## Notes
- Subscriptions are per-signal-class, but subscribing to a base signal class will receive emissions from all its subclasses.
- All signal fields are validated using Pydantic.
- The system is designed to be thread-safe for most use cases, but heavy concurrent mutation of subscriptions is not recommended.

---

For more advanced usage, see the source code in `src/zbricks/signals/__init__.py`.
