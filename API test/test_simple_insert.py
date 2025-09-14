# test_simple_insert.py
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_simple_insert():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        # 간단한 테스트 데이터
        test_data = {
            'ingredient_name': '테스트성분',
            'inci_name': 'Test Ingredient',
            'cas_number': '123-45-6',
            'korean_name': '테스트성분',
            'origin_definition': '테스트용 성분입니다',
            'data_source': 'TEST',
            'regulatory_status': 'APPROVED'
        }
        
        print("테스트 데이터 삽입 시도...")
        print(f"데이터: {test_data}")
        
        # 기존 데이터 삭제 (테스트용)
        cursor.execute("DELETE FROM INGREDIENTS WHERE ingredient_name = %s", (test_data['ingredient_name'],))
        
        # 삽입 시도
        query = """
        INSERT INTO INGREDIENTS (
            ingredient_name, inci_name, cas_number, korean_name,
            origin_definition, data_source, regulatory_status,
            created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        values = (
            test_data['ingredient_name'],
            test_data['inci_name'],
            test_data['cas_number'],
            test_data['korean_name'],
            test_data['origin_definition'],
            test_data['data_source'],
            test_data['regulatory_status'],
            now,
            now
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        print("✅ 테스트 삽입 성공!")
        
        # 확인
        cursor.execute("SELECT * FROM INGREDIENTS WHERE ingredient_name = %s", (test_data['ingredient_name'],))
        result = cursor.fetchone()
        print(f"저장된 데이터: {result}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 삽입 실패: {e}")
        return False

if __name__ == "__main__":
    test_simple_insert()