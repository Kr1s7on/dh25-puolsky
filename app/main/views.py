from flask import Blueprint, render_template, jsonify

from app.models import EditableHTML

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('main/index.html', show_sidebar=False)


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)


@main.route('/health')
def health():
    """Health check endpoint for Render."""
    return jsonify(status="healthy")
