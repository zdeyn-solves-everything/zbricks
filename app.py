from flask import Flask, render_template
from zbricks.bricks.templating import Templating

def create_app():
    app = Flask(__name__)
    templating = Templating(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()