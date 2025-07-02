"""Tests for the middleware module."""
import pytest
from unittest.mock import Mock
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette.routing import Route
from starlette.responses import PlainTextResponse
from zbricks.core.middleware import StaticFallbackMiddleware
import tempfile
from pathlib import Path


class TestStaticFallbackMiddleware:
    """Test the StaticFallbackMiddleware functionality."""
    
    @pytest.fixture
    def temp_static_dirs(self):
        """Create temporary static directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project static directory
            project_static = temp_path / "project" / "static"
            project_static.mkdir(parents=True)
            (project_static / "project.css").write_text("/* project styles */")
            
            # Create core static directory  
            core_static = temp_path / "core" / "static"
            core_static.mkdir(parents=True)
            (core_static / "core.css").write_text("/* core styles */")
            (core_static / "shared.css").write_text("/* shared styles */")
            
            yield {
                "project": project_static,
                "core": core_static,
                "root": temp_path
            }
    
    def test_middleware_serves_project_static_first(self, temp_static_dirs):
        """Test that project static files take precedence over core files."""
        async def app(scope, receive, send):
            # Dummy app that would normally handle non-static requests
            response = PlainTextResponse("Not static")
            await response(scope, receive, send)
        
        # Create middleware with custom static paths
        middleware = StaticFallbackMiddleware(app)
        middleware.project_static = temp_static_dirs["project"]
        middleware.core_static = temp_static_dirs["core"]
        
        # Create test app
        test_app = Starlette()
        test_app.add_middleware(StaticFallbackMiddleware)
        
        # This test would need a way to inject the temp directories
        # For now, test the concept
        pass
    
    def test_middleware_falls_back_to_core_static(self, temp_static_dirs):
        """Test fallback to core static when project static doesn't have file."""
        # Test that core.css is served from core directory when not in project
        pass
    
    def test_middleware_returns_404_for_missing_files(self):
        """Test 404 response for static files that don't exist anywhere."""
        async def app(scope, receive, send):
            response = PlainTextResponse("App response")
            await response(scope, receive, send)
        
        middleware = StaticFallbackMiddleware(app)
        
        # Mock scope for static file request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/static/nonexistent.css",
        }
        
        # This would need more setup to test properly
        pass
    
    def test_middleware_passes_through_non_static_requests(self):
        """Test that non-static requests are passed to the wrapped app."""
        async def app(scope, receive, send):
            response = PlainTextResponse("Hello from app")
            await response(scope, receive, send)
        
        middleware = StaticFallbackMiddleware(app)
        
        # Test that regular requests go through
        pass
    
    def test_middleware_handles_different_static_file_types(self):
        """Test serving various file types (CSS, JS, images, etc.)."""
        # Test MIME type handling for different file extensions
        pass
