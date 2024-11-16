from flask import Blueprint, render_template, request

bp = Blueprint('orchestration', __name__, template_folder='templates')

@bp.route('/orchestration-content')
def orchestration_content():
    if request.headers.get("HX-Request"):
        # Return partial template for HTMX request
        return render_template('orchestration_content.html')
    else:
        # Render full page layout if directly accessed
        return render_template('base.html', content=render_template('orchestration_content.html'))    
    
