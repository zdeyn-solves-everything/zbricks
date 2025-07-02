import pytest
from starlette.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to the path for imports (where app.py is located)
example_dir = Path(__file__).parent.parent
sys.path.insert(0, str(example_dir))

from app import app

@pytest.fixture
def client():
    """Create a test client for the hello world example."""
    return TestClient(app)

def test_hello_world_root_endpoint(client):
    """Test that the root endpoint returns the expected HTML response."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Check that the response contains expected content
    content = response.text
    assert "Hello World Example" in content  # From the title block
    assert "Welcome to zBricks!" in content  # From the header block
    assert "Hello, world! This is the minimal zbricks example." in content  # From the content block
    assert "<!DOCTYPE html>" in content  # Proper HTML structure

def test_hello_world_template_inheritance(client):
    """Test that template inheritance is working correctly."""
    response = client.get("/")
    content = response.text
    
    # Check that base template structure is present
    assert "<header>" in content
    assert "<main>" in content
    assert "<title>" in content
    
    # Check that the specific content from index.html is present
    assert "Hello, world! This is the minimal zbricks example." in content

def test_hello_world_nonexistent_endpoint(client):
    """Test that non-existent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404

def test_hello_world_methods(client):
    """Test that only GET is supported for the root endpoint."""
    # GET should work
    response = client.get("/")
    assert response.status_code == 200
    
    # POST should return method not allowed
    response = client.post("/")
    assert response.status_code == 405
