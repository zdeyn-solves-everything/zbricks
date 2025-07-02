from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from zbricks.core.templating import render_template

async def hello_world(request: Request):
    return render_template(request, "index.html", {})

routes = [
    Route("/", endpoint=hello_world)
]

app = Starlette(routes=routes)
