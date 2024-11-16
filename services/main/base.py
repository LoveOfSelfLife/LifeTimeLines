from flask import redirect, render_template, request, Blueprint

bp = Blueprint('base', __name__)  

    
@bp.route("/")
def index():
    return render_template("base.html")
