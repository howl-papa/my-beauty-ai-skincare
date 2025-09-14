import psycopg2
import os
import re
from dotenv import load_dotenv

def clean_concatenated_ingredients():
    """'이하동'이 포함된 잘못된 성분 데이터를 분리하고 재처리합니다."""
    load_dotenv()
    conn = None
    
    db_info = {
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    try:
        conn = psycopg2.connect(**db_info)
        cur = conn.cursor()
        print("데이터베이스 연결 성공")

        # 2. '이하동'이 포함된 문제 성분 데이터 조회
        cur.execute("SELECT ingredient_id, korean_name FROM INGREDIENTS WHERE korean_name LIKE '%이하동%'")
        problem_ingredients = cur.fetchall()
        print(f"총 {len(problem_ingredients)}개의 문제 성분 데이터를 정제합니다.")

        for ingredient_id_to_delete, long_name in problem_ingredients:
            print(f"\n처리 시작: (ID: {ingredient_id_to_delete}) {long_name}")

            # a. 성분명 분리
            # '이하동'과 앞뒤에 있는 다른 성분명을 분리
            parts = long_name.split('이하동')
            # 불필요한 공백 제거 및 정리
            clean_names = [p.strip() for part in parts for p in part.split(' ') if p.strip()]

            if not clean_names:
                print("  -> 유효한 성분명을 찾지 못했습니다. 건너뜁니다.")
                continue

            print(f"  -> 분리된 성분명: {clean_names}")

            # b. 현재 이 성분과 연결된 모든 product_id 찾기
            cur.execute("SELECT product_id FROM PRODUCT_INGREDIENTS WHERE ingredient_id = %s", (ingredient_id_to_delete,))
            product_ids = [item[0] for item in cur.fetchall()]
            
            if not product_ids:
                print("  -> 연결된 상품이 없습니다. 원본 성분만 삭제합니다.")
            else:
                print(f"  -> {len(product_ids)}개의 상품과 재연결이 필요합니다.")

            # c. 분리된 각 성분에 대해 올바른 관계로 재설정
            for name in clean_names:
                # 'Get or Create' 로직으로 올바른 ingredient_id 확보
                cur.execute("SELECT ingredient_id FROM INGREDIENTS WHERE korean_name = %s", (name,))
                result = cur.fetchone()
                
                new_ingredient_id = None
                if result:
                    new_ingredient_id = result[0]
                else:
                    print(f"    -> 새로운 성분 '{name}'을(를) INGREDIENTS 테이블에 추가합니다.")
                    cur.execute(
                        "INSERT INTO INGREDIENTS (ingredient_name, korean_name) VALUES (%s, %s) RETURNING ingredient_id",
                        (name, name)
                    )
                    new_ingredient_id = cur.fetchone()[0]

                # 찾아낸 product_id들과 새로운 ingredient_id를 연결
                for pid in product_ids:
                    cur.execute(
                        "INSERT INTO PRODUCT_INGREDIENTS (product_id, ingredient_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (pid, new_ingredient_id)
                    )
            
            # d. 기존의 잘못된 긴 성분 데이터 삭제
            print(f"  -> 원본 문제 성분(ID: {ingredient_id_to_delete})을(를) 삭제합니다.")
            cur.execute("DELETE FROM INGREDIENTS WHERE ingredient_id = %s", (ingredient_id_to_delete,))

        conn.commit()
        print("\n모든 정제 작업이 완료되었습니다.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"오류 발생: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
            print("데이터베이스 연결 종료")

if __name__ == "__main__":
    clean_concatenated_ingredients()