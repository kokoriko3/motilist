
from flask import Blueprint, redirect, url_for, session
from flask_login import current_user

root_bp = Blueprint("root", __name__)

@root_bp.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated or session.get("user_id"):
        return redirect(url_for("plan.plan_list"))
    return redirect(url_for("auth.login"))
