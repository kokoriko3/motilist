import re
import json
import os
from datetime import datetime, date

# app/routes/plan_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from app.services.db_service import PlanDBService
from app.forms.plan_form import PlanCreateForm
from flask_login import current_user
from app.services import ai_service, hotel_service, db_service
from app.models.user import User
from app.extensions import db
from app.models.plan import Plan, TransportSnapshot, HotelSnapshot, Schedule

plan_bp = Blueprint("plan", __name__, url_prefix="/plans")

# ----------------------------------------
#  プラン一覧（トップ）
# ----------------------------------------
@plan_bp.route("/", methods=["GET"])
def plan_list():
    # アプリとしての「有効なユーザID」を決める
    if current_user.is_authenticated:
        print("Flask-Login ログインあり")
        user_id = current_user.id
        show_login_link = False
    else:
        user_id = session.get("user_id")
        show_login_link = True

    if not user_id:
        print("ユーザIDなし（完全未ログイン＆ゲストも未作成）")
        return render_template("plan/list.html", plans=[], show_login_link=True)

    print("ユーザIDあり:", user_id)
    templates = PlanDBService.get_all_templates_by_user_id(user_id=user_id)

    # --------------------------
    # ★ テンプレートごとに追加情報を付ける
    # --------------------------
    for tpl in templates:
        # ===== 交通手段（既存処理）=====
        traffic_methods = []
        outline = tpl.itinerary_outline_json or {}
        days = outline.get("days", [])
        for d in days:
            tm = d.get("traffic_method")
            if tm and tm not in traffic_methods:
                traffic_methods.append(tm)
        tpl.transport_summary = " / ".join(traffic_methods) if traffic_methods else ""

        # ===== ホテル名（新規追加）=====
        # Plan を取得
        plan = PlanDBService.get_plan_by_id(tpl.plan_id, user_id)
        hotel_json = plan.hotel or {}

        selected_id = hotel_json.get("selected_id")
        candidates = hotel_json.get("candidates", [])

        selected_hotel = None
        if selected_id:
            selected_hotel = next(
                (c for c in candidates if c.get("id") == selected_id),
                None
            )

        # list.html で使えるよう template 側に載せる
        tpl.hotel_name = selected_hotel["name"] if selected_hotel else "選択中"

    return render_template(
        "plan/list.html",
        plans=templates,
        show_login_link=show_login_link,
    )

# 公開プラン一覧
@plan_bp.route("/public", methods=["GET"])
def public_plan_list():
    q = request.args.get("q", "")

    # アプリとしての「有効なユーザID」を決める
    if current_user.is_authenticated:
        print("Flask-Login ログインあり")
        user_id = current_user.id
        show_login_link = False
    else:
        user_id = session.get("user_id")
        show_login_link = True  # ここは UI の好みに応じて

    # 公開一覧は「ログインしてなくても見せる」仕様にしてもいいけど、
    # 今の方針に合わせておく
    if not user_id:
        print("ユーザIDなし（完全未ログイン＆ゲストも未作成）")
        return render_template(
            "plan/public_list.html",
            plans=[],
            query=q,
            result_count=0,
            active_nav="public",
            show_login_link=True,
        )

    print("ユーザIDあり:", user_id)
    templates = PlanDBService.get_public_templates()

    # --------------------------
    # ★ Template ごとに表示用フィールドを作る
    # --------------------------
    for tpl in templates:
        # ===== 交通手段まとめ =====
        traffic_methods = []
        outline = tpl.itinerary_outline_json or {}
        days = outline.get("days", [])
        for d in days:
            tm = d.get("traffic_method")
            if tm and tm not in traffic_methods:
                traffic_methods.append(tm)
        tpl.transport_summary = " / ".join(traffic_methods) if traffic_methods else ""

        # ===== ホテル名（Plan 経由で取得） =====
        plan = Plan.query.get(tpl.plan_id)  # 公開なので user_id で絞らない
        if plan and plan.hotel:
            hotel_json = plan.hotel or {}
            selected_id = hotel_json.get("selected_id")
            candidates = hotel_json.get("candidates", []) or []

            selected_hotel = None
            if selected_id:
                selected_hotel = next(
                    (c for c in candidates if c.get("id") == selected_id),
                    None
                )
            tpl.hotel_name = selected_hotel["name"] if selected_hotel else "選択中"
        else:
            tpl.hotel_name = "未設定"

    return render_template(
        "plan/public_list.html",
        plans=templates,
        query=q,
        result_count=len(templates),
        active_nav="public",
        show_login_link=show_login_link,
    )


# ----------------------------------------
#  交通手段選択画面
# ----------------------------------------
# ----------------------------------------
#  ????????
# ----------------------------------------
# ----------------------------------------
#  ????????
# ----------------------------------------
@plan_bp.route("/transit", methods=["GET", "POST"])
def plan_transit():
    plan_id = session.get("plan_id")
    
    if not plan_id:
        flash("プランが選択されていません。先にプランを作成してください。", "warning")
        return redirect(url_for("plan.plan_create_form"))

    user_id = current_user.id if current_user.is_authenticated else session.get("user_id")

    options = PlanDBService.get_transit_by_id(plan_id, user_id=user_id)
    selected_transit = PlanDBService.get_selected_transit(plan_id, user_id=user_id)
    selected_type = selected_transit.type if selected_transit else None

    if request.method == "POST":
        selected_type = request.form.get("transit_type")
        if not selected_type:
            flash("交通手段を選択してください。", "warning")
        else:
            saved = PlanDBService.select_transit(plan_id, selected_type, user_id=user_id)
            if not saved:
                flash("交通手段の保存に失敗しました。", "danger")
            else:
                flash("交通手段を確定しました。", "success")
                options = PlanDBService.get_transit_by_id(plan_id, user_id=user_id)
                selected_transit = PlanDBService.get_selected_transit(plan_id, user_id=user_id)
                selected_type = selected_transit.type if selected_transit else selected_type

    button_label = "変更" if selected_type else "確定"

    return render_template(
        "plan/transit.html",
        options=options,
        selected_type=selected_type,
        confirm_target=url_for("plan.stay_select"),
        button_label=button_label
    )

@plan_bp.route("/stay/", methods=["GET", "POST"])
def stay_select():
    # 共通：どのプランか決める
    plan_id = session.get("plan_id")
    if plan_id is None:
        flash("プランが指定されていません。", "error")
        return redirect(url_for("plan.plan_list"))
    
    # ユーザ判定（transit と同じロジックに揃える）
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get("user_id")

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)

    print("[DEBUG] plan =", plan)
    print("[DEBUG] plan.hotel =", plan.hotel)
    if not plan:
        flash("プランが見つかりません。", "warning")
        return redirect(url_for("plan.plan_create_form"))
    
    # ここから hotel JSON を安全に扱う
    hotel_json = plan.hotel or {}              # None 対策
    selected_id = hotel_json.get("selected_id")  # キー未定義対策

    # 宿泊先を確定している場合のルーティング
    # ★ reselect=1 が付いてない普通の GET のときだけ、自動で confirm に飛ばす
    reselect = request.args.get("reselect")
    if request.method == "GET" and selected_id is not None and reselect != "1":
        return redirect(url_for("plan.stay_confirm"))
    
    

    print("[DEBUG] method =", request.method)
    # ---------- POST: 選択確定 & リダイレクト ----------
    if request.method == "POST":
        # form から選択されたホテルIDを受け取る
        selected_id = request.form.get("hotel_id", type=int)
        if selected_id is None:
            flash("宿泊先が選択されていません。", "error")
            return redirect(url_for("plan.stay_select"))

        hotel_json = plan.hotel or {}
        candidates = hotel_json.get("candidates", [])

        # JSON の中から選ばれた候補を探す
        selected = next((c for c in candidates if c.get("id") == selected_id), None)

        print("[DEBUG] request.form =", request.form)
        print("[DEBUG] selected_id =", selected_id)
        print("[DEBUG] candidates =", candidates)
        print("[DEBUG] selected =", selected)
        if selected is None:
            flash("不正な宿泊先が指定されました。", "error")
            print("不正な宿泊先")
            return redirect(url_for("plan.stay_select"))

        # Plan.hotel 側の JSON を更新（どれを選んだか覚えておく）
        hotel_json["selected_id"] = selected_id
        print(hotel_json)  # 追加
        plan.hotel = hotel_json

        db.session.commit()
        print(plan.hotel) # 追加
        flash("宿泊先を決定しました！次は日程を確認しましょう。", "success")
        print("宿泊先の決定")
        # ★ ここで「選択完了後の処理」へ飛ぶ
        # 例: スケジュール編集画面
        return redirect(url_for("plan.stay_confirm"))

    # ---------- GET: 一覧表示 ----------
    hotel_json = plan.hotel or {}
    candidates = hotel_json.get("candidates", [])
    selected_id = hotel_json.get("selected_id")

    stay_options = []
    for c in candidates:
        raw_review = c.get("review")
        try:
            review_value = float(raw_review) if raw_review not in (None, "", "None") else None
        except ValueError:
            review_value = None

        stay_options.append(
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "price": c.get("price"),
                "address": c.get("address"),
                "url": c.get("url"),
                "image_url": c.get("image_url"),
                "review": review_value,
                "is_selected": (c.get("id") == selected_id),
            }
        )
    return render_template("plan/hotel_select.html", plan=plan, stay_options=stay_options)

@plan_bp.route("/stay/confirm", methods=["GET"])
def stay_confirm():
    plan_id = session.get("plan_id")
    if plan_id is None:
        flash("プランが指定されていません。", "error")
        return redirect(url_for("plan.plan_list"))

    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get("user_id")
    plan = PlanDBService.get_plan_by_id(plan_id, user_id)


    hotel_json = plan.hotel or {}
    candidates = hotel_json.get("candidates", [])
    selected_id = hotel_json.get("selected_id")

    print("[DEBUG] request.form =", request.form)
    print("[DEBUG] hotel_json =", hotel_json)
    print("[DEBUG] candidates =", candidates)
    print("[DEBUG] selected_id =", selected_id)
    if not selected_id:
        flash("宿泊先が選択されていません。", "error")
        return redirect(url_for("plan.stay_select"))
    
    selected = next(
        (c for c in candidates if c.get("id") == selected_id),
        None
    )
    if not selected:
        flash("宿泊先情報の取得に失敗しました。", "error")
        return redirect(url_for("plan.stay_select"))

    return render_template(
        "plan/hotel_confirm.html",
        plan=plan,
        hotel=selected
    )

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

# プラン詳細ページ
@plan_bp.route("/<int:template_id>", methods=["GET"])
def plan_detail(template_id):
    # --- ユーザー判定 ---
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get("user_id")

    # --- Template を主役に取得 ---
    template = PlanDBService.get_all_templates_by_id(template_id=template_id)
    if not template:
        print(f"指定されたテンプレートが存在しません: template_id={template_id}")
        flash("指定されたプランは存在しません。", "error")
        return redirect(url_for("plan.plan_list"))

    # 紐づく Plan を取得
    plan = PlanDBService.get_plan_by_id(template.plan_id, user_id)
    if not plan:
        print(f"紐づくプランが存在しません: plan_id={template.plan_id}, user_id={user_id}")
        flash("指定されたプランは存在しません。", "error")
        return redirect(url_for("plan.plan_list"))

    # 日数（Template 優先、なければ Plan.days）
    template_days = template.days or plan.days
    template_note = template.short_note or "説明が設定されていません。"

    # --- 交通手段一覧を itinerary_outline_json から抽出 ---
    traffic_methods = []
    if template.itinerary_outline_json:
        days_data = template.itinerary_outline_json.get("days", [])
        for d in days_data:
            tm = d.get("traffic_method")
            if tm:
                traffic_methods.append(tm)

    # 重複排除
    traffic_methods = list(dict.fromkeys(traffic_methods))

    # --- 宿泊先（Plan.hotel JSON から） ---
    hotel_json = plan.hotel or {}
    selected_id = hotel_json.get("selected_id")
    candidates = hotel_json.get("candidates", [])

    selected_hotel = None
    if selected_id:
        selected_hotel = next(
            (c for c in candidates if c.get("id") == selected_id),
            None
        )

    if selected_hotel:
        accommodation_label = selected_hotel.get("name")
        hotel_price = selected_hotel.get("price")
    else:
        accommodation_label = "選択中です"
        hotel_price = None

    # --- メタ情報 ---
    created_on_str = (
        plan.created_at.strftime("%Y-%m-%d %H:%M")
        if getattr(plan, "created_at", None)
        else ""
    )

    packing_summary = template.checklist_summary_json or {}
    meta = {
        "created_on": created_on_str,
        "price": f"{hotel_price}円 / 泊" if hotel_price is not None else "",
        "items_total": packing_summary.get("items_total", 0),
    }

    # --- 主な滞在場所 ---
    stay_locations = []
    if template.itinerary_outline_json:
        days_data = template.itinerary_outline_json.get("days", [])
        for d in days_data:
            for place in d.get("places", []):
                stay_locations.append(place)
    stay_locations = list(dict.fromkeys(stay_locations))

    # 自分のプランかどうか
    is_owned = (plan.user_id == user_id)


    return render_template(
        "plan/detail.html",
        plan=plan,
        template_days=template_days,
        traffic_methods=traffic_methods,
        accommodation_label=accommodation_label,
        meta=meta,
        stay_locations=stay_locations,
        packing_summary=packing_summary,
        is_owned=is_owned,
        template_note=template_note,
        template_id=template_id,  # 必要なら渡しておく
    )

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
            hotel = dummy_plan_data.get("hotel"),
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
