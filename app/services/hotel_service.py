import requests
from flask import current_app
import json

# 楽天トラベル キーワード検索API のURL
RAKUTEN_KEYWORD_SEARCH_URL = "https://app.rakuten.co.jp/services/api/Travel/KeywordHotelSearch/20170426"

def search_rakuten_hotels(keyword):
    # config.py からAPIキーを読み込む
    app_id = current_app.config.get('RAKUTEN_APP_ID')
    
    if not app_id:
        current_app.logger.warning("RAKUTEN_APP_ID が設定されていません。")
        return []

    # メインの検索処理を行う内部関数
    def _execute_search(search_keyword):
        current_app.logger.info(f"楽天API検索開始: キーワード='{search_keyword}'")

        params = {
            "applicationId": app_id,
            "format": "json",
            "keyword": search_keyword,
            "hits": 30, 
        }
        
        try:
            response = requests.get(RAKUTEN_KEYWORD_SEARCH_URL, params=params)
            
            # 404 (Data Not Found) の場合は None を返して呼び出し元で判断させる
            if response.status_code == 404:
                current_app.logger.info(f"楽天API: キーワード '{search_keyword}' での検索結果は0件でした (404 Not Found)。")
                return None
                
            # その他のエラーはログに出して例外発生
            if response.status_code != 200:
                current_app.logger.error(f"楽天APIエラー詳細 [Status: {response.status_code}]: {response.text}")
                response.raise_for_status()

            data = response.json()
            
            # ▼▼▼ デバッグ用: レスポンスのキーを確認 ▼▼▼
            current_app.logger.debug(f"楽天APIレスポンスキー: {list(data.keys())}")
            if "error" in data:
                 current_app.logger.error(f"楽天APIエラーレスポンス: {data}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"楽天APIリクエストエラー: {e}")
            raise # 上位の try-except でキャッチさせる

    try:
        # 1回目の検索
        data = _execute_search(keyword)

        # もし404（見つからない）なら、キーワードを調整して再検索
        if data is None:
            fallback_keyword = "東京" # デフォルトのフォールバック先
            current_app.logger.info(f"キーワード '{keyword}' で見つからなかったため、'{fallback_keyword}' で再検索します。")
            data = _execute_search(fallback_keyword)
        
        # それでもダメ、またはデータがない場合
        if data is None:
             current_app.logger.warning(f"楽天API: データがNoneのため終了します。")
             return []
             
        # キー名の揺らぎに対応（hotels または Hotels）
        hotels_found = None
        if "hotels" in data:
            hotels_found = data['hotels']
        elif "Hotels" in data:
            hotels_found = data['Hotels']
            
        if not hotels_found:
            current_app.logger.warning(f"楽天API: レスポンスに 'hotels' または 'Hotels' キーが含まれていません。レスポンス内容: {json.dumps(data, ensure_ascii=False)[:200]}...")
            return []

        current_app.logger.info(f"楽天API: 合計 {len(hotels_found)} 件のホテルが見つかりました。")

        simplified_hotels = []
        for item in hotels_found:
            # ホテル情報は item['hotel'][0]['hotelBasicInfo'] にある想定
            # 念のため構造チェック
            if 'hotel' not in item or len(item['hotel']) == 0:
                continue
                
            hotel_info = None
            # 構造が複雑なため、hotelBasicInfoを探す
            for h_item in item['hotel']:
                if 'hotelBasicInfo' in h_item:
                    hotel_info = h_item['hotelBasicInfo']
                    break
            
            if not hotel_info:
                continue

            simplified_hotels.append({
                "id": hotel_info['hotelNo'],
                "name": hotel_info['hotelName'],
                "url": hotel_info['hotelInformationUrl'],
                "imageUrl": hotel_info.get('hotelImageUrl'),
                "price": hotel_info.get('hotelMinCharge'),
                "address": hotel_info.get('address1', '') + hotel_info.get('address2', ''),
                "review": hotel_info.get('reviewAverage', 'N/A')
            })
            
        # 取得データのログ出力
        current_app.logger.info(f"取得したホテルリスト: {json.dumps(simplified_hotels, ensure_ascii=False, indent=2)}")
        
        return simplified_hotels

    except Exception as e:
        current_app.logger.error(f"楽天API処理でエラーが発生しました（プラン作成は続行します）: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return []