import re

# app/routes/plan_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.services.db_service import PlanDBService
from app.forms.plan_form import PlanCreateForm
from flask_login import current_user

plan_bp = Blueprint("plan", __name__, url_prefix="/plans")


# ----------------------------------------
#  プラン一覧（トップ）
#  /plansfrom flask_login import current_user

@plan_bp.route("/", methods=["GET"])
def plan_list():
    if not current_user.is_authenticated:
        # ログインしてないとき：プラン無し + ログインを促す
        plans = []
        return render_template("plan/list.html", plans=plans, show_login_link=True)

    # ログインしているとき：自分のプランだけ表示
    plans = PlanDBService.get_all_plans(user_id=current_user.id)
    return render_template("plan/list.html", plans=plans, show_login_link=False)


# 公開プラン一覧
@plan_bp.route("/public", methods=["GET"])
def public_plan_list():
    # 誰でも見れる想定なのでログインチェックなし
    q = request.args.get("q", "")

    plans = PlanDBService.get_public_plans()

    return render_template(
        "plan/public_list.html",  # or "plan/list.html" を流用でもOK
        plans=plans,
        query=q,
        result_count=len(plans),
        active_nav="public",
    )



# ----------------------------------------
#  プラン詳細ページ
#  /plans/<id>
# ----------------------------------------
@plan_bp.route("/<int:plan_id>", methods=["GET"])
def plan_detail(plan_id):
    plan = PlanDBService.get_plan_by_id(plan_id)
    if not plan:
        flash("指定されたプランは存在しません。")
        return redirect(url_for("plan.plan_list"))

    return render_template("plan/detail.html", plan=plan)


# ----------------------------------------
#  プラン作成画面（AIに生成依頼）
#  /plans/create
# ----------------------------------------
@plan_bp.route("/create", methods=["GET"])
def plan_create():
    form_state = {
        "system_error": False,
        "missing_required": False,
        "selected_origin": "current",
        "custom_origin": "",
        "purpose_values": [],
        "needs": ["安く行きたい", "ゆっくりしたい", "アクティビティ重視"],
        "selected_needs": [],
        "destination": "",
        "days": "",
        "start_date": "",
    }
    return render_template(
        "plan/plan_create.html",
        form_state=form_state,
        active_nav="plans"
    )


def _split_to_list(raw: str) -> list[str]:
    """
    「,」「、」「改行」で区切って list[str] にするユーティリティ
    """
    if not raw:
        return []

    parts = re.split(r"[,、\n\r]+", raw)
    return [p.strip() for p in parts if p.strip()]

# # プラン作成フォーム送信後のルーティングと処理
# @plan_bp.route("/create_form", methods=["GET", "POST"])
# # @login_required
# def plan_create_form():
#     form = PlanCreateForm()

#     if request.method == "POST":
#         if form.validate_on_submit():
#             # DBにプラン作成 → id を返す
#             new_plan_id = PlanDBService.create_plan(form)

#             # AI生成は JS(AJAX) で行うためここではしない
#             flash("プランを作成しました。詳細画面で編集できます。")
#             return redirect(url_for("plan.plan_detail", plan_id=new_plan_id))

#         flash("入力内容に誤りがあります。")

#     return render_template("plan/plan_create.html", form=form)


# # ----------------------------------------
# #  交通手段選択画面
# #  /plans/<id>/transit
# # ----------------------------------------
# @plan_bp.route("/<int:plan_id>/transit", methods=["GET", "POST"])
# def plan_transit(plan_id):
#     plan = PlanDBService.get_plan_by_id(plan_id)

#     if not plan:
#         flash("プランが存在しません。")
#         return redirect(url_for("plan.plan_list"))

#     if request.method == "POST":
#         # 選択された交通手段をDBに保存
#         transit = request.form.get("transit")
#         PlanDBService.update_transit(plan_id, transit)

#         flash("交通手段を更新しました。")
#         return redirect(url_for("plan.plan_detail", plan_id=plan_id))

#     return render_template("plan/transit.html", plan=plan)


# # ----------------------------------------
# #  ホテル選択画面
# #  /plans/<id>/hotel
# # ----------------------------------------
# @plan_bp.route("/<int:plan_id>/hotel", methods=["GET", "POST"])
# def plan_hotel(plan_id):
#     plan = PlanDBService.get_plan_by_id(plan_id)

#     if not plan:
#         flash("プランが存在しません。")
#         return redirect(url_for("plan.plan_list"))

#     if request.method == "POST":
#         hotel = request.form.get("hotel")
#         PlanDBService.update_hotel(plan_id, hotel)

#         flash("ホテル情報を更新しました。")
#         return redirect(url_for("plan.plan_detail", plan_id=plan_id))

#     return render_template("plan/hotel.html", plan=plan)


# # ----------------------------------------
# #  日程確定画面（編集可）
# #  /plans/<id>/schedule
# # ----------------------------------------
# @plan_bp.route("/<int:plan_id>/schedule", methods=["GET", "POST"])
# def plan_schedule(plan_id):
#     plan = PlanDBService.get_plan_with_schedule(plan_id)

#     if not plan:
#         flash("プランが存在しません。")
#         return redirect(url_for("plan.plan_list"))

#     if request.method == "POST":
#         updated_schedule = request.form.to_dict()
#         PlanDBService.update_schedule(plan_id, updated_schedule)

#         flash("日程を更新しました。")
#         return redirect(url_for("plan.plan_detail", plan_id=plan_id))

#     return render_template("plan/schedule.html", plan=plan)


# # ----------------------------------------
# #  持ち物リスト編集画面
# #  /plans/<id>/items
# # ----------------------------------------
# @plan_bp.route("/<int:plan_id>/items", methods=["GET", "POST"])
# def plan_items(plan_id):
#     plan = PlanDBService.get_plan_with_items(plan_id)

#     if not plan:
#         flash("プランが存在しません。")
#         return redirect(url_for("plan.plan_list"))

#     if request.method == "POST":
#         updated_items = request.form.to_dict()
#         PlanDBService.update_items(plan_id, updated_items)

#         flash("持ち物リストを更新しました。")
#         return redirect(url_for("plan.plan_detail", plan_id=plan_id))

#     return render_template("plan/item_list.html", plan=plan)
