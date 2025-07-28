#!/bin/bash

# 에이전틱 파이프라인 건강 검진 스크립트
# Usage: ./scripts/health-check.sh

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "🏥 에이전틱 개발 파이프라인 건강 검진"
    echo "=================================================="
    echo ""
}

print_status() {
    echo -e "${BLUE}[검진]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌]${NC} $1"
}

# 시스템 기본 요구사항 확인
check_system_requirements() {
    print_status "시스템 요구사항 확인 중..."
    
    # Node.js 확인
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            print_success "Node.js $(node --version) - 버전 적합"
        else
            print_error "Node.js 버전 부적합: $(node --version) (18+ 필요)"
        fi
    else
        print_error "Node.js가 설치되지 않음"
    fi
    
    # npm 확인
    if command -v npm &> /dev/null; then
        print_success "npm $(npm --version) - 설치됨"
    else
        print_error "npm이 설치되지 않음"
    fi
    
    # Git 확인
    if command -v git &> /dev/null; then
        print_success "Git $(git --version | cut -d' ' -f3) - 설치됨"
    else
        print_error "Git이 설치되지 않음"
    fi
    
    # Docker 확인
    if command -v docker &> /dev/null; then
        if docker ps &> /dev/null; then
            print_success "Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1) - 실행 중"
        else
            print_warning "Docker가 설치되어 있지만 실행되지 않음"
        fi
    else
        print_warning "Docker가 설치되지 않음 (일부 기능 제한)"
    fi
}

# Claude Code 상태 확인
check_claude_code() {
    print_status "Claude Code 상태 확인 중..."
    
    # Claude Code 설치 확인
    if command -v claude &> /dev/null; then
        print_success "Claude Code $(claude --version 2>/dev/null || echo 'unknown') - 설치됨"
        
        # 인증 상태 확인
        if claude /status &> /dev/null; then
            print_success "Claude Code 인증 - 정상"
        else
            print_warning "Claude Code 인증 필요 (claude auth login 실행)"
        fi
    else
        print_error "Claude Code가 설치되지 않음"
    fi
}

# 환경 변수 확인
check_environment_variables() {
    print_status "환경 변수 확인 중..."
    
    # .env 파일이 있으면 로드
    if [ -f ".env" ]; then
        # .env 파일에서 환경 변수 로드
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
        print_success ".env 파일 - 로드됨"
    else
        print_warning ".env 파일이 없음 (.env.example 참조)"
    fi
    
    # 필수 환경 변수 확인
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        print_success "ANTHROPIC_API_KEY - 설정됨"
    else
        print_warning "ANTHROPIC_API_KEY - 미설정"
    fi
    
    # 선택적 환경 변수 확인
    if [ -n "$GITHUB_TOKEN" ]; then
        print_success "GITHUB_TOKEN - 설정됨"
    else
        print_warning "GITHUB_TOKEN - 미설정 (GitHub 통합 제한)"
    fi
}

# MCP 서버 상태 확인
check_mcp_servers() {
    print_status "MCP 서버 상태 확인 중..."
    
    if command -v claude &> /dev/null; then
        # .mcp.json 파일 확인
        if [ -f ".mcp.json" ]; then
            print_success ".mcp.json 설정 파일 - 존재함"
            
            # MCP 서버 목록 확인
            if claude mcp list &> /dev/null; then
                SERVER_COUNT=$(claude mcp list 2>/dev/null | grep -c "name:" || echo "0")
                print_success "MCP 서버 - $SERVER_COUNT개 설정됨"
            else
                print_warning "MCP 서버 상태 확인 실패"
            fi
        else
            print_warning ".mcp.json 파일이 없음"
        fi
    else
        print_warning "Claude Code 미설치로 MCP 확인 불가"
    fi
}

# 프로젝트 구조 확인
check_project_structure() {
    print_status "프로젝트 구조 확인 중..."
    
    # 필수 디렉토리 확인
    required_dirs=("docs" "configs" "workflows" "scripts" "templates")
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "$dir/ 디렉토리 - 존재함"
        else
            print_warning "$dir/ 디렉토리 - 없음"
        fi
    done
    
    # 핵심 파일 확인
    required_files=("README.md" "CLAUDE.md" "package.json")
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file - 존재함"
        else
            print_warning "$file - 없음"
        fi
    done
    
    # 워크플로우 파일 확인
    if [ -f "workflows/basic-development.md" ]; then
        print_success "기본 워크플로우 - 존재함"
    else
        print_error "기본 워크플로우 파일이 없음"
    fi
}

# 디스크 공간 확인
check_system_resources() {
    print_status "시스템 리소스 확인 중..."
    
    # 디스크 공간 확인 (리눅스/맥OS)
    if command -v df &> /dev/null; then
        available_kb=$(df . | awk 'NR==2 {print $4}')
        available_gb=$((available_kb / 1024 / 1024))
        
        if [ $available_gb -gt 5 ]; then
            print_success "디스크 공간 - ${available_gb}GB 사용 가능"
        elif [ $available_gb -gt 1 ]; then
            print_warning "디스크 공간 - ${available_gb}GB 사용 가능 (부족할 수 있음)"
        else
            print_error "디스크 공간 부족 - ${available_gb}GB 사용 가능"
        fi
    fi
    
    # 메모리 확인 (가능한 경우)
    if command -v free &> /dev/null; then
        # Linux
        available_mem=$(free -g | awk 'NR==2{print $7}')
        if [ $available_mem -gt 4 ]; then
            print_success "메모리 - ${available_mem}GB 사용 가능"
        else
            print_warning "메모리 - ${available_mem}GB 사용 가능 (부족할 수 있음)"
        fi
    elif command -v vm_stat &> /dev/null; then
        # macOS - 간단한 확인
        print_success "메모리 상태 - 확인됨 (macOS)"
    fi
}

# 네트워크 연결 확인
check_network_connectivity() {
    print_status "네트워크 연결 확인 중..."
    
    # 필수 서비스 연결 확인
    services=("api.anthropic.com" "api.github.com" "registry.npmjs.org")
    
    for service in "${services[@]}"; do
        if ping -c 1 "$service" &> /dev/null; then
            print_success "$service - 연결 가능"
        else
            print_warning "$service - 연결 실패"
        fi
    done
}

# Docker 환경 확인
check_docker_environment() {
    if command -v docker &> /dev/null && docker ps &> /dev/null; then
        print_status "Docker 환경 확인 중..."
        
        # Docker Compose 파일 확인
        if [ -f "docker-compose.yml" ]; then
            print_success "docker-compose.yml - 존재함"
            
            # Docker Compose 설정 검증
            if docker-compose config &> /dev/null; then
                print_success "Docker Compose 설정 - 유효함"
            else
                print_warning "Docker Compose 설정 - 오류 있음"
            fi
        else
            print_warning "docker-compose.yml - 없음"
        fi
        
        # 실행 중인 컨테이너 확인
        running_containers=$(docker ps --format "table {{.Names}}" | tail -n +2 | wc -l)
        print_success "실행 중인 컨테이너 - ${running_containers}개"
    fi
}

# 권한 확인
check_permissions() {
    print_status "파일 권한 확인 중..."
    
    # 스크립트 실행 권한 확인
    if [ -x "scripts/setup.sh" ]; then
        print_success "setup.sh - 실행 권한 있음"
    else
        print_warning "setup.sh - 실행 권한 없음"
    fi
    
    # 쓰기 권한 확인
    if [ -w "." ]; then
        print_success "현재 디렉토리 - 쓰기 권한 있음"
    else
        print_error "현재 디렉토리 - 쓰기 권한 없음"
    fi
}

# 종합 점수 계산 및 권장사항
generate_recommendations() {
    echo ""
    echo "📋 건강 검진 완료"
    echo "=================================================="
    echo ""
    
    echo "🎯 권장사항:"
    echo ""
    
    # Claude Code 관련
    if ! command -v claude &> /dev/null; then
        echo "1. Claude Code 설치:"
        echo "   npm install -g @anthropic-ai/claude-code"
        echo ""
    fi
    
    # 환경 변수 관련
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "2. API 키 설정:"
        echo "   cp .env.example .env"
        echo "   # .env 파일에서 ANTHROPIC_API_KEY 설정"
        echo ""
    fi
    
    # MCP 서버 관련
    if [ ! -f ".mcp.json" ]; then
        echo "3. MCP 서버 설정:"
        echo "   # .mcp.json 파일 생성 및 GitHub 토큰 설정"
        echo ""
    fi
    
    # Docker 관련
    if ! command -v docker &> /dev/null || ! docker ps &> /dev/null; then
        echo "4. Docker 환경 설정:"
        echo "   # Docker Desktop 설치 및 실행"
        echo "   docker-compose up -d"
        echo ""
    fi
    
    echo "🚀 다음 단계:"
    echo "1. 권장사항 적용"
    echo "2. claude /status 로 전체 상태 재확인"
    echo "3. 첫 번째 파이프라인 실행:"
    echo "   claude -f workflows/basic-development.md"
    echo ""
}

# 메인 실행
main() {
    print_header
    
    check_system_requirements
    echo ""
    
    check_claude_code
    echo ""
    
    check_environment_variables
    echo ""
    
    check_mcp_servers
    echo ""
    
    check_project_structure
    echo ""
    
    check_system_resources
    echo ""
    
    check_network_connectivity
    echo ""
    
    check_docker_environment
    echo ""
    
    check_permissions
    echo ""
    
    generate_recommendations
}

# 스크립트 실행
main "$@"
