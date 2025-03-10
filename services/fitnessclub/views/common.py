from flask import render_template, request
from services.fitnessclub.active_fitness_registry import get_active_fitness_entity_names

def hx_render_template(template, **kwargs):
    # kwargs['configs'] = get_editable_entity_names()
    if request.headers.get("HX-Request"):
        return render_template(template, **kwargs)
    else:
        return render_template('base.html', 
                               content=render_template(template, **kwargs), 
                               ctx={"configs":get_active_fitness_entity_names()} )
