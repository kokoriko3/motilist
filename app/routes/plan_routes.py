from flask import Blueprint, render_template, flash, url_for, redirect, request

bp = Blueprint(
    "plan",
    __name__
)

@bp.route("/")
def index():
    return "hello world"

@bp.route("plan_create")
def plan_create():
    return render_template("plan_create.html")