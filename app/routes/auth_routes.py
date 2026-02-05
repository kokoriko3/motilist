from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user
from app.forms.auth_form import LoginForm
from app.services.db_service import UserDBService
from app.extensions import db, bcrypt
from app.models.user import User
from app.forms.register_form import RegisterForm


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")




@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = UserDBService.get_user_by_email(form.email.data)

        if user is None:
            flash("メールアドレスまたはパスワードが間違っています", "error")
            return render_template("auth/login.html", form=form)

        if not bcrypt.check_password_hash(user.passwordHash, form.password.data):
            flash("メールアドレスまたはパスワードが間違っています", "error")
            return render_template("auth/login.html", form=form)

        login_user(user)
        session["user_id"] = user.user_id
        # flash("ログインしました", "success")
        return redirect(url_for("plan.plan_list"))
    return render_template("auth/login.html", form=form)




@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    新規登録画面の表示と登録処理。
    - GET: フォームを表示
    - POST: バリデーション → メール重複チェック → 登録 → 完了画面へ
    """
    form = RegisterForm()

    # POST 時の処理
    if form.validate_on_submit():

        # メールアドレスの重複チェック
        if User.query.filter_by(email=form.email.data).first():
            flash("このメールアドレスは既に使用されています。", "error")
            return render_template("auth/register.html", form=form)

        # パスワードをハッシュ化
        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode("utf-8")

        # ユーザー作成
        new_user = User(
            # 修正前: displayName=form.displayName.data,
            display_name=form.displayName.data,  # 👈 Userモデルの定義に合わせる

            email=form.email.data,
            passwordHash=hashed_password,  # これは Userモデルでも passwordHash なのでOK

            # 修正前: anonymousId=None
            anonymous_id=None  # 👈 Userモデルの定義に合わせる
        )

        # DBに保存
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        session["user_id"] = new_user.user_id

        # 完了画面へリダイレクト
        return redirect(url_for("auth.register_complete"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/register/complete")
def register_complete():
    """登録完了画面"""
    return render_template("auth/register_complete.html")


@auth_bp.route('/logout', methods=["GET"])
def logout():
    """
    ログアウト処理
    セッション情報をクリアしてログインページへリダイレクトする
    """
    logout_user()
    session.clear()  # セッションをすべて削除
    return redirect(url_for('auth.login'))  # ログインページへリダイレクト
