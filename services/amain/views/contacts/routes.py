from quart import (
    Quart, redirect, render_template, request, flash, jsonify, send_file, Blueprint
)
from werkzeug.utils import secure_filename
# from services.main.views.common import hx_render_template
from views.common import hx_render_template
from ..contacts.contacts_model import Contact, Archiver
import os

bp = Blueprint('contacts', __name__, template_folder='templates')  

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = {'txt', 'json'}

def init():
    Contact.load_db()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/upload", methods=("POST",))
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            # return redirect(request.url)
            return ("", 404) 
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            # return redirect(request.url)
            return ("", 404)             
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('UPLOAD_FOLDER', filename))

    return ("", 204)  # return empty response so htmx does not overwrite the progress bar value


@bp.route("/")
def contacts():
    search = request.args.get("q")
    page = int(request.args.get("page", 1))
    if search is not None:
        contacts_set = Contact.search(search)
        if request.headers.get('HX-Trigger') == 'search':
            return hx_render_template("contacts/rows.html", contacts=contacts_set)
    else:
        contacts_set = Contact.all()
    
    hx_render_template("contacts/contacts.html", contacts=contacts_set, archiver=Archiver.get())

@bp.route("/archive", methods=["POST"])
def start_archive():
    archiver = Archiver.get()
    archiver.run()
    return render_template("contacts/archive_ui.html", archiver=archiver)


@bp.route("/archive", methods=["GET"])
def archive_status():
    archiver = Archiver.get()
    return render_template("contacts/archive_ui.html", archiver=archiver)


@bp.route("/archive/file", methods=["GET"])
def archive_content():
    archiver = Archiver.get()
    return send_file(archiver.archive_file(), "archive.json", as_attachment=True)


@bp.route("/archive", methods=["DELETE"])
def reset_archive():
    archiver = Archiver.get()
    archiver.reset()
    return render_template("contacts/archive_ui.html", archiver=archiver)


@bp.route("/count")
def contacts_count():
    count = Contact.count()
    return "(" + str(count) + " total Contacts)"


@bp.route("/new", methods=['GET'])
def contacts_new_get():
    return render_template("contacts/new.html", contact=Contact())


@bp.route("/new", methods=['POST'])
def contacts_new():
    c = Contact(None, request.form['first_name'], request.form['last_name'], request.form['phone'],
                request.form['email'])
    if c.save():
        flash("Created New Contact!")
        if request.headers.get("HX-Request"):
            print("HX-Request is true")
        return redirect("/contacts")
    else:
        return render_template("contacts/new.html", contact=c)


@bp.route("/<contact_id>")
def contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return render_template("contacts/show.html", contact=contact)


@bp.route("/<contact_id>/edit", methods=["GET"])
def contacts_edit_get(contact_id=0):
    contact = Contact.find(contact_id)
    return render_template("contacts/edit.html", contact=contact)


@bp.route("/<contact_id>/edit", methods=["POST"])
def contacts_edit_post(contact_id=0):
    c = Contact.find(contact_id)
    c.update(request.form['first_name'], request.form['last_name'], request.form['phone'], request.form['email'])
    if c.save():
        flash("Updated Contact!")
        return redirect("/contacts/" + str(contact_id))
    else:
        return render_template("contacts/edit.html", contact=c)


@bp.route("/<contact_id>/email", methods=["GET"])
def contacts_email_get(contact_id=0):
    c = Contact.find(contact_id)
    c.email = request.args.get('email')
    c.validate()
    return c.errors.get('email') or ""


@bp.route("/<contact_id>", methods=["DELETE"])
def contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    contact.delete()
    if request.headers.get('HX-Trigger') == 'delete-btn':
        flash("Deleted Contact!")
        contacts_set = Contact.all()
        content_html = render_template("contacts/contacts.html", contacts=contacts_set, archiver=Archiver.get())
        return render_template("base.html", content=content_html)
    else:
        return ""


@bp.route("/", methods=["DELETE"])
def contacts_delete_all():
    contact_ids = list(map(int, request.form.getlist("selected_contact_ids")))
    for contact_id in contact_ids:
        contact = Contact.find(contact_id)
        contact.delete()
    flash("Deleted Contacts!")
    contacts_set = Contact.all(1)
    archiver = Archiver.get()    
    content_html = render_template("contacts/contacts.html", contacts=contacts_set, archiver=Archiver.get())
    # if request.headers.get("HX-Request"):
    #     return content_html
    # else:
    #     return render_template("base.html", content=content_html)
    return render_template("base.html", content=content_html)    
    
# ===========================================================
# JSON Data API
# ===========================================================

@bp.route("/api/v1/contacts", methods=["GET"])
def json_contacts():
    contacts_set = Contact.all()
    return {"contacts": [c.__dict__ for c in contacts_set]}


@bp.route("/api/v1/contacts", methods=["POST"])
def json_contacts_new():
    c = Contact(None, request.form.get('first_name'), request.form.get('last_name'), request.form.get('phone'),
                request.form.get('email'))
    if c.save():
        return c.__dict__
    else:
        return {"errors": c.errors}, 400


@bp.route("/api/v1/contacts/<contact_id>", methods=["GET"])
def json_contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return contact.__dict__


@bp.route("/api/v1/contacts/<contact_id>", methods=["PUT"])
def json_contacts_edit(contact_id):
    c = Contact.find(contact_id)
    c.update(request.form['first_name'], request.form['last_name'], request.form['phone'], request.form['email'])
    if c.save():
        return c.__dict__
    else:
        return {"errors": c.errors}, 400


@bp.route("/api/v1/contacts/<contact_id>", methods=["DELETE"])
def json_contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    contact.delete()
    return jsonify({"success": True})
