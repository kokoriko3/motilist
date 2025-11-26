import re
import json
import os
from datetime import datetime, date

# app/routes/plan_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from app.services.db_service import PlanDBService
from app.forms.plan_form import PlanCreateForm
from flask_login import current_user
from app.services import ai_service, hotel_service
from app.models.user import User
from app.extensions import db
from app.models.plan import Plan, TransportSnapshot, HotelSnapshot, Schedule

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
    plan_id = session["plan_id"]
    user_id = session["user_id"]

    schedule_obj = PlanDBService.get_schedule_by_id(plan_id,user_id)
    format_days = []

    data = schedule_obj.daily_plan_json

    for day_data in data:
        day_num = day_data.get("day")
        details = day_data.get("details")

        activities = []
        for detail in details:
            activities.append({
                "time": detail.get("time"),
                # 修正1: キーを 'activite' から HTMLが期待する 'title' に変更
                "title": detail.get("activity"), 
                "note": detail.get("transport_notes")
            })
        
        format_days.append({
            "day": day_num,
            # 修正2: HTMLが期待する 'label' を追加 (例: "1日目")
            "label": f"{day_num}日目", 
            # 修正3: キーを 'detail' から HTMLが期待する 'activities' に変更
            "activities": activities 
        })
        
    # current_app.logger.info(format_days)
    
    return render_template("plan/schedule_list.html", days=format_days)

@plan_bp.route("/schedule/edit", methods=["GET"])
def schedule_edit():
    plan_id = session.get("plan_id")
    user_id = session.get("user_id")

    # 1. 既存のデータを取得 (schedule_listと同じロジック)
    schedule_obj = PlanDBService.get_schedule_by_id(plan_id, user_id)
    
    # データがない場合のガード
    if not schedule_obj:
        flash("スケジュールが見つかりません", "warning")
        return redirect(url_for("plan.schedule_list"))

    data = schedule_obj.daily_plan_json
    format_days = []

    # 2. テンプレート用に整形 (キー名をHTMLに合わせる)
    for day_data in data:
        day_num = day_data.get("day")
        details = day_data.get("details", [])

        activities = []
        for detail in details:
            activities.append({
                "time": detail.get("time", ""),
                "title": detail.get("activity", ""), # DBはactivity, 表示はtitle
                "note": detail.get("transport_notes", "")
            })
        
        format_days.append({
            "day": day_num,
            "label": f"{day_num}日目",
            "activities": activities
        })

    return render_template("plan/schedule_edit.html", days=format_days)

@plan_bp.route("/schedule/update", methods=["POST"])
def schedule_update():
    plan_id = session.get("plan_id")
    # user_id = session.get("user_id") # 必要に応じて権限チェック

    # 1. JavaScriptから送信されたJSONを受け取る
    new_schedule_data = request.get_json()
    
    if not new_schedule_data:
        return jsonify({"error": "データがありません"}), 400

    try:
        # 2. DB更新処理 (Serviceにメソッドを追加するか、ここで直接更新)
        # ここでは既存のScheduleモデルを更新する例を書きます
        schedule = Schedule.query.filter_by(plan_id=plan_id).first()
        if schedule:
            schedule.daily_plan_json = new_schedule_data
            db.session.commit()
            return jsonify({"status": "success", "redirect": url_for("plan.schedule_list")})
        else:
            return jsonify({"error": "スケジュールが見つかりません"}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
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
            current_app.logger.info("aiからの返答：",ai_response)    
            
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

@plan_bp.route("/create_dummy", methods=["POST"])
def create_dummy_plan():
    """
    seed_data.json からダミーデータを読み込んでプランを作成する
    （AI生成をスキップして開発をスムーズにするためのルート）
    """
    
    # ログインチェック
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get("user_id")
    
    valid_user = User.query.get(user_id) if user_id else None
    if not valid_user:
        session.clear()
        flash("セッションが無効です。ログインしてください。", "danger")
        return redirect(url_for("auth.login"))

    try:
        # seed_data.json のパス
        seed_file = os.path.join(current_app.root_path, '..', 'seed_data.json')
        
        if not os.path.exists(seed_file):
            flash("ダミーデータ(seed_data.json)が見つかりません。'python manage_data.py dump' で作成してください。", "warning")
            return redirect(url_for("plan.plan_create_form"))

        with open(seed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # データ構造チェック
        if not data.get("plans"):
            flash("seed_data.json にプランデータが含まれていません。", "warning")
            return redirect(url_for("plan.plan_create_form"))

        # 最新の1件を取得（リストの最後にあると仮定、あるいは0番目）
        # dumpの仕様に合わせて調整してください。今回は[0]を使います。
        dummy_plan_data = data["plans"][0]

        # 1. プランの保存（新規作成として扱うためIDは除外して作成）
        # 日付文字列をオブジェクトに変換
        start_date_val = dummy_plan_data["start_date"]
        if isinstance(start_date_val, str):
            start_date_val = date.fromisoformat(start_date_val)

        plan_id = PlanDBService.create_plan(
            user_id=user_id, # 現在のユーザーIDを使う
            destination=dummy_plan_data["destination"],
            departure=dummy_plan_data["departure"],
            start_date=start_date_val,
            days=dummy_plan_data["days"],
            purpose=dummy_plan_data["purpose"],
            options=dummy_plan_data["options"],
            plan_title=f"[Dummy] {dummy_plan_data['title']}", # ダミーとわかるようにタイトル変更
        )
        session["plan_id"] = plan_id

        # 2. 関連データの復元
        # 元のプランIDに紐づいていたデータを取得して、新しいプランIDで保存し直す
        original_plan_id = dummy_plan_data["id"]

        # Transport
        for t_data in data.get("transport_snapshots", []):
            if t_data["plan_id"] == original_plan_id:
                # 新しいプランIDで保存
                snapshot = TransportSnapshot(
                    plan_id=plan_id,
                    type=t_data["type"],
                    transport_method=t_data["transport_method"],
                    cost=t_data["cost"],
                    duration=t_data["duration"],
                    transit_count=t_data["transit_count"],
                    departure_time=t_data["departure_time"],
                    arrival_time=t_data["arrival_time"],
                    is_selected=t_data["is_selected"]
                )
                db.session.add(snapshot)

        # Hotel
        for h_data in data.get("hotel_snapshots", []):
            if h_data["plan_id"] == original_plan_id:
                snapshot = HotelSnapshot(
                    plan_id=plan_id,
                    hotel_no=h_data["hotel_no"],
                    name=h_data["name"],
                    url=h_data["url"],
                    image_url=h_data["image_url"],
                    price=h_data["price"],
                    address=h_data["address"],
                    review=h_data["review"],
                    is_selected=h_data["is_selected"]
                )
                db.session.add(snapshot)

        # Schedule
        for s_data in data.get("schedules", []):
            if s_data["plan_id"] == original_plan_id:
                schedule = Schedule(
                    plan_id=plan_id,
                    daily_plan_json=s_data["daily_plan_json"]
                )
                db.session.add(schedule)

        db.session.commit()
        
        flash("ダミーデータからプランを作成しました！", "success")
        return redirect(url_for("plan.plan_transit"))

    except Exception as e:
        db.session.rollback()
        print(f"Dummy creation error: {e}")
        import traceback
        traceback.print_exc()
        flash(f"ダミー作成エラー: {e}", "danger")
        return redirect(url_for("plan.plan_create_form"))