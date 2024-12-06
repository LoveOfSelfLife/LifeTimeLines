from quart import render_template, request

# from services.main.views.configurations.editable_entities import get_editable_entity_names
from common.entities.entity_registry import get_editable_entity_names
async def hx_render_template(template, **kwargs):
    # kwargs['configs'] = get_editable_entity_names()
    if request.headers.get("HX-Request"):
        return await render_template(template, **kwargs)
    else:
        return await render_template('base.html', 
                               content=await render_template(template, **kwargs), 
                               ctx={"configs":get_editable_entity_names()} )
