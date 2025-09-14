# test_api_final.py
import os
from dotenv import load_dotenv
import urllib.parse
import requests
import json

load_dotenv()

def test_final_api():
    # API 키 디코딩
    raw_key = os.getenv('KFDA_API_KEY')
    decoded_key = urllib.parse.unquote(urllib.parse.unquote(raw_key))
    
    print(f"원본 키 (일부): {raw_key[:30]}...")
    print(f"디코딩된 키 (일부): {decoded_key[:30]}...")
    
    # 공공데이터포털 표준 테스트
    test_url = "http://apis.data.go.kr/1471000/CosmeticIngrdntInfoService1/getCosmeticIngrdntInfo"
    
    params = {
        'serviceKey': decoded_key,
        'pageNo': 1,
        'numOfRows': 5,
        'type': 'json'
    }
    
    try:
        print(f"\n테스트 URL: {test_url}")
        print(f"파라미터: pageNo=1, numOfRows=5, type=json")
        
        response = requests.get(
            test_url, 
            params=params, 
            timeout=10,
            verify=False,  # SSL 검증 비활성화
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용 (처음 1000자):")
        print(response.text[:1000])
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n✅ JSON 파싱 성공!")
                print(f"응답 구조 키들: {list(data.keys())}")
                
                # 데이터 구조 확인
                if 'response' in data:
                    result_code = data['response']['header'].get('resultCode')
                    result_msg = data['response']['header'].get('resultMsg')
                    print(f"결과 코드: {result_code}")
                    print(f"결과 메시지: {result_msg}")
                    
                    if result_code == '00':
                        print("🎉 API 호출 성공!")
                        body = data['response'].get('body', {})
                        if 'items' in body:
                            items = body['items']
                            print(f"수집된 아이템 수: {len(items)}")
                            if items:
                                print(f"첫 번째 아이템: {items[0]}")
                        return True
                    else:
                        print(f"❌ API 오류: {result_msg}")
                
            except json.JSONDecodeError:
                print("❌ JSON 파싱 실패")
                
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
    
    return False

if __name__ == "__main__":
    success = test_final_api()
    if success:
        print("\n🎉 API 테스트 성공! 다음 단계로 진행 가능합니다.")
    else:
        print("\n💡 API 키를 공공데이터포털에서 다시 확인해보세요.")