# zbricks
zBricks - build cool stuff with Starlette

---

## What is this project?

zBricks is a modern Python toolkit for building web applications using Starlette and friends. It provides:

- **Smart templating** with automatic template discovery and inheritance
- **Static file handling** with fallback support
- **Modular architecture** for clean, maintainable code
- **Built-in middleware** for common web app needs

## Quick Start

### Install the library
```bash
pip install zbricks
```

### Install with examples
```bash
pip install zbricks[examples]
```

### Basic Usage
```python
from starlette.applications import Starlette
from starlette.routing import Route
from zbricks.core.templating import render_template

async def hello_world(request):
    return render_template(request, "index.html", {"message": "Hello, world!"})

app = Starlette(routes=[Route("/", endpoint=hello_world)])
```

## Project Structure

- **`src/zbricks/`** - Main library source code
- **`tests/`** - Library tests  
- **`examples/`** - Example applications with their own tests
- **`docs/`** - Documentation

## Examples

See the `examples/` directory for complete working examples:

- **`01-hello-world/`** - Minimal example showing template inheritance
- More examples coming soon!

## Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Development workflow, contribution guidelines, and technical details
- **[Architecture](docs/ARCHITECTURE.md)** - Library architecture and design principles  
- **[Examples Guide](docs/EXAMPLES.md)** - Complete guide to all examples and how to create new ones

## License

See `LICENSE` file.
