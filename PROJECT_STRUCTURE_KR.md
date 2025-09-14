# My Beauty AI - 프로젝트 구조 설명서 📂

> **My Beauty AI** 프로젝트의 디렉토리 구조와 각 파일의 역할을 상세히 설명합니다.

## 📋 목차

- [전체 프로젝트 구조](#-전체-프로젝트-구조)
- [디렉토리별 상세 설명](#-디렉토리별-상세-설명)
- [핵심 파일 설명](#-핵심-파일-설명)
- [데이터베이스 구조](#-데이터베이스-구조)
- [API 구조](#-api-구조)
- [설정 파일](#-설정-파일)
- [개발 가이드라인](#-개발-가이드라인)

## 🏗 전체 프로젝트 구조

```
My-Beauty-AI/
├── 📄 README.md                 # 프로젝트 소개 (영문)
├── 📄 README_KR.md              # 프로젝트 소개 (한글)
├── 📄 requirements.txt          # Python 의존성 패키지 목록
├── 📄 .env.example             # 환경변수 설정 템플릿
├── 📄 .gitignore               # Git 버전 관리 제외 파일 목록
├── 📄 LICENSE                  # 프로젝트 라이센스
├── 🐍 app.py                   # FastAPI 메인 애플리케이션 서버
├── 🐍 config.py                # 애플리케이션 설정 관리
├── 🐍 models.py                # SQLAlchemy 데이터베이스 모델 정의
├── 🐍 rag_system.py            # LlamaIndex RAG 시스템 구현
├── 🐍 conflict_analyzer.py     # 화장품 성분 충돌 분석 모듈
├── 🐍 routine_optimizer.py     # 개인화 루틴 최적화 모듈
├── 📁 api/                     # API 엔드포인트 모듈
│   ├── 🐍 __init__.py          
│   ├── 🐍 products.py          # 제품 관련 API
│   ├── 🐍 ingredients.py       # 성분 관련 API
│   ├── 🐍 analysis.py          # 분석 관련 API
│   └── 🐍 chat.py              # AI 채팅 API
├── 📁 database/               # 데이터베이스 관련 파일
│   ├── 📄 schema.sql          # PostgreSQL 테이블 스키마
│   ├── 📄 migrations/         # 데이터베이스 마이그레이션
│   │   ├── 📄 001_initial.sql
│   │   └── 📄 002_indexes.sql
│   └── 📄 seed_data.sql       # 초기 데이터
├── 📁 docs/                   # 프로젝트 문서
│   ├── 📄 PROJECT_STRUCTURE_KR.md  # 프로젝트 구조 설명 (한글)
│   ├── 📄 API_GUIDE_KR.md          # API 사용 가이드 (한글)
│   ├── 📄 INSTALLATION_KR.md       # 설치 가이드 (한글)
│   ├── 📄 CONTRIBUTING_KR.md       # 기여 가이드 (한글)
│   ├── 📄 ARCHITECTURE.md          # 시스템 아키텍처
│   └── 📁 images/                  # 문서용 이미지
│       ├── 🖼️ erd_diagram.png
│       └── 🖼️ architecture.png
├── 📁 tests/                  # 테스트 코드
│   ├── 🐍 __init__.py
│   ├── 🐍 test_config.py
│   ├── 🐍 test_models.py
│   ├── 🐍 test_conflict_analyzer.py
│   ├── 🐍 test_routine_optimizer.py
│   ├── 🐍 test_rag_system.py
│   └── 📁 fixtures/           # 테스트용 데이터
│       ├── 📄 sample_products.json
│       └── 📄 sample_ingredients.json
├── 📁 data/                   # 데이터 파일
│   ├── 📄 ingredients_database.json    # 성분 데이터베이스
│   ├── 📄 interaction_rules.json       # 성분 상호작용 규칙
│   ├── 📄 routine_templates.json       # 루틴 템플릿
│   └── 📁 vector_store/               # Vector Database 저장소
│       ├── 📄 ingredients_vectors.pkl
│       └── 📄 knowledge_base_vectors.pkl
├── 📁 scripts/                # 유틸리티 스크립트
│   ├── 🐍 setup_database.py   # 데이터베이스 초기 설정
│   ├── 🐍 data_migration.py   # 데이터 마이그레이션
│   ├── 🐍 vector_indexing.py  # 벡터 인덱스 생성
│   └── 🐍 backup_restore.py   # 백업 및 복원
├── 📁 utils/                  # 공통 유틸리티
│   ├── 🐍 __init__.py
│   ├── 🐍 database.py         # 데이터베이스 연결 관리
│   ├── 🐍 logger.py           # 로깅 유틸리티
│   ├── 🐍 validators.py       # 데이터 유효성 검사
│   └── 🐍 exceptions.py       # 커스텀 예외 클래스
├── 📁 frontend/              # 프론트엔드 (선택사항)
│   ├── 📄 index.html
│   ├── 📄 style.css
│   └── 📄 script.js
└── 📁 docker/                # Docker 관련 파일
    ├── 📄 Dockerfile
    ├── 📄 docker-compose.yml
    └── 📄 docker-compose.dev.yml
```

## 📂 디렉토리별 상세 설명

### 🔧 **Root Directory** (프로젝트 루트)
프로젝트의 기본 설정과 메인 모듈들이 위치합니다.

### 🌐 **api/** - API 엔드포인트
```
api/
├── __init__.py          # API 패키지 초기화
├── products.py          # 제품 CRUD 및 검색 API
├── ingredients.py       # 성분 정보 및 검색 API  
├── analysis.py          # 충돌 분석 및 루틴 최적화 API
└── chat.py             # AI 채팅 상담 API
```

**주요 기능:**
- RESTful API 엔드포인트 정의
- 요청/응답 데이터 검증
- 비즈니스 로직과 API 레이어 분리

### 🗄️ **database/** - 데이터베이스 관련
```
database/
├── schema.sql           # PostgreSQL 테이블 스키마
├── migrations/          # 스키마 변경 이력
│   ├── 001_initial.sql
│   └── 002_indexes.sql
└── seed_data.sql       # 초기 샘플 데이터
```

**주요 구성요소:**
- **BRANDS**: 화장품 브랜드 정보
- **PRODUCTS**: 제품 상세 정보
- **INGREDIENTS**: 성분 마스터 데이터
- **PRODUCT_INGREDIENTS**: 제품-성분 관계 테이블

### 📚 **docs/** - 프로젝트 문서
```
docs/
├── PROJECT_STRUCTURE_KR.md  # 프로젝트 구조 설명 (본 문서)
├── API_GUIDE_KR.md         # API 사용 가이드
├── INSTALLATION_KR.md      # 상세 설치 가이드
├── CONTRIBUTING_KR.md      # 개발자 기여 가이드
├── ARCHITECTURE.md         # 시스템 아키텍처 문서
└── images/                 # 다이어그램 및 스크린샷
    ├── erd_diagram.png
    └── architecture.png
```

### 🧪 **tests/** - 테스트 코드
```
tests/
├── test_config.py              # 설정 테스트
├── test_models.py              # 데이터베이스 모델 테스트
├── test_conflict_analyzer.py   # 충돌 분석 테스트
├── test_routine_optimizer.py   # 루틴 최적화 테스트
├── test_rag_system.py         # RAG 시스템 테스트
└── fixtures/                   # 테스트 데이터
    ├── sample_products.json
    └── sample_ingredients.json
```

### 💾 **data/** - 데이터 저장소
```
data/
├── ingredients_database.json    # 성분 정보 데이터베이스
├── interaction_rules.json       # 성분 상호작용 규칙
├── routine_templates.json       # 루틴 템플릿
└── vector_store/               # Vector Database
    ├── ingredients_vectors.pkl
    └── knowledge_base_vectors.pkl
```

### 🔧 **scripts/** - 유틸리티 스크립트
```
scripts/
├── setup_database.py   # 초기 DB 설정 자동화
├── data_migration.py   # 데이터 마이그레이션
├── vector_indexing.py  # 벡터 인덱스 생성 및 업데이트
└── backup_restore.py   # 데이터 백업/복원
```

### 🛠️ **utils/** - 공통 유틸리티
```
utils/
├── database.py         # DB 연결 및 세션 관리
├── logger.py          # 구조화된 로깅
├── validators.py      # 입력 데이터 검증
└── exceptions.py      # 커스텀 예외 정의
```

## 🔑 핵심 파일 설명

### **app.py** - 메인 애플리케이션
```python
# FastAPI 애플리케이션 진입점
from fastapi import FastAPI
from api import products, ingredients, analysis, chat

app = FastAPI(title="My Beauty AI", version="1.0.0")

# API 라우터 등록
app.include_router(products.router, prefix="/api/v1")
app.include_router(ingredients.router, prefix="/api/v1")  
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
```

### **config.py** - 설정 관리
```python
# 환경별 설정 관리
class Settings:
    database_url: str
    openai_api_key: str
    vector_db_url: str
    redis_url: str
    debug_mode: bool = False
```

### **models.py** - 데이터베이스 모델
```python
# SQLAlchemy ORM 모델 정의
class Brand(Base):
    __tablename__ = "brands"
    brand_id = Column(Integer, primary_key=True)
    brand_name = Column(String, unique=True, nullable=False)

class Product(Base):
    __tablename__ = "products"
    # ... 필드 정의
```

### **rag_system.py** - RAG 시스템
```python
# LlamaIndex 기반 RAG 구현
class BeautyRAGSystem:
    def __init__(self):
        self.index = VectorStoreIndex(...)
        self.retriever = self.index.as_retriever()

    async def query(self, question: str) -> str:
        # 지식 검색 및 응답 생성
        pass
```

### **conflict_analyzer.py** - 성분 충돌 분석
```python
# 화장품 성분 간 상호작용 분석
class ConflictAnalyzer:
    async def analyze_conflicts(self, product_ids: List[str]) -> List[Conflict]:
        # 성분 추출 -> 상호작용 규칙 적용 -> 위험도 계산
        pass
```

### **routine_optimizer.py** - 루틴 최적화
```python
# 개인화된 스킨케어 루틴 생성
class RoutineOptimizer:
    async def optimize_routine(self, user_profile: dict, products: List[str]) -> Routine:
        # 사용자 프로필 분석 -> 제품 호환성 검사 -> 최적 순서 결정
        pass
```

## 🗄️ 데이터베이스 구조

### ERD (Entity-Relationship Diagram)
```
BRANDS (1) ──── (M) PRODUCTS (M) ──── (M) INGREDIENTS
                       │                       │
                       └─── PRODUCT_INGREDIENTS ───┘
                               (Junction Table)
```

### 테이블 상세 설명

#### **BRANDS** - 브랜드 정보
```sql
brand_id (PK)      | SERIAL    | 브랜드 고유 ID
brand_name (UNIQUE)| VARCHAR   | 브랜드명 (예: "Innisfree")
```

#### **PRODUCTS** - 제품 정보  
```sql
product_id (PK)    | SERIAL    | 제품 고유 ID
product_name       | VARCHAR   | 제품명
brand_id (FK)      | INTEGER   | 브랜드 외래키
image_url          | VARCHAR   | 제품 이미지 URL
barcode (UNIQUE)   | VARCHAR   | 제품 바코드
ingredients        | TEXT      | 전체 성분 텍스트
```

#### **INGREDIENTS** - 성분 마스터
```sql
ingredient_id (PK) | SERIAL       | 성분 고유 ID
ingredient_name    | VARCHAR(255) | 성분명 (INCI)
inci_name          | VARCHAR(255) | 국제 성분명
korean_name        | VARCHAR      | 한글 성분명  
cas_number         | VARCHAR(50)  | CAS 등록번호
origin_definition  | TEXT         | 성분 원료 정의
data_source        | VARCHAR      | 데이터 출처
regulatory_status  | VARCHAR      | 규제 승인 상태
created_at         | TIMESTAMP    | 생성일시
updated_at         | TIMESTAMP    | 수정일시
```

#### **PRODUCT_INGREDIENTS** - 제품-성분 관계
```sql
product_id (PK,FK) | INTEGER   | 제품 외래키
ingredient_id (PK,FK)| INTEGER | 성분 외래키
```

## 🌐 API 구조

### API 버전 관리
- **Base URL**: `/api/v1`
- **인증**: JWT 토큰 (선택적)
- **응답 형식**: JSON

### 주요 엔드포인트

#### 제품 관련 API
```
GET    /api/v1/products           # 제품 목록 조회 (페이지네이션)
GET    /api/v1/products/{id}      # 특정 제품 상세 정보
POST   /api/v1/products/search    # 제품 검색 (이름, 브랜드, 성분)
```

#### 성분 관련 API
```
GET    /api/v1/ingredients        # 성분 목록 조회
GET    /api/v1/ingredients/{id}   # 특정 성분 상세 정보
POST   /api/v1/ingredients/search # 성분 검색
```

#### 분석 관련 API  
```
POST   /api/v1/analyze-conflicts  # 성분 충돌 분석
POST   /api/v1/optimize-routine   # 루틴 최적화
GET    /api/v1/analysis-history   # 분석 이력 조회
```

#### AI 채팅 API
```
POST   /api/v1/chat               # AI 상담 채팅
GET    /api/v1/chat/history       # 채팅 이력 조회
```

## ⚙️ 설정 파일

### **.env.example** - 환경변수 템플릿
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/mybeautyai

# AI/ML Configuration  
OPENAI_API_KEY=sk-your-openai-api-key
VECTOR_DB_URL=http://localhost:6333

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379/0

# Application Settings
DEBUG_MODE=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### **requirements.txt** - Python 의존성
```text
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
llamaindex==0.9.5
openai==1.3.7
redis==5.0.1
pydantic==2.5.0
python-multipart==0.0.6
python-jose==3.3.0
```

## 📋 개발 가이드라인

### **코드 스타일**
- **PEP 8** Python 코딩 컨벤션 준수
- **Type Hints** 모든 함수에 타입 힌트 적용
- **Docstrings** Google 스타일 문서화
- **Variable Naming**: snake_case 사용

### **Git 워크플로우**
```bash
# Feature 개발
git checkout -b feature/ingredient-analysis
git commit -m "feat: Add ingredient interaction analysis"
git push origin feature/ingredient-analysis

# Pull Request 생성 후 Code Review
# 승인 후 main 브랜치로 병합
```

### **테스트 가이드라인**
```bash
# 단위 테스트 실행
pytest tests/ -v

# 커버리지 측정
pytest --cov=. tests/

# 특정 모듈 테스트
pytest tests/test_conflict_analyzer.py
```

### **로깅 규칙**
```python
# 구조화된 로깅 사용
import logging

logger = logging.getLogger(__name__)

logger.info("성분 충돌 분석 시작", extra={
    "user_id": user_id,
    "product_count": len(products),
    "analysis_type": "conflict_detection"
})
```

### **에러 처리**
```python
# 커스텀 예외 사용
from utils.exceptions import IngredientNotFoundError, ConflictAnalysisError

try:
    result = await analyzer.analyze_conflicts(products)
except ConflictAnalysisError as e:
    logger.error(f"충돌 분석 실패: {e}")
    raise HTTPException(status_code=422, detail=str(e))
```

## 🔄 배포 및 운영

### **Docker 컨테이너화**
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **환경별 설정**
- **Development**: SQLite + 로컬 Vector DB
- **Staging**: PostgreSQL + Chroma Cloud  
- **Production**: PostgreSQL + Pinecone + Redis Cluster

---

**이 문서는 My Beauty AI 프로젝트의 구조를 이해하고 개발에 참여하는 모든 개발자를 위한 가이드입니다. 추가 질문이나 개선 사항이 있으면 언제든 문의해주세요!** 🚀
