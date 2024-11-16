from flask import render_template, request

def hx_render_template(template, **kwargs):
    if request.headers.get("HX-Request"):
        return render_template(template, **kwargs)
    else:
        return render_template('base.html', content=render_template(template, **kwargs))
