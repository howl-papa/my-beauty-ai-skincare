# test_postman_headers.py
import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET

load_dotenv()

def test_with_postman_headers():
    api_key = os.getenv('KFDA_API_KEY')
    url = "https://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01"
    
    params = {
        'serviceKey': api_key,
        'pageNo': 1,
        'numOfRows': 3,
        'type': 'xml'
    }
    
    # Postman과 동일한 헤더 설정
    headers = {
        'User-Agent': 'PostmanRuntime/7.37.3',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        print(f"테스트 URL: {url}")
        print(f"파라미터: {params}")
        print(f"헤더: {headers}")
        
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            timeout=30,
            verify=True  # SSL 검증 활성화 (Postman과 동일)
        )
        
        print(f"\n응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print(f"응답 내용:")
        print(response.text)
        
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.text)
                
                # 결과 코드 확인
                result_code = root.find('.//resultCode').text
                result_msg = root.find('.//resultMsg').text
                total_count = root.find('.//totalCount').text
                
                print(f"\n✅ 파싱 결과:")
                print(f"결과 코드: {result_code}")
                print(f"결과 메시지: {result_msg}")
                print(f"전체 개수: {total_count}")
                
                # 첫 번째 아이템 출력
                items = root.findall('.//item')
                if items:
                    print(f"\n📝 첫 번째 성분:")
                    first_item = items[0]
                    for child in first_item:
                        print(f"  {child.tag}: {child.text}")
                
                return True
                
            except ET.ParseError as e:
                print(f"❌ XML 파싱 오류: {e}")
                
        return False
        
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_with_postman_headers()
    if success:
        print("\n🎉 Python에서도 성공! 이제 전체 데이터 수집 가능!")
    else:
        print("\n❌ 여전히 실패. 추가 디버깅 필요.")