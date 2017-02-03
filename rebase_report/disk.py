import jinja2
import os

def grab_file(path):
    with open(path, 'r') as f:
        return f.read()

def get_templates_dir():
    path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(path, 'templates/')

def get_schema():
    path = get_templates_dir()
    schema_path = os.path.join(path, 'rebase.sql')
    schema = open(schema_path, 'r')
    return schema.read()

def get_jinja_template():
    path = get_templates_dir()
    html_path = os.path.join(path, 'rebase.html')
    html = open(html_path, 'r')
    template = jinja2.Template(html.read())
    html.close()
    return template
