from flask import Blueprint, render_template, redirect, url_for, request, flash, session
# from app.forms.auth_form import LoginForm
from app.services.db_service import UserDBService
from app.extensions import bcrypt


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")




# -------------------------
# ログイン画面表示 + 処理
# -------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)


    # 初回アクセスは単純に画面表示
    if request.method == "GET":
        return render_template("auth/login.html", form=form)


    # POST（ログイン処理）
    if form.validate():
        user = UserDBService.get_user_by_email(form.email.data)


    if user is None:
        flash("メールアドレスが登録されていません", "error")
    return render_template("auth/login.html", form=form)


    # パスワードチェック
    if not bcrypt.check_password_hash(user.passwordHash, form.password.data):
        flash("パスワードが一致しません", "error")
    return render_template("auth/login.html", form=form)


    # 認証成功 → session へ
    session["user_id"] = user.userId
    flash("ログインしました", "success")
    return redirect(url_for("plan.list")) # プラン一覧へ


    return render_template("auth/login.html", form=form)




    # -------------------------
    # ログアウト
    # -------------------------
    @auth_bp.route("/logout")
    def logout():
        session.clear()
    flash("ログアウトしました", "success")
    return redirect(url_for("auth.login"))