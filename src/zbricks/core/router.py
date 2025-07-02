from starlette.routing import Route
from zbricks.core.templating import render_template

async def core_index(request):
    return render_template(request, "index.html", {"title": "Welcome (core)"})

core_routes = [
    Route("/", endpoint=core_index)
]
