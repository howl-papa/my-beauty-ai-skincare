import psycopg2
import os
import re
from dotenv import load_dotenv

def process_product_ingredients():
    """
    PRODUCTS 테이블의 ingredients 텍스트를 파싱하여
    INGREDIENTS와 PRODUCT_INGREDIENTS 테이블에 관계 데이터를 구축합니다.
    """
    load_dotenv()
    conn = None
    
    # DB 연결 정보 (환경 변수에서 가져오기)
    db_info = {
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    try:
        # --- 1. DB 연결 ---
        conn = psycopg2.connect(**db_info)
        cur = conn.cursor()
        print("데이터베이스 연결 성공")

        # --- 2. PRODUCTS 데이터 조회 ---
        # 전성분 정보가 비어있지 않은 모든 상품을 가져옵니다.
        cur.execute("SELECT product_id, ingredients FROM PRODUCTS WHERE ingredients IS NOT NULL AND ingredients != ''")
        products = cur.fetchall()
        print(f"총 {len(products)}개의 상품에 대한 성분 처리 시작...")

        # --- 3. 데이터 반복 처리 ---
        for product_id, ingredients_text in products:
            
            # --- 가. 성분 텍스트 파싱 (★★★★★ 개선된 부분 ★★★★★) ---
            
            # 1. 괄호와 그 안의 내용 제거 (예: "(10%)", "(비타민C)")
            processed_text = re.sub(r'\([^)]*\)', '', ingredients_text)
            
            # 2. 쉼표, 점, 슬래시 등을 기준으로 분리
            #    하나의 긴 이름 안에 공백이 있는 경우(예: '하이드록시에틸 셀룰로오스')를 고려
            ingredient_names = re.split(r'[,./•]|\s{2,}', processed_text)

            # 임시 저장 리스트
            temp_list = []
            for name in ingredient_names:
                # 3. 각 성분명 앞/뒤 공백 제거 및 불필요한 특수문자 제거
                #    한글, 영어, 숫자, 하이픈(-)만 남김
                cleaned_name = re.sub(r'[^a-zA-Z0-9가-힣\-\s]', '', name).strip()
                
                # 4. 이름이 너무 짧거나(예: 숫자만 남은 경우) 빈 문자열이면 제외
                if len(cleaned_name) > 1:
                    temp_list.append(cleaned_name)

            ingredient_names = temp_list
            # --- (개선된 파싱 로직 끝) ---
            
            for name in ingredient_names:

                # --- 나. 성분 ID 확인 및 생성 (Get or Create) ---
                # 먼저 성분이 INGREDIENTS 테이블에 있는지 확인
                cur.execute("SELECT ingredient_id FROM INGREDIENTS WHERE korean_name = %s", (name,))
                result = cur.fetchone()
                
                ingredient_id = None
                if result:
                    # 성분이 이미 존재하면 id를 사용
                    ingredient_id = result[0]
                else:
                    # 성분이 없으면 새로 INSERT 하고 id를 받아옴
                    print(f"  -> 새로운 성분 발견: '{name}', INGREDIENTS 테이블에 추가합니다.")
                    cur.execute(
                         """
                        INSERT INTO INGREDIENTS (ingredient_name, korean_name)
                        VALUES (%s, %s)
                        RETURNING ingredient_id
                        """,
                        (name, name)  # name 변수를 두 번 전달하여 각 컬럼에 값을 넣어줍니다.
                    )
                    ingredient_id = cur.fetchone()[0]

                # --- 다. 중간 테이블에 저장 ---
                if ingredient_id:
                    # product_id와 ingredient_id의 관계를 PRODUCT_INGREDIENTS에 저장
                    # 중복 저장을 방지하기 위해 ON CONFLICT DO NOTHING 사용
                    cur.execute(
                        """
                        INSERT INTO PRODUCT_INGREDIENTS (product_id, ingredient_id)
                        VALUES (%s, %s)
                        ON CONFLICT (product_id, ingredient_id) DO NOTHING
                        """,
                        (product_id, ingredient_id)
                    )

        # --- 4. DB 변경사항 저장 ---
        conn.commit()
        print("모든 상품의 성분 관계 데이터 구축 완료!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"오류 발생: {error}")
        if conn:
            conn.rollback() # 오류 발생 시 작업 되돌리기
    finally:
        if conn:
            # --- 연결 종료 ---
            cur.close()
            conn.close()
            print("데이터베이스 연결 종료")


if __name__ == "__main__":
    process_product_ingredients()