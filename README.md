# QA Learning App - Backend

FastAPI 기반의 QA 학습 애플리케이션 백엔드 서버입니다.

## 기능

- 🔐 JWT 기반 인증 시스템
- 👥 사용자 관리 (관리자, 모더레이터, 일반 사용자)
- 📝 게시글 CRUD 및 태그 시스템
- ✅ Todo 리스트 관리
- 💬 댓글 시스템 (중첩 댓글 지원)
- 📁 파일 업로드 및 관리
- 🔄 실시간 WebSocket 통신
- 📧 이메일 서비스
- 🚦 Rate limiting
- 📊 페이지네이션 및 필터링

## 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Cache**: Redis
- **File Storage**: Local filesystem
- **Email**: SMTP
- **WebSocket**: FastAPI WebSocket

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.development` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.development .env
```

### 4. 데이터베이스 설정

PostgreSQL 데이터베이스를 생성하고 `.env` 파일에 연결 정보를 설정합니다.

### 5. 데이터베이스 초기화 및 시드 데이터 생성

```bash
python seeds/seed_data.py
```

### 6. 서버 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --reload --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
backend/
├── api/
│   └── v1/          # API 엔드포인트
├── core/            # 핵심 설정 및 보안
├── models/          # 데이터베이스 모델
├── schemas/         # Pydantic 스키마
├── services/        # 비즈니스 로직
├── utils/           # 유틸리티 함수
├── seeds/           # 시드 데이터
├── main.py          # 애플리케이션 진입점
├── database.py      # 데이터베이스 연결
├── dependencies.py  # 의존성 주입
└── middleware.py    # 미들웨어 설정
```

## 기본 계정

시드 데이터 실행 시 생성되는 기본 계정:

- **관리자**: admin@example.com / password123
- **일반 사용자**: john@example.com / password123
- **모더레이터**: moderator@example.com / password123

## 개발

### 마이그레이션

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "설명"

# 마이그레이션 실행
alembic upgrade head
```

### 테스트

```bash
pytest
```

## 라이선스

MIT