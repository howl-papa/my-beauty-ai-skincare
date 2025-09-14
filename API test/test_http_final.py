# test_http_final.py
import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

def test_http_final():
    api_key = os.getenv('KFDA_API_KEY')
    # HTTPS를 HTTP로 변경
    url = "http://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01"
    
    params = {
        'serviceKey': api_key,
        'pageNo': 1,
        'numOfRows': 3,
        'type': 'xml'
    }
    
    # 간단한 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"테스트 URL: {url}")
        print(f"파라미터: {params}")
        
        response = requests.get(
            url, 
            params=params, 
            headers=headers,
            timeout=30,
            verify=False
        )
        
        print(f"\n응답 상태 코드: {response.status_code}")
        print(f"응답 내용 (처음 1000자):")
        print(response.text[:1000])
        
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.text)
                
                # 결과 확인
                result_code = root.find('.//resultCode')
                result_msg = root.find('.//resultMsg')
                
                if result_code is not None:
                    print(f"\n✅ XML 파싱 성공!")
                    print(f"결과 코드: {result_code.text}")
                    print(f"결과 메시지: {result_msg.text if result_msg is not None else 'N/A'}")
                    
                    if result_code.text == '00':
                        total_count = root.find('.//totalCount')
                        print(f"전체 성분 수: {total_count.text if total_count is not None else 'N/A'}")
                        
                        items = root.findall('.//item')
                        print(f"현재 페이지 아이템: {len(items)}개")
                        
                        if items:
                            print(f"\n📝 첫 번째 성분:")
                            for child in items[0]:
                                if child.text:
                                    print(f"  {child.tag}: {child.text}")
                        
                        return True
                    else:
                        print(f"❌ API 오류: {result_msg.text if result_msg else 'Unknown'}")
                
            except ET.ParseError as e:
                print(f"❌ XML 파싱 오류: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_http_final()
    if success:
        print("\n🎉 HTTP로 성공! 이제 전체 수집 진행 가능!")
    else:
        print("\n❌ HTTP도 실패. API 키나 서비스 문제일 수 있음.")