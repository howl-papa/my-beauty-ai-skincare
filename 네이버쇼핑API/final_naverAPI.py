import requests
import psycopg2
import re # HTML 태그 제거를 위해 re 라이브러리 추가
import os  # os 라이브러리 추가
from dotenv import load_dotenv  # dotenv 라이브러리 추가

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

# --- 1. 설정 정보 (환경 변수에서 불러오기) ---
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- 2. 네이버 쇼핑 API 호출 함수 ---
def search_naver_shopping(query):
    """네이버 쇼핑 API를 호출하여 검색 결과를 JSON 형태로 반환합니다."""
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": 20  # 가져올 상품 개수
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # 오류가 발생하면 예외를 발생시킴
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 호출 중 오류 발생: {e}")
        return None

# --- 3. 데이터베이스에 상품 정보 입력 함수 ---
def insert_products_to_db(products):
    """API에서 받아온 상품 목록을 DB에 입력합니다."""
    conn = None
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            client_encoding='UTF8'
        )
        cur = conn.cursor()

        # 각 상품에 대해 처리
        for item in products['items']:
            # <b>, </b> HTML 태그 제거
            product_name = re.sub(r'</?b>', '', item['title'])
            brand_name = item.get('brand', '기타') # 브랜드가 없는 경우 '기타'로 처리
            
            # 1. 브랜드 처리 (UPSERT: 없으면 넣고, 있으면 무시)
            # ON CONFLICT (brand_name) DO NOTHING: 이미 해당 브랜드 이름이 있으면 INSERT를 무시합니다.
            cur.execute(
                "INSERT INTO BRANDS (brand_name) VALUES (%s) ON CONFLICT (brand_name) DO NOTHING",
                (brand_name,)
            )
            
            # 2. 방금 입력했거나 이미 존재하는 브랜드의 ID 가져오기
            cur.execute(
                "SELECT brand_id FROM BRANDS WHERE brand_name = %s",
                (brand_name,)
            )
            brand_id_result = cur.fetchone()
            if not brand_id_result:
                print(f"브랜드 ID를 찾을 수 없습니다: {brand_name}")
                continue
            brand_id = brand_id_result[0]

            # 3. 상품 정보 입력 (중복 방지 로직 추가 가능)
            # 예: 같은 이름과 브랜드의 상품이 이미 있는지 확인 후 INSERT
            cur.execute(
                """
                INSERT INTO PRODUCTS (product_name, brand_id, image_url, barcode)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (barcode) DO NOTHING
                """,
                (product_name, brand_id, item.get('image'), item.get('productId')) # productId를 barcode로 활용
            )
            print(f"입력 완료: {product_name}")

        # 변경사항을 DB에 최종 반영
        conn.commit()
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"데이터베이스 작업 중 오류 발생: {error}")
        if conn is not None:
            conn.rollback() # 오류 발생 시 작업을 모두 되돌림
    finally:
        if conn is not None:
            conn.close() # 연결 종료

# --- 4. 메인 실행 부분 ---
if __name__ == "__main__":
    search_query = "크림"
    print(f"'{search_query}' 검색을 시작합니다...")
    
    shopping_data = search_naver_shopping(search_query)
    
    if shopping_data and shopping_data['items']:
        print(f"{len(shopping_data['items'])}개의 상품을 찾았습니다. DB 입력을 시작합니다.")
        insert_products_to_db(shopping_data)
        print("모든 작업이 완료되었습니다.")
    else:
        print("검색된 상품이 없거나 API 호출에 실패했습니다.")