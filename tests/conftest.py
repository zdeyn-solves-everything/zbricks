import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_template_dir():
    """Create a temporary directory with test templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "templates"
        template_dir.mkdir()
        
        # Create base template
        base_template = template_dir / "base.html"
        base_template.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Default Title{% endblock %}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
        """.strip())
        
        # Create child template
        child_template = template_dir / "child.html"
        child_template.write_text("""
{% extends "base.html" %}
{% block title %}Child Page{% endblock %}
{% block content %}
<h1>{{ heading }}</h1>
<p>{{ content }}</p>
{% endblock %}
        """.strip())
        
        # Create index template for router tests
        index_template = template_dir / "index.html"
        index_template.write_text("""
{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<h1>Welcome to Core</h1>
<p>Title: {{ title }}</p>
{% endblock %}
        """.strip())
        
        yield template_dir

@pytest.fixture
def create_core_index_template():
    """Create the missing index.html template in zbricks core templates."""
    core_templates_dir = Path(__file__).parent.parent / "src" / "zbricks" / "core" / "templates"
    index_template = core_templates_dir / "index.html"
    
    # Create the template if it doesn't exist
    if not index_template.exists():
        index_template.write_text("""
{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<h1>Welcome to Core</h1>
<p>Title: {{ title }}</p>
{% endblock %}
        """.strip())
        
        # Yield the path so we can clean up
        yield index_template
        
        # Clean up after test
        if index_template.exists():
            index_template.unlink()
    else:
        yield index_template

@pytest.fixture
def sample_app():
    """Create a sample ZBricks app for testing."""
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.testclient import TestClient
    from zbricks.core.templating import render_template
    
    async def test_endpoint(request):
        return render_template(request, "base.html", {"title": "Test App"})
    
    async def json_endpoint(request):
        from starlette.responses import JSONResponse
        return JSONResponse({"message": "Hello from API"})
    
    routes = [
        Route("/", endpoint=test_endpoint),
        Route("/api/test", endpoint=json_endpoint),
    ]
    
    app = Starlette(routes=routes)
    return TestClient(app)

@pytest.fixture
def starlette_app():
    """Create a basic Starlette app without ZBricks dependencies."""
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import PlainTextResponse
    
    async def hello(request):
        return PlainTextResponse("Hello, World!")
    
    routes = [Route("/", endpoint=hello)]
    return Starlette(routes=routes)

@pytest.fixture
def mock_request():
    """Create a mock HTTP request object compatible with Starlette."""
    from starlette.requests import Request
    
    def _create_request(method="GET", path="/", headers=None, body=b"", query_string=""):
        scope = {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
            "query_string": query_string.encode() if isinstance(query_string, str) else query_string,
            "root_path": "",
        }
        return Request(scope)
    
    return _create_request

@pytest.fixture
def mock_response():
    """Create a mock HTTP response object."""
    from starlette.responses import Response
    
    class MockResponse(Response):
        def __init__(self, content="", status_code=200, headers=None):
            super().__init__(content=content, status_code=status_code, headers=headers or {})
    
    return MockResponse