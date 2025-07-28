# 문제 해결 가이드

## 🚨 일반적인 문제 및 해결책

### Claude Code 관련 문제

#### 1. 인증 및 연결 문제

**문제**: Claude Code 인증 실패
```bash
Error: Authentication failed. Please check your API key.
```

**해결책**:
```bash
# API 키 확인
echo $ANTHROPIC_API_KEY

# API 키가 없으면 설정
export ANTHROPIC_API_KEY="your_api_key_here"

# 또는 .env 파일에 추가
echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env

# Claude Code 재인증
claude auth logout
claude auth login
```

**문제**: Claude Code 설치 실패
```bash
npm ERR! Failed to install @anthropic-ai/claude-code
```

**해결책**:
```bash
# Node.js 버전 확인 (18+ 필요)
node --version

# npm 캐시 정리
npm cache clean --force

# 전역 설치 권한 확인
sudo npm install -g @anthropic-ai/claude-code

# 또는 npx 사용
npx @anthropic-ai/claude-code --version
```

#### 2. MCP 서버 연결 문제

**문제**: MCP 서버가 연결되지 않음
```bash
Error: MCP server 'github' failed to start
```

**해결책**:
```bash
# MCP 서버 상태 확인
claude mcp list

# 특정 서버 디버깅
claude --mcp-debug mcp list

# 서버 재시작
claude mcp restart github

# 설정 파일 확인
cat .mcp.json

# 환경 변수 확인
echo $GITHUB_TOKEN
```

**문제**: GitHub MCP 서버 권한 오류
```bash
Error: GitHub API returned 403 Forbidden
```

**해결책**:
```bash
# GitHub 토큰 권한 확인 (필요한 scopes)
# - repo
# - issues  
# - pull_requests
# - actions
# - contents

# 새 토큰 생성
# GitHub → Settings → Developer settings → Personal access tokens

# 토큰 테스트
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### 워크플로우 실행 문제

#### 3. 파이프라인 실행 실패

**문제**: 워크플로우 파일을 찾을 수 없음
```bash
Error: Could not find workflow file: workflows/basic-development.md
```

**해결책**:
```bash
# 현재 디렉토리 확인
pwd

# 파일 존재 확인
ls -la workflows/

# 절대 경로 사용
claude -f /full/path/to/workflows/basic-development.md

# 또는 올바른 디렉토리로 이동
cd /Users/ldm/work/workspace/agentic-dev-pipeline
claude -f workflows/basic-development.md
```

**문제**: 환경 변수 미설정으로 실행 실패
```bash
Error: REQUIREMENTS variable is not set
```

**해결책**:
```bash
# 필수 환경 변수 설정
export REQUIREMENTS="웹 애플리케이션 개발"
export PROJECT_NAME="my-app"

# 또는 .env 파일 사용
cp .env.example .env
# .env 파일 편집 후

# 환경 변수 로드
source .env

# 또는 inline으로 실행
REQUIREMENTS="블로그 시스템" claude -f workflows/basic-development.md
```

#### 4. 권한 및 파일 시스템 오류

**문제**: 파일 생성/수정 권한 없음
```bash
Error: Permission denied: Cannot write to file
```

**해결책**:
```bash
# 현재 디렉토리 권한 확인
ls -ld .

# 쓰기 권한 부여
chmod u+w .

# 소유자 변경 (필요시)
sudo chown $USER:$USER .

# 또는 권한이 있는 디렉토리로 이동
cd ~/projects/
mkdir my-new-project && cd my-new-project
```

**문제**: Docker 관련 오류
```bash
Error: Cannot connect to the Docker daemon
```

**해결책**:
```bash
# Docker 데몬 상태 확인
docker ps

# Docker Desktop 시작 (macOS/Windows)
# 또는 Linux에서 Docker 서비스 시작
sudo systemctl start docker

# Docker 권한 확인
sudo usermod -aG docker $USER
# 로그아웃 후 다시 로그인 필요

# Docker Compose 파일 확인
docker-compose config
```

### 성능 및 리소스 문제

#### 5. 토큰 사용량 과다

**문제**: API 비용이 예상보다 높음
```bash
Warning: High token usage detected
```

**해결책**:
```bash
# 비용 확인
claude /cost

# 토큰 사용량 모니터링
claude --track-tokens -f workflows/basic-development.md

# 프롬프트 최적화
# - 중복 요청 제거
# - 구체적이고 간결한 지시사항
# - 불필요한 컨텍스트 제거

# 비용 한도 설정
export ANTHROPIC_MAX_COST=50  # $50 한도
```

#### 6. 메모리 부족 오류

**문제**: 시스템 메모리 부족
```bash
Error: JavaScript heap out of memory
```

**해결책**:
```bash
# Node.js 메모리 한도 증가
export NODE_OPTIONS="--max-old-space-size=8192"

# 또는 워크플로우 분할 실행
claude -f workflows/planning-only.md
claude -f workflows/development-only.md
claude -f workflows/testing-only.md

# 시스템 메모리 확인
free -h  # Linux
vm_stat  # macOS
```

### 네트워크 및 연결 문제

#### 7. 외부 서비스 연결 실패

**문제**: GitHub API 연결 실패
```bash
Error: Request failed with status code 500
```

**해결책**:
```bash
# GitHub 상태 확인
curl -s https://www.githubstatus.com/api/v2/status.json

# 네트워크 연결 확인
ping api.github.com

# 프록시 설정 확인
echo $HTTP_PROXY
echo $HTTPS_PROXY

# DNS 확인
nslookup api.github.com

# 재시도 정책 적용
claude --retry-attempts=3 -f workflows/basic-development.md
```

**문제**: Docker Hub 연결 실패
```bash
Error: Failed to pull image
```

**해결책**:
```bash
# Docker Hub 상태 확인
curl -s https://status.docker.com/api/v2/status.json

# 레지스트리 로그인
docker login

# 대체 레지스트리 사용
# docker-compose.yml에서 이미지 변경
# postgres:15-alpine → registry.gitlab.com/postgres:15

# 로컬 이미지 빌드
docker build -t local/postgres:15 .
```

## 🔧 디버깅 모드

### 상세 로깅 활성화
```bash
# 디버그 모드 실행
claude --debug -f workflows/basic-development.md

# 특정 컴포넌트 디버깅
export DEBUG=claude:*
claude -f workflows/basic-development.md

# 로그 파일로 저장
claude -f workflows/basic-development.md > pipeline.log 2>&1
```

### 단계별 디버깅
```bash
# 단계별 실행 및 확인
claude -p "1단계만 실행: 요구사항 분석"
claude -p "현재 상태 확인"
claude -p "2단계 실행: 개발 시작"
```

### 상태 확인 명령어
```bash
# 전체 상태 확인
claude /status

# MCP 서버 상태
claude mcp list

# 허용된 도구 확인  
claude /allowed-tools

# 메모리 상태 확인
claude /memory

# 비용 확인
claude /cost
```

## 📞 지원 및 도움 요청

### 자체 해결 체크리스트
- [ ] 환경 변수 설정 확인
- [ ] 파일 권한 확인  
- [ ] 네트워크 연결 확인
- [ ] 디스크 공간 확인
- [ ] 메모리 사용량 확인
- [ ] 로그 파일 검토

### 로그 수집
```bash
# 종합 로그 수집 스크립트
cat > collect-logs.sh << 'EOF'
#!/bin/bash
echo "=== System Info ===" > debug-info.txt
uname -a >> debug-info.txt
node --version >> debug-info.txt
npm --version >> debug-info.txt
docker --version >> debug-info.txt

echo "=== Environment Variables ===" >> debug-info.txt
env | grep -E "(ANTHROPIC|GITHUB|CLAUDE)" >> debug-info.txt

echo "=== Claude Status ===" >> debug-info.txt
claude /status >> debug-info.txt 2>&1

echo "=== MCP Status ===" >> debug-info.txt  
claude mcp list >> debug-info.txt 2>&1

echo "=== Recent Logs ===" >> debug-info.txt
tail -n 100 ~/.claude/logs/*.log >> debug-info.txt 2>/dev/null

echo "Debug info collected in debug-info.txt"
EOF

chmod +x collect-logs.sh
./collect-logs.sh
```

### 커뮤니티 지원
- GitHub Issues: 프로젝트 저장소에 이슈 등록
- Discord/Slack: 커뮤니티 채널에서 질문
- Stack Overflow: `claude-code` 태그로 질문

### 공식 지원
- Anthropic 공식 문서: https://docs.anthropic.com
- Claude Code 문서: https://docs.anthropic.com/claude-code
- 지원 이메일: support@anthropic.com

## 🎯 예방 조치

### 정기 점검 스크립트
```bash
#!/bin/bash
# health-check.sh

echo "🏥 에이전틱 파이프라인 건강 검진"

# API 키 확인
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY 미설정"
else
    echo "✅ ANTHROPIC_API_KEY 설정됨"
fi

# Claude Code 버전 확인
if claude --version >/dev/null 2>&1; then
    echo "✅ Claude Code $(claude --version)"
else
    echo "❌ Claude Code 설치 필요"
fi

# MCP 서버 상태
if claude mcp list >/dev/null 2>&1; then
    echo "✅ MCP 서버 정상"
else
    echo "⚠️ MCP 서버 점검 필요"
fi

# 디스크 공간 확인
available=$(df . | awk 'NR==2 {print $4}')
if [ $available -lt 1048576 ]; then  # 1GB
    echo "⚠️ 디스크 공간 부족: $(($available/1024))MB 남음"
else
    echo "✅ 디스크 공간 충분"
fi

echo "건강 검진 완료!"
```

### 백업 전략
```bash
# 중요 설정 파일 백업
tar -czf backup-$(date +%Y%m%d).tar.gz \
    .env \
    .mcp.json \
    CLAUDE.md \
    workflows/ \
    configs/

# 클라우드 백업 (선택사항)
# aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://my-backup-bucket/
```

이 문제 해결 가이드를 참고하여 대부분의 이슈를 자체적으로 해결할 수 있습니다.
