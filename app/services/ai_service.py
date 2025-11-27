import os
import json
import google.generativeai as genai # ★ OpenAI の代わりに Gemini をインポート
import google.generativeai as genai
from google.generativeai import GenerationConfig
from flask import current_app # flask から current_app をインポート

def generate_plan_from_inputs(destination,start_point, days, purpose_raw, **kwargs):    
    try:
        api_key = current_app.config['GEMINI_API_KEY']
        
        if not api_key:
            raise ValueError("GEMINI_API_KEYが設定されていません。")

        genai.configure(api_key=api_key)

        system_prompt = "あなたは日本の旅行プランを作成するプロのAIアシスタントです。"

        user_prompt = f"""
        以下の条件に基づいて、日本の旅行プランを「主要交通手段の提案」「日程」を含む
        厳密なJSON形式で出力してください。
        
        # 条件
        - 目的地: {destination}
        - 日数: {days}日間
        - 出発地点: {start_point}
        - 旅行の目的: {purpose_raw}
        - その他の希望: {kwargs.get('travel_style', '特になし')}
        
        #指示
        1.  「transport_options」キーで、出発地から目的地までの主要な交通手段を4パターン提案してください。
            - 「価格重視」（価格重視）
            - 「速度重視」（速度重視）
            - 「おすすめ」（AIのおすすめバランス）
            - 「車利用」（車利用）
            - 各提案には `method` (手段), `estimated_cost` (円), `estimated_time` (分) を含めてください。
            - 概算で構いません。不明な場合は null を入れてください。
        2.  「itinerary」の日程詳細(details)では、目的地に到着してからの短距離移動（徒歩、バス、タクシーなど）のみを
            `transport_notes` キーとして簡潔に提案してください。

        # 出力JSON形式
        {{
          "plan_title": "（AIが考えたプランのタイトル）",
          "transport_options": {{
            "価格重視": {{
              "method": "夜行バス + 徒歩"
              "estimated_cost": 8000,
              "estimated_time": 480,
              "transit_count":1,
              "departure_time":7:00,
              "arrival_time":14:00
            }},
            "速度重視": {{
              "method": "新幹線 + 電車",
              "estimated_cost": 25000,
              "estimated_time": 180,
              "transit_count":3,
              "departure_time":7:00,
              "arrival_time":10:00
            }},
            "おすすめ": {{
              "method": "飛行機（LCC） + 電車",
              "estimated_cost": 15000,
              "estimated_time": 240,
              "transit_count":3,
              "departure_time":7:00,
              "arrival_time":12:00
            }},
            "車": {{
              "method": "自家用車（高速道路利用）",
              "estimated_cost": 12000,
              "estimated_time": 420
            }}
          }},
          "itinerary": [
            {{
              "day": 1,
              "details": [
                {{"time": "09:00", "activity": "〇〇ホテル 到着", "transport_notes": "空港から電車（約30分）"}},
                {{"time": "12:00", "activity": "ランチ：〇〇名物", "transport_notes": "ホテルから徒歩5分"}}
              ]
            }}
          ]
        }}
        """


        generation_config = GenerationConfig(response_mime_type="application/json")
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction=system_prompt
        )

        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )

        if not response.text:
            raise Exception("AIからの応答が空でした。")

        ai_response_content = response.text
            
        return json.loads(ai_response_content)

    except Exception as e:
        current_app.logger.error(f"AIサービスでエラーが発生: {e}")
        raise Exception(f"AIプランの生成に失敗しました: {e}")
    

def generate_item_list_from_plan(plan):    
    try:
        api_key = current_app.config['GEMINI_API_KEY']
        
        if not api_key:
            raise ValueError("GEMINI_API_KEYが設定されていません。")

        genai.configure(api_key=api_key)

        system_prompt = "あなたは日本の旅行プランから旅行に必要な持ち物を提案するプロのAIアシスタントです。"

        user_prompt = f"""
        以下の条件に基づいて、日本の旅行プランから持ち物リストを
        厳密なJSON形式で出力してください。
        
        # 条件
        - 旅行プラン:{plan}
        
        # 出力JSON形式
        {{
          "checklist": [
            {{
              "category": "貴重品",
              "required_items": ["財布", "スマホ"],
              "items": [""]
            }},
            {{
              "category": "衣類",
              "required_items": ["下着"],
              "items": ["Tシャツ（○日分）"]
            }},
            {{
              "category": "バス用品、コスメ",
              "required_items": ["日焼け止め"],
              "items": ["シャンプー"]
            }},
            {{
              "category": "その他",
              "required_items": ["虫よけスプレー"]
              "items": ["保険証"],
            }}
          ]
        }}
        """

        generation_config = GenerationConfig(response_mime_type="application/json")
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction=system_prompt
        )

        response = model.generate_content(
            user_prompt,
            generation_config=generation_config
        )

        if not response.text:
            raise Exception("AIからの応答が空でした。")

        ai_response_content = response.text
            
        return json.loads(ai_response_content)

    except Exception as e:
        current_app.logger.error(f"AIサービスでエラーが発生: {e}")
        raise Exception(f"AIプランの生成に失敗しました: {e}")
    
    # def dev_generate_plan_from_inputs():
    #     plan = 
    #     return 