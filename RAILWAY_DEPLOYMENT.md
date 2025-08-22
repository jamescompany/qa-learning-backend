# Railway 배포 가이드

## 🚀 Railway 환경 변수 설정

Railway 대시보드에서 다음 환경 변수를 설정해야 합니다:

### 필수 환경 변수

```bash
# Application
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=[Railway 대시보드에서 설정 - 최소 32자 이상의 랜덤 문자열]
JWT_SECRET_KEY=[Railway 대시보드에서 설정 - 최소 32자 이상의 랜덤 문자열]

# Database (Railway PostgreSQL)
DATABASE_URL=[Railway PostgreSQL 서비스에서 제공하는 DATABASE_URL]

# Redis (Railway Redis 추가 필요)
REDIS_URL=redis://localhost:6379  # Railway Redis 서비스 추가 후 변경

# CORS
CORS_ORIGINS=https://www.qalearningweb.com

# Email (Zoho Mail)
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=[이메일 주소]
SMTP_PASSWORD=[Zoho 앱 비밀번호]  # Zoho 계정에서 생성 필요
SMTP_FROM=[발신 이메일 주소]
ADMIN_EMAIL=[관리자 이메일 주소]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Logging
LOG_LEVEL=WARNING

# Security
SECURE_HEADERS_ENABLED=true
HSTS_ENABLED=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict
```

## 📝 중요 사항

### 1. 데이터베이스 보안
- ✅ PostgreSQL 비밀번호가 변경되었습니다
- ⚠️ 프로덕션용 별도 데이터베이스 생성 권장

### 2. Redis 설정
- Railway에서 Redis 서비스 추가 필요
- 또는 Redis Cloud 사용 고려

### 3. 이메일 설정 (Zoho Mail)
1. Zoho 계정 로그인
2. 설정 → 보안 → 앱 비밀번호
3. 새 앱 비밀번호 생성
4. SMTP_PASSWORD에 설정

### 4. 프론트엔드 CORS
- 실제 프로덕션 도메인으로 변경 필요
- 현재: https://www.qalearningweb.com

## 🔒 보안 체크리스트

- [x] 데이터베이스 비밀번호 변경됨
- [x] SECRET_KEY 생성됨 (48자)
- [x] JWT_SECRET_KEY 생성됨 (48자)
- [x] .gitignore에 환경 파일 추가됨
- [x] alembic.ini에서 하드코딩된 정보 제거됨
- [x] Railway 대시보드에 환경 변수 설정
- [x] Zoho 앱 비밀번호 생성 및 설정
- [ ] Redis 서비스 설정

## 🚨 GitGuardian 알림 해결

1. GitGuardian 대시보드 접속
2. 해당 알림 찾기
3. "Resolved" 또는 "Fixed" 표시
4. 이유: "Credentials rotated and removed from code"

## 📦 Railway 배포 명령

```bash
# Railway CLI 설치 (처음 한 번만)
npm install -g @railway/cli

# Railway 로그인
railway login

# 프로젝트 연결
railway link

# 배포
railway up
```

## 🔄 업데이트 필요 사항

1. **별도 프로덕션 데이터베이스 생성**
   - 현재는 개발/프로덕션이 같은 DB 사용
   - Railway에서 새 PostgreSQL 인스턴스 생성 권장

2. **Redis 서비스 추가**
   - Railway Redis 또는 Redis Cloud 설정

3. **Sentry 설정** (선택사항)
   - 에러 모니터링을 위해 Sentry DSN 추가

4. **도메인 설정**
   - Railway 커스텀 도메인 설정
   - SSL 인증서 자동 적용됨