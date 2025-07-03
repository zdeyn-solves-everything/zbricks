"""
Minimal Starlette+Jinja2 dev docs server for YAML-frontmatter Markdown docs.
"""
import glob
import os

import yaml
from jinja2 import ChoiceLoader, FileSystemLoader
from markdown_it import MarkdownIt
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates

DOCS_CONTENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "content"))
USER_THEME = os.path.abspath(os.path.join(os.path.dirname(__file__), "theme"))
LIB_THEME = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../zbricks/theme"))

md = MarkdownIt()
# Layered theme: user theme first, then library default
templates = Jinja2Templates(directory=USER_THEME)
templates.env.loader = ChoiceLoader([
    FileSystemLoader(USER_THEME),
    FileSystemLoader(LIB_THEME),
])

def parse_doc(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm)
    else:
        meta = {}
        body = text
    html = md.render(body)
    slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    title = meta.get("title") or slug
    return {"slug": slug, "title": title, "html": html, "meta": meta, "path": path}

def scan_docs():
    docs = []
    for path in glob.glob(os.path.join(DOCS_CONTENT, "**/*.md"), recursive=True):
        docs.append(parse_doc(path))
    return docs

def get_docs():
    docs = scan_docs()
    docs_by_slug = {doc["slug"]: doc for doc in docs}
    return docs, docs_by_slug

def index(request: Request):
    docs, _ = get_docs()
    return templates.TemplateResponse("index.html", {"request": request, "docs": docs})

def doc_page(request: Request):
    _, docs_by_slug = get_docs()
    slug = request.path_params["slug"]
    doc = docs_by_slug.get(slug)
    if not doc:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("doc.html", {"request": request, "doc": doc})

routes = [
    Route("/", index),
    Route("/docs/{slug}", doc_page),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("zbricks.docs.app:app", host="0.0.0.0", port=9001, reload=True)
