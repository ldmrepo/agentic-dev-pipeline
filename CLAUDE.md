# 에이전틱 개발 파이프라인 프로젝트

## 프로젝트 개요
- **목적**: AI 에이전트를 활용한 자동화된 소프트웨어 개발 파이프라인
- **아키텍처**: 마이크로서비스 아키텍처
- **주요 기술**: Node.js, TypeScript, React, PostgreSQL, Docker, Kubernetes

## 개발 가이드라인

### 코딩 표준
- TypeScript strict mode 사용
- ESLint + Prettier 적용
- Conventional Commits 준수
- 테스트 커버리지 85% 이상 유지

### 아키텍처 원칙
- Clean Architecture 패턴 적용
- SOLID 원칙 준수
- DDD (Domain Driven Design) 접근
- Event-Driven Architecture

### 품질 보장
- 코드 리뷰 필수
- 자동화된 테스트 (Unit, Integration, E2E)
- 보안 스캔 통과
- 성능 기준 달성 (응답시간 < 200ms)

## 워크플로우 설정

### 브랜치 전략
- main: 프로덕션 브랜치
- develop: 개발 통합 브랜치
- feature/*: 기능 개발 브랜치
- hotfix/*: 긴급 수정 브랜치

### 배포 전략
- Staging 환경 자동 배포
- Production 환경 승인 후 배포
- Blue-Green 배포 전략
- 자동 롤백 메커니즘

## 에이전트 설정

### Planning Agent
- 요구사항 분석 시 비즈니스 가치 우선 고려
- 기술적 부채 최소화
- 확장성과 유지보수성 중시
- 보안 고려사항 필수 포함

### Development Agent
- TDD (Test Driven Development) 적용
- 코드 품질 지표 준수
- 성능 최적화 고려
- 문서화 자동 생성

### Testing Agent
- 테스트 피라미드 전략 (70% Unit, 20% Integration, 10% E2E)
- 자동 테스트 케이스 생성
- 성능 테스트 포함
- 보안 테스트 수행

### Deployment Agent
- 무중단 배포 보장
- 헬스체크 및 모니터링
- 자동 롤백 조건: 에러율 > 1%, 응답시간 > 500ms
- 단계별 트래픽 증가: 5% → 25% → 50% → 100%

## 명령어 가이드

### 개발 관련
- `npm run dev`: 개발 서버 시작
- `npm run build`: 프로덕션 빌드
- `npm run test`: 전체 테스트 실행
- `npm run test:unit`: 단위 테스트만 실행
- `npm run test:e2e`: E2E 테스트 실행
- `npm run lint`: 코드 린팅
- `npm run format`: 코드 포매팅

### Docker 관련
- `docker-compose up -d`: 로컬 인프라 시작
- `docker-compose down`: 로컬 인프라 정지
- `docker build -t app:latest .`: 애플리케이션 이미지 빌드

### 파이프라인 관련
- `claude /pipeline`: 기본 개발 파이프라인 실행
- `claude /hotfix`: 긴급 수정 파이프라인 실행
- `claude /deploy`: 배포 파이프라인 실행
- `claude /status`: 파이프라인 상태 확인

## 중요 알림

### 필수 확인사항
- 모든 커밋 전 테스트 실행 필수
- 프로덕션 배포 전 승인 필요
- 보안 스캔 Critical/High 취약점 해결 필수
- 성능 기준 미달 시 배포 차단

### 자동화 수준
현재 설정: **Standard** (프로덕션 배포와 보안 변경시에만 승인 필요)

변경을 원할 경우:
- Conservative: 더 많은 승인 단계
- Aggressive: 최소한의 승인
- Autonomous: 완전 자동화 (테스트 환경만 권장)
