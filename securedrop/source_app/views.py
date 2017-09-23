from flask import Blueprint, render_template


def add_blueprints(app):
    app.register_blueprint(_main_blueprint())


def _main_blueprint():
    view = Blueprint('main', 'main')

    @view.route('/')
    def index():
        return render_template('index.html')

    return view
