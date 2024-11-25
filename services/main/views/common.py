from flask import render_template, request

# from services.main.views.configurations.editable_entities import get_editable_entity_names
from .configurations.editable_entities import get_editable_entity_names
def hx_render_template(template, **kwargs):
    # kwargs['configs'] = get_editable_entity_names()
    if request.headers.get("HX-Request"):
        return render_template(template, **kwargs)
    else:
        return render_template('base.html', 
                               content=render_template(template, **kwargs), 
                               ctx={"configs":get_editable_entity_names()} )
