# test_api_detailed.py
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def test_api_connection():
    api_key = os.getenv('KFDA_API_KEY')
    base_url = os.getenv('KFDA_API_URL')
    
    print(f"API Key: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else api_key}")
    print(f"Base URL: {base_url}")
    
    # 여러 URL 패턴 시도
    test_urls = [
        f"{base_url}/getCosmeticIngrdntInfo",
        f"{base_url}/getCsmtcsIngdCpntInfo",
        "https://apis.data.go.kr/1471000/CosmeticIngrdntInfoService1/getCosmeticIngrdntInfo",
        "http://apis.data.go.kr/1471000/CosmeticIngrdntInfoService1/getCosmeticIngrdntInfo"
    ]
    
    params = {
        'serviceKey': api_key,
        'pageNo': 1,
        'numOfRows': 5,
        'type': 'json'
    }
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- 테스트 {i}: {url} ---")
        try:
            response = requests.get(url, params=params, timeout=10, verify=True)
            print(f"응답 코드: {response.status_code}")
            print(f"응답 내용 (처음 300자): {response.text[:300]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("JSON 파싱 성공!")
                    print(f"응답 구조: {list(data.keys())}")
                    return True
                except:
                    print("JSON 파싱 실패, XML 형태일 수 있음")
                    
        except Exception as e:
            print(f"오류: {e}")
    
    return False

if __name__ == "__main__":
    success = test_api_connection()
    if success:
        print("\n✅ API 연결 성공!")
    else:
        print("\n❌ API 연결 실패!")