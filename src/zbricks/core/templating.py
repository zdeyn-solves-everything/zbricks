from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape
from starlette.responses import HTMLResponse
from pathlib import Path
import os
import inspect

def get_template_environment_for_caller():
    # Get the calling frame to determine where the render_template was called from
    frame = inspect.currentframe()
    caller_frame = None
    if frame and frame.f_back and frame.f_back.f_back:
        caller_frame = frame.f_back.f_back  # Go up two frames to get the actual caller
    
    # Find zbricks core templates
    zbricks_core = Path(__file__).parent / "templates"
    
    template_paths = []
    
    # Add caller's templates directory first (highest priority)
    if caller_frame:
        caller_file = Path(caller_frame.f_globals.get('__file__', ''))
        if caller_file.exists():
            caller_templates = caller_file.parent / "templates"
            if caller_templates.exists():
                template_paths.append(str(caller_templates))
    
    # Add zbricks core templates as fallback
    if zbricks_core.exists():
        template_paths.append(str(zbricks_core))
    
    return Environment(
        loader=ChoiceLoader([FileSystemLoader(p) for p in template_paths]),
        autoescape=select_autoescape(['html', 'xml'])
    )

def render_template(request, template_name, context=None):
    if context is None:
        context = {}
    context = dict(context)
    context["request"] = request
    
    # Create environment dynamically based on caller location
    env = get_template_environment_for_caller()
    template = env.get_template(template_name)
    content = template.render(context)
    return HTMLResponse(content)
