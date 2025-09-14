# My Beauty AI - API 사용 가이드 📚

> **My Beauty AI**의 RESTful API를 활용하여 화장품 분석 및 루틴 최적화 서비스를 연동하는 완전한 가이드입니다.

## 📋 목차

- [API 개요](#-api-개요)
- [인증 및 인가](#-인증-및-인가)
- [공통 응답 형식](#-공통-응답-형식)
- [제품 API](#-제품-api)
- [성분 API](#-성분-api)
- [분석 API](#-분석-api)
- [AI 채팅 API](#-ai-채팅-api)
- [에러 처리](#-에러-처리)
- [SDK 및 라이브러리](#-sdk-및-라이브러리)
- [실습 예제](#-실습-예제)

## 🌐 API 개요

### Base URL
```
개발환경: http://localhost:8000
스테이징: https://staging-api.mybeauty.ai
프로덕션: https://api.mybeauty.ai
```

### API 버전
- **현재 버전**: v1
- **Base Path**: `/api/v1`
- **응답 형식**: JSON
- **문자 인코딩**: UTF-8

### 요청 헤더
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer {jwt_token}  # 인증이 필요한 경우
```

## 🔐 인증 및 인가

### JWT 토큰 발급
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "user@example.com",
  "password": "securepassword"
}'
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 인증된 요청
```bash
curl -X GET "http://localhost:8000/api/v1/protected-endpoint" \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 📋 공통 응답 형식

### 성공 응답
```json
{
  "success": true,
  "data": {
    // 실제 데이터
  },
  "message": "요청이 성공적으로 처리되었습니다",
  "timestamp": "2024-01-15T09:30:00Z",
  "request_id": "req_12345"
}
```

### 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 유효하지 않습니다",
    "details": [
      {
        "field": "product_ids",
        "message": "최소 1개 이상의 제품 ID가 필요합니다"
      }
    ]
  },
  "timestamp": "2024-01-15T09:30:00Z",
  "request_id": "req_12345"
}
```

## 🧴 제품 API

### 제품 목록 조회
```http
GET /api/v1/products
```

**쿼리 파라미터:**
```
page: int = 1          # 페이지 번호
size: int = 20         # 페이지 크기 (최대 100)
brand: str = None      # 브랜드 필터
category: str = None   # 카테고리 필터
search: str = None     # 검색어 (제품명, 성분)
```

**예제:**
```bash
curl -X GET "http://localhost:8000/api/v1/products?page=1&size=10&brand=innisfree&search=serum"
```

**응답:**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "product_id": "prod_001",
        "product_name": "Green Tea Seed Serum",
        "brand": {
          "brand_id": "brand_001",
          "brand_name": "Innisfree"
        },
        "image_url": "https://example.com/image.jpg",
        "barcode": "8809612860789",
        "ingredients": "Water, Camellia Sinensis Leaf Extract...",
        "ingredient_list": [
          {
            "ingredient_id": "ing_001",
            "ingredient_name": "Water",
            "inci_name": "Aqua"
          }
        ]
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 15,
      "total_items": 150,
      "page_size": 10
    }
  }
}
```

### 특정 제품 상세 조회
```http
GET /api/v1/products/{product_id}
```

**예제:**
```bash
curl -X GET "http://localhost:8000/api/v1/products/prod_001"
```

### 제품 검색
```http
POST /api/v1/products/search
```

**요청 본문:**
```json
{
  "query": "vitamin c serum",
  "filters": {
    "brands": ["innisfree", "laneige"],
    "categories": ["serum", "essence"],
    "ingredients": ["ascorbic acid", "niacinamide"],
    "price_range": {
      "min": 10000,
      "max": 50000
    }
  },
  "sort": {
    "field": "popularity",
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "size": 20
  }
}
```

## 🧪 성분 API

### 성분 목록 조회
```http
GET /api/v1/ingredients
```

**쿼리 파라미터:**
```
page: int = 1              # 페이지 번호
size: int = 50             # 페이지 크기
category: str = None       # 성분 카테고리
function: str = None       # 성분 기능
safety_level: str = None   # 안전 등급
```

**예제:**
```bash
curl -X GET "http://localhost:8000/api/v1/ingredients?category=active&function=anti-aging"
```

### 특정 성분 상세 조회
```http
GET /api/v1/ingredients/{ingredient_id}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "ingredient_id": "ing_001",
    "ingredient_name": "Retinol",
    "inci_name": "Retinol",
    "korean_name": "레티놀",
    "cas_number": "68-26-8",
    "origin_definition": "Vitamin A의 한 형태로 강력한 안티에이징 성분",
    "functions": ["anti-aging", "wrinkle-improvement"],
    "safety_info": {
      "safety_level": "caution",
      "pregnancy_safe": false,
      "concentration_limit": 1.0,
      "usage_notes": "야간 사용 권장, 자외선 차단제 필수"
    },
    "interactions": [
      {
        "ingredient": "Vitamin C",
        "interaction_type": "chemical_conflict",
        "severity": "medium",
        "description": "산화 반응으로 인한 효능 감소"
      }
    ]
  }
}
```

### 성분 상호작용 조회
```http
POST /api/v1/ingredients/interactions
```

**요청 본문:**
```json
{
  "ingredient_ids": ["ing_001", "ing_002", "ing_003"]
}
```

## 🔬 분석 API

### 성분 충돌 분석
```http
POST /api/v1/analyze-conflicts
```

**요청 본문:**
```json
{
  "products": [
    {
      "product_id": "prod_001",
      "usage_time": "morning"
    },
    {
      "product_id": "prod_002", 
      "usage_time": "evening"
    }
  ],
  "user_profile": {
    "skin_type": "combination",
    "age": 28,
    "concerns": ["acne", "pore_size"],
    "allergies": ["fragrance", "sulfates"]
  }
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_12345",
    "overall_risk": "medium",
    "conflicts": [
      {
        "conflict_id": "conflict_001",
        "type": "chemical_interaction",
        "severity": "medium",
        "ingredients": [
          {
            "ingredient_id": "ing_001",
            "ingredient_name": "Retinol",
            "product_id": "prod_001"
          },
          {
            "ingredient_id": "ing_002",
            "ingredient_name": "Salicylic Acid",
            "product_id": "prod_002"
          }
        ],
        "description": "동시 사용 시 피부 자극 위험 증가",
        "recommendation": "사용 시간을 분리하거나 농도를 낮춰주세요",
        "alternatives": [
          {
            "product_id": "prod_003",
            "product_name": "Gentle Retinol Serum"
          }
        ]
      }
    ],
    "recommendations": [
      "레티놀 제품은 저녁에, 살리실산 제품은 아침에 사용하세요",
      "처음 사용 시 격일로 사용하여 피부 적응도를 확인하세요"
    ]
  }
}
```

### 루틴 최적화
```http
POST /api/v1/optimize-routine
```

**요청 본문:**
```json
{
  "user_profile": {
    "skin_type": "oily",
    "age": 25,
    "concerns": ["acne", "blackheads", "oily_t_zone"],
    "current_products": ["cleanser_001", "toner_002"],
    "budget_range": {
      "min": 50000,
      "max": 200000
    }
  },
  "goals": [
    "reduce_acne",
    "control_oil",
    "minimize_pores"
  ],
  "preferences": {
    "routine_complexity": "moderate",
    "time_constraints": {
      "morning": 10,
      "evening": 20
    },
    "product_preferences": {
      "natural_ingredients": true,
      "fragrance_free": true
    }
  }
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "routine_id": "routine_12345",
    "morning_routine": [
      {
        "step": 1,
        "category": "cleanser",
        "product": {
          "product_id": "prod_001",
          "product_name": "Gentle Foam Cleanser",
          "usage_amount": "1-2 pumps",
          "application_method": "거품을 내어 30초간 마사지"
        },
        "wait_time": 0
      },
      {
        "step": 2,
        "category": "toner",
        "product": {
          "product_id": "prod_002",
          "product_name": "BHA Toner",
          "usage_amount": "적당량",
          "application_method": "화장솜에 적셔 T존 위주로 발라주세요"
        },
        "wait_time": 60
      }
    ],
    "evening_routine": [
      // 저녁 루틴 단계들...
    ],
    "weekly_treatments": [
      {
        "treatment": "clay_mask",
        "frequency": "2times_per_week",
        "product_recommendation": {
          "product_id": "prod_005",
          "product_name": "Deep Cleansing Clay Mask"
        }
      }
    ],
    "expected_results": {
      "timeline": "4-6 weeks",
      "improvements": [
        "유분 조절 개선",
        "모공 크기 감소",
        "트러블 예방"
      ]
    }
  }
}
```

## 💬 AI 채팅 API

### AI 상담 채팅
```http
POST /api/v1/chat
```

**요청 본문:**
```json
{
  "message": "레티놀과 비타민C를 함께 사용해도 될까요?",
  "context": {
    "user_id": "user_123",
    "conversation_id": "conv_456",
    "user_profile": {
      "skin_type": "sensitive",
      "age": 30
    }
  }
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "message_id": "msg_789",
    "response": "레티놀과 비타민C는 일반적으로 동시 사용을 권장하지 않습니다. 두 성분 모두 강력한 활성 성분이어서 함께 사용하면 피부 자극을 일으킬 수 있어요. 레티놀은 저녁에, 비타민C는 아침에 사용하시는 것이 좋습니다.",
    "confidence": 0.95,
    "sources": [
      {
        "type": "research_paper",
        "title": "Retinol and Vitamin C Interactions in Skincare",
        "url": "https://example.com/research"
      }
    ],
    "recommendations": [
      {
        "type": "usage_schedule",
        "description": "레티놀: 저녁 사용, 비타민C: 아침 사용"
      }
    ]
  }
}
```

### 채팅 이력 조회
```http
GET /api/v1/chat/history
```

**쿼리 파라미터:**
```
user_id: str           # 사용자 ID
conversation_id: str   # 대화 ID (선택사항)
limit: int = 50        # 메시지 개수 제한
```

## ⚠️ 에러 처리

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 422 | Unprocessable Entity | 유효성 검사 실패 |
| 429 | Too Many Requests | 요청 한도 초과 |
| 500 | Internal Server Error | 서버 오류 |

### 에러 코드 목록

```json
{
  "VALIDATION_ERROR": "입력 데이터 유효성 검사 실패",
  "PRODUCT_NOT_FOUND": "제품을 찾을 수 없음",
  "INGREDIENT_NOT_FOUND": "성분을 찾을 수 없음",
  "ANALYSIS_FAILED": "분석 처리 실패",
  "RATE_LIMIT_EXCEEDED": "API 호출 한도 초과",
  "INSUFFICIENT_CREDITS": "분석 크레딧 부족",
  "AI_SERVICE_UNAVAILABLE": "AI 서비스 일시 중단"
}
```

### 에러 처리 예제 (Python)
```python
import requests

try:
    response = requests.post(
        'http://localhost:8000/api/v1/analyze-conflicts',
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()

    result = response.json()
    if result['success']:
        return result['data']
    else:
        print(f"API 에러: {result['error']['message']}")

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print("API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
    elif e.response.status_code == 422:
        error_details = e.response.json()['error']['details']
        print(f"입력 데이터 오류: {error_details}")
    else:
        print(f"HTTP 에러: {e.response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"네트워크 에러: {e}")
```

## 📦 SDK 및 라이브러리

### Python SDK
```python
from mybeauty_ai import BeautyAI

# 클라이언트 초기화
client = BeautyAI(api_key='your_api_key', base_url='http://localhost:8000')

# 성분 충돌 분석
conflicts = await client.analyze_conflicts([
    {'product_id': 'prod_001', 'usage_time': 'morning'},
    {'product_id': 'prod_002', 'usage_time': 'evening'}
])

# 루틴 최적화
routine = await client.optimize_routine(
    user_profile={'skin_type': 'oily', 'age': 25},
    goals=['reduce_acne', 'control_oil']
)
```

### JavaScript SDK
```javascript
import { BeautyAI } from '@mybeauty-ai/sdk';

const client = new BeautyAI({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8000'
});

// 제품 검색
const products = await client.products.search({
  query: 'vitamin c serum',
  filters: { brands: ['innisfree'] }
});

// AI 채팅
const response = await client.chat.send({
  message: '민감성 피부에 좋은 제품 추천해주세요',
  context: { skinType: 'sensitive' }
});
```

## 🎯 실습 예제

### 완전한 스킨케어 루틴 분석 워크플로우

```python
import asyncio
import aiohttp

class BeautyAnalyzer:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def complete_analysis(self, products: list, user_profile: dict):
        async with aiohttp.ClientSession() as session:
            # 1. 성분 충돌 분석
            conflicts = await self.analyze_conflicts(session, products, user_profile)

            # 2. 루틴 최적화
            if not conflicts or conflicts['overall_risk'] == 'low':
                routine = await self.optimize_routine(session, products, user_profile)
            else:
                # 충돌이 있는 경우 대안 제품 추천
                alternatives = await self.get_alternatives(session, conflicts)
                routine = await self.optimize_routine(session, alternatives, user_profile)

            # 3. AI 상담으로 추가 조언 받기
            ai_advice = await self.get_ai_advice(session, routine, conflicts)

            return {
                'conflicts': conflicts,
                'routine': routine,
                'ai_advice': ai_advice
            }

    async def analyze_conflicts(self, session, products, user_profile):
        url = f"{self.base_url}/api/v1/analyze-conflicts"
        payload = {
            'products': products,
            'user_profile': user_profile
        }
        headers = {'Authorization': f'Bearer {self.api_key}'}

        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            return result['data']

# 사용 예제
async def main():
    analyzer = BeautyAnalyzer(
        api_key='your_api_key',
        base_url='http://localhost:8000'
    )

    products = [
        {'product_id': 'prod_001', 'usage_time': 'morning'},
        {'product_id': 'prod_002', 'usage_time': 'evening'}
    ]

    user_profile = {
        'skin_type': 'combination',
        'age': 28,
        'concerns': ['acne', 'dullness']
    }

    results = await analyzer.complete_analysis(products, user_profile)

    print("=== 충돌 분석 결과 ===")
    print(f"전체 위험도: {results['conflicts']['overall_risk']}")

    print("\n=== 추천 루틴 ===")
    for step in results['routine']['morning_routine']:
        print(f"{step['step']}. {step['product']['product_name']}")

    print(f"\n=== AI 조언 ===")
    print(results['ai_advice']['response'])

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 API 사용량 및 제한

### 요청 제한 (Rate Limiting)
```
무료 플랜: 100 요청/시간
기본 플랜: 1,000 요청/시간  
프리미엄 플랜: 10,000 요청/시간
엔터프라이즈: 무제한
```

### 응답 시간
```
제품 조회: < 200ms
성분 분석: < 2초
루틴 최적화: < 5초
AI 채팅: < 3초
```

---

**이 가이드는 My Beauty AI API의 모든 기능을 활용하는 데 필요한 정보를 제공합니다. 추가 질문이나 지원이 필요하면 [yongrak.pro@gmail.com](mailto:yongrak.pro@gmail.com)로 연락해주세요!** 🚀
