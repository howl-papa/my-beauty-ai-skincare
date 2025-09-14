import os
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
import psycopg2

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_collection_safe.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

load_dotenv()

class SafeIngredientCollector:
    def __init__(self):
        self.api_key = os.getenv('KFDA_API_KEY')
        self.api_url = "http://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.db_config = {
            'host': os.getenv('DB_HOST', ''),
            'port': os.getenv('DB_PORT', ''),
            'database': os.getenv('DB_NAME', ''),
            'user': os.getenv('DB_USER', ''),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    def get_api_data(self, page_no=1, num_of_rows=100):
        """API 데이터 조회"""
        params = {
            'serviceKey': self.api_key,
            'pageNo': page_no,
            'numOfRows': num_of_rows,
            'type': 'xml'
        }
        
        try:
            response = requests.get(
                self.api_url, 
                params=params, 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                
                result_code = root.find('.//resultCode')
                if result_code is not None and result_code.text == '00':
                    total_count_elem = root.find('.//totalCount')
                    total_count = int(total_count_elem.text) if total_count_elem is not None else 0
                    
                    items = []
                    for item in root.findall('.//item'):
                        item_data = {}
                        for child in item:
                            item_data[child.tag] = child.text if child.text else ''
                        items.append(item_data)
                    
                    return items, total_count
                else:
                    result_msg = root.find('.//resultMsg')
                    logging.error(f"API 오류: {result_msg.text if result_msg is not None else 'Unknown'}")
                    return [], 0
            else:
                logging.error(f"HTTP 오류: {response.status_code}")
                return [], 0
                
        except Exception as e:
            logging.error(f"API 호출 실패: {e}")
            return [], 0
    
    def save_to_database(self, ingredients):
        """안전한 데이터베이스 저장"""
        if not ingredients:
            return 0
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            success_count = 0
            error_count = 0
            
            for ingredient in ingredients:
                try:
                    ingredient_name = ingredient.get('INGR_KOR_NAME', '').strip()
                    if not ingredient_name:
                        continue
                    
                    # 길이 제한
                    ingredient_name = ingredient_name[:255]
                    inci_name = ingredient.get('INGR_ENG_NAME', '')[:255]
                    cas_number = ingredient.get('CAS_NO', '')[:50]
                    origin_definition = ingredient.get('ORIGIN_MAJOR_KOR_NAME', '')
                    
                    # UPSERT 쿼리 (중복 시 업데이트)
                    query = """
                    INSERT INTO INGREDIENTS (
                        ingredient_name, inci_name, cas_number, korean_name,
                        origin_definition, data_source, regulatory_status,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ingredient_name) DO UPDATE SET
                        inci_name = EXCLUDED.inci_name,
                        cas_number = EXCLUDED.cas_number,
                        origin_definition = EXCLUDED.origin_definition,
                        updated_at = EXCLUDED.updated_at
                    """
                    
                    now = datetime.now()
                    values = (
                        ingredient_name,
                        inci_name,
                        cas_number,
                        ingredient_name,  # korean_name
                        origin_definition,
                        'KFDA_API',
                        'APPROVED',
                        now,
                        now
                    )
                    
                    cursor.execute(query, values)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:  # 처음 3개 오류만 로깅
                        logging.warning(f"개별 저장 실패: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            
            if error_count > 0:
                logging.info(f"배치 저장: 성공 {success_count}개, 실패 {error_count}개")
            else:
                logging.info(f"배치 저장: {success_count}개 성공")
            
            return success_count
            
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"배치 저장 전체 실패: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def collect_all_safe(self):
        """안전한 전체 수집"""
        logging.info("=" * 60)
        logging.info("화장품 성분 데이터 안전 수집 시작")
        logging.info("=" * 60)
        
        # 전체 개수 확인
        items, total_count = self.get_api_data(1, 100)
        if not items:
            logging.error("첫 페이지 데이터 조회 실패")
            return False
        
        logging.info(f"수집 대상: {total_count:,}개 성분")
        total_pages = (total_count + 99) // 100
        
        total_saved = 0
        start_time = time.time()
        
        try:
            for page in range(1, total_pages + 1):
                # 진행률 계산
                progress = (page / total_pages) * 100
                
                # 상세 진행 정보 (매 10페이지마다)
                if page % 10 == 0 or page == 1:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / page if page > 0 else 0
                    remaining_time = avg_time * (total_pages - page)
                    
                    logging.info(f"📊 페이지 {page:,}/{total_pages:,} ({progress:.1f}%) | "
                               f"예상 남은 시간: {remaining_time/60:.1f}분")
                
                # API 데이터 조회
                items, _ = self.get_api_data(page, 100)
                
                if items:
                    # 즉시 저장 (배치 크기 100)
                    saved = self.save_to_database(items)
                    total_saved += saved
                    
                    if page % 50 == 0:  # 50페이지마다 누적 현황 출력
                        logging.info(f"🔄 중간 저장 현황: {total_saved:,}개 저장 완료")
                else:
                    logging.warning(f"페이지 {page} 데이터 없음")
                
                # API 호출 간격 (서버 부하 방지)
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            logging.info("사용자 중단 요청. 현재까지 진행 상황 저장됨.")
        except Exception as e:
            logging.error(f"수집 중 오류: {e}")
        
        # 최종 결과
        elapsed_total = time.time() - start_time
        logging.info("=" * 60)
        logging.info(f"수집 완료!")
        logging.info(f"총 저장된 성분: {total_saved:,}개")
        logging.info(f"소요 시간: {elapsed_total/60:.1f}분")
        logging.info("=" * 60)
        
        return total_saved > 0

if __name__ == "__main__":
    collector = SafeIngredientCollector()
    
    print("🚀 안전한 전체 화장품 성분 수집을 시작합니다!")
    print("예상 소요시간: 약 3-5분")
    print("진행 중 Ctrl+C로 중단 가능 (진행사항은 저장됨)")
    
    confirm = input("\n계속 진행하시겠습니까? (y/N): ")
    
    if confirm.lower() in ['y', 'yes']:
        success = collector.collect_all_safe()
        
        if success:
            print("\n🎉 전체 수집 성공!")
            print("📁 로그 파일: full_collection_safe.log")
            print("🔍 pgAdmin4에서 INGREDIENTS 테이블을 확인해보세요!")
        else:
            print("\n❌ 수집 실패. 로그를 확인하세요.")
    else:
        print("수집이 취소되었습니다.")