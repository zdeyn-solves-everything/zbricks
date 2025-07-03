"""
Serve the documentation live from source using Starlette and Jinja2.

Usage:
    python -m zbricks.docs.serve [--host 0.0.0.0] [--port 9001] [--src /path/to/docs/content] \
        [--theme /path/to/theme] [--reload]
"""
import argparse
import os
import sys
import yaml
import markdown_it
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from jinja2 import FileSystemLoader, ChoiceLoader
import uvicorn


def crawl_docs(src_dir):
    """Crawl the docs source directory for Markdown/YAML files and return a docs index."""
    docs = []
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if fname.endswith(".md"):
                path = os.path.join(root, fname)
                rel_path = os.path.relpath(path, src_dir)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Parse YAML frontmatter if present
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        meta = yaml.safe_load(parts[1])
                        body = parts[2].lstrip()
                    else:
                        meta = {}
                        body = content
                else:
                    meta = {}
                    body = content
                # Prefer explicit slug, else use rel_path without .md
                slug = meta.get("slug") or rel_path[:-3] if rel_path.endswith(".md") else rel_path
                docs.append({"meta": meta, "body": body, "slug": slug, "title": meta.get("title") or os.path.splitext(os.path.basename(rel_path))[0]})
    return {doc["slug"]: doc for doc in docs}


def create_app(src_dir, theme_dir):
    docs = crawl_docs(src_dir)
    # Layered template loading: user theme, then default theme
    loaders = []
    if theme_dir and os.path.isdir(theme_dir):
        loaders.append(FileSystemLoader(theme_dir))
    # Always add the default theme (assume it's in zbricks/themes/_default)
    default_theme = os.path.join(os.path.dirname(__file__), "../../themes/_default")
    loaders.append(FileSystemLoader(default_theme))
    templates = Jinja2Templates(directory=theme_dir or default_theme)
    templates.env.loader = ChoiceLoader(loaders)
    md = markdown_it.MarkdownIt()

    async def index(request):
        # List all docs
        doc_list = [
            {"slug": k, "title": v["title"]}
            for k, v in docs.items()
        ]
        return templates.TemplateResponse(
            request, "index.html", {"docs": doc_list}
        )

    async def doc_page(request):
        slug = request.path_params["slug"]
        if slug in docs:
            doc = docs[slug]
            html = md.render(doc["body"])
            return templates.TemplateResponse(
                request,
                "doc.html",
                {
                    "doc": doc,  # Pass the whole doc object
                    "meta": doc["meta"],
                    "content": html,
                    "slug": slug,
                },
            )
        return Response("Not found", status_code=404)

    routes = [
        Route("/", index),
        Route("/{slug}", doc_page),
    ]
    app = Starlette(routes=routes, middleware=[Middleware(SessionMiddleware, secret_key="docs")])
    app.state.docs = docs
    app.state.src_dir = src_dir
    app.state.theme_dir = theme_dir
    app.state.templates = templates
    app.state.md = md
    return app


def watch_and_reload(app, src_dir):
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        sys.stderr.write(
            "watchdog is required for --reload. Install with 'pip install watchdog'\n"
        )
        sys.exit(1)
    class ReloadHandler(FileSystemEventHandler):
        def on_any_event(self, event):
            app.state.docs = crawl_docs(src_dir)
            sys.stdout.write("[docs] Reloaded docs context\n")
    observer = Observer()
    observer.schedule(ReloadHandler(), src_dir, recursive=True)
    observer.start()
    sys.stdout.write(f"[docs] Watching {src_dir} for changes...\n")
    return observer


def main():
    parser = argparse.ArgumentParser(description="Serve docs live from source.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9001, help="Port to bind (default: 9001)")
    parser.add_argument("--src", default=None, help="Docs source directory (default: ./src/docs/content)")
    parser.add_argument("--theme", default=None, help="Theme directory (default: ./src/docs/theme)")
    parser.add_argument("--reload", action="store_true", help="Watch docs source and reload on change")
    args = parser.parse_args()
    src_dir = args.src or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs/content"))
    theme_dir = args.theme or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs/theme"))
    if not os.path.isdir(src_dir):
        sys.stderr.write(f"Could not find docs source directory: {src_dir}\n")
        sys.exit(1)
    app = create_app(src_dir, theme_dir)
    observer = None
    if args.reload:
        observer = watch_and_reload(app, src_dir)
    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        if observer:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    main()
