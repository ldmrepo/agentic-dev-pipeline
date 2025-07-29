# 🚀 빠른 시작 가이드

5분 안에 AI가 자동으로 애플리케이션을 개발하는 경험을 해보세요!

## 📋 전제 조건

- Python 3.11+
- Docker Desktop
- PostgreSQL 15+
- Redis 7+
- Git

## 🎯 1단계: 설치 (2분)

```bash
# 저장소 클론
git clone <repository-url>
cd agentic-dev-pipeline

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY 설정 (필수!)

# Docker 서비스 시작
docker-compose up -d

# 데이터베이스 초기화
alembic upgrade head
```

## 🔥 2단계: API 서버 실행 (1분)

```bash
# 개발 서버 실행
make run
# 또는
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## 🎉 3단계: 파이프라인 실행

### API를 통한 파이프라인 실행

```bash
# 파이프라인 생성
curl -X POST http://localhost:8000/api/v1/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Pipeline",
    "type": "basic_development",
    "config": {
      "task": "TODO 애플리케이션 개발",
      "requirements": "사용자 인증, CRUD 기능, 반응형 UI"
    }
  }'

# 파이프라인 상태 확인
curl http://localhost:8000/api/v1/pipelines/{pipeline_id}/status
```

### Python 클라이언트 사용

```python
from src.orchestration.engine import WorkflowEngine
from src.orchestration.state import WorkflowState

# 엔진 초기화
engine = WorkflowEngine()

# 파이프라인 실행
state = WorkflowState(
    task_type="development",
    requirements="TODO 애플리케이션 개발",
    config={"framework": "react", "backend": "fastapi"}
)

result = await engine.execute("main_workflow", state)
print(f"Pipeline completed: {result}")
```

## 📊 모니터링

### Prometheus + Grafana 시작
```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

모니터링 대시보드:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

## 🛠️ 유용한 명령어

```bash
# 테스트 실행
make test

# 테스트 커버리지
make test-cov

# 코드 포맷팅
make format

# 린트 검사
make lint

# Docker 정리
make docker-down

# 로그 확인
docker-compose logs -f app
```

## 💡 팁

1. **API 키 설정**: `.env` 파일에 `ANTHROPIC_API_KEY`를 반드시 설정하세요.

2. **설정 검증**: 서버 시작 시 자동으로 설정이 검증됩니다. 에러 메시지를 확인하세요.

3. **로깅**: JSON 형식의 구조화된 로그가 `logs/` 디렉토리에 저장됩니다.

## 🎓 다음 단계

- [시스템 아키텍처](docs/architecture/system-architecture.md) 이해하기
- [구현 가이드](docs/guides/implementation.md) 읽어보기
- [API 문서](http://localhost:8000/docs) 확인하기

## 🆘 도움이 필요하신가요?

- GitHub Issues: 버그 리포트 및 기능 요청
- Discord 커뮤니티: 실시간 도움말 (준비 중)
- 문서: [전체 문서](README.md)

---

**🎊 축하합니다!** 이제 AI가 당신을 위해 코드를 작성합니다. 창의적인 문제 해결에 집중하세요!