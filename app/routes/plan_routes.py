import re
import json
import os
import math
from datetime import datetime, date, timedelta
from uuid import uuid4

# app/routes/plan_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from app.services.db_service import PlanDBService
from app.forms.plan_form import PlanCreateForm
from flask_login import current_user
from app.services import ai_service, hotel_service, db_service
from app.models.user import User
from app.extensions import db
# 修正: Checklist関連のモデルをインポート
from app.models.plan import Plan, TransportSnapshot, HotelSnapshot, Schedule, Template, Share
from app.models.checklist import Checklist, ChecklistItem, Item, Category

plan_bp = Blueprint("plan", __name__, url_prefix="/plans")


@plan_bp.before_request
def require_login():
    if request.endpoint == "plan.share_view":
        return None
    if current_user.is_authenticated or session.get("user_id"):
        return None
    flash("ログインしてください", "error")
    session["next_url"] = url_for("plan.plan_create_form")
    return redirect(url_for("auth.login"))


def paginate_items(items, page, per_page):
    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / per_page)) if total_items else 1
    page = max(1, min(page or 1, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], page, total_pages


def build_pagination(current_page, total_pages):
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    pages = {1, total_pages}

    if current_page <= 4:
        pages.update(range(1, 5))
    elif current_page >= total_pages - 3:
        pages.update(range(total_pages - 3, total_pages + 1))
    else:
        pages.update(range(current_page - 1, current_page + 2))

    sorted_pages = sorted(p for p in pages if 1 <= p <= total_pages)
    output = []
    last_page = 0
    for page in sorted_pages:
        if page - last_page > 1:
            output.append(None)
        output.append(page)
        last_page = page
    return output


def resolve_selected_hotel(plan):
    if not plan:
        return None
    hotel_json = plan.hotel or {}
    candidates = hotel_json.get("candidates", []) or []
    selected_id = hotel_json.get("selected_id")

    selected_hotel = None
    if selected_id is not None:
        selected_hotel = next(
            (c for c in candidates if str(c.get("id")) == str(selected_id)),
            None,
        )
    if not selected_hotel:
        selected_hotel = next(
            (c for c in candidates if c.get("is_selected")),
            None,
        )
    if not selected_hotel:
        snapshot = HotelSnapshot.query.filter_by(plan_id=plan.id, is_selected=True).first()
        if snapshot:
            selected_hotel = {"name": snapshot.name, "price": snapshot.price}
    return selected_hotel

# ----------------------------------------
#  プラン一覧（トップ）
# ----------------------------------------
@plan_bp.route("/", methods=["GET"])
def plan_list():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    page_size = 8

    # アプリとしての「有効なユーザID」を決める
    if current_user.is_authenticated:
        print("Flask-Login ログインあり")
        user_id = current_user.user_id
        show_login_link = False
    else:
        user_id = session.get("user_id")
        show_login_link = True

    if not user_id:
        print("ユーザIDなし（完全未ログイン＆ゲストも未作成）")
        return render_template(
            "plan/list.html",
            plans=[],
            show_login_link=True,
            active_nav="plans",
            query=q,
            page=1,
            total_pages=1,
            pagination=[],
        )

    print("ユーザIDあり:", user_id)
    templates = PlanDBService.get_all_templates_by_user_id(user_id=user_id)
    if q:
        q_lower = q.casefold()
        templates = [
            tpl for tpl in templates
            if q_lower in (tpl.public_title or "").casefold()
        ]

    templates_page, page, total_pages = paginate_items(templates, page, page_size)

    # --------------------------
    # ★ テンプレートごとに追加情報を付ける
    # --------------------------
    for tpl in templates_page:
        # ===== 交通手段 =====
        plan = PlanDBService.get_plan_by_id(tpl.plan_id, user_id)
        if plan:
            selected_transit = PlanDBService.get_selected_transit(plan.id, user_id)
            if selected_transit:
                tpl.transport_summary = selected_transit.transport_method
            else:
                # itinerary_outline_json から抽出
                traffic_methods = []
                outline = tpl.itinerary_outline_json or {}
                days = []
                if isinstance(outline, dict):
                    days = outline.get("days", [])
                for d in days:
                    tm = d.get("traffic_method")
                    if tm and tm not in traffic_methods:
                        traffic_methods.append(tm)
                tpl.transport_summary = " / ".join(traffic_methods) if traffic_methods else ""
        else:
            tpl.transport_summary = ""

        # ===== ホテル名（新規追加）=====
        # Plan を取得
        plan = PlanDBService.get_plan_by_id(tpl.plan_id, user_id)
        if not plan:
            tpl.hotel_name = "未設定"
            continue

        selected_hotel = resolve_selected_hotel(plan)
        tpl.hotel_name = selected_hotel.get("name") if selected_hotel and selected_hotel.get("name") else "選択中"

    return render_template(
        "plan/list.html",
        plans=templates_page,
        show_login_link=show_login_link,
        active_nav="plans",
        query=q,
        page=page,
        total_pages=total_pages,
        pagination=build_pagination(page, total_pages),
    )

# 公開プラン一覧
@plan_bp.route("/public", methods=["GET"])
def public_plan_list():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    page_size = 8

    # アプリとしての「有効なユーザID」を決める
    if current_user.is_authenticated:
        print("Flask-Login ログインあり")
        user_id = current_user.user_id
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
            page=1,
            total_pages=1,
            pagination=[],
        )

    print("ユーザIDあり:", user_id)
    try :

        templates = PlanDBService.get_public_templates()
        if q:
            q_lower = q.casefold()
            templates = [
                tpl for tpl in templates
                if q_lower in (tpl.public_title or "").casefold()
            ]

        templates_page, page, total_pages = paginate_items(templates, page, page_size)

        # --------------------------
        # ★ Template ごとに表示用フィールドを作る
        # --------------------------
        for tpl in templates_page:
            # ===== 交通手段まとめ =====
            plan = Plan.query.get(tpl.plan_id)  # 公開なので user_id で絞らない
            if plan:
                selected_transit = PlanDBService.get_selected_transit(plan.id, tpl.user_id)
                if selected_transit:
                    tpl.transport_summary = selected_transit.type
                else:
                    # itinerary_outline_json から抽出
                    traffic_methods = []
                    outline = tpl.itinerary_outline_json or {}
                    days = []
                    if isinstance(outline, dict):
                        days = outline.get("days", [])
                    for d in days:
                        tm = d.get("traffic_method")
                        if tm and tm not in traffic_methods:
                            traffic_methods.append(tm)
                    tpl.transport_summary = " / ".join(traffic_methods) if traffic_methods else ""
            else:
                tpl.transport_summary = ""

            # ===== ホテル名（Plan 経由で取得） =====
            if plan and plan.hotel:
                selected_hotel = resolve_selected_hotel(plan)
                tpl.hotel_name = selected_hotel.get("name") if selected_hotel and selected_hotel.get("name") else "選択中"
            else:
                tpl.hotel_name = "未設定"

        return render_template(
            "plan/public_list.html",
            plans=templates_page,
            query=q,
            result_count=len(templates),
            active_nav="public",
            show_login_link=show_login_link,
            page=page,
            total_pages=total_pages,
            pagination=build_pagination(page, total_pages),
        )

    except Exception as e:
        current_app.logger.error(f"Public plan list error: {e}")
        flash("表示されるデータがありませんでした")
        return render_template(
            "plan/public_list.html",
            plans=[],              # エラー時は空リスト
            query=q,
            result_count=0,
            active_nav="public",
            show_login_link=show_login_link,
            page=1,
            total_pages=1,
            pagination=[],
        )

@plan_bp.route("/<int:template_id>/delete", methods=["POST"])
def delete_plan(template_id):
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    if not user_id:
        flash("ログインしてください", "error")
        return redirect(url_for("auth.login"))

    template = Template.query.filter_by(template_id=template_id, user_id=user_id).first()
    if not template:
        flash("対象のプランが見つかりません。", "error")
        return redirect(url_for("plan.plan_list"))

    plan = Plan.query.filter_by(id=template.plan_id, user_id=user_id).first()

    try:
        if plan:
            db.session.delete(plan)
        else:
            db.session.delete(template)
        db.session.commit()
        flash("プランを削除しました。", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete plan failed: {e}")
        flash("プランの削除に失敗しました。", "error")

    return redirect(url_for("plan.plan_list"))


# ----------------------------------------
#  交通手段選択画面
# ----------------------------------------
@plan_bp.route("/transit", methods=["GET", "POST"])
def plan_transit():
    plan_id = session.get("plan_id")
    
    if not plan_id:
        flash("プランが選択されていません。先にプランを作成してください。", "warning")
        return redirect(url_for("plan.plan_create_form"))

    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    options = PlanDBService.get_transit_by_id(plan_id, user_id=user_id)
    selected_transit = PlanDBService.get_selected_transit(plan_id, user_id=user_id)
    selected_type = selected_transit.transport_method if selected_transit else None

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
                return redirect(url_for("plan.transit_confirm"))

    button_label = "変更" if selected_type else "確定"

    return render_template(
        "plan/transit.html",
        plan=plan,
        options=options,
        selected_type=selected_type,
        confirm_target=url_for("plan.stay_select"),
        button_label=button_label
    )

@plan_bp.route("/transit/confirm", methods=["GET"])
def transit_confirm():
    plan_id = session.get("plan_id")
    if not plan_id:
        flash("プランが選択されていません。先にプランを作成してください。", "warning")
        return redirect(url_for("plan.plan_create_form"))

    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    selected_transit = PlanDBService.get_selected_transit(plan_id, user_id=user_id)

    if not selected_transit:
        flash("交通手段を選択してください。", "warning")
        return redirect(url_for("plan.plan_transit"))

    return render_template(
        "plan/transport_confirm.html",
        plan=plan,
        selected_transit=selected_transit,
    )

@plan_bp.route("/stay/", methods=["GET", "POST"])
def stay_select():
    """??????Plan.hotel ???? HotelSnapshot ??????????"""
    plan_id = session.get("plan_id")
    if plan_id is None:
        flash("??????????????", "error")
        return redirect(url_for("plan.plan_list"))

    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    if not plan:
        flash("????????????", "warning")
        return redirect(url_for("plan.plan_create_form"))

    hotel_json = plan.hotel or {}
    selected_id = hotel_json.get("selected_id")

    # ????????????reselect=1 ??????
    reselect = request.args.get("reselect")
    sort_key = request.args.get("sort")
    page = request.args.get("page", 1, type=int)
    if request.method == "GET" and selected_id is not None and reselect != "1":
        return redirect(url_for("plan.stay_confirm"))

    # ---------- POST: ???? ----------
    if request.method == "POST":
        selected_id = request.form.get("hotel_id", type=int)
        if selected_id is None:
            flash("??????????????", "error")
            return redirect(url_for("plan.stay_select"))

        hotel_json = plan.hotel or {}
        candidates = hotel_json.get("candidates", [])
        selected = next((c for c in candidates if c.get("id") == selected_id), None)
        if selected is None:
            flash("???????????????", "error")
            return redirect(url_for("plan.stay_select"))

        hotel_json["selected_id"] = selected_id
        plan.hotel = hotel_json
        db.session.commit()
        flash("????????????????????????", "success")
        return redirect(url_for("plan.stay_confirm"))

    # ---------- GET: ???? ----------
    candidates = hotel_json.get("candidates", [])

    # Plan.hotel ?????????????????????????????
    if not candidates:
        snapshots = PlanDBService.get_hotels_by_id(plan_id, user_id=user_id)
        candidates = []
        selected_snapshot_id = None
        for snap in snapshots:
            try:
                price_val = int(snap.price) if snap.price not in (None, "", "None") else None
            except (TypeError, ValueError):
                price_val = None

            try:
                review_val = float(snap.review) if snap.review not in (None, "", "None") else None
            except (TypeError, ValueError):
                review_val = None

            candidates.append(
                {
                    "id": snap.id,  # ????????ID??????
                    "hotel_no": snap.hotel_no,
                    "name": snap.name,
                    "url": snap.url,
                    "image_url": snap.image_url,
                    "price": price_val,
                    "address": snap.address,
                    "review": review_val,
                    "is_selected": snap.is_selected,
                }
            )
            if snap.is_selected:
                selected_snapshot_id = snap.id

        if candidates:
            hotel_json = {
                "candidates": candidates,
                "selected_id": selected_snapshot_id or selected_id,
            }
            plan.hotel = hotel_json
            db.session.commit()
            selected_id = hotel_json.get("selected_id")

    stay_options = []
    for c in candidates:
        raw_price = c.get("price")
        try:
            price_value = int(raw_price) if raw_price not in (None, "", "None") else None
        except (TypeError, ValueError):
            price_value = None

        raw_review = c.get("review")
        try:
            review_value = float(raw_review) if raw_review not in (None, "", "None") else None
        except (TypeError, ValueError):
            review_value = None

        stay_options.append(
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "price": price_value,
                "address": c.get("address"),
                "url": c.get("url"),
                "image_url": c.get("image_url"),
                "review": review_value,
                "is_selected": (c.get("id") == selected_id),
            }
        )

    # ??????????
    def safe_price(val, default):
        return val if val is not None else default

    def safe_review(val):
        return val if val is not None else float("-inf")

    if sort_key == "price-asc":
        stay_options.sort(key=lambda s: (safe_price(s["price"], float("inf")), s["id"] or 0))
    elif sort_key == "price-desc":
        stay_options.sort(key=lambda s: (safe_price(s["price"], float("-inf")), s["id"] or 0), reverse=True)
    elif sort_key == "review-desc":
        stay_options.sort(key=lambda s: (safe_review(s["review"]), s["id"] or 0), reverse=True)

    # ??????5?/????
    page_size = 5
    total_pages = max(1, math.ceil(len(stay_options) / page_size)) if stay_options else 1
    page = max(1, min(page or 1, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    stay_options_page = stay_options[start:end]

    return render_template(
        "plan/hotel_select.html",
        plan=plan,
        stay_options=stay_options_page,
        page=page,
        total_pages=total_pages,
        sort_key=sort_key,
    )


@plan_bp.route("/stay/confirm", methods=["GET"])
def stay_confirm():
    plan_id = session.get("plan_id")
    if plan_id is None:
        flash("プランが指定されていません。", "error")
        return redirect(url_for("plan.plan_list"))

    if current_user.is_authenticated:
        user_id = current_user.user_id
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
    plan_id = session.get("plan_id")
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")

    if not plan_id or not user_id:
        flash("プランが指定されていません。最初からやり直してください。", "warning")
        return redirect(url_for("plan.plan_list"))

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    schedule_obj = PlanDBService.get_schedule_by_id(plan_id,user_id)

    if not plan or not schedule_obj:
        flash("プラン情報の取得に失敗しました。", "warning")
        return redirect(url_for("plan.plan_list"))

    format_days = []

    data = schedule_obj.daily_plan_json or []

    for day_data in data:
        day_num = day_data.get("day")
        details = day_data.get("details", [])

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
        
    duration_label = ""
    date_range_label = ""
    try:
        nights = max(plan.days - 1, 0) if plan.days else 0
        duration_label = f"{nights}泊{plan.days}日" if plan.days else ""
        if plan.start_date:
            end_date = plan.start_date + timedelta(days=max(plan.days - 1, 0) if plan.days else 0)
            date_range_label = f"{plan.start_date.month}月{plan.start_date.day}日~{end_date.month}月{end_date.day}日"
    except Exception:
        pass

    return render_template(
        "plan/schedule_list.html",
        days=format_days,
        plan=plan,
        duration_label=duration_label,
        date_range_label=date_range_label
    )

@plan_bp.route("/schedule/edit", methods=["GET"])
def schedule_edit():
    plan_id = session.get("plan_id")
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")

    # 1. 既存のデータを取得 (schedule_listと同じロジック)
    schedule_obj = PlanDBService.get_schedule_by_id(plan_id, user_id)
    
    # データがない場合のガード
    if not schedule_obj:
        flash("スケジュールが見つかりません", "warning")
        return redirect(url_for("plan.schedule_list"))

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)

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

    return render_template("plan/schedule_edit.html", days=format_days, plan=plan)

@plan_bp.route("/schedule/update", methods=["POST"])
def schedule_update():
    plan_id = session.get("plan_id")
    # user_id = session.get("user_id") # 必要に応じて権限チェック

    # 1. JavaScriptから送信されたJSONを受け取る
    new_schedule_data = request.get_json()
    
    if not new_schedule_data:
        return jsonify({"error": "データがありません"}), 400

    try:
        # raise Exception("これはテスト用の意図的なエラーです！")
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
        return jsonify({"error": "保存に失敗しました"}), 500

@plan_bp.route("/save", methods=["POST"])
def save_plan_template():
    plan_id = session.get("plan_id")
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")

    payload = request.get_json() or {}
    title = (payload.get("title") or "").strip()
    public_title = (payload.get("public_title") or "").strip()
    description = (payload.get("description") or "").strip()
    tags = (payload.get("tags") or "").strip()
    visibility = (payload.get("visibility") or "private").strip() or "private"
    storage = (payload.get("storage") or "server").strip() or "server"
    flag_a = bool(payload.get("flag_a"))
    flag_b = bool(payload.get("flag_b"))
    target_date = (payload.get("date") or "").strip()
    publish_date = None

    if visibility not in ("public", "private", "link"):
        visibility = "private"
    if storage not in ("local", "server"):
        storage = "server"

    if not plan_id or not user_id:
        return jsonify({"status": "error", "message": "プランが選択されていません。"}), 400

    if not title:
        return jsonify({"status": "error", "message": "タイトルを入力してください。"}), 400
    if len(title) > 50:
        return jsonify({"status": "error", "message": "タイトルは50文字以内で入力してください。"}), 400
    if public_title and len(public_title) > 60:
        return jsonify({"status": "error", "message": "公開タイトルは60文字以内で入力してください。"}), 400
    if len(description) > 500:
        return jsonify({"status": "error", "message": "説明は500文字以内で入力してください。"}), 400
    if tags and len(tags) > 100:
        return jsonify({"status": "error", "message": "タグは100文字以内で入力してください。"}), 400
    if target_date:
        try:
            publish_date = date.fromisoformat(target_date)
        except ValueError:
            return jsonify({"status": "error", "message": "日付を正しく入力してください。"}), 400

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    schedule = PlanDBService.get_schedule_by_id(plan_id, user_id)

    if not plan or not schedule:
        return jsonify({"status": "error", "message": "プラン情報の取得に失敗しました。"}), 404

    if title:
        plan.title = title

    template = PlanDBService.save_template(
        plan=plan,
        schedule=schedule,
        title=public_title or title,
        short_note=description,
        visibility=visibility,
        tags=tags,
        storage=storage,
        flag_a=flag_a,
        flag_b=flag_b,
        publish_date=publish_date,
    )

    if not template:
        return jsonify({"status": "error", "message": "保存に失敗しました。"}), 500

    return jsonify(
        {
            "status": "success",
            "redirect": url_for("plan.plan_list"),
        }
    )

@plan_bp.route("/share", methods=["POST"])
def share_plan():
    plan_id = session.get("plan_id")
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")

    if not plan_id or not user_id:
        return jsonify({"status": "error", "message": "プランが選択されていません。"}), 400

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    schedule = PlanDBService.get_schedule_by_id(plan_id, user_id)

    if not plan or not schedule:
        return jsonify({"status": "error", "message": "プラン情報の取得に失敗しました。"}), 404

    # テンプレートを生成/更新して公開にする
    template = PlanDBService.save_template(
        plan=plan,
        schedule=schedule,
        title=plan.title or (plan.destination or "無題のプラン"),
        short_note=plan.purpose or "",
        visibility="public",
        storage="server",
        flag_a=False,
        flag_b=False,
        publish_date=None,
    )
    if not template:
        return jsonify({"status": "error", "message": "共有URLの生成に失敗しました。"}), 500

    # 共有レコード生成
    share = PlanDBService.create_share(template)
    if not share:
        return jsonify({"status": "error", "message": "共有URLの生成に失敗しました。"}), 500

    share_url = f"{request.host_url.rstrip('/')}{url_for('plan.share_view', token=share.url_token)}"

    return jsonify({"status": "success", "url": share_url})

@plan_bp.route("/share/<token>", methods=["GET"])
def share_view(token):
    share = PlanDBService.get_share_by_token(token)
    if not share:
        flash("チェックリストが存在しません", "warning")
        return redirect(url_for("plan.plan_list"))

    template = share.template
    plan = Plan.query.get(template.plan_id) if template else None

    # 日数（Template 優先、なければ Plan.days）
    template_days = template.days or plan.days
    template_note = template.short_note or "説明が設定されていません。"
    
    # まず、選択された交通手段を取得
    selected_transit = PlanDBService.get_selected_transit(plan.id, template.user_id)
    if selected_transit:
        traffic_methods = [selected_transit.transport_method]
    else:
        # 選択されていない場合、itinerary_outline_json から抽出
        if template.itinerary_outline_json:
            itinerary_outline = template.itinerary_outline_json
            days_data = []
            if isinstance(itinerary_outline, dict):
                days_data = itinerary_outline.get("days", [])
            for d in days_data:
                tm = d.get("traffic_method")
                if tm:
                    traffic_methods.append(tm)
            # 重複排除
            traffic_methods = list(dict.fromkeys(traffic_methods))

    # --- 宿泊先（Plan.hotel JSON から） ---
    selected_hotel = resolve_selected_hotel(plan)
    if selected_hotel and selected_hotel.get("name"):
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
    if not packing_summary or (not packing_summary.get("essential") and not packing_summary.get("extra")):
        summary = PlanDBService.get_checklist_summary(plan.id, template.user_id)
        if summary.get("items_total", 0) > 0:
            packing_summary = summary

    # 共有ビューでは常にチェックリスト形式で表示
    checklist_display = {
        "essential": [
            {"id": f"guest_essential_{i}", "name": item["name"], "quantity": item.get("quantity", 1), "unit": item.get("unit", ""), "is_checked": False}
            for i, item in enumerate(packing_summary.get("essential", []))
        ],
        "extra": [
            {"id": f"guest_extra_{i}", "name": item["name"], "quantity": item.get("quantity", 1), "unit": item.get("unit", ""), "is_checked": False}
            for i, item in enumerate(packing_summary.get("extra", []))
        ]
    }
    display_total = len(checklist_display.get("essential", [])) + len(checklist_display.get("extra", []))

    meta = {
        "created_on": created_on_str,
        "price": f"{hotel_price}円 / 泊" if hotel_price is not None else "",
        "items_total": display_total,
    }

    # --- 主な滞在場所 ---
    stay_locations = []
    if template.itinerary_outline_json:
        itinerary_outline = template.itinerary_outline_json
        days_data = []
        if isinstance(itinerary_outline, dict):
            days_data = itinerary_outline.get("days", [])
        for d in days_data:
            for place in d.get("places", []):
                stay_locations.append(place)
    stay_locations = list(dict.fromkeys(stay_locations))

    display_title = template.public_title or plan.title or plan.destination or "プラン"

    is_logged_in = current_user.is_authenticated

    return render_template("plan/share_view.html", 
        template=template, 
        plan=plan, 
        share_url=request.url,
        template_days=template_days,
        traffic_methods=traffic_methods,
        accommodation_label=accommodation_label,
        meta=meta,
        stay_locations=stay_locations,
        checklist_display=checklist_display,
        template_note=template_note,
        display_title=display_title,
        is_logged_in=is_logged_in
    )

@plan_bp.route("/checklists", methods=["GET"])
def checklist_list():
    plan_id = session.get("plan_id")
    if not plan_id:
        flash("プランが選択されていません。", "warning")
        return redirect(url_for("plan.plan_list"))

    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    if not plan:
        flash("プランが見つかりません。", "warning")
        return redirect(url_for("plan.plan_list"))

    checklist_obj = PlanDBService.get_checklist_by_id(plan_id, user_id)
    if not checklist_obj:
        return render_template("plan/checklist_create.html", plan=plan)
    
    checklist_items = PlanDBService.get_checklist_item_by_id(checklist_obj.checklist_id)
    
    categories_dict = {}
    for item in checklist_items:
        category_name = item.category.name if item.category else "その他"
        if category_name not in categories_dict:
            categories_dict[category_name] = {
                "category_id": item.category.category_id if item.category else 0,
                "items": []
            }
        
        categories_dict[category_name]["items"].append({
            "id": item.checklist_item_id, # テンプレート側では 'id' として扱う
            "name": item.item.name,
            "checked": item.is_checked,
            "is_required": item.is_required,
            "quantity": item.quantity,
            "memo": item.memo
        })
    
    categories_list = [{"name": name, **data} for name, data in categories_dict.items()]
    return render_template("plan/checklist_list.html", categories=categories_list, plan=plan)

@plan_bp.route("/checklists/edit", methods=["GET"])
def checklist_edit():
    # 編集画面用にデータを取得して表示するロジックを追加
    plan_id = session.get("plan_id")
    if not plan_id:
        flash("プランが選択されていません。", "warning")
        return redirect(url_for("plan.plan_create_form"))

    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")

    plan = PlanDBService.get_plan_by_id(plan_id, user_id)
    if not plan:
        flash("プランが見つかりません。", "warning")
        return redirect(url_for("plan.plan_list"))
    
    checklist_obj = PlanDBService.get_checklist_by_id(plan_id, user_id)
    if not checklist_obj:
        # データがない場合は一覧（作成画面）へ戻す
        return redirect(url_for("plan.checklist_list"))

    checklist_items = PlanDBService.get_checklist_item_by_id(checklist_obj.checklist_id)
    
    # カテゴリごとにアイテムをグループ化
    # checklist_edit.html は category.title, category.id を期待しているためキーを合わせる
    categories_dict = {}
    for item in checklist_items:
        category_name = item.category.name if item.category else "その他"
        if category_name not in categories_dict:
            categories_dict[category_name] = {
                "id": item.category.category_id if item.category else 0,
                "title": category_name,
                "items": []
            }
        
        categories_dict[category_name]["items"].append({
            "name": item.item.name,
            "quantity": item.quantity,
            "is_checked": item.is_checked,
            "is_required": item.is_required
            # 必要に応じて他フィールドも
        })
    
    categories_list = list(categories_dict.values())

    return render_template("plan/checklist_edit.html", categories=categories_list, plan=plan)

@plan_bp.route("/checklists/update", methods=["POST"])
def checklist_update():
    plan_id = session.get("plan_id")
    if plan_id is None:
        return jsonify({"error": "プランが指定されていません。"}), 400
    
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    if not user_id:
        return jsonify({"error": "ユーザー情報が見つかりません。"}), 401

    data = request.get_json()
    if not data or 'categories' not in data:
        return jsonify({"error": "送信データが不正です。"}), 400
    
    categories_data = data['categories']

    try:
        # raise Exception("テスト用ののエラー")
        # 1. 既存のチェックリストを取得
        checklist = PlanDBService.get_checklist_by_id(plan_id, user_id)
        if not checklist:
            # なければ作成（念のため）
            plan = PlanDBService.get_plan_by_id(plan_id, user_id)
            if not plan: return jsonify({"error": "プランが見つかりません"}), 404
            checklist = PlanDBService.create_checklist(plan_id, title=f"{plan.title}の持ち物リスト")
        
        # 2. 既存のアイテムを一度全て削除（シンプルに洗い替え戦略）
        # ※DBServiceにメソッドがないため、ここで直接モデル操作を行います
        #   本来はService層に delete_checklist_items のようなメソッドを作るのが望ましいです
        ChecklistItem.query.filter_by(checklist_id=checklist.checklist_id).delete()
        
        # 3. 送信されたデータを登録
        for cat_data in categories_data:
            category_name = cat_data.get('category')
            items = cat_data.get('items', [])
            
            if not category_name or not items:
                continue

            category = PlanDBService.get_or_create_category(category_name)
            
            for item_data in items:
                name = item_data.get('name')
                qty = item_data.get('quantity') or "1"
                
                if not name: continue

                item_obj = PlanDBService.get_or_create_item(name, category.category_id)
                
                new_checklist_item = ChecklistItem(
                    checklist_id=checklist.checklist_id,
                    item_id=item_obj.item_id,
                    category_id=category.category_id,
                    quantity=qty,
                    is_required=bool(item_data.get('is_required')),
                    is_checked=False   # 編集でリセットするか、保持するかは仕様次第（ここではリセット）
                )
                db.session.add(new_checklist_item)
        
        db.session.commit()
        PlanDBService.update_template_checklist_summary(plan_id, user_id)
        return jsonify({"status": "success", "redirect_url": url_for("plan.checklist_list")})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"保存中にエラーが発生しました: {str(e)}"}), 500

@plan_bp.route("/checklists/items/<int:item_id>", methods=["PATCH"])
def checklist_item_toggle(item_id):
    """持ち物アイテムのチェック状態を切り替えるAPI"""
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json() or {}
    is_checked = payload.get("is_checked")

    # Service側で checklist_item_id を用いて更新
    success = PlanDBService.toggle_checklist_item(item_id, is_checked)
    if success:
        try:
            PlanDBService.update_template_checklist_summary_by_item(item_id, user_id)
        except Exception as e:
            current_app.logger.error(f"Summary update error: {str(e)}")
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Update failed"}), 400

@plan_bp.route('/<int:plan_id>/checklist/reorder', methods=['POST'])
def reorder_checklist(plan_id):
    """ドラッグ&ドロップによる並び替え順の保存"""
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.get_json()
    try:
        # 文字列として送られてくる可能性があるので明示的にint変換
        dragged_id = int(data.get('dragged_id'))
        target_id = int(data.get('target_id'))
        
        # Service層を呼び出し。
        # 内部で「.id」を使っている箇所があれば、Service側で「.checklist_item_id」に修正が必要です。
        success = PlanDBService.reorder_checklist_items(plan_id, dragged_id, target_id, user_id=user_id)
        
        return jsonify({'success': bool(success)})
    except Exception as e:
        current_app.logger.error(f"Reorder Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    
@plan_bp.route("/checklists/generate", methods=["POST"])
def checklist_generate():
    plan_id = session.get("plan_id")
    if plan_id is None:
        return jsonify({"error": "プランが指定されていません。"}), 400
    
    user_id = current_user.user_id if current_user.is_authenticated else session.get("user_id")
    if not user_id:
        return jsonify({"error": "ユーザー情報が見つかりません。"}), 401

    # 既存のチェックリストを確認
    existing_checklist = PlanDBService.get_checklist_by_id(plan_id, user_id)
    if existing_checklist:
        return jsonify({"error": "チェックリストは既に存在します。", "redirect_url": url_for("plan.checklist_list")}), 409

    try:
        # raise Exception("テスト")
        plan = PlanDBService.get_plan_by_id(plan_id, user_id)
        if not plan:
            return jsonify({"error": "対象のプランが見つかりません。"}), 404

        schedule_obj = PlanDBService.get_schedule_by_id(plan_id, user_id)
        if not schedule_obj:
            return jsonify({"error": "スケジュールの取得に失敗しました。"}), 404

        # AIから持ち物リストを生成
        response_data = ai_service.generate_item_list_from_plan(plan, schedule_obj.daily_plan_json)
        
        if not response_data or 'checklist' not in response_data:
            return jsonify({"error": "AIによる持ち物リストの生成に失敗しました。"}), 500

        item_list = response_data.get('checklist', [])

        # チェックリストをDBに保存
        checklist = PlanDBService.create_checklist(plan_id=plan.id, title=f"{plan.title}の持ち物リスト")
        if not checklist:
            return jsonify({"error": "チェックリストの作成に失敗しました。"}), 500

        # アイテムをDBに保存
        success = PlanDBService.add_items_to_checklist(checklist.checklist_id, item_list)
        
        if success:
            flash("AIが持ち物リストを生成しました！", "success") # flashメッセージはリダイレクト先で表示される
            return jsonify({"status": "success", "redirect_url": url_for("plan.checklist_list")})
        else:
            return jsonify({"error": "持ち物リストの保存中にエラーが発生しました。"}), 500

    except Exception as e:
        current_app.logger.error(f"Checklist generation failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "予期せぬエラーにより、持ち物リストの生成に失敗しました。"}), 500
# プラン詳細ページ
@plan_bp.route("/<int:template_id>", methods=["GET"])
def plan_detail(template_id):
    # --- ユーザー判定 ---
    if current_user.is_authenticated:
        user_id = current_user.user_id
    else:
        user_id = session.get("user_id")

    # --- Template を主役に取得 ---
    template = PlanDBService.get_all_templates_by_id(template_id=template_id)
    if not template:
        print(f"指定されたテンプレートが存在しません: template_id={template_id}")
        flash("指定されたプランは存在しません。", "error")
        return redirect(url_for("plan.plan_list"))

    # --- 可視性に応じて Plan の取得方法を切り替える ---
    is_owned = False  # デフォルトは他人所有
    plan = None

    if template.visibility == "public":
        plan = Plan.query.get(template.plan_id)
        if user_id and plan:
             is_owned = (plan.user_id == user_id)
    
    # public でない場合、または public だが上記で plan が取れなかった場合
    if not plan:
        # ログイン済み or ゲストセッションがあるかチェック
        if not user_id:
            # ログインを促すページにリダイレクト
            flash("このプランを閲覧するにはログインが必要です。", "info")
            # sessionに遷移先を保存
            session['next_url'] = url_for('plan.plan_detail', template_id=template_id)
            return redirect(url_for("auth.login_form"))
        
        # 自分自身のプランとして取得を試みる
        plan = PlanDBService.get_plan_by_id(template.plan_id, user_id)
        if plan:
            is_owned = True

    if not plan:
        print(f"権限がないか、紐づくプランが存在しません: plan_id={template.plan_id}, user_id={user_id}")
        flash("指定されたプランを閲覧する権限がありません。", "error")
        return redirect(url_for("plan.plan_list"))

    # 日数（Template 優先、なければ Plan.days）
    template_days = template.days or plan.days
    template_note = template.short_note or "説明が設定されていません。"

    # --- 交通手段一覧を取得 ---
    traffic_methods = []
    
    # まず、選択された交通手段を取得
    selected_transit = PlanDBService.get_selected_transit(plan.id, template.user_id)
    if selected_transit:
        traffic_methods = [selected_transit.transport_method]
    else:
        # 選択されていない場合、itinerary_outline_json から抽出
        if template.itinerary_outline_json:
            itinerary_outline = template.itinerary_outline_json
            days_data = []
            if isinstance(itinerary_outline, dict):
                days_data = itinerary_outline.get("days", [])
            for d in days_data:
                tm = d.get("traffic_method")
                if tm:
                    traffic_methods.append(tm)
            # 重複排除
            traffic_methods = list(dict.fromkeys(traffic_methods))

    # --- 宿泊先（Plan.hotel JSON から） ---
    selected_hotel = resolve_selected_hotel(plan)
    if selected_hotel and selected_hotel.get("name"):
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
    if not packing_summary or (not packing_summary.get("essential") and not packing_summary.get("extra")):
        summary = PlanDBService.get_checklist_summary(plan.id, template.user_id)
        if summary.get("items_total", 0) > 0:
            packing_summary = summary
            if user_id == template.user_id:
                template.checklist_summary_json = summary
                template.items_count = summary.get("items_total", 0)
                db.session.commit()

    checklist_display = None
    display_total = None
    if is_owned:
        checklist_display = PlanDBService.get_checklist_display(plan.id, user_id)
        if checklist_display and (checklist_display.get("essential") or checklist_display.get("extra")):
            display_total = len(checklist_display.get("essential", [])) + len(checklist_display.get("extra", []))
    else:
        # 所有者でない場合、checklist_display は None のまま（テーブル表示）
        pass

    meta = {
        "created_on": created_on_str,
        "price": f"{hotel_price}円 / 泊" if hotel_price is not None else "",
        "items_total": display_total if display_total is not None else packing_summary.get("items_total", 0),
    }

    # --- 主な滞在場所 ---
    stay_locations = []
    if template.itinerary_outline_json:
        itinerary_outline = template.itinerary_outline_json
        days_data = []
        if isinstance(itinerary_outline, dict):
            days_data = itinerary_outline.get("days", [])
        for d in days_data:
            for place in d.get("places", []):
                stay_locations.append(place)
    stay_locations = list(dict.fromkeys(stay_locations))

    source = request.args.get("source")
    if source == "public":
        active_nav = "public"
    elif source == "own":
        active_nav = "plans"
    else:
        active_nav = "plans" if is_owned else "public"

    if is_owned:
        session["plan_id"] = plan.id

    display_title = template.public_title or plan.title or plan.destination or "プラン"

    return render_template(
        "plan/detail.html",
        plan=plan,
        template_days=template_days,
        traffic_methods=traffic_methods,
        accommodation_label=accommodation_label,
        meta=meta,
        stay_locations=stay_locations,
        packing_summary=packing_summary,
        checklist_display=checklist_display,
        is_owned=is_owned,
        template_note=template_note,
        display_title=display_title,
        active_nav=active_nav,
        template_id=template_id,  # 必要なら渡しておく
    )

# ----------------------------------------
# 他人のプランをコピーして保存するルート
# ----------------------------------------
# HTMLのリンク(<a>)から呼ばれるため、GETメソッドを許可する必要があります
@plan_bp.route("/plan_modals/<int:plan_id>", methods=["GET", "POST"])
def plan_modals(plan_id):
    # ユーザーIDの取得
    if current_user.is_authenticated:
        user_id = current_user.user_id
    else:
        user_id = session.get("user_id")
    
    if not user_id:
        flash("ユーザー認証が切れています。再度ログインしてください。", "warning")
        return redirect(url_for("auth.login"))

    # サービス層の copy_plan を呼び出す
    new_plan_id = PlanDBService.copy_plan(plan_id, user_id)

    if new_plan_id:
        flash("プランを自分のプランとして保存しました！", "success")
        # 新しく作ったプランを操作対象にするためセッションを更新
        session["plan_id"] = new_plan_id
    else:
        flash("プランの保存に失敗しました。", "danger")

    return redirect(url_for("plan.plan_list"))


# ----------------------------------------
# 自分のプランを編集モードで開くルート
# ----------------------------------------
# HTMLのリンク(<a>)から呼ばれるため、GETメソッドに変更します
@plan_bp.route("/plan/edit/<int:plan_id>", methods=["GET"])
def plan_edit(plan_id):
    # 編集対象のプランIDをセッションにセット
    session["plan_id"] = plan_id
    
    # 交通手段選択画面（編集フローの最初）へリダイレクト
    return redirect(url_for("plan.plan_transit"))
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
            user_id = current_user.user_id
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
            current_app.logger.error("Error generating plan", exc_info=True)
            flash(f"プラン生成中にエラーが発生しました: {e}", "danger")
            return (
                render_template(
                    "plan/plan_create.html",
                    form=form,
                    need_options=need_options,
                    active_nav="plans",
                ),
                502,
            )
    
    if request.method == "POST" and not form.validate():
        flash("入力内容を確認してください。", "danger")

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
        user_id = current_user.user_id
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


