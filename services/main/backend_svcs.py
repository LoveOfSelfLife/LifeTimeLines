from flask import (
    Flask, redirect, render_template, request, flash, jsonify, send_file, Blueprint
)
import time
import os

main = Blueprint('be', __name__)  

@main.route("/be")
def contacts():
    return render_template("be.html")

# ===========================================================
# JSON Data API
# ===========================================================

@main.route("/api/v1/be", methods=["GET"])
def json_be():
    return {"be": "be"}, 200

if __name__ == "__main__":
    pass
