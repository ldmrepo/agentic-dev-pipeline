# 🚀 빠른 시작 가이드

5분 안에 AI가 자동으로 애플리케이션을 개발하는 경험을 해보세요!

## 📋 전제 조건

- Node.js 18+
- Docker Desktop
- Claude Code CLI (설치되어 있지 않다면 [여기](https://docs.anthropic.com/claude-code)에서 설치)

## 🎯 1단계: 설치 (1분)

```bash
# 저장소 클론
git clone <repository-url>
cd agentic-dev-pipeline

# 초기 설정
./scripts/setup.sh

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY 설정

# 명령어를 사용자 레벨로 설정 (한 번만)
mkdir -p ~/.claude/commands
cp .claude/commands/*.md ~/.claude/commands/
```

## 🔥 2단계: 첫 번째 앱 만들기 (3분)

### 프로젝트 디렉토리 생성
```bash
mkdir ~/projects/my-first-app
cd ~/projects/my-first-app
```

### 옵션 1: TODO 애플리케이션
```bash
claude /basic-development "사용자 인증이 있는 TODO 애플리케이션"
```

### 옵션 2: 실시간 채팅 앱
```bash
claude /basic-development "실시간 채팅 애플리케이션 (WebSocket 사용)"
```

### 옵션 3: 블로그 플랫폼
```bash
claude /basic-development "마크다운 지원 블로그 플랫폼"
```

## 🎉 3단계: 결과 확인 (1분)

AI가 생성한 파일들:
```
my-app/
├── frontend/        # React 애플리케이션
├── backend/         # Express API 서버
├── database/        # PostgreSQL 스키마
├── docker/          # 컨테이너 설정
├── tests/           # 자동 생성된 테스트
└── docs/            # API 문서
```

앱 실행:
```bash
cd my-app
docker-compose up -d
```

브라우저에서 확인:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API 문서: http://localhost:8080/docs

## 🎨 고급 워크플로우 체험

### 데이터 파이프라인 (실시간 분석)
```bash
claude /data-pipeline "웹사이트 클릭 스트림 실시간 분석 파이프라인"
```

### ML 모델 개발 (추천 시스템)
```bash
claude /ml-ai-model "콘텐츠 기반 영화 추천 시스템"
```

### 모바일 앱 (날씨 앱)
```bash
claude /mobile-app "위치 기반 날씨 예보 앱"
```

### 마이크로서비스 (이커머스)
```bash
claude /microservices-development "간단한 이커머스 백엔드 (상품, 주문, 결제)"
```

## 🛠️ 유용한 명령어

```bash
# 상태 확인
claude /status

# 프로젝트 건강 상태
./scripts/health-check.sh

# 로그 확인
npm run docker:logs

# 정리
npm run docker:clean
```

## 💡 팁

1. **요구사항을 구체적으로**: "사용자 인증이 있는" 같은 세부사항을 추가하면 더 완성도 높은 결과물이 생성됩니다.

2. **단계별 진행**: AI가 각 단계를 보고하므로 진행 상황을 실시간으로 확인할 수 있습니다.

3. **문제 발생 시**: `claude /status`로 현재 상태를 확인하고, 필요시 `npm run docker:logs`로 로그를 확인하세요.

## 🎓 다음 단계

- [고급 사용법](docs/guides/advanced-usage.md) 읽어보기
- [커스텀 에이전트 만들기](docs/guides/custom-agents.md)
- [프로덕션 배포 가이드](docs/guides/production-deployment.md)

## 🆘 도움이 필요하신가요?

- GitHub Issues: 버그 리포트 및 기능 요청
- Discord 커뮤니티: 실시간 도움말 (준비 중)
- 문서: [전체 문서](README.md)

---

**🎊 축하합니다!** 이제 AI가 당신을 위해 코드를 작성합니다. 창의적인 문제 해결에 집중하세요!