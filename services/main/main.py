from flask import (
    Flask, redirect, render_template, request, flash, jsonify, send_file, Blueprint
)
from contacts_model import Contact, Archiver
import time

main = Blueprint('main', __name__)  # Create a blueprint named 'main'

@main.route("/")
def index():
    return redirect("/contacts")


@main.route("/contacts")
def contacts():
    search = request.args.get("q")
    page = int(request.args.get("page", 1))
    if search is not None:
        contacts_set = Contact.search(search)
        if request.headers.get('HX-Trigger') == 'search':
            return render_template("rows.html", contacts=contacts_set)
    else:
        contacts_set = Contact.all()
    return render_template("index.html", contacts=contacts_set, archiver=Archiver.get())


@main.route("/contacts/archive", methods=["POST"])
def start_archive():
    archiver = Archiver.get()
    archiver.run()
    return render_template("archive_ui.html", archiver=archiver)


@main.route("/contacts/archive", methods=["GET"])
def archive_status():
    archiver = Archiver.get()
    return render_template("archive_ui.html", archiver=archiver)


@main.route("/contacts/archive/file", methods=["GET"])
def archive_content():
    archiver = Archiver.get()
    return send_file(archiver.archive_file(), "archive.json", as_attachment=True)


@main.route("/contacts/archive", methods=["DELETE"])
def reset_archive():
    archiver = Archiver.get()
    archiver.reset()
    return render_template("archive_ui.html", archiver=archiver)


@main.route("/contacts/count")
def contacts_count():
    count = Contact.count()
    return "(" + str(count) + " total Contacts)"


@main.route("/contacts/new", methods=['GET'])
def contacts_new_get():
    return render_template("new.html", contact=Contact())


@main.route("/contacts/new", methods=['POST'])
def contacts_new():
    c = Contact(None, request.form['first_name'], request.form['last_name'], request.form['phone'],
                request.form['email'])
    if c.save():
        flash("Created New Contact!")
        return redirect("/contacts")
    else:
        return render_template("new.html", contact=c)


@main.route("/contacts/<contact_id>")
def contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return render_template("show.html", contact=contact)


@main.route("/contacts/<contact_id>/edit", methods=["GET"])
def contacts_edit_get(contact_id=0):
    contact = Contact.find(contact_id)
    return render_template("edit.html", contact=contact)


@main.route("/contacts/<contact_id>/edit", methods=["POST"])
def contacts_edit_post(contact_id=0):
    c = Contact.find(contact_id)
    c.update(request.form['first_name'], request.form['last_name'], request.form['phone'], request.form['email'])
    if c.save():
        flash("Updated Contact!")
        return redirect("/contacts/" + str(contact_id))
    else:
        return render_template("edit.html", contact=c)


@main.route("/contacts/<contact_id>/email", methods=["GET"])
def contacts_email_get(contact_id=0):
    c = Contact.find(contact_id)
    c.email = request.args.get('email')
    c.validate()
    return c.errors.get('email') or ""


@main.route("/contacts/<contact_id>", methods=["DELETE"])
def contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    contact.delete()
    if request.headers.get('HX-Trigger') == 'delete-btn':
        flash("Deleted Contact!")
        return redirect("/contacts", 303)
    else:
        return ""


@main.route("/contacts/", methods=["DELETE"])
def contacts_delete_all():
    contact_ids = list(map(int, request.form.getlist("selected_contact_ids")))
    for contact_id in contact_ids:
        contact = Contact.find(contact_id)
        contact.delete()
    flash("Deleted Contacts!")
    contacts_set = Contact.all(1)
    archiver = Archiver.get()    
    return render_template("index.html", contacts=contacts_set, archiver=archiver)


# ===========================================================
# JSON Data API
# ===========================================================

@main.route("/api/v1/contacts", methods=["GET"])
def json_contacts():
    contacts_set = Contact.all()
    return {"contacts": [c.__dict__ for c in contacts_set]}


@main.route("/api/v1/contacts", methods=["POST"])
def json_contacts_new():
    c = Contact(None, request.form.get('first_name'), request.form.get('last_name'), request.form.get('phone'),
                request.form.get('email'))
    if c.save():
        return c.__dict__
    else:
        return {"errors": c.errors}, 400


@main.route("/api/v1/contacts/<contact_id>", methods=["GET"])
def json_contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return contact.__dict__


@main.route("/api/v1/contacts/<contact_id>", methods=["PUT"])
def json_contacts_edit(contact_id):
    c = Contact.find(contact_id)
    c.update(request.form['first_name'], request.form['last_name'], request.form['phone'], request.form['email'])
    if c.save():
        return c.__dict__
    else:
        return {"errors": c.errors}, 400


@main.route("/api/v1/contacts/<contact_id>", methods=["DELETE"])
def json_contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    contact.delete()
    return jsonify({"success": True})


if __name__ == "__main__":
    pass
