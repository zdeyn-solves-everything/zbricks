import pytest
from starlette.testclient import TestClient
from zbricks.core.templating import render_template
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route


def test_render_template_basic():
    """Test basic template rendering functionality"""
    # Create a minimal Starlette app for testing
    async def dummy_endpoint(request):
        return render_template(request, "base.html", {"title": "Test"})
    
    app = Starlette(routes=[Route("/", endpoint=dummy_endpoint)])
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    assert "Test" in response.text
    assert "Welcome to zBricks!" in response.text


def test_template_inheritance():
    """Test that templates can inherit from base templates"""
    # This would require a test template that extends base.html
    # For now, just test that the templating system works
    async def dummy_endpoint(request):
        return render_template(request, "base.html", {})
    
    app = Starlette(routes=[Route("/", endpoint=dummy_endpoint)])
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    assert "html" in response.text.lower()
    assert "Welcome to zBricks!" in response.text
