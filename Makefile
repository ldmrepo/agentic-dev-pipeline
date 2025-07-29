# Agentic Development Pipeline Makefile

.PHONY: help install dev-install test lint format clean docker-build docker-up docker-down

# 기본 타겟
help:
	@echo "사용 가능한 명령어:"
	@echo "  make install       - 프로덕션 의존성 설치"
	@echo "  make dev-install   - 개발 의존성 포함 설치"
	@echo "  make test          - 테스트 실행"
	@echo "  make lint          - 코드 검사"
	@echo "  make format        - 코드 포맷팅"
	@echo "  make clean         - 캐시 및 빌드 파일 정리"
	@echo "  make docker-build  - Docker 이미지 빌드"
	@echo "  make docker-up     - Docker Compose 실행"
	@echo "  make docker-down   - Docker Compose 중지"

# 설치
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# 테스트
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/ -v -m unit

test-integration:
	pytest tests/ -v -m integration

# 코드 품질
lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	ruff check src/ tests/ --fix

# 정리
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage

# Docker
docker-build:
	docker build -t agentic-dev-pipeline:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

# 데이터베이스
db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head

# 개발 서버
run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 환경 설정
env-setup:
	cp .env.example .env
	@echo "환경 파일이 생성되었습니다. .env 파일을 편집하세요."