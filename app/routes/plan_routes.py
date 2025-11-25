import re

# app/routes/plan_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.services.db_service import PlanDBService
from app.forms.plan_form import PlanCreateForm
from flask_login import current_user
from app.services import ai_service, hotel_service
from app.models.user import User

plan_bp = Blueprint("plan", __name__, url_prefix="/plans")

# ----------------------------------------
#  プラン一覧（トップ）
# ----------------------------------------
@plan_bp.route("/", methods=["GET"])
def plan_list():
    if not current_user.is_authenticated:
        plans = []
        return render_template("plan/list.html", plans=plans, show_login_link=True)

    plans = PlanDBService.get_all_plans(user_id=current_user.id)
    return render_template("plan/list.html", plans=plans, show_login_link=False)

# 公開プラン一覧
@plan_bp.route("/public", methods=["GET"])
def public_plan_list():
    q = request.args.get("q", "")
    plans = PlanDBService.get_public_plans()
    return render_template(
        "plan/public_list.html",
        plans=plans,
        query=q,
        result_count=len(plans),
        active_nav="public",
    )

# ----------------------------------------
#  交通手段選択画面
# ----------------------------------------
@plan_bp.route("/transit", methods=["GET", "POST"])
def plan_transit():
    plan_id = session.get("plan_id")
    
    if not plan_id:
        flash("プランが見つかりません。最初から作成してください。", "warning")
        return redirect(url_for("plan.plan_create_form"))

    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get("user_id")

    options = PlanDBService.get_transit_by_id(plan_id, user_id=user_id)

    if request.method == "POST":
        selected_type = request.form.get("transit_type") 
        flash("交通手段を決定しました！次は宿泊先を選びましょう。", "success")
        return redirect(url_for("plan.stay_select"))

    return render_template(
        "plan/transit.html",
        options=options,
        confirm_target=url_for("plan.stay_select"),
        button_label="宿泊候補を見に行く",
    )

@plan_bp.route("/stay", methods=["GET"])
def stay_select():
    return render_template("plan/hotel_select.html", stay_options=[])

@plan_bp.route("/schedule", methods=["GET"])
def schedule_list():
    return render_template("plan/schedule_list.html", days=[])

@plan_bp.route("/schedule/edit", methods=["GET"])
def schedule_edit():
    return render_template("plan/schedule_edit.html", days=[])

@plan_bp.route("/checklists", methods=["GET"])
def checklist_list():
    return render_template("plan/checklist_list.html", categories=[])

@plan_bp.route("/checklists/edit", methods=["GET"])
def checklist_edit():
    return render_template("plan/checklist_edit.html", categories=[])

# ----------------------------------------
#  プラン詳細ページ
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
# ----------------------------------------
@plan_bp.route("/create_form", methods=["GET", "POST"])
def plan_create_form():
    form = PlanCreateForm()
    need_options = ["節約重視", "ちょっと贅沢", "アクティブ", "ゆったり", "グルメ",
          "ショッピング", "歴史", "自然", "穴場スポット", "定番スポット"]
    
    if form.validate_on_submit():
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            user_id = session.get("user_id")
        
        # ユーザー存在チェック
        valid_user = User.query.get(user_id) if user_id else None
        if not valid_user:
            session.clear()
            flash("セッションが切断されました。再度ログインしてください。", "danger")
            return redirect(url_for("auth.login"))

        destination = form.destination.data
        departure = form.departure.data
        start_date = form.start_date.data
        days = form.days.data
        purpose_raw = form.purposes_raw.data
        options = form.options.data

        try:
            # オプションの文字列化
            travel_style_str = ", ".join(options) if options else "特になし"

            ai_response = ai_service.generate_plan_from_inputs(
                destination,
                start_point=departure,
                days=days,
                purpose_raw=purpose_raw,
                travel_style=travel_style_str
            )
            
            plan_title, transit, schedule = format_json(ai_response=ai_response)

            # 1. プランの保存
            plan_id = PlanDBService.create_plan(
                user_id=user_id,
                destination=destination,
                departure=departure,
                start_date=start_date,
                days=days,
                purpose=purpose_raw,
                options=options,
                plan_title=plan_title
            )
            session["plan_id"] = plan_id

            # 2. 交通手段候補の保存
            PlanDBService.create_transit(plan_id, transit)

            # 3. 日程の保存
            PlanDBService.create_schedule(plan_id=plan_id, ai_schedule=schedule)
            
            # 4. ホテル情報の取得と保存
            simplified_hotels = hotel_service.search_rakuten_hotels(destination)
            PlanDBService.create_hotel(plan_id, simplified_hotels)

            return redirect(url_for("plan.plan_transit"))

        except Exception as e:
            print(f"Error generating plan: {e}")
            import traceback
            traceback.print_exc()
            flash(f"プラン生成中にエラーが発生しました: {e}", "danger")
            return redirect(url_for("plan.plan_create_form"))
    
    if request.method == "POST" and not form.validate():
        flash(f"入力エラー詳細: {form.errors}", "danger")

    return render_template(
        "plan/plan_create.html",
        form=form, 
        need_options=need_options,           
        active_nav="plans",
    )

def format_json(ai_response):
    plan_title = ai_response.get("plan_title", "無題のプラン")
    transit = ai_response.get("transport_options", {}) 
    schedule = ai_response.get("itinerary", [])
    return plan_title, transit, schedule

def _split_to_list(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,、\n\r]+", raw)
    return [p.strip() for p in parts if p.strip()]