from flask import Blueprint, render_template, flash, url_for, redirect, request
# from app.forms.auth_forms import ○○

bp = Blueprint(
    "plan",
    __name__
)

@bp.route("/signup", methods=["EGT", "POST"])
def signup():
    return "hello signup"