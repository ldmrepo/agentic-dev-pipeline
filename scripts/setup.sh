#!/bin/bash

# 에이전틱 개발 파이프라인 초기 설정 스크립트
# Usage: ./scripts/setup.sh

set -e

echo "🚀 에이전틱 개발 파이프라인 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 전제 조건 확인
check_prerequisites() {
    print_status "전제 조건을 확인하는 중..."
    
    # Node.js 확인
    if ! command -v node &> /dev/null; then
        print_error "Node.js가 설치되어 있지 않습니다. https://nodejs.org 에서 설치해주세요."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js 18 이상이 필요합니다. 현재 버전: $(node --version)"
        exit 1
    fi
    print_success "Node.js $(node --version) 확인됨"
    
    # Git 확인
    if ! command -v git &> /dev/null; then
        print_error "Git이 설치되어 있지 않습니다."
        exit 1
    fi
    print_success "Git $(git --version | cut -d' ' -f3) 확인됨"
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        print_warning "Docker가 설치되어 있지 않습니다. 일부 기능이 제한될 수 있습니다."
    else
        print_success "Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1) 확인됨"
    fi
}

# Claude Code 설치 및 설정
setup_claude_code() {
    print_status "Claude Code를 설정하는 중..."
    
    # Claude Code 설치 확인
    if ! command -v claude &> /dev/null; then
        print_status "Claude Code를 설치하는 중..."
        npm install -g @anthropic-ai/claude-code
        if [ $? -eq 0 ]; then
            print_success "Claude Code 설치 완료"
        else
            print_error "Claude Code 설치 실패"
            exit 1
        fi
    else
        print_success "Claude Code $(claude --version) 이미 설치됨"
    fi
    
    # API 키 확인
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_warning "ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다."
        echo "다음 명령어로 API 키를 설정하세요:"
        echo "export ANTHROPIC_API_KEY='your_api_key_here'"
        echo "또는 .env 파일에 추가하세요."
    else
        print_success "ANTHROPIC_API_KEY 설정됨"
    fi
}

# 환경 변수 파일 생성
create_env_file() {
    print_status "환경 변수 파일을 생성하는 중..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name

# Slack Integration (Optional)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_CHANNEL_ID=your-channel-id

# Docker Registry (Optional)
DOCKER_REGISTRY=your-registry-url
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password

# Monitoring (Optional)
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000

# Database (Optional)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379

# Logging (Optional)
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
        print_success ".env 파일이 생성되었습니다. API 키들을 설정해주세요."
    else
        print_warning ".env 파일이 이미 존재합니다."
    fi
}

# 디렉토리 구조 생성
create_directory_structure() {
    print_status "프로젝트 디렉토리 구조를 생성하는 중..."
    
    # 필요한 디렉토리들 생성
    mkdir -p .claude/commands
    mkdir -p .claude/memory
    mkdir -p .claude/logs
    mkdir -p configs/agents
    mkdir -p configs/tools
    mkdir -p configs/environments
    mkdir -p templates/projects
    mkdir -p templates/workflows
    mkdir -p workflows
    mkdir -p scripts
    mkdir -p logs
    mkdir -p tmp
    
    print_success "디렉토리 구조 생성 완료"
}

# CLAUDE.md 프로젝트 설정 파일 생성
create_claude_config() {
    print_status "CLAUDE.md 설정 파일을 생성하는 중..."
    
    if [ ! -f "CLAUDE.md" ]; then
        cat > CLAUDE.md << 'EOF'
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
EOF
        print_success "CLAUDE.md 설정 파일 생성 완료"
    else
        print_warning "CLAUDE.md 파일이 이미 존재합니다."
    fi
}

# MCP 서버 설정 파일 생성
create_mcp_config() {
    print_status "MCP 서버 설정 파일을 생성하는 중..."
    
    if [ ! -f ".mcp.json" ]; then
        cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "args": ["--allowed-directory", "./"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    }
  }
}
EOF
        print_success ".mcp.json 설정 파일 생성 완료"
    else
        print_warning ".mcp.json 파일이 이미 존재합니다."
    fi
}

# 기본 커맨드 파일들 생성
create_commands() {
    print_status "기본 명령어 파일들을 생성하는 중..."
    
    # 파이프라인 실행 명령어
    cat > .claude/commands/pipeline.md << 'EOF'
# 기본 개발 파이프라인 실행

전체 개발 파이프라인을 실행해줘:

## 1단계: 계획 수립
- 프로젝트 요구사항 분석
- 아키텍처 설계
- 개발 계획 수립
- 의존성 매핑

## 2단계: 병렬 개발
- Backend 개발 (API, 데이터베이스)
- Frontend 개발 (UI, 상태관리)  
- Infrastructure 설정 (Docker, K8s)

## 3단계: 품질 보장
- 자동 테스트 실행
- 코드 품질 검사
- 보안 스캔
- 성능 테스트

## 4단계: 배포
- Staging 환경 배포
- Production 배포 준비
- 모니터링 설정

각 단계 완료시 진행상황을 보고해줘.
EOF

    # 핫픽스 명령어
    cat > .claude/commands/hotfix.md << 'EOF'
# 긴급 수정 파이프라인

긴급 버그 수정을 위한 빠른 파이프라인을 실행해줘:

## 분석 (5분)
- 이슈 영향도 분석: $ISSUE_DESCRIPTION
- 근본 원인 파악
- 최소 수정 범위 결정

## 수정 (20분)
- 타겟 수정 구현
- 관련 테스트 작성
- 회귀 테스트 확인

## 검증 (10분)
- 수정 사항 검증
- 사이드 이펙트 확인
- 성능 영향 측정

## 배포 (10분)
- Staging 배포 및 검증
- Production 배포
- 모니터링 강화

전체 45분 내 완료를 목표로 해줘.
EOF

    # 상태 확인 명령어
    cat > .claude/commands/status.md << 'EOF'
# 파이프라인 상태 확인

현재 프로젝트와 파이프라인 상태를 확인해줘:

## 프로젝트 상태
- Git 저장소 상태 (브랜치, 변경사항)
- 의존성 상태 (package.json, 보안 취약점)
- 빌드 상태 (최근 빌드 결과)

## 코드 품질
- 테스트 커버리지
- 코드 품질 지표
- 보안 스캔 결과

## 인프라 상태
- 개발 환경 상태
- Staging 환경 상태
- Production 환경 상태

## 최근 활동
- 최근 커밋 내역
- 배포 히스토리
- 이슈 및 PR 상태

상태를 요약해서 보고해줘.
EOF

    print_success "기본 명령어 파일들 생성 완료"
}

# Docker Compose 파일 생성
create_docker_compose() {
    print_status "Docker Compose 파일을 생성하는 중..."
    
    if [ ! -f "docker-compose.yml" ]; then
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL 데이터베이스
  postgres:
    image: postgres:15-alpine
    container_name: agentic-postgres
    environment:
      POSTGRES_DB: agentic_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 캐시
  redis:
    image: redis:7-alpine
    container_name: agentic-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Prometheus 모니터링
  prometheus:
    image: prom/prometheus:latest
    container_name: agentic-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  # Grafana 대시보드
  grafana:
    image: grafana/grafana:latest
    container_name: agentic-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana:/etc/grafana/provisioning
    depends_on:
      - prometheus

  # Elasticsearch (로깅)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: agentic-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  # Kibana (로그 시각화)
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    container_name: agentic-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  default:
    name: agentic-network
EOF
        print_success "docker-compose.yml 파일 생성 완료"
    else
        print_warning "docker-compose.yml 파일이 이미 존재합니다."
    fi
}

# 기본 설정 파일들 생성
create_config_files() {
    print_status "기본 설정 파일들을 생성하는 중..."
    
    # .gitignore 파일
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << 'EOF'
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.production
.env.staging

# Logs
logs/
*.log
.claude/logs/

# Temporary files
tmp/
temp/
.tmp/

# Build outputs
dist/
build/
.next/
out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.docker/

# Claude Code specific
.claude/settings.local.json

# Monitoring data
prometheus_data/
grafana_data/
elasticsearch_data/
EOF
        print_success ".gitignore 파일 생성 완료"
    fi
    
    # package.json 파일 (기본 스크립트만)
    if [ ! -f "package.json" ]; then
        cat > package.json << 'EOF'
{
  "name": "agentic-dev-pipeline",
  "version": "1.0.0",
  "description": "AI Agent-powered Development Pipeline",
  "main": "index.js",
  "scripts": {
    "setup": "./scripts/setup.sh",
    "dev": "echo 'Development server starting...'",
    "build": "echo 'Building application...'",
    "test": "echo 'Running tests...'",
    "lint": "echo 'Linting code...'",
    "format": "echo 'Formatting code...'",
    "docker:up": "docker-compose up -d",
    "docker:down": "docker-compose down",
    "pipeline": "claude /pipeline",
    "hotfix": "claude /hotfix",
    "status": "claude /status"
  },
  "keywords": ["ai", "agent", "pipeline", "automation", "claude"],
  "author": "",
  "license": "MIT",
  "devDependencies": {
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0"
  }
}
EOF
        print_success "package.json 파일 생성 완료"
    fi
}

# 권한 설정
set_permissions() {
    print_status "파일 권한을 설정하는 중..."
    
    # 스크립트 파일들 실행 권한 부여
    chmod +x scripts/*.sh 2>/dev/null || true
    
    # Claude 설정 디렉토리 권한 설정
    chmod -R 755 .claude/ 2>/dev/null || true
    
    print_success "파일 권한 설정 완료"
}

# 초기 테스트
run_initial_test() {
    print_status "초기 테스트를 실행하는 중..."
    
    # Claude Code 연결 테스트
    if command -v claude &> /dev/null; then
        if claude --version &> /dev/null; then
            print_success "Claude Code 연결 테스트 통과"
        else
            print_warning "Claude Code가 설치되었지만 인증이 필요할 수 있습니다."
            echo "다음 명령어로 로그인하세요: claude auth login"
        fi
    fi
    
    # Docker 테스트 (설치된 경우)
    if command -v docker &> /dev/null; then
        if docker ps &> /dev/null; then
            print_success "Docker 연결 테스트 통과"
        else
            print_warning "Docker가 실행되지 않고 있습니다. Docker Desktop을 시작해주세요."
        fi
    fi
}

# 설정 완료 안내
print_completion_guide() {
    echo ""
    echo "🎉 에이전틱 개발 파이프라인 초기 설정이 완료되었습니다!"
    echo ""
    echo "📋 다음 단계를 진행해주세요:"
    echo ""
    echo "1️⃣  환경 변수 설정:"
    echo "   - .env 파일을 열어서 API 키들을 설정하세요"
    echo "   - 특히 ANTHROPIC_API_KEY는 필수입니다"
    echo ""
    echo "2️⃣  Claude Code 인증:"
    echo "   claude auth login"
    echo ""
    echo "3️⃣  개발 환경 시작:"
    echo "   docker-compose up -d  # 로컬 인프라 시작"
    echo "   npm run status        # 현재 상태 확인"
    echo ""
    echo "4️⃣  첫 번째 파이프라인 실행:"
    echo "   claude /pipeline      # 기본 개발 파이프라인"
    echo ""
    echo "📚 추가 정보:"
    echo "   - 문서: docs/ 디렉토리"
    echo "   - 워크플로우: workflows/ 디렉토리"
    echo "   - 설정: configs/ 디렉토리"
    echo ""
    echo "❓ 문제가 발생하면:"
    echo "   - 로그 확인: tail -f .claude/logs/*.log"
    echo "   - 상태 확인: claude /status"
    echo "   - 도움말: claude --help"
    echo ""
}

# 메인 실행 함수
main() {
    echo "=================================================="
    echo "  에이전틱 개발 파이프라인 설정"
    echo "=================================================="
    echo ""
    
    check_prerequisites
    echo ""
    
    setup_claude_code
    echo ""
    
    create_env_file
    echo ""
    
    create_directory_structure
    echo ""
    
    create_claude_config
    echo ""
    
    create_mcp_config
    echo ""
    
    create_commands
    echo ""
    
    create_docker_compose
    echo ""
    
    create_config_files
    echo ""
    
    set_permissions
    echo ""
    
    run_initial_test
    echo ""
    
    print_completion_guide
}

# 스크립트 실행
main "$@"
