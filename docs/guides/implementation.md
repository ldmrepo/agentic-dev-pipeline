# 구현 가이드

## 🚀 프로젝트 시작하기

### 전제 조건
- Node.js 18+ 설치
- Claude Code CLI 설치 (`npm install -g @anthropic-ai/claude-code`)
- Docker 및 Docker Compose 설치
- Git 설치 및 설정
- Anthropic API 키 발급

### 초기 설정

#### 1. 환경 변수 설정
```bash
# 환경 변수 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here
DOCKER_REGISTRY=your_registry_url
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

#### 2. Claude Code 인증
```bash
# Claude Code 로그인
claude auth login

# 상태 확인
claude --version
claude /status
```

#### 3. 프로젝트 초기화
```bash
# 프로젝트 디렉토리 생성
mkdir my-agentic-project
cd my-agentic-project

# 에이전틱 파이프라인 초기화
claude -p "
새로운 에이전틱 개발 프로젝트를 초기화해줘:
1. 기본 폴더 구조 생성
2. CLAUDE.md 설정 파일 생성
3. 기본 워크플로우 템플릿 설정
4. MCP 서버 설정
"
```

## 📁 프로젝트 구조 설정

### 권장 폴더 구조
```
my-agentic-project/
├── .claude/                    # Claude Code 설정
│   ├── commands/              # 커스텀 명령어
│   ├── memory/                # 프로젝트 메모리
│   └── settings.json          # 로컬 설정
├── .mcp.json                  # MCP 서버 설정
├── CLAUDE.md                  # 프로젝트 컨텍스트
├── workflows/                 # 워크플로우 정의
│   ├── basic-development.yaml
│   ├── testing-pipeline.yaml
│   └── deployment-flow.yaml
├── configs/                   # 설정 파일
│   ├── agents/               # 에이전트별 설정
│   ├── tools/                # 도구별 설정
│   └── environments/         # 환경별 설정
├── src/                      # 소스 코드
├── tests/                    # 테스트 코드
├── docs/                     # 문서
├── docker-compose.yml        # 로컬 개발 환경
└── README.md                 # 프로젝트 설명
```

### CLAUDE.md 설정
```markdown
# 프로젝트: My Agentic Application

## 프로젝트 개요
- **목적**: 에이전틱 개발 파이프라인 데모 애플리케이션
- **아키텍처**: 마이크로서비스 (Node.js + React)
- **데이터베이스**: PostgreSQL + Redis
- **인프라**: Docker + Kubernetes

## 개발 가이드라인

### 코딩 스타일
- TypeScript 사용 (strict mode)
- ESLint + Prettier 적용
- Conventional Commits 준수
- 테스트 커버리지 85% 이상

### 브랜치 전략
- main: 프로덕션 브랜치
- develop: 개발 브랜치  
- feature/*: 기능 브랜치
- hotfix/*: 긴급 수정 브랜치

### 배포 전략
- Staging 환경 자동 배포
- Production 환경 수동 승인
- Blue-Green 배포 적용
- 롤백 계획 필수

## 명령어 목록
- `npm run dev`: 개발 서버 시작
- `npm run test`: 테스트 실행
- `npm run build`: 프로덕션 빌드
- `npm run lint`: 코드 검사
- `docker-compose up`: 로컬 인프라 시작

## 에이전트 설정
### Planning Agent
- 요구사항 분석 시 비즈니스 가치 우선 고려
- 기술적 부채 최소화 지향
- 확장성과 유지보수성 중시

### Development Agent  
- TDD 방법론 적용
- Clean Architecture 패턴 사용
- 보안 취약점 사전 방지

### Testing Agent
- 피라미드 테스트 전략 (70% Unit, 20% Integration, 10% E2E)
- 자동 테스트 생성 시 엣지 케이스 포함
- 성능 테스트 기준: 응답시간 < 200ms

### Deployment Agent
- 무중단 배포 보장
- 자동 롤백 조건: 에러율 > 1%
- 단계별 트래픽 증가: 5% → 25% → 50% → 100%
```

## 🔧 핵심 컴포넌트 구현

### 1. Pipeline Orchestrator 설정

#### .claude/commands/pipeline.md
```markdown
# 에이전틱 파이프라인 실행

다음 단계로 전체 개발 파이프라인을 실행해줘:

## 1. 계획 수립 단계
- 요구사항 분석: $REQUIREMENTS
- 아키텍처 설계 및 검토
- 개발 작업 분해 및 우선순위 설정
- 의존성 매핑 및 일정 추정

## 2. 병렬 개발 단계
### Backend 개발
- API 설계 및 구현
- 데이터베이스 스키마 설계
- 비즈니스 로직 구현
- 단위 테스트 작성

### Frontend 개발  
- UI 컴포넌트 개발
- 상태 관리 구현
- API 연동 구현
- E2E 테스트 작성

### Infrastructure 설정
- Docker 컨테이너화
- Kubernetes 매니페스트 작성
- CI/CD 파이프라인 구성
- 모니터링 설정

## 3. 품질 보장 단계
- 코드 품질 검사 (ESLint, SonarQube)
- 보안 취약점 스캔 (Snyk, OWASP ZAP)
- 성능 테스트 실행 (k6)
- 통합 테스트 검증

## 4. 배포 단계
- Staging 환경 배포
- Smoke 테스트 실행
- Production 환경 배포 준비
- 모니터링 및 알림 설정

각 단계 완료 시 진행 상황을 보고하고, 실패 시 자동 복구 또는 에스컬레이션해줘.
```

### 2. MCP 서버 설정

#### .mcp.json
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "args": ["--allowed-directory", "./"]
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    },
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-kubernetes"]
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
        "SLACK_APP_TOKEN": "${SLACK_APP_TOKEN}"
      }
    },
    "prometheus": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-prometheus"],
      "env": {
        "PROMETHEUS_URL": "http://localhost:9090"
      }
    }
  }
}
```

### 3. 워크플로우 템플릿 구현

#### workflows/basic-development.yaml
```yaml
name: "Basic Development Workflow"
version: "1.0"
description: "기본 개발 워크플로우"

variables:
  project_name: "${PROJECT_NAME}"
  tech_stack: "${TECH_STACK}"
  target_coverage: 85

stages:
  planning:
    agent: "planning_agent"
    timeout: "15m"
    
    tasks:
      - name: "analyze_requirements"
        claude_command: |
          다음 요구사항을 분석해줘:
          ${REQUIREMENTS}
          
          분석 결과:
          1. 기능적 요구사항 목록
          2. 비기능적 요구사항 정의  
          3. 제약사항 및 가정사항
          4. 우선순위 매트릭스
          
          결과를 requirements-analysis.md로 저장해줘.
      
      - name: "design_architecture"
        depends_on: ["analyze_requirements"]
        claude_command: |
          requirements-analysis.md를 기반으로 시스템 아키텍처를 설계해줘:
          1. 전체 시스템 구조도
          2. 컴포넌트 간 인터페이스
          3. 데이터 플로우
          4. 기술 스택 선정 근거
          
          결과를 architecture-design.md로 저장해줘.

  development:
    type: "parallel"
    depends_on: ["planning"]
    max_concurrency: 3
    
    jobs:
      backend:
        agent: "development_agent"
        claude_command: |
          architecture-design.md를 참고해서 백엔드 개발을 시작해줘:
          1. 프로젝트 구조 생성
          2. 데이터베이스 스키마 설계
          3. API 엔드포인트 구현
          4. 미들웨어 및 보안 설정
          5. 단위 테스트 작성 (커버리지 ${target_coverage}% 이상)
          
      frontend:
        agent: "development_agent"  
        claude_command: |
          architecture-design.md를 참고해서 프론트엔드 개발을 시작해줘:
          1. React 프로젝트 초기화
          2. 컴포넌트 구조 설계
          3. 상태 관리 설정 (Redux Toolkit)
          4. API 클라이언트 구현
          5. E2E 테스트 작성
          
      infrastructure:
        agent: "development_agent"
        claude_command: |
          애플리케이션 인프라를 구성해줘:
          1. Dockerfile 작성 (멀티스테이지 빌드)
          2. docker-compose.yml 설정
          3. Kubernetes 매니페스트 작성
          4. GitHub Actions 워크플로우 구성
          5. 모니터링 설정 (Prometheus + Grafana)

quality_gates:
  - name: "code_coverage"
    condition: "coverage >= ${target_coverage}"
    
  - name: "security_scan"
    condition: "vulnerabilities_high == 0"
    
  - name: "performance_baseline"
    condition: "response_time < 200ms"

on_failure:
  - action: "notify_slack"
    channel: "#dev-alerts"
    
  - action: "create_github_issue"
    labels: ["bug", "pipeline-failure"]
    
  - action: "rollback"
    condition: "stage == 'deployment'"
```

## 🛡️ 보안 및 권한 관리

### 권한 설정
```bash
# Claude Code 허용 도구 설정
claude /allowed-tools

# 추가할 도구들:
# - Bash commands: git, npm, docker, kubectl
# - File operations: read, write, create, delete
# - Network operations: HTTP requests to specific domains
```

### 보안 정책 설정
```json
{
  "security_policies": {
    "file_access": {
      "allowed_paths": ["./src", "./tests", "./docs"],
      "forbidden_paths": [".env", "secrets/", "*.key"]
    },
    "network_access": {
      "allowed_domains": ["api.github.com", "registry.npmjs.org"],
      "forbidden_ips": ["169.254.169.254"]
    },
    "command_execution": {
      "allowed_commands": ["git", "npm", "docker", "kubectl", "terraform"],
      "forbidden_commands": ["rm -rf", "dd", "mkfs"]
    }
  }
}
```

## 📊 모니터링 설정

### 메트릭 수집 설정
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./configs/grafana:/etc/grafana/provisioning
      
  agent-exporter:
    build: ./monitoring/agent-exporter
    ports:
      - "8080:8080"
    environment:
      - PIPELINE_METRICS_PORT=8080
```

### 알림 설정
```yaml
# configs/alertmanager.yml
global:
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - channel: '#dev-alerts'
    title: 'Agentic Pipeline Alert'
    text: 'Alert: {{ .GroupLabels.alertname }}'
```

## 🔄 실행 및 테스트

### 기본 파이프라인 실행
```bash
# 기본 개발 워크플로우 실행
claude /pipeline

# 또는 특정 워크플로우 실행
claude -f workflows/basic-development.yaml
```

### 핫픽스 파이프라인 실행
```bash
# 긴급 수정 워크플로우
claude -p "
긴급 버그 수정 파이프라인을 실행해줘:
1. 현재 이슈 분석: ${ISSUE_DESCRIPTION}
2. 최소한의 수정으로 문제 해결
3. 타겟 테스트 실행
4. 스테이징 배포 및 검증
5. 프로덕션 배포 준비

전체 과정을 80분 내에 완료해줘.
"
```

### 테스트 시나리오
```bash
# 1. 단순 기능 개발 테스트
claude -p "간단한 REST API (사용자 CRUD) 개발해줘"

# 2. 복잡한 기능 개발 테스트  
claude -p "실시간 채팅 기능이 있는 웹 애플리케이션 개발해줘"

# 3. 마이크로서비스 개발 테스트
claude -p "사용자, 주문, 결제 마이크로서비스로 구성된 이커머스 시스템 개발해줘"
```

## 🎯 최적화 및 튜닝

### 성능 최적화
```bash
# 파이프라인 성능 분석
claude -p "
지난 7일간의 파이프라인 실행 데이터를 분석해서:
1. 병목 구간 식별
2. 리소스 사용률 분석
3. 최적화 방안 제시
4. 자동 개선 스크립트 생성

분석 결과를 performance-analysis.md로 저장하고
개선 사항을 즉시 적용해줘.
"
```

### 비용 최적화
```bash
# 토큰 사용량 최적화
claude -p "
프롬프트 효율성을 분석해서:
1. 중복되는 요청 패턴 식별
2. 토큰 사용량이 많은 명령어 최적화
3. 캐싱 전략 적용
4. 배치 처리 방안 제시

최적화 결과를 적용하고 비용 절감 효과를 측정해줘.
"
```

## 🚨 문제 해결

### 일반적인 문제들

#### 1. Claude Code 연결 문제
```bash
# API 키 확인
echo $ANTHROPIC_API_KEY

# 연결 테스트
claude -p "Hello, Claude!"

# 로그 확인
claude --debug -p "test command"
```

#### 2. MCP 서버 연결 실패
```bash
# MCP 서버 상태 확인
claude mcp list

# 특정 서버 디버깅
claude --mcp-debug -p "GitHub 저장소 목록 가져와줘"

# 서버 재시작
claude mcp restart github
```

#### 3. 파이프라인 실행 실패
```bash
# 실행 로그 확인
tail -f ~/.claude/logs/pipeline.log

# 상태 복구
claude -p "마지막 성공한 체크포인트부터 파이프라인 재시작해줘"
```

### 디버깅 모드 활성화
```bash
# 상세 로깅 활성화
export CLAUDE_DEBUG=true
export CLAUDE_LOG_LEVEL=debug

# 특정 에이전트 디버깅
claude --debug-agent=development_agent -p "백엔드 개발 시작해줘"
```

## 📈 고급 기능

### 커스텀 에이전트 개발
```bash
# 새로운 전문 에이전트 생성
claude -p "
데이터 분석 전문 에이전트를 생성해줘:
1. 에이전트 역할 및 책임 정의
2. 필요한 스킬 및 도구 목록
3. 다른 에이전트와의 협업 인터페이스
4. 품질 메트릭 및 성공 기준

configs/agents/data-analyst-agent.yaml로 저장해줘.
"
```

### 워크플로우 템플릿 생성
```bash
# 도메인별 워크플로우 템플릿 생성
claude -p "
금융 서비스 개발을 위한 전용 워크플로우 템플릿을 생성해줘:
1. 규제 준수 검증 단계 추가
2. 보안 강화 테스트 포함
3. 성능 및 확장성 검증
4. 감사 추적 기능

workflows/fintech-development.yaml로 저장해줘.
"
```

이 구현 가이드를 따라하면 완전히 동작하는 에이전틱 개발 파이프라인을 구축할 수 있습니다.
