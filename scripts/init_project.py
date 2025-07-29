#!/usr/bin/env python3
"""
프로젝트 초기화 스크립트
Phase 1: 기반 인프라 구축을 위한 디렉토리 구조 생성
"""

import os
import subprocess
from pathlib import Path
import json

def create_project_structure():
    """프로젝트 디렉토리 구조 생성"""
    print("🏗️  Creating project directory structure...")
    
    base_dirs = [
        # API
        "src/api/routes",
        "src/api/middleware",
        
        # Core
        "src/core",
        
        # Orchestration
        "src/orchestration/graphs",
        "src/orchestration/nodes",
        
        # Agents
        "src/agents/planning",
        "src/agents/development",
        "src/agents/testing",
        "src/agents/deployment",
        "src/agents/monitoring",
        
        # Integrations
        "src/integrations/mcp",
        "src/integrations/tools",
        
        # Storage
        "src/storage",
        
        # Utils
        "src/utils",
        
        # Tests
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        
        # Scripts
        "scripts",
        
        # Docker
        "docker",
        
        # K8s
        "k8s",
        
        # Docs
        "docs/api",
        "docs/deployment",
        
        # Configs
        "configs",
        
        # MCP
        ".claude/commands",
        ".claude/servers"
    ]
    
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # __init__.py 생성 (src 디렉토리만)
        if dir_path.startswith("src/"):
            init_file = Path(dir_path) / "__init__.py"
            init_file.touch()
            print(f"  ✅ Created {dir_path}/")

def create_requirements_file():
    """requirements.txt 생성"""
    print("\n📦 Creating requirements.txt...")
    
    requirements = """# Core
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Cache
redis==5.0.1
hiredis==2.3.2

# Vector Store
chromadb==0.4.22

# AI/ML
langchain==0.1.0
langchain-anthropic==0.1.1
langgraph==0.0.26

# Monitoring
prometheus-client==0.19.0
sentry-sdk==1.39.2

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0

# Development
black==23.12.1
ruff==0.1.11
mypy==1.8.0
pre-commit==3.6.0

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==2.0.0"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements.strip())
    print("  ✅ requirements.txt created")

def create_pyproject_toml():
    """pyproject.toml 생성"""
    print("\n📋 Creating pyproject.toml...")
    
    pyproject = """[tool.poetry]
name = "agentic-dev-pipeline"
version = "1.0.0"
description = "AI Agent-powered Development Pipeline"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"

[tool.black]
line-length = 100
target-version = ['py311']
include = '\\.pyi?$'

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
pythonpath = ["."]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
    
    with open("pyproject.toml", "w") as f:
        f.write(pyproject.strip())
    print("  ✅ pyproject.toml created")

def create_env_example():
    """환경 변수 템플릿 생성"""
    print("\n🔐 Creating .env.example...")
    
    env_example = """# Application
APP_NAME="Agentic Development Pipeline"
APP_VERSION="1.0.0"
ENVIRONMENT=development
DEBUG=true

# API
API_V1_STR=/api/v1
API_KEY=your-api-key-here

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=agentic
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_DB=agentic_pipeline

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Claude API
ANTHROPIC_API_KEY=your-anthropic-api-key
CLAUDE_MODEL=claude-3-opus-20240229
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.1

# LangGraph
LANGGRAPH_RECURSION_LIMIT=50
LANGGRAPH_CHECKPOINT_TTL=86400

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Monitoring
SENTRY_DSN=
PROMETHEUS_PORT=8081

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# GitHub Integration
GITHUB_TOKEN=your-github-token
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repository-name

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json"""
    
    with open(".env.example", "w") as f:
        f.write(env_example.strip())
    print("  ✅ .env.example created")

def create_gitignore():
    """.gitignore 파일 생성"""
    print("\n📝 Creating .gitignore...")
    
    gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/

# Environment
.env
.env.local
.env.production
.env.staging

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Docker
.docker/

# Temporary
tmp/
temp/
.tmp/

# Build
dist/
build/
*.egg-info/

# Database
*.db
*.sqlite
*.sqlite3

# Claude Code
.claude/logs/
.claude/memory/
.claude/settings.local.json

# Monitoring data
prometheus_data/
grafana_data/
elasticsearch_data/"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore.strip())
    print("  ✅ .gitignore created")

def create_dockerfile():
    """Dockerfile 생성"""
    print("\n🐳 Creating Docker configuration...")
    
    dockerfile = """FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY configs/ ./configs/
COPY .claude/ ./.claude/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]"""
    
    with open("docker/Dockerfile", "w") as f:
        f.write(dockerfile.strip())
    print("  ✅ docker/Dockerfile created")

def create_docker_compose():
    """docker-compose.yml 생성"""
    docker_compose = """version: '3.9'

services:
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    container_name: agentic-postgres
    environment:
      POSTGRES_DB: agentic_pipeline
      POSTGRES_USER: agentic
      POSTGRES_PASSWORD: agentic123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentic"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: agentic-redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ChromaDB
  chromadb:
    image: chromadb/chroma:latest
    container_name: agentic-chromadb
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      IS_PERSISTENT: TRUE
      ANONYMIZED_TELEMETRY: FALSE

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: agentic-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: agentic-grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  chroma_data:
  prometheus_data:
  grafana_data:"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose.strip())
    print("  ✅ docker-compose.yml created")

def create_makefile():
    """Makefile 생성"""
    print("\n🔧 Creating Makefile...")
    
    makefile = """# Makefile for Agentic Development Pipeline

.PHONY: help install dev test lint format clean docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080

test: ## Run tests
	pytest tests/unit -v
	pytest tests/integration -v

lint: ## Run linting
	ruff check src tests
	mypy src

format: ## Format code
	black src tests
	ruff check --fix src tests

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage .mypy_cache

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

migrate: ## Run database migrations
	alembic upgrade head

seed: ## Seed database
	python scripts/seed.py"""
    
    with open("Makefile", "w") as f:
        f.write(makefile.strip())
    print("  ✅ Makefile created")

def create_alembic_ini():
    """alembic.ini 생성"""
    print("\n🗃️  Creating Alembic configuration...")
    
    alembic_ini = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; This defaults
# to alembic/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path.
# The path separator used here should be the separator specified by "version_path_separator" below.
# version_locations = %(here)s/bar:%(here)s/bat:alembic/versions

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# If this key is omitted entirely, it falls back to the legacy behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os  # Use os.pathsep.
# set to 'true' to search source files recursively
# in each "version_locations" directory
# new in Alembic version 1.10
# recursive_version_locations = false

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://agentic:agentic123@localhost/agentic_pipeline


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S"""
    
    with open("alembic.ini", "w") as f:
        f.write(alembic_ini.strip())
    print("  ✅ alembic.ini created")

def initialize_alembic():
    """Alembic 초기화"""
    print("\n🔄 Initializing Alembic...")
    
    # alembic 디렉토리 생성
    Path("alembic").mkdir(exist_ok=True)
    
    # env.py 생성
    env_py = '''"""Alembic Environment Configuration"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.models import Base
from src.core.config import get_settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    
    with open("alembic/env.py", "w") as f:
        f.write(env_py)
    
    # script.py.mako 생성
    script_mako = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
    
    with open("alembic/script.py.mako", "w") as f:
        f.write(script_mako)
    
    # versions 디렉토리 생성
    Path("alembic/versions").mkdir(exist_ok=True)
    
    print("  ✅ Alembic initialized")

def create_github_actions():
    """GitHub Actions 워크플로우 생성"""
    print("\n🚀 Creating GitHub Actions workflows...")
    
    Path(".github/workflows").mkdir(parents=True, exist_ok=True)
    
    ci_workflow = """name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install ruff black mypy
    
    - name: Run Ruff
      run: ruff check src tests
    
    - name: Run Black
      run: black --check src tests
    
    - name: Run MyPy
      run: mypy src

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/test
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/unit -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml"""
    
    with open(".github/workflows/ci.yml", "w") as f:
        f.write(ci_workflow.strip())
    
    print("  ✅ .github/workflows/ci.yml created")

def setup_venv():
    """가상 환경 설정"""
    print("\n🐍 Setting up Python virtual environment...")
    
    if not Path("venv").exists():
        subprocess.run(["python3", "-m", "venv", "venv"])
        print("  ✅ Virtual environment created")
        print("  📌 Activate with: source venv/bin/activate")
    else:
        print("  ⚠️  Virtual environment already exists")

def create_mcp_config():
    """MCP 설정 파일 생성"""
    print("\n🤖 Creating MCP configuration...")
    
    mcp_config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "--allowed-directory", "."],
                "env": {}
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
                "args": ["-y", "@modelcontextprotocol/server-docker"],
                "env": {}
            }
        }
    }
    
    with open(".claude/mcp.json", "w") as f:
        json.dump(mcp_config, f, indent=2)
    
    print("  ✅ .claude/mcp.json created")

def main():
    """메인 실행 함수"""
    print("🚀 Initializing Agentic Development Pipeline Project")
    print("=" * 50)
    
    # 1. 디렉토리 구조 생성
    create_project_structure()
    
    # 2. 설정 파일 생성
    create_requirements_file()
    create_pyproject_toml()
    create_env_example()
    create_gitignore()
    
    # 3. Docker 설정
    create_dockerfile()
    create_docker_compose()
    
    # 4. 개발 도구 설정
    create_makefile()
    create_alembic_ini()
    initialize_alembic()
    
    # 5. CI/CD 설정
    create_github_actions()
    
    # 6. Python 환경 설정
    setup_venv()
    
    # 7. MCP 설정
    create_mcp_config()
    
    print("\n✨ Project initialization completed!")
    print("\n📋 Next steps:")
    print("  1. Copy .env.example to .env and configure")
    print("  2. Activate virtual environment: source venv/bin/activate")
    print("  3. Install dependencies: pip install -r requirements.txt")
    print("  4. Start Docker services: make docker-up")
    print("  5. Run migrations: make migrate")
    print("  6. Start development server: make dev")

if __name__ == "__main__":
    main()