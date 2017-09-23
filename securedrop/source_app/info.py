from flask import Blueprint, render_template


def make_blueprint():
    view = Blueprint('info', __name__)

    @view.route('/tor2web-warning')
    def tor2web_warning():
        return render_template("tor2web-warning.html")

    return view
