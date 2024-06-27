from flask import Flask, Blueprint, render_template
import os

def create_blueprint():
    bp = Blueprint('templating', __name__, template_folder='templates')

    @bp.route('/base')
    def base():
        return render_template('base.html')

    return bp

TMPL_FOLDER = f"{os.path.dirname(__file__)}/templates"
print(TMPL_FOLDER)

class Templating:
    def __init__(self, flask=None):
        if flask is not None:
            self.init_app(flask)

    def init_app(self, flask: Flask):
        blueprint = create_blueprint()
        flask.register_blueprint(blueprint)
        # print (flask.)
        flask.jinja_loader.searchpath.append(TMPL_FOLDER)
