# test_http_api.py
import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

def test_http_api():
    api_key = os.getenv('KFDA_API_KEY')
    
    # HTTP로 변경 (HTTPS에서 SSL 오류 발생)
    url = "http://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01"
    
    params = {
        'serviceKey': api_key,
        'pageNo': 1,
        'numOfRows': 5,
        'type': 'xml'
    }
    
    try:
        print(f"테스트 URL: {url}")
        print(f"파라미터: {params}")
        
        # 세션 설정
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        response = session.get(
            url, 
            params=params, 
            timeout=30,
            verify=False
        )
        
        print(f"\n응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print(f"응답 내용 (처음 1500자):")
        print(response.text[:1500])
        
        if response.status_code == 200:
            print("\n✅ HTTP API 호출 성공!")
            
            # XML 파싱 시도
            try:
                root = ET.fromstring(response.text)
                print("\n📋 XML 파싱 성공!")
                
                # XML 구조 출력
                def print_xml_structure(element, depth=0):
                    indent = "  " * depth
                    if element.text and element.text.strip():
                        print(f"{indent}{element.tag}: {element.text.strip()}")
                    else:
                        print(f"{indent}{element.tag}")
                    
                    for child in element:
                        if depth < 3:  # 깊이 제한
                            print_xml_structure(child, depth + 1)
                
                print("\nXML 구조:")
                print_xml_structure(root)
                
                # 결과 코드 확인
                result_code_elem = root.find('.//resultCode')
                result_msg_elem = root.find('.//resultMsg')
                
                if result_code_elem is not None:
                    result_code = result_code_elem.text
                    result_msg = result_msg_elem.text if result_msg_elem is not None else "N/A"
                    
                    print(f"\n결과 코드: {result_code}")
                    print(f"결과 메시지: {result_msg}")
                    
                    if result_code == '00':
                        print("🎉 데이터 조회 성공!")
                        
                        # 전체 개수 확인
                        total_count_elem = root.find('.//totalCount')
                        if total_count_elem is not None:
                            print(f"전체 데이터 개수: {total_count_elem.text}")
                        
                        # 아이템 개수 확인
                        items = root.findall('.//item')
                        print(f"현재 페이지 아이템 수: {len(items)}")
                        
                        # 첫 번째 아이템 정보 출력
                        if items:
                            first_item = items[0]
                            print(f"\n📝 첫 번째 성분 정보:")
                            for child in first_item:
                                if child.text:
                                    print(f"  {child.tag}: {child.text}")
                        
                        return True, len(items), total_count_elem.text if total_count_elem is not None else 0
                    else:
                        print(f"❌ API 오류: {result_code} - {result_msg}")
                        return False, 0, 0
                else:
                    print("❌ 결과 코드를 찾을 수 없습니다.")
                    return False, 0, 0
                
            except ET.ParseError as e:
                print(f"❌ XML 파싱 오류: {e}")
                print("원본 XML 내용:")
                print(response.text)
                return False, 0, 0
                
        elif response.status_code == 500:
            print("❌ 서버 오류 (500) - API 키나 파라미터 문제일 수 있습니다.")
            print("응답 내용을 확인해보세요.")
            return False, 0, 0
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            return False, 0, 0
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL 오류: {e}")
        return False, 0, 0
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False, 0, 0
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False, 0, 0

if __name__ == "__main__":
    success, item_count, total_count = test_http_api()
    
    if success:
        print(f"\n🎉 성공! 다음 단계로 진행 가능합니다.")
        print(f"📊 통계: 현재 {item_count}개 조회, 전체 {total_count}개 성분")
        print("\n다음 실행할 명령:")
        print("python full_ingredient_collector.py")
    else:
        print(f"\n🔍 문제 해결이 필요합니다.")
        print("1. API 키가 올바른지 확인")
        print("2. 공공데이터포털에서 API 활용신청 승인 상태 확인")
        print("3. 네트워크 연결 상태 확인")