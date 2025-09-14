# My Beauty AI

> AI 기반 화장품 성분 분석 및 개인 맞춤형 뷰티 스킨케어 루틴 최적화 시스템

단순한 제품 추천을 넘어, 과학적인 데이터를 기반으로 성분 간의 화학적 상호작용, 제형의 물리적 호환성까지 고려하여 안전하고 효과적인 뷰티 경험을 제공합니다.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-0.9+-purple.svg)](https://www.llamaindex.ai/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [기술 스택](#️-기술-스택)
- [시스템 아키텍처](#-시스템-아키텍처)
- [설치 가이드](#-설치-가이드)
- [사용법](#-사용법)
- [API 문서](#-api-문서)
- [프로젝트 구조](#-프로젝트-구조)
- [기여 방법](#-기여-방법)
- [라이센스](#-라이센스)
- [연락처](#-연락처)

## 🎯 프로젝트 개요

**My Beauty AI**는 자신의 피부에 가장 잘 맞는 제품을 찾을 수 있도록 돕는 서비스 입니다. AI 기술과 RAG(Retrieval-Augmented Generation) 시스템을 결합하여, 두 개 이상의 화장품을 함께 사용할 때 발생할 수 있는 성분 간의 충돌을 분석하고, 아침과 저녁에 최적화된 스킨케어 루틴을 설계해 드립니다.

프로젝트의 초기 기획 및 설계 과정이 궁금하시다면 아래 Miro 링크에서 확인하실 수 있습니다.

[Miro 보드에서 초기 설계 보기](https://miro.com/welcomeonboard/aEorTGJXTGZVcU9ZZFRTaFBqNW5Fc0lYcCtkaUprTmd6K1Mwc0kvOXBmUWhQdEEvbWRNWXJqMHY1M1NJVEpZS2dZZlJlSEpGdjdiTVl3Z3hMZDR6Mm4zK2VwSVMyeWNuS1hvVktxejVpOWNjNDcyNTE0THpHTmQ4OUlGd1BBSWFnbHpza3F6REdEcmNpNEFOMmJXWXBBPT0hdjE=?)

### 🌟 핵심 가치

- **개인화**: 사용자의 피부 타입, 관심사, 기존 루틴을 고려한 맞춤형 추천
- **안전성**: 성분 간 상호작용 분석을 통한 사전 경고 시스템
- **과학적 근거**: 피부과학 및 화장품 화학 연구 자료 기반 분석
- **사용자 친화적**: 직관적인 인터페이스와 명확한 가이드 제공

## ✨ 주요 기능

### 🔬 성분 충돌 분석 시스템
- **화학적 상호작용 분석**: 두 개 이상의 제품을 함께 사용할 때 발생할 수 있는 성분 간 화학 반응 예측
- **물리적 호환성 검사**: 제형 간의 물리적 충돌(밀림, 응고 등) 사전 경고
- **pH 레벨 분석**: 산성/알칼리성 성분 조합으로 인한 잠재적 문제점 식별
- **농도별 위험도 평가**: 성분 농도에 따른 상호작용 위험도 계산

### 💡 개인화 루틴 최적화
- **시간대별 루틴 설계**: 아침/저녁 스킨케어 루틴 최적화
- **사용 순서 가이드**: 제품별 최적 사용 순서 및 대기 시간 제안
- **주기적 사용 계획**: 각 제품의 효과적인 사용 주기 및 빈도 추천
- **계절별 조정**: 환경 요인을 고려한 계절별 루틴 조정 제안

### 🤖 AI 기반 분석 엔진
- **LlamaIndex RAG**: 최신 화장품 성분 연구 자료 기반 지능형 검색 및 분석
- **Vector Database**: 고속 유사도 검색을 통한 실시간 성분 매칭
- **자연어 처리**: 사용자 질의에 대한 자연스러운 대화형 응답

### 📚 방대한 데이터베이스
- **네이버 쇼핑 API**를 통해 확보한 스킨케어 상품DB
- **식품의약품안전처**의 성분 데이터
- **MDPI, 대한화장품학회** 등의 최신 논문과 **과학,헬스케어** 저서 학습

## 🛠️ 기술 스택

### Backend
- **Python 3.9+**: 메인 개발 언어
- **FastAPI**: 고성능 웹 프레임워크
- **PostgreSQL**: 관계형 데이터베이스
- **SQLAlchemy**: ORM 및 데이터베이스 관리

### AI/ML
- **LlamaIndex**: RAG 시스템 구현
- **OpenAI GPT-4**: 자연어 처리 및 생성
- **Chroma/Pinecone**: Vector Database
- **Sentence Transformers**: 텍스트 임베딩

### 인프라
- **Docker**: 컨테이너화
- **Redis**: 캐싱 및 세션 관리
- **Nginx**: 로드 밸런싱 및 프록시
- **GitHub Actions**: CI/CD

## 🏗 시스템 아키텍처

```mermaid
graph TB
    A[사용자 인터페이스] --> B[FastAPI 서버]
    B --> C[성분 충돌 분석기]
    B --> D[루틴 최적화기]
    B --> E[RAG 시스템]

    C --> F[PostgreSQL DB]
    D --> F
    E --> G[Vector DB]
    E --> H[LLM API]

    F --> I[BRANDS 테이블]
    F --> J[PRODUCTS 테이블]
    F --> K[INGREDIENTS 테이블]
    F --> L[PRODUCT_INGREDIENTS 테이블]

    G --> M[성분 지식 벡터]
    G --> N[루틴 패턴 벡터]
```

## 🚀 설치 가이드

### 필수 요구사항
- Python 3.9 이상
- PostgreSQL 13 이상
- Redis (선택사항, 캐싱 기능용)
- OpenAI API 키

### 1. 저장소 클론
```bash
git clone https://github.com/howl-papa/My-Beauty-AI.git
cd My-Beauty-AI
```

### 2. 가상 환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 다음 값들을 설정하세요:
# DATABASE_URL=postgresql://username:password@localhost/mybeautyai
# OPENAI_API_KEY=your_openai_api_key
# VECTOR_DB_URL=your_vector_db_url
```

### 4. 데이터베이스 초기화
```bash
# PostgreSQL 데이터베이스 생성
createdb mybeautyai

# 스키마 생성
psql -d mybeautyai -f database/schema.sql
```

### 5. 서버 실행
```bash
# 개발 모드
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📖 사용법

### 기본 사용법

#### 1. 성분 충돌 분석
```python
from conflict_analyzer import ConflictAnalyzer

analyzer = ConflictAnalyzer()
products = ["product_id_1", "product_id_2"]
conflicts = await analyzer.analyze_conflicts(products)

if conflicts:
    for conflict in conflicts:
        print(f"경고: {conflict['message']}")
        print(f"위험도: {conflict['severity']}")
```

#### 2. 루틴 최적화
```python
from routine_optimizer import RoutineOptimizer

optimizer = RoutineOptimizer()
user_profile = {
    "skin_type": "oily",
    "age": 25,
    "concerns": ["acne", "pore_size"]
}
products = ["cleanser_id", "toner_id", "serum_id", "moisturizer_id"]

routine = await optimizer.optimize_routine(user_profile, products)
print(f"추천 루틴: {routine}")
```

### API 사용 예시

#### 성분 충돌 검사 API
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-conflicts" \
-H "Content-Type: application/json" \
-d '{
  "product_ids": ["prod_1", "prod_2", "prod_3"],
  "user_id": "user123"
}'
```

#### 루틴 최적화 API
```bash
curl -X POST "http://localhost:8000/api/v1/optimize-routine" \
-H "Content-Type: application/json" \
-d '{
  "user_profile": {
    "skin_type": "combination",
    "age": 30,
    "concerns": ["wrinkles", "dullness"]
  },
  "products": ["cleanser", "essence", "serum", "cream"]
}'
```

## 📚 API 문서

서버 실행 후 다음 URL에서 상세한 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

| 메소드 | 엔드포인트 | 설명 |
|--------|------------|------|
| GET | `/api/v1/products` | 제품 목록 조회 |
| GET | `/api/v1/products/{id}` | 특정 제품 상세 정보 |
| POST | `/api/v1/analyze-conflicts` | 성분 충돌 분석 |
| POST | `/api/v1/optimize-routine` | 루틴 최적화 |
| GET | `/api/v1/ingredients` | 성분 목록 조회 |
| POST | `/api/v1/chat` | AI 채팅 상담 |

## 📁 프로젝트 구조

```
My-Beauty-AI/
├── 📄 README.md                 # 프로젝트 소개 (영문)
├── 📄 README_KR.md              # 프로젝트 소개 (한글)
├── 📄 requirements.txt          # Python 의존성
├── 📄 .env.example             # 환경변수 템플릿
├── 📄 .gitignore               # Git 제외 파일
├── 🐍 app.py                   # FastAPI 메인 애플리케이션
├── 🐍 config.py                # 설정 관리
├── 🐍 models.py                # 데이터베이스 모델
├── 🐍 rag_system.py            # RAG 시스템 구현
├── 🐍 conflict_analyzer.py     # 성분 충돌 분석기
├── 🐍 routine_optimizer.py     # 루틴 최적화기
├── 📁 database/               # 데이터베이스 관련
│   └── 📄 schema.sql          # DB 스키마
├── 📁 docs/                   # 문서
│   ├── 📄 API_GUIDE_KR.md     # API 가이드 (한글)
│   ├── 📄 INSTALLATION_KR.md  # 설치 가이드 (한글)
│   └── 📄 CONTRIBUTING_KR.md  # 기여 가이드 (한글)
├── 📁 tests/                  # 테스트 코드
├── 📁 data/                   # 샘플 데이터
└── 📁 scripts/                # 유틸리티 스크립트
```

## 🤝 기여 방법

### 버그 리포트 및 기능 제안
이슈를 통해 버그 리포트나 새로운 기능을 제안해주세요:
- [Issues](https://github.com/howl-papa/My-Beauty-AI/issues)

### 개발 참여
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 코딩 스타일
- PEP 8 Python 코딩 스타일 준수
- Type hints 사용 권장
- Docstring 작성 (Google 스타일)
- 테스트 코드 작성 필수

## ⚖️ 면책 조항

> **중요**: 본 시스템은 정보 제공 목적으로만 사용되어야 합니다.
> 
> - 개인의 피부 상태와 알레르기 반응은 매우 다양하므로, 새로운 제품 사용 전 반드시 패치 테스트를 실시하세요.
> - 심각한 피부 문제가 있거나 의학적 조언이 필요한 경우, 피부과 전문의와 상담하시기 바랍니다.
> - 본 서비스의 분석 결과에 대한 의학적, 법적 책임을 지지 않습니다.

## 📄 라이센스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

## 📞 연락처

**개발자**: howl-papa  
**이메일**: yongrak.pro@gmail.com  
**GitHub**: [@howl-papa](https://github.com/howl-papa)  
**프로젝트 링크**: [https://github.com/howl-papa/My-Beauty-AI](https://github.com/howl-papa/My-Beauty-AI)

---

### 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 도움을 받았습니다:
- [LlamaIndex](https://www.llamaindex.ai/) - RAG 시스템 구현
- [FastAPI](https://fastapi.tiangolo.com/) - 웹 프레임워크
- [PostgreSQL](https://www.postgresql.org/) - 데이터베이스
- [OpenAI](https://openai.com/) - AI 모델 API

### 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=howl-papa/My-Beauty-AI&type=Date)](https://star-history.com/#howl-papa/My-Beauty-AI&Date)

---

**Made with ❤️ by [howl-papa](https://github.com/howl-papa)**
