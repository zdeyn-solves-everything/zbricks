import pytest
from zbricks import hello_world

def test_hello_world_returns_expected_value():
    assert hello_world() == "Hello, World!"