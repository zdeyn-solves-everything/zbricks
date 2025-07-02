import pytest
from starlette.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to the path for imports (where app.py is located)
example_dir = Path(__file__).parent.parent
sys.path.insert(0, str(example_dir))

from app import app


def test_hello_world_endpoint():
    """Test the hello world endpoint returns correct response"""
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"


def test_hello_world_content():
    """Test the hello world endpoint returns expected content"""
    client = TestClient(app)
    response = client.get("/")
    
    content = response.text
    assert "Hello World Example" in content
    assert "Hello, world!" in content
    assert "Welcome to zBricks!" in content


def test_template_inheritance():
    """Test that the example template properly inherits from base template"""
    client = TestClient(app)
    response = client.get("/")
    
    content = response.text
    # Check for base template structure
    assert "<!DOCTYPE html>" in content
    assert "<header>" in content
    assert "<main>" in content
    # Check for example-specific content
    assert "This is the minimal zbricks example" in content


@pytest.mark.asyncio
async def test_hello_world_view_function():
    """Test the hello_world view function directly"""
    from starlette.requests import Request
    from app import hello_world
    
    # Create a mock request
    scope = {
        "type": "http",
        "method": "GET", 
        "path": "/",
        "headers": [],
        "query_string": b"",
        "root_path": "",
    }
    request = Request(scope)
    response = await hello_world(request)
    
    assert response.status_code == 200
    assert "text/html" in response.media_type
