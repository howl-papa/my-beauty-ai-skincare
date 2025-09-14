import psycopg2
import os
from dotenv import load_dotenv
import json

def merge_duplicate_ingredients():
    """
    띄어쓰기만 다른 중복 성분들을 찾아서 하나의 대표 성분으로 통합하고,
    관계 데이터를 이전한 뒤 중복 데이터를 삭제합니다.
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
        # --- DB 연결 ---
        conn = psycopg2.connect(**db_info)
        cur = conn.cursor()
        print("✅ 데이터베이스 연결 성공")

        # --- 1. 중복 성분 그룹 조회 ---
        # 띄어쓰기를 제거한 이름을 기준으로 그룹화하고, 각 그룹의 id와 원래 이름을 json으로 가져옵니다.
        cur.execute("""
            SELECT
                REPLACE(korean_name, ' ', '') AS standardized_name,
                JSON_AGG(json_build_object('id', ingredient_id, 'name', korean_name)) AS items
            FROM
                INGREDIENTS
            GROUP BY
                standardized_name
            HAVING
                COUNT(*) > 1;
        """)
        duplicate_groups = cur.fetchall()
        
        if not duplicate_groups:
            print("🟢 처리할 중복 성분이 없습니다. 데이터가 깨끗합니다.")
            return

        print(f"✨ 총 {len(duplicate_groups)}개의 중복 성분 그룹을 발견했습니다. 병합 작업을 시작합니다.")

        # --- 2. 각 그룹을 순회하며 병합 작업 실행 ---
        for standardized_name, items_json in duplicate_groups:
            
            # id를 기준으로 정렬하여 가장 낮은 id를 '대표 성분'으로 선택
            items = sorted(items_json, key=lambda x: x['id'])
            
            winner = items[0]
            losers = items[1:]
            
            good_id = winner['id']
            
            print(f"\n--- 그룹 '{standardized_name}' 처리 중 ---")
            print(f"  - 대표 성분: ID {good_id} ('{winner['name']}')")
            
            # --- 3. 대표 성분 이름 표준화 ---
            # 대표 성분의 이름에 공백이 있다면 제거하여 표준화합니다.
            if winner['name'] != standardized_name:
                cur.execute(
                    "UPDATE INGREDIENTS SET korean_name = %s WHERE ingredient_id = %s",
                    (standardized_name, good_id)
                )
                print(f"  - 대표 성분 이름을 '{standardized_name}' (으)로 표준화했습니다.")

            # --- 4. 나머지 중복 성분들을 대표 성분으로 병합 ---
            for loser in losers:
                bad_id = loser['id']
                print(f"  - '{loser['name']}' (ID: {bad_id})  ->  '{standardized_name}' (ID: {good_id}) (으)로 병합 시도...")

                # --- 4-1. PRODUCT_INGREDIENTS 관계 이전 ---
                # 상품에 대표-중복 성분이 모두 연결된 경우를 대비하여, 중복 연결을 먼저 삭제
                cur.execute("""
                    DELETE FROM PRODUCT_INGREDIENTS
                    WHERE ingredient_id = %s
                    AND product_id IN (
                        SELECT product_id FROM PRODUCT_INGREDIENTS WHERE ingredient_id = %s
                    )
                """, (bad_id, good_id))
                
                # 나머지 관계를 대표 성분 ID로 업데이트
                cur.execute(
                    "UPDATE PRODUCT_INGREDIENTS SET ingredient_id = %s WHERE ingredient_id = %s",
                    (good_id, bad_id)
                )

                # --- 4-2. INGREDIENTS 테이블에서 중복 성분 삭제 ---
                cur.execute("DELETE FROM INGREDIENTS WHERE ingredient_id = %s", (bad_id,))
                print(f"  - ID {bad_id} 병합 및 삭제 완료.")

        # --- 5. 모든 변경사항 최종 저장 ---
        conn.commit()
        print("\n🎉 모든 중복 성분 병합 작업이 성공적으로 완료되었습니다.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"\n❌ 오류 발생: {error}")
        if conn:
            conn.rollback() # 오류 발생 시 모든 작업 되돌리기
    finally:
        if conn:
            cur.close()
            conn.close()
            print("🔌 데이터베이스 연결 종료")


if __name__ == "__main__":
    merge_duplicate_ingredients()