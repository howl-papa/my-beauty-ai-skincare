# My Beauty AI - 기여 가이드라인 🤝

> **My Beauty AI** 프로젝트에 기여하고 싶으신 모든 개발자를 환영합니다! 이 가이드는 프로젝트에 효과적으로 기여하는 방법을 안내합니다.

## 📋 목차

- [기여 방법 개요](#-기여-방법-개요)
- [개발 환경 설정](#-개발-환경-설정)
- [코드 기여하기](#-코드-기여하기)
- [코딩 스타일 가이드](#-코딩-스타일-가이드)
- [테스트 가이드라인](#-테스트-가이드라인)
- [문서화 기여](#-문서화-기여)
- [이슈 및 버그 리포트](#-이슈-및-버그-리포트)
- [커뮤니티 가이드라인](#-커뮤니티-가이드라인)
- [라이센스 정보](#-라이센스-정보)

## 🌟 기여 방법 개요

### 기여할 수 있는 영역

**🔬 알고리즘 개선**
- 성분 충돌 분석 알고리즘 향상
- 루틴 최적화 로직 개선
- RAG 시스템 성능 향상

**🐍 코드 기여**
- 새로운 기능 개발
- 기존 기능 개선 및 최적화
- 버그 수정 및 성능 개선

**📚 문서화**
- API 문서 개선
- 사용자 가이드 작성
- 코드 주석 및 Docstring 개선

**🧪 테스트**
- 단위 테스트 작성
- 통합 테스트 개선
- 성능 테스트 구현

**🎨 UI/UX**
- 프론트엔드 인터페이스 개선
- 사용자 경험 향상
- 반응형 디자인 구현

## 🛠️ 개발 환경 설정

### 1. 저장소 포크 및 클론
```bash
# 1. GitHub에서 프로젝트 포크
# 2. 로컬에 클론
git clone https://github.com/your-username/My-Beauty-AI.git
cd My-Beauty-AI

# 3. 원본 저장소를 upstream으로 추가
git remote add upstream https://github.com/howl-papa/My-Beauty-AI.git
```

### 2. 개발 환경 구축
```bash
# Python 가상환경 생성 (3.9+ 권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (개발용 포함)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 개발용 의존성
pip install pytest pytest-cov black isort flake8 mypy pre-commit
```

### 3. 데이터베이스 설정
```bash
# PostgreSQL 설치 및 데이터베이스 생성
createdb mybeautyai_dev

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 개발용 설정 입력

# 데이터베이스 스키마 생성
python scripts/setup_database.py
```

### 4. Pre-commit 훅 설정
```bash
# Pre-commit 훅 설치
pre-commit install

# 모든 파일에 대해 pre-commit 실행 (선택사항)
pre-commit run --all-files
```

## 💻 코드 기여하기

### Git 워크플로우

#### 1. 브랜치 생성
```bash
# 최신 main 브랜치로 동기화
git checkout main
git pull upstream main

# 기능별 브랜치 생성
git checkout -b feature/ingredient-analysis-improvement
# 또는
git checkout -b fix/api-response-validation
# 또는  
git checkout -b docs/api-guide-update
```

#### 2. 브랜치 명명 규칙
```
feature/기능명       # 새로운 기능 추가
fix/수정내용         # 버그 수정
docs/문서명          # 문서 업데이트  
refactor/리팩토링명   # 코드 리팩토링
test/테스트명        # 테스트 추가/개선
chore/작업명         # 기타 작업 (빌드, 설정 등)
```

#### 3. 커밋 메시지 규칙
```bash
# 형식: type(scope): description
git commit -m "feat(analyzer): Add chemical interaction detection algorithm"
git commit -m "fix(api): Resolve validation error in product endpoint"
git commit -m "docs(readme): Update installation guide for macOS"
git commit -m "test(routine): Add unit tests for optimization logic"
```

**커밋 타입:**
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정  
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 과정 또는 보조 도구 변경

## 📏 코딩 스타일 가이드

### Python 코드 스타일

#### 1. PEP 8 준수 및 타입 힌트
```python
# ✅ 좋은 예시
from typing import List, Dict, Optional

def analyze_ingredient_conflicts(
    ingredients: List[str], 
    user_profile: Dict[str, Any]
) -> Optional[Dict[str, List[str]]]:
    """성분 간 상호작용을 분석합니다."""
    if not ingredients:
        raise ValueError("성분 목록이 비어있습니다")

    conflicts = []
    for ingredient in ingredients:
        conflict = self._check_individual_conflict(ingredient, user_profile)
        if conflict:
            conflicts.append(conflict)

    return {"conflicts": conflicts} if conflicts else None

# ❌ 나쁜 예시  
def analyze(ing,up):  # 타입 힌트 없음, 변수명 불분명
    if not ing: return None  # 한 줄에 여러 구문
    conflicts=[]  # 띄어쓰기 없음
    for i in ing:  # 의미없는 변수명
        c=self.check(i,up)  
        if c:conflicts.append(c)
    return {"conflicts": conflicts} if conflicts else None
```

#### 2. Docstring 스타일 (Google 스타일)
```python
class ConflictAnalyzer:
    """화장품 성분 간 충돌을 분석하는 클래스.

    이 클래스는 여러 화장품 성분들 간의 화학적, 물리적 상호작용을
    분석하여 잠재적 충돌 위험을 감지합니다.

    Attributes:
        interaction_db: 성분 상호작용 데이터베이스
        severity_calculator: 위험도 계산 모듈
    """

    def __init__(self, interaction_db: InteractionDatabase):
        """ConflictAnalyzer 초기화.

        Args:
            interaction_db: 성분 상호작용 정보를 담은 데이터베이스
        """
        self.interaction_db = interaction_db
        self.severity_calculator = SeverityCalculator()
```

## 🧪 테스트 가이드라인

### 테스트 구조
```
tests/
├── unit/                    # 단위 테스트
│   ├── test_conflict_analyzer.py
│   ├── test_routine_optimizer.py
│   └── test_rag_system.py
├── integration/            # 통합 테스트  
│   ├── test_api_endpoints.py
│   └── test_database_operations.py
├── fixtures/               # 테스트 데이터
│   ├── sample_products.json
│   └── sample_ingredients.json
└── conftest.py            # pytest 설정
```

### 단위 테스트 작성 예시
```python
import pytest
from unittest.mock import Mock, patch
from src.conflict_analyzer import ConflictAnalyzer

class TestConflictAnalyzer:

    @pytest.fixture
    def analyzer(self):
        """ConflictAnalyzer 인스턴스 픽스처."""
        mock_db = Mock()
        return ConflictAnalyzer(interaction_db=mock_db)

    def test_analyze_conflicts_with_known_interaction(self, analyzer):
        """알려진 상호작용이 있는 성분들의 충돌 분석 테스트."""
        # Given
        ingredients = ["retinol", "vitamin_c"]
        analyzer.interaction_db.get_interactions.return_value = [
            {"type": "chemical", "severity": "medium"}
        ]

        # When
        result = analyzer.analyze_conflicts(ingredients)

        # Then
        assert result is not None
        assert len(result["conflicts"]) == 1

    def test_analyze_conflicts_with_empty_ingredients(self, analyzer):
        """빈 성분 목록에 대한 예외 처리 테스트."""
        with pytest.raises(ValueError, match="성분 목록이 비어있습니다"):
            analyzer.analyze_conflicts([])
```

## 📚 문서화 기여

### API 문서 작성 예시
```python
@app.post("/api/v1/analyze-conflicts")
async def analyze_conflicts(request: ConflictAnalysisRequest):
    """제품 간 성분 충돌을 분석합니다.

    두 개 이상의 화장품 제품을 함께 사용할 때 발생할 수 있는
    성분 간의 화학적, 물리적 상호작용을 분석합니다.

    **주의사항:**
    - 분석 결과는 참고용이며 개인차가 있을 수 있습니다
    - 심각한 피부 트러블이 있는 경우 전문의 상담을 받으세요
    """
    pass
```

## 🐛 이슈 및 버그 리포트

### 버그 리포트 템플릿
```markdown
## 🐛 버그 설명
버그에 대한 명확하고 간단한 설명

## 🔄 재현 단계
1. 특정 API 엔드포인트 호출
2. 특정 데이터 입력
3. 오류 발생

## 🎯 예상 동작
정상적으로 동작해야 하는 내용

## 💻 환경 정보
- OS: [예: macOS 13.0]
- Python 버전: [예: 3.9.7]
- 의존성 버전: requirements.txt 참고
```

## 🌍 커뮤니티 가이드라인

### 행동 강령
- 모든 참여자를 존중하고 포용적인 환경 조성
- 건설적인 피드백과 비판 제공
- 다양한 관점과 경험을 수용

### 커뮤니케이션 채널
- **GitHub Issues**: 버그 리포트, 기능 제안
- **Pull Request**: 코드 리뷰 및 토론
- **이메일**: yongrak.pro@gmail.com

## 📄 라이센스 정보

**My Beauty AI**는 MIT License 하에 배포됩니다. 기여하신 모든 코드는 동일한 라이센스 하에 배포됩니다.

---

## 🙏 감사의 말

**My Beauty AI** 프로젝트에 기여해주시는 모든 분들께 진심으로 감사드립니다!

**질문이나 도움이 필요하시면 언제든 연락해주세요:**
- **GitHub**: [@howl-papa](https://github.com/howl-papa)  
- **이메일**: yongrak.pro@gmail.com

**함께 만들어가는 My Beauty AI! 🌸✨**
