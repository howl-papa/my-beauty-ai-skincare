# My Beauty AI - 설치 및 배포 가이드 ⚙️

> **My Beauty AI** 프로젝트를 로컬 개발 환경부터 프로덕션 배포까지 완전하게 설정하는 상세한 가이드입니다.

## 📋 목차

- [시스템 요구사항](#-시스템-요구사항)
- [로컬 개발 환경 설정](#-로컬-개발-환경-설정)
- [데이터베이스 설정](#-데이터베이스-설정)
- [환경변수 설정](#-환경변수-설정)
- [개발 서버 실행](#-개발-서버-실행)
- [Docker를 이용한 설치](#-docker를-이용한-설치)
- [프로덕션 배포](#-프로덕션-배포)
- [문제 해결 가이드](#-문제-해결-가이드)

## 💻 시스템 요구사항

### 필수 요구사항
- **Python**: 3.9 이상 (3.11 권장)
- **PostgreSQL**: 13 이상
- **Node.js**: 16 이상 (프론트엔드가 있는 경우)
- **Git**: 2.30 이상

### 권장 요구사항
- **RAM**: 8GB 이상 (개발환경), 16GB 이상 (프로덕션)
- **저장공간**: 10GB 이상
- **OS**: macOS 11+, Ubuntu 20.04+, Windows 10+

### 외부 서비스
- **OpenAI API**: GPT-4 접근을 위한 API 키
- **Vector Database**: Chroma (로컬) 또는 Pinecone (클라우드)
- **Redis** (선택사항): 캐싱 및 세션 관리용

## 🚀 로컬 개발 환경 설정

### 1. 저장소 클론
```bash
# GitHub에서 프로젝트 클론
git clone https://github.com/howl-papa/My-Beauty-AI.git
cd My-Beauty-AI

# 또는 SSH 사용
git clone git@github.com:howl-papa/My-Beauty-AI.git
cd My-Beauty-AI
```

### 2. Python 가상환경 설정

#### macOS/Linux
```bash
# Python 3.9+ 설치 확인
python3 --version

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip
```

#### Windows
```cmd
# Python 설치 확인
python --version

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# pip 업그레이드
python -m pip install --upgrade pip
```

### 3. 패키지 설치
```bash
# 프로덕션 의존성 설치
pip install -r requirements.txt

# 개발용 의존성 설치 (선택사항)
pip install -r requirements-dev.txt

# 설치 확인
pip list | grep -E "(fastapi|sqlalchemy|llamaindex)"
```

### 4. 환경 설정 파일 생성
```bash
# 환경변수 템플릿 복사
cp .env.example .env

# 설정 파일 편집 (다음 섹션 참고)
nano .env  # 또는 원하는 편집기 사용
```

## 🗄️ 데이터베이스 설정

### PostgreSQL 설치

#### macOS (Homebrew 사용)
```bash
# PostgreSQL 설치
brew install postgresql

# 서비스 시작
brew services start postgresql

# 사용자 계정으로 접속
psql postgres
```

#### Ubuntu/Debian
```bash
# 패키지 업데이트 및 설치
sudo apt update
sudo apt install postgresql postgresql-contrib

# 서비스 시작 및 활성화
sudo systemctl start postgresql
sudo systemctl enable postgresql

# postgres 사용자로 전환
sudo -u postgres psql
```

#### Windows
```bash
# PostgreSQL 공식 설치 프로그램 다운로드 및 실행
# https://www.postgresql.org/download/windows/

# 설치 후 psql 실행
psql -U postgres
```

### 데이터베이스 생성 및 설정
```sql
-- PostgreSQL 콘솔에서 실행
CREATE DATABASE mybeautyai_dev;
CREATE USER mybeautyai_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mybeautyai_dev TO mybeautyai_user;

-- 권한 확인
\l  -- 데이터베이스 목록 확인
\q  -- PostgreSQL 콘솔 종료
```

### 스키마 생성
```bash
# 가상환경이 활성화된 상태에서
python scripts/setup_database.py

# 또는 직접 SQL 실행
psql -d mybeautyai_dev -f database/schema.sql
```

### 초기 데이터 로드 (선택사항)
```bash
# 샘플 데이터 로드
python scripts/load_sample_data.py

# 또는 SQL 파일로 직접 로드
psql -d mybeautyai_dev -f database/seed_data.sql
```

## ⚙️ 환경변수 설정

### .env 파일 설정
`.env` 파일을 열어서 다음과 같이 설정합니다:

```bash
# 데이터베이스 설정
DATABASE_URL=postgresql://mybeautyai_user:secure_password@localhost:5432/mybeautyai_dev

# AI/ML 서비스 설정
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Vector Database 설정 (Chroma 로컬 사용)
VECTOR_DB_TYPE=chroma
VECTOR_DB_PATH=./data/vector_store

# 또는 Pinecone 사용시
# VECTOR_DB_TYPE=pinecone
# PINECONE_API_KEY=your-pinecone-api-key
# PINECONE_ENVIRONMENT=your-pinecone-environment

# Redis 설정 (선택사항)
REDIS_URL=redis://localhost:6379/0

# 애플리케이션 설정
SECRET_KEY=your-very-secure-secret-key-here
DEBUG_MODE=true
LOG_LEVEL=INFO

# CORS 설정
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000

# API 설정
MAX_REQUESTS_PER_MINUTE=100
```

### 필수 API 키 발급

#### OpenAI API 키 발급
1. [OpenAI 웹사이트](https://platform.openai.com/) 접속
2. 계정 생성 또는 로그인
3. API Keys 섹션에서 새 키 생성
4. 생성된 키를 `.env` 파일에 추가

#### Pinecone 설정 (선택사항)
```bash
# Pinecone 사용시 추가 설정
pip install pinecone-client

# .env 파일에 추가
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-environment
PINECONE_INDEX_NAME=beauty-ai-index
```

## 🔧 개발 서버 실행

### 1. Vector Database 초기화
```bash
# Chroma 벡터 스토어 초기화
python scripts/init_vector_store.py

# 성분 데이터 인덱싱
python scripts/index_ingredients.py
```

### 2. 개발 서버 시작
```bash
# FastAPI 개발 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 또는 Python 직접 실행
python -m uvicorn app:app --reload --port 8000
```

### 3. 서비스 확인
```bash
# API 서버 상태 확인
curl http://localhost:8000/health

# API 문서 확인
# 브라우저에서 http://localhost:8000/docs 접속

# 간단한 API 테스트
curl -X GET "http://localhost:8000/api/v1/products?limit=5"
```

## 🐳 Docker를 이용한 설치

### Docker Compose를 이용한 전체 스택 실행

#### 1. Docker 설치 확인
```bash
# Docker 및 Docker Compose 설치 확인
docker --version
docker-compose --version
```

#### 2. 환경 설정
```bash
# Docker용 환경변수 설정
cp .env.example .env.docker

# Docker 설정에 맞게 .env.docker 편집
# DATABASE_URL=postgresql://postgres:postgres@db:5432/mybeautyai
```

#### 3. 서비스 시작
```bash
# 모든 서비스 시작 (백그라운드)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f app
```

#### 4. 개발 모드로 실행
```bash
# 개발 모드 설정 사용
docker-compose -f docker-compose.dev.yml up

# 코드 변경시 자동 재시작 활성화
docker-compose -f docker-compose.dev.yml up --build
```

### Docker 개별 서비스 관리
```bash
# 데이터베이스만 시작
docker-compose up -d db

# 애플리케이션 재빌드
docker-compose build app

# 서비스 중지
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
```

## 🌐 프로덕션 배포

### 1. 환경 준비

#### 서버 사양 권장사항
```
CPU: 4 cores 이상
RAM: 16GB 이상
Storage: 100GB SSD 이상
네트워크: 1Gbps 이상
```

#### Ubuntu 서버 기본 설정
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y git python3-pip python3-venv postgresql nginx redis-server

# 방화벽 설정
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. 애플리케이션 배포

#### 소스코드 배포
```bash
# 배포용 디렉토리 생성
sudo mkdir -p /var/www/mybeautyai
sudo chown $USER:$USER /var/www/mybeautyai

# 프로젝트 클론
cd /var/www/mybeautyai
git clone https://github.com/howl-papa/My-Beauty-AI.git .

# 프로덕션 브랜치 체크아웃 (있는 경우)
git checkout production
```

#### Python 환경 설정
```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 프로덕션 의존성 설치
pip install -r requirements.txt

# Gunicorn 설치 (WSGI 서버)
pip install gunicorn
```

#### 환경변수 설정
```bash
# 프로덕션용 환경변수 설정
cp .env.example .env
nano .env

# 주요 프로덕션 설정
DEBUG_MODE=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://username:password@localhost:5432/mybeautyai_prod
```

### 3. 데이터베이스 설정

#### PostgreSQL 프로덕션 설정
```bash
# PostgreSQL 서비스 설정
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 보안 설정
sudo -u postgres psql -c "CREATE DATABASE mybeautyai_prod;"
sudo -u postgres psql -c "CREATE USER prod_user WITH ENCRYPTED PASSWORD 'very_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mybeautyai_prod TO prod_user;"
```

#### 스키마 및 데이터 마이그레이션
```bash
# 프로덕션 DB에 스키마 적용
psql -d mybeautyai_prod -f database/schema.sql

# 필요시 데이터 마이그레이션
python scripts/migrate_data.py
```

### 4. 웹 서버 설정

#### Gunicorn 설정
```bash
# Gunicorn 설정 파일 생성
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
user = "www-data"
group = "www-data"
preload_app = True
EOF
```

#### Systemd 서비스 설정
```bash
# 서비스 파일 생성
sudo tee /etc/systemd/system/mybeautyai.service > /dev/null << EOF
[Unit]
Description=My Beauty AI FastAPI application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/mybeautyai
Environment=PATH=/var/www/mybeautyai/venv/bin
ExecStart=/var/www/mybeautyai/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable mybeautyai
sudo systemctl start mybeautyai
```

#### Nginx 리버스 프록시 설정
```bash
# Nginx 사이트 설정
sudo tee /etc/nginx/sites-available/mybeautyai << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;

        # CORS 헤더
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
    }

    location /static/ {
        alias /var/www/mybeautyai/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 사이트 활성화
sudo ln -s /etc/nginx/sites-available/mybeautyai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL 인증서 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 설정 확인
sudo crontab -l | grep certbot
```

### 6. 모니터링 및 로그 설정

#### 로그 파일 설정
```bash
# 로그 디렉토리 생성
sudo mkdir -p /var/log/mybeautyai
sudo chown www-data:www-data /var/log/mybeautyai

# 로그 로테이션 설정
sudo tee /etc/logrotate.d/mybeautyai << EOF
/var/log/mybeautyai/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload mybeautyai
    endscript
}
EOF
```

## 🔍 문제 해결 가이드

### 일반적인 설치 문제

#### Python 가상환경 문제
```bash
# 가상환경이 활성화되지 않는 경우
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Windows에서 실행 정책 오류
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 패키지 설치 오류
```bash
# pip 캐시 클리어
pip cache purge

# 의존성 충돌 해결
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --force-reinstall
```

#### 데이터베이스 연결 문제
```bash
# PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql

# 연결 테스트
pg_isready -h localhost -p 5432

# 권한 확인
psql -d mybeautyai_dev -c "SELECT current_user, current_database();"
```

### API 서버 문제

#### 서버 시작 오류
```bash
# 포트 사용 확인
netstat -tlnp | grep :8000
lsof -i :8000

# 환경변수 확인
python -c "from config import settings; print(settings.database_url)"

# 디버그 모드로 실행
DEBUG_MODE=true uvicorn app:app --reload --log-level debug
```

#### 성능 문제
```bash
# CPU 및 메모리 사용량 확인
htop
sudo iotop

# 데이터베이스 연결 풀 상태 확인
psql -d mybeautyai_dev -c "SELECT * FROM pg_stat_activity;"
```

### Docker 관련 문제

#### 컨테이너 시작 실패
```bash
# 로그 확인
docker-compose logs app

# 컨테이너 내부 접속
docker-compose exec app bash

# 이미지 재빌드
docker-compose build --no-cache app
```

#### 볼륨 마운트 문제
```bash
# 권한 확인
ls -la ./data/

# 볼륨 권한 수정
sudo chown -R 1000:1000 ./data/
```

### 프로덕션 배포 문제

#### 서비스 시작 실패
```bash
# 서비스 상태 확인
sudo systemctl status mybeautyai

# 로그 확인
sudo journalctl -u mybeautyai -f

# 설정 파일 권한 확인
sudo chown www-data:www-data /var/www/mybeautyai/.env
sudo chmod 600 /var/www/mybeautyai/.env
```

#### Nginx 설정 오류
```bash
# 설정 파일 테스트
sudo nginx -t

# Nginx 로그 확인
sudo tail -f /var/log/nginx/error.log

# SSL 인증서 갱신
sudo certbot renew --dry-run
```

## 📊 성능 최적화 팁

### 데이터베이스 최적화
```sql
-- 인덱스 최적화
CREATE INDEX CONCURRENTLY idx_products_brand_id ON products(brand_id);
CREATE INDEX CONCURRENTLY idx_ingredients_name ON ingredients(ingredient_name);

-- 통계 정보 업데이트
ANALYZE;
```

### 애플리케이션 최적화
```python
# config.py에서 연결 풀 설정
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}
```

### Redis 캐싱 활용
```bash
# Redis 설정 최적화
sudo nano /etc/redis/redis.conf

# 메모리 사용량 제한
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

**My Beauty AI 설치가 완료되었습니다! 🎉**

추가 도움이 필요하시면:
- **GitHub Issues**: [문제 신고](https://github.com/howl-papa/My-Beauty-AI/issues)
- **이메일**: yongrak.pro@gmail.com
- **문서**: [프로젝트 위키](https://github.com/howl-papa/My-Beauty-AI/wiki)
