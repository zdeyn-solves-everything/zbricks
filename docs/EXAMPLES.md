# Examples Guide

This document provides an overview of all zBricks examples and how to use them for learning and development.

---

## Overview

The `examples/` directory contains complete, working applications that demonstrate different aspects of the zBricks framework. Each example is a self-contained project with its own configuration and tests.

## Example Structure

Each example follows this structure:
```
examples/xx-name/
├── pyproject.toml       # Example-specific dependencies and config
├── app.py              # Main application code
├── test_app.py         # Tests for the example
├── templates/          # Example-specific templates
│   └── *.html
├── static/             # Example-specific static files
│   └── *.css, *.js, etc.
└── README.md           # Example-specific documentation (optional)
```

---

## Available Examples

### 01-hello-world

**Purpose**: Minimal example demonstrating basic zBricks usage and template inheritance.

**Features Demonstrated**:
- Basic Starlette application setup
- Template inheritance from zBricks base templates
- Simple routing with `render_template()`

**Key Files**:
- `app.py`: Single route returning rendered template
- `templates/index.html`: Extends zBricks `base.html`
- `test_app.py`: Basic endpoint and template tests

**Running**:
```bash
# From project root
uv run uvicorn examples.01-hello-world.app:app --reload

# Test
uv run pytest examples/01-hello-world/test_app.py -v
```

**Learning Points**:
- How template discovery works
- Basic template inheritance patterns
- Simple application structure

---

## Running Examples

### From Project Root (Recommended)

All examples are designed to run from the main project root:

```bash
# Navigate to project root
cd /path/to/zbricks

# Run specific example
uv run uvicorn examples.01-hello-world.app:app --reload --port 8000

# Test specific example
uv run pytest examples/01-hello-world/test_app.py -v

# Test all examples
uv run pytest examples/ -v
```

### Individual Example Development

For focused development on a single example:

```bash
# Navigate to example
cd examples/01-hello-world

# The example will import zbricks from the parent project
# No need to install zbricks separately

# Run tests (note: still run from project root for imports)
cd ../../
uv run pytest examples/01-hello-world/test_app.py -v
```

---

## Creating New Examples

### Step 1: Create Directory Structure

```bash
mkdir examples/02-your-example
cd examples/02-your-example
```

### Step 2: Create pyproject.toml

```toml
[project]
name = "zbricks-your-example"
version = "0.1.0"
description = "Description of your example"
dependencies = [
    "starlette>=0.47.1",
    "uvicorn>=0.35.0",
    # Add other dependencies as needed
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=1.0.0",
    "httpx>=0.28.1",
]

[tool.pytest.ini_options]
testpaths = ["."]
python_files = ["test_*.py"]
```

### Step 3: Create Application Code

**app.py**:
```python
from starlette.applications import Starlette
from starlette.routing import Route
from zbricks.core.templating import render_template

async def my_view(request):
    return render_template(request, "my_template.html", {
        "title": "My Example",
        "message": "Hello from my example!"
    })

routes = [
    Route("/", endpoint=my_view)
]

app = Starlette(routes=routes)
```

### Step 4: Create Templates

**templates/my_template.html**:
```html
{% extends 'base.html' %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<h2>{{ title }}</h2>
<p>{{ message }}</p>
{% endblock %}
```

### Step 5: Create Tests

**test_app.py**:
```python
import pytest
from starlette.testclient import TestClient
from app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_my_view(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "My Example" in response.text
```

### Step 6: Test and Document

```bash
# Test your example
cd ../../  # Back to project root
uv run pytest examples/02-your-example/test_app.py -v

# Run your example
uv run uvicorn examples.02-your-example.app:app --reload
```

---

## Example Categories

As the project grows, examples will be organized into categories:

### Basic Examples (01-xx)
- Hello world
- Template inheritance
- Basic routing

### Intermediate Examples (02-xx)
- Forms and validation
- Static file handling
- Custom middleware

### Advanced Examples (03-xx)
- Database integration
- Authentication
- API development

### Real-world Examples (04-xx)
- Blog application
- REST API service
- Multi-page application

---

## Best Practices for Examples

### Code Quality
- Keep examples simple and focused
- Include comprehensive tests
- Use type hints where helpful
- Follow Python naming conventions

### Documentation
- Include inline comments for complex logic
- Add docstrings for functions
- Consider adding example-specific README.md

### Testing
- Test all major functionality
- Include both positive and negative test cases
- Test template rendering and context

### Dependencies
- Keep dependencies minimal
- Only include what the example actually uses
- Document any special requirements

---

## Contributing Examples

We welcome example contributions! When creating examples:

1. **Focus on teaching**: Each example should demonstrate specific concepts
2. **Keep it simple**: Examples should be easy to understand
3. **Test thoroughly**: Include comprehensive tests
4. **Document well**: Explain what the example demonstrates
5. **Follow conventions**: Use the established structure and patterns

See `docs/DEVELOPMENT.md` for contribution guidelines.
