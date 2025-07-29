# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY configs/ ./configs/

# MCP 서버 설정 복사
COPY .claude/ ./.claude/

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV AGENTIC_ENV=production

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]