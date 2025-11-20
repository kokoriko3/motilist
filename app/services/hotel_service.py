import requests
from flask import current_app

# 楽天トラベル キーワード検索API のURL
RAKUTEN_KEYWORD_SEARCH_URL = "https://app.rakuten.co.jp/services/api/Travel/KeywordHotelSearch/20170426"

def search_rakuten_hotels(keyword):
    
    # config.py からAPIキーを読み込む
    app_id = current_app.config['RAKUTEN_APP_ID']
    
    if not app_id:
        # APIキーが設定されていない場合はエラー（または空）を返す
        current_app.logger.warning("RAKUTEN_APP_ID が設定されていません。")
        return []

    params = {
        "applicationId": app_id,
        "format": "json",
        "keyword": keyword, # 例: "福岡"
        "hits": 30, # 取得件数 (最大30)
        "responseType": "medium", 
    }

    try:
        response = requests.get(RAKUTEN_KEYWORD_SEARCH_URL, params=params)
        response.raise_for_status() # HTTPエラーがあれば例外を発生
        data = response.json()

        if "Hotels" not in data:
            return []

        simplified_hotels = []
        for item in data['Hotels']:
            hotel = item['hotel'][0]['hotelBasicInfo'] # [0] に基本情報が入っている
            
            simplified_hotels.append({
                "id": hotel['hotelNo'],
                "name": hotel['hotelName'],
                "url": hotel['hotelInformationUrl'], # 予約ページのURL
                "imageUrl": hotel.get('hotelImageUrl'),
                "price": hotel.get('hotelMinCharge'), # 最安値（無い場合もある）
                "address": hotel.get('address1', '') + hotel.get('address2', ''),
                "review": hotel.get('reviewAverage', 'N/A')
            })
            
        return simplified_hotels

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"楽天APIの呼び出しに失敗しました: {e}")
        return [] # エラー時は空のリストを返す
    except Exception as e:
        current_app.logger.error(f"楽天APIのデータ処理に失敗しました: {e}")
        return []