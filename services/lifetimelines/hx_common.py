from ast import pattern

from flask import render_template, render_template_string, request, session

def rm_spaces(s):
    return s.replace(' ', '_').lower() if s else s

def render_template_string_or_file(template_file=None, template_string=None, **kwargs):
    """
    Renders a template from a file or a string based on whether the request has a file or a string.
    """
    if template_string:
        return render_template_string(template_string, **kwargs)
    else:
        return render_template(template_file, **kwargs)

def hx_render_string(template_string=None, **kwargs):
    return render_template_string_or_file(template_string=template_string, **kwargs)

def hx_render_template(template_file=None, template_string=None, **kwargs):

    if request.headers.get("HX-Request"):
        return render_template_string_or_file(template_file, template_string, **kwargs)
    else:
        content = render_template_string_or_file(template_file, template_string)
        return render_template('base.html', content=content, **kwargs)
