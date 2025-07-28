# 에이전틱 개발 파이프라인 프로젝트 구조 v1.1

## 📁 전체 프로젝트 구조

```
agentic-dev-pipeline/
├── README.md                           # 프로젝트 개요 및 시작 가이드
├── CHANGELOG.md                        # 버전별 변경 기록
├── QUICKSTART.md                       # 5분 빠른 시작 가이드
├── PROJECT_STRUCTURE.md                # 프로젝트 구조 설명 (이 파일)
├── CLAUDE.md                           # Claude Code 설정 및 컨텍스트
├── LICENSE                             # MIT 라이선스
├── .env.example                        # 환경 변수 템플릿
├── .gitignore                          # Git 무시 파일 목록
├── package.json                        # Node.js 프로젝트 설정 (v1.1.0)
├── docker-compose.yml                  # 로컬 개발 환경 구성
│
├── 📁 .claude/                        # 🤖 Claude Code 전용 디렉토리
│   ├── .gitignore                     # Claude 전용 Git 설정
│   ├── mcp.json                       # MCP 서버 설정
│   └── 📁 commands/                   # Slash 명령어 (v1.1 신규)
│       ├── basic-development.md       # /basic-development
│       ├── data-pipeline.md           # /data-pipeline
│       ├── hotfix.md                  # /hotfix
│       ├── microservices-development.md # /microservices-development
│       ├── ml-ai-model.md             # /ml-ai-model
│       ├── mobile-app.md              # /mobile-app
│       ├── pipeline.md                # /pipeline
│       └── status.md                  # /status
│
├── 📁 src/                           # 🎯 소스 코드
│   └── 📁 agents/                    # 특화 AI 에이전트 (v1.1 신규)
│       ├── performance_optimization_agent.py  # 성능 최적화 에이전트
│       ├── security_audit_agent.py           # 보안 감사 에이전트
│       └── ui_ux_design_agent.py             # UI/UX 디자인 에이전트
│
├── 📁 docs/                          # 📚 프로젝트 문서
│   ├── 📁 architecture/              # 아키텍처 설계 문서
│   │   └── system-architecture.md    # 시스템 전체 아키텍처
│   │
│   ├── 📁 design/                    # 상세 설계 문서
│   │   ├── agent-design.md           # 에이전트 설계 명세
│   │   └── workflow-design.md        # 워크플로우 설계 명세
│   │
│   └── 📁 guides/                    # 사용자 가이드
│       ├── implementation.md         # 구현 가이드
│       ├── tool-integration.md       # 도구 통합 가이드
│       ├── troubleshooting.md        # 문제 해결 가이드
│       └── best-practices.md         # 베스트 프랙티스
│
├── 📁 configs/                       # ⚙️ 설정 파일
│   ├── pipeline.yaml                 # 파이프라인 기본 설정
│   ├── 📁 agents/                    # 에이전트별 설정
│   │   ├── performance-optimization-agent.yaml  # (v1.1 신규)
│   │   ├── security-audit-agent.yaml           # (v1.1 신규)
│   │   └── ui-ux-design-agent.yaml             # (v1.1 신규)
│   ├── 📁 tools/                     # 도구별 설정
│   └── 📁 environments/              # 환경별 설정
│
├── 📁 templates/                     # 📋 프로젝트 템플릿
│   ├── projects.yaml                 # 프로젝트 타입별 템플릿
│   └── 📁 projects/                  # 프로젝트 템플릿 파일
│       └── 📁 workflows/             # 워크플로우 템플릿
│
├── 📁 archived-workflows/            # 📦 아카이브된 워크플로우 (v1.1)
│   ├── README.md                     # 아카이브 설명
│   ├── basic-development.md          # 이전 버전 워크플로우들
│   ├── data-pipeline-development.md
│   ├── hotfix-pipeline.md
│   ├── microservices-development.md
│   ├── ml-ai-model-development.md
│   └── mobile-app-development.md
│
├── 📁 scripts/                       # 🔧 유틸리티 스크립트
│   ├── setup.sh                      # 초기 설정 스크립트
│   └── health-check.sh               # 프로젝트 건강 상태 확인 (v1.1 개선)
│
├── 📁 monitoring/                    # 📊 모니터링 구성
│   └── 📁 prometheus/
│       ├── prometheus.yml
│       └── alerts.yml
│
├── 📁 examples/                      # 💡 사용 예시
│   └── README.md
│
├── 📁 logs/                         # 📝 로그 디렉토리
└── 📁 tmp/                          # 🗑️ 임시 파일

```

## 🆕 v1.1 주요 변경사항

### 새로운 디렉토리
- **`.claude/commands/`**: Slash 명령어 워크플로우 (8개)
- **`src/agents/`**: 특화 AI 에이전트 구현 (3개)
- **`archived-workflows/`**: 이전 버전 워크플로우 백업

### 새로운 파일
- **`CHANGELOG.md`**: 버전별 변경 기록
- **`QUICKSTART.md`**: 5분 빠른 시작 가이드

### 업데이트된 파일
- **`README.md`**: v1.1 기능 반영, 빠른 참조 추가
- **`package.json`**: 버전 1.1.0, 새로운 스크립트
- **`scripts/health-check.sh`**: .env 자동 로드 기능

## 📋 주요 파일 설명

### 🤖 Claude 관련 파일
- **CLAUDE.md**: 프로젝트별 Claude Code 설정 및 컨텍스트
- **.claude/mcp.json**: MCP 서버 연동 설정
- **.claude/commands/*.md**: Slash 명령어 정의 (v1.1 방식)

### ⚙️ 설정 파일
- **pipeline.yaml**: 파이프라인 기본 구성
- **docker-compose.yml**: 로컬 개발 환경 (PostgreSQL, Redis, Prometheus 등)
- **.env**: 환경 변수 (ANTHROPIC_API_KEY, GITHUB_TOKEN 등)

### 🎯 특화 에이전트 (v1.1)
- **performance_optimization_agent.py**: 코드 프로파일링, DB 최적화, 캐싱
- **security_audit_agent.py**: OWASP 스캔, 취약점 수정, 컴플라이언스
- **ui_ux_design_agent.py**: 접근성 분석, 디자인 시스템 생성

## 🚀 시작하기 (v1.1 방식)

### 1. 초기 설정
```bash
# 프로젝트 클론
git clone <repository-url>
cd agentic-dev-pipeline

# 자동 설정 실행
./scripts/setup.sh
```

### 2. 환경 구성
```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에서 ANTHROPIC_API_KEY 설정

# 로컬 인프라 시작
docker-compose up -d
```

### 3. Claude Code 설정
```bash
# Claude Code 인증
claude auth login

# 건강 상태 확인
./scripts/health-check.sh
```

### 4. 워크플로우 실행 (v1.1 방식)
```bash
# 기본 개발 워크플로우
claude /basic-development "TODO 애플리케이션"

# 데이터 파이프라인
claude /data-pipeline "실시간 로그 분석"

# ML/AI 모델 개발
claude /ml-ai-model "고객 이탈 예측"

# 모바일 앱 개발
claude /mobile-app "피트니스 트래킹 앱"

# 마이크로서비스
claude /microservices-development "이커머스 백엔드"
```

## 🎯 사용 가능한 Slash 명령어

| 명령어 | 설명 | 완료 시간 |
|--------|------|-----------|
| `/basic-development` | 풀스택 웹 애플리케이션 개발 | 2-4시간 |
| `/data-pipeline` | 데이터 파이프라인 구축 | 2-3시간 |
| `/ml-ai-model` | ML/AI 모델 개발 및 배포 | 3-4시간 |
| `/mobile-app` | 크로스플랫폼 모바일 앱 | 3-4시간 |
| `/microservices-development` | 마이크로서비스 아키텍처 | 4-5시간 |
| `/hotfix` | 긴급 버그 수정 | 60분 이내 |
| `/pipeline` | 기본 파이프라인 실행 | 2-4시간 |
| `/status` | 프로젝트 상태 확인 | 즉시 |

## 🔧 커스터마이징

### 새로운 Slash 명령어 추가
```bash
# 새로운 명령어 생성
cat > .claude/commands/my-workflow.md << 'EOF'
# 나만의 워크플로우

다음 작업을 수행해줘: $ARGUMENTS

1. 요구사항 분석
2. 구현
3. 테스트
4. 배포
EOF

# 사용
claude /my-workflow "설명"
```

### 새로운 특화 에이전트 추가
```python
# src/agents/my_custom_agent.py 생성
class MyCustomAgent:
    def __init__(self):
        # 초기화
        pass
    
    async def execute(self, task):
        # 에이전트 로직
        pass
```

```yaml
# configs/agents/my-custom-agent.yaml 생성
agent:
  name: "My Custom Agent"
  capabilities:
    - custom_task_1
    - custom_task_2
```

## 📊 프로젝트 통계

- **Slash 명령어**: 8개
- **특화 AI 에이전트**: 3개
- **지원 워크플로우**: 7개
- **Docker 서비스**: 9개
- **지원 언어**: Python, JavaScript, Go, Java

## 🔄 마이그레이션 가이드

### v1.0 → v1.1
1. **워크플로우 실행 방식 변경**:
   ```bash
   # 이전 (v1.0)
   claude -f workflows/basic-development.md
   
   # 현재 (v1.1)
   claude /basic-development "요구사항"
   ```

2. **환경 변수 로드**:
   - `health-check.sh`가 이제 `.env` 파일을 자동으로 로드합니다

3. **새로운 에이전트 활용**:
   - 성능 최적화가 필요할 때: Performance Optimization Agent
   - 보안 감사가 필요할 때: Security Audit Agent
   - UI/UX 개선이 필요할 때: UI/UX Design Agent

이 프로젝트 구조는 확장 가능하고 유지보수 가능한 에이전틱 개발 환경을 제공합니다.