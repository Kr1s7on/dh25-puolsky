# Let templates be found in subdirectories of app/templates
def get_template_path(template_name):
    # This function helps ensure templates can be found even if there are directory issues
    if not template_name.endswith('.html'):
        template_name += '.html'
    return template_name

def init_template_utils(app):
    """Initialize template utilities."""
    app.jinja_env.globals['get_template'] = get_template_path
