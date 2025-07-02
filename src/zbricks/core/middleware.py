from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import FileResponse, Response
from pathlib import Path

class StaticFallbackMiddleware:
    """
    Serves /static/* files, checking project/static first,
    then core/static. 404 if not found.
    """
    def __init__(self, app: ASGIApp):
        self.app = app
        self.project_static = Path(__file__).parent.parent / "project" / "static"
        self.core_static = Path(__file__).parent / "static"

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["path"].startswith("/static/"):
            rel_path = scope["path"].removeprefix("/static/")
            file_path = self.project_static / rel_path
            if file_path.exists() and file_path.is_file():
                response = FileResponse(str(file_path))
                await response(scope, receive, send)
                return
            file_path = self.core_static / rel_path
            if file_path.exists() and file_path.is_file():
                response = FileResponse(str(file_path))
                await response(scope, receive, send)
                return
            response = Response("Static file not found.", status_code=404)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
