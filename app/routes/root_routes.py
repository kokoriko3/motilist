
from flask import Blueprint, redirect, url_for, session, flash
from flask_login import current_user

root_bp = Blueprint("root", __name__)

@root_bp.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated or session.get("user_id"):
        return redirect(url_for("plan.plan_list"))
    flash("ログインしてください", "error")
    session["next_url"] = url_for("plan.plan_create_form")
    return redirect(url_for("auth.login"))
