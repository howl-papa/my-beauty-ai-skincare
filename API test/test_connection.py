import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        print("환경변수 확인:")
        print(f"DB_HOST: {os.getenv('DB_HOST')}")
        print(f"DB_PORT: {os.getenv('DB_PORT')}")  
        print(f"DB_NAME: {os.getenv('DB_NAME')}")
        print(f"DB_USER: {os.getenv('DB_USER')}")
        print(f"DB_PASSWORD: {'*' * len(os.getenv('DB_PASSWORD', '')) if os.getenv('DB_PASSWORD') else 'None'}")
        
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = connection.cursor()
        cursor.execute('SELECT version();')
        result = cursor.fetchone()
        print(f"연결 성공! PostgreSQL 버전: {result[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"연결 실패: {e}")
        return False

if __name__ == "__main__":
    test_connection()