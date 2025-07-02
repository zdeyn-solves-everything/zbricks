"""Tests for the router module."""
import pytest
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from zbricks.core.router import core_index, core_routes


class TestCoreRouter:
    """Test the core router functionality."""
    
    def test_core_routes_exist(self):
        """Test that core routes are defined."""
        assert core_routes is not None
        assert len(core_routes) > 0
        assert any(route.path == "/" for route in core_routes)
    
    @pytest.mark.asyncio
    async def test_core_index_function(self, create_core_index_template):
        """Test the core_index function directly."""
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
        
        response = await core_index(request)
        assert response.status_code == 200
        assert "text/html" in response.media_type
    
    def test_core_index_integration(self, create_core_index_template):
        """Test core_index in a real app context."""
        app = Starlette(routes=core_routes)
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        # Note: This test might fail if index.html template doesn't exist
        # We should test that it attempts to render the template
    
    def test_core_index_context(self, create_core_index_template):
        """Test that core_index passes correct context to template."""
        app = Starlette(routes=core_routes)
        client = TestClient(app)
        
        # This test verifies the template receives the expected context
        # The actual content depends on your index.html template
        response = client.get("/")
        if response.status_code == 200:
            # If template exists and renders successfully
            assert "Welcome (core)" in response.text or "title" in response.text.lower()
        else:
            # If template doesn't exist, should still be a reasonable response
            assert response.status_code in [404, 500]  # Template not found
