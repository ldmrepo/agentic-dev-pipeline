# 사용 예시

이 디렉토리는 에이전틱 개발 파이프라인을 활용한 다양한 프로젝트 예시를 포함합니다.

## 📁 예시 프로젝트 목록

### 1. Simple API Server
**위치**: `examples/simple-api/`
**설명**: Express.js 기반 간단한 REST API 서버
**소요시간**: 약 30분
**학습목표**: 기본 파이프라인 이해

```bash
cd examples/simple-api/
claude -f ../../workflows/basic-development.md
```

### 2. Web Application
**위치**: `examples/web-app/`
**설명**: React + Node.js 풀스택 웹 애플리케이션
**소요시간**: 약 2시간
**학습목표**: 프론트엔드-백엔드 통합 개발

```bash
cd examples/web-app/
export REQUIREMENTS="사용자 인증과 프로필 관리가 있는 웹 애플리케이션"
claude -f ../../workflows/basic-development.md
```

### 3. Microservices
**위치**: `examples/microservices/`
**설명**: 마이크로서비스 아키텍처 기반 시스템
**소요시간**: 약 3-4시간
**학습목표**: 복잡한 분산 시스템 개발

```bash
cd examples/microservices/
export REQUIREMENTS="사용자, 주문, 결제 마이크로서비스"
claude -f ../../workflows/microservices-development.md
```

### 4. Data Pipeline
**위치**: `examples/data-pipeline/`
**설명**: 데이터 수집, 처리, 분석 파이프라인
**소요시간**: 약 1-2시간
**학습목표**: 데이터 처리 워크플로우

```bash
cd examples/data-pipeline/
claude -f ../../workflows/data-pipeline.md
```

## 🚀 빠른 시작

### 전제 조건
- Claude Code 설치 및 인증 완료
- Docker 실행 중
- 기본 MCP 서버 설정 완료

### 첫 번째 예시 실행
```bash
# 1. 간단한 API 서버 예시
mkdir -p examples/my-first-api
cd examples/my-first-api

# 2. 요구사항 설정
export REQUIREMENTS="사용자 CRUD API 서버"
export PROJECT_NAME="my-first-api"

# 3. 파이프라인 실행
claude -f ../../workflows/basic-development.md

# 4. 결과 확인
ls -la
npm test
docker-compose up -d
```

## 📚 학습 가이드

### 초급자 과정
1. **Simple API** → 기본 개념 이해
2. **Web Application** → 풀스택 개발 경험
3. **Documentation** → 자동 문서화 학습

### 중급자 과정
1. **Microservices** → 분산 시스템 설계
2. **Data Pipeline** → 데이터 처리 워크플로우
3. **Performance Testing** → 성능 최적화

### 고급자 과정
1. **Multi-Cloud Deployment** → 클라우드 네이티브
2. **Custom Agents** → 전용 에이전트 개발
3. **Enterprise Integration** → 대규모 시스템 통합

## 💡 팁과 요령

### 성공적인 실행을 위한 팁
- 충분한 시스템 리소스 확보 (메모리 8GB 이상 권장)
- 안정적인 인터넷 연결 필요
- 단계별로 진행하며 결과 확인
- 오류 발생 시 로그 확인 후 재시도

### 커스터마이징 방법
- REQUIREMENTS 환경 변수로 요구사항 조정
- CLAUDE.md 파일로 프로젝트별 설정
- 워크플로우 파일 수정으로 프로세스 변경
