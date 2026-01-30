
from flask import Blueprint, redirect, url_for, session, flash
from flask_login import current_user

root_bp = Blueprint("root", __name__)

@root_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("auth.login"))
