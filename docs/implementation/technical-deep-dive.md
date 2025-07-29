# 기술 심화 분석: Claude Code & LangGraph

## 📚 목차
1. [Claude Code 기술 세부사항](#claude-code-기술-세부사항)
2. [LangGraph 기술 세부사항](#langgraph-기술-세부사항)
3. [통합 아키텍처 심화](#통합-아키텍처-심화)
4. [구현 시 주의사항](#구현-시-주의사항)

## Claude Code 기술 세부사항

### 1. 핵심 아키텍처

#### 설치 및 요구사항
```bash
# Node.js 18+ 필수
npm install -g @anthropic-ai/claude-code

# 프로젝트에서 실행
cd your-project
claude
```

#### 주요 특징
- **터미널 기반**: GUI 없이 CLI 환경에서 직접 작동
- **파일 편집 권한**: 프로젝트 파일 직접 수정 가능
- **명령 실행**: 시스템 명령어 실행 권한
- **Git 통합**: 커밋 생성 및 버전 관리
- **Unix 철학**: 파이프라인 가능, 스크립트화 가능

### 2. MCP (Model Context Protocol) 통합

#### MCP 서버 타입
```javascript
// MCP 서버 설정 예시
{
  "mcpServers": {
    // 파일시스템 접근
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {}
    },
    // GitHub 통합
    "github": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    // 커스텀 서버
    "custom-tools": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "API_KEY": "${CUSTOM_API_KEY}"
      }
    }
  }
}
```

#### MCP 통신 프로토콜
- **stdio**: 표준 입출력 (기본)
- **WebSockets**: 실시간 양방향 통신
- **HTTP SSE**: 서버 전송 이벤트 (레거시)
- **Streamable HTTP**: 서버리스 최적화 (2025 신규)

### 3. 배포 옵션

```python
# 다양한 배포 환경 지원
deployment_options = {
    "anthropic_api": {
        "endpoint": "https://api.anthropic.com",
        "auth": "API_KEY"
    },
    "amazon_bedrock": {
        "region": "us-east-1",
        "model_id": "anthropic.claude-v3"
    },
    "google_vertex": {
        "project_id": "your-project",
        "location": "us-central1"
    },
    "corporate_proxy": {
        "proxy_url": "http://corp-proxy:8080",
        "auth_method": "NTLM"
    }
}
```

## LangGraph 기술 세부사항

### 1. 그래프 구성 요소

#### State 정의
```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
import operator

# 다양한 State 정의 방법
# 1. TypedDict 사용
class WorkflowState(TypedDict):
    messages: Annotated[List[Message], add_messages]  # 내장 리듀서
    current_task: str
    results: Annotated[dict, operator.or_]  # 커스텀 리듀서
    
# 2. Pydantic 모델 사용
from pydantic import BaseModel

class PydanticState(BaseModel):
    messages: List[Message]
    metadata: dict
    
# 3. Dataclass 사용
from dataclasses import dataclass

@dataclass
class DataclassState:
    messages: List[Message]
    context: dict
```

#### Node 구현
```python
# 동기 노드
def planning_node(state: WorkflowState, config: RunnableConfig) -> dict:
    """동기 노드 함수"""
    # 상태 읽기
    current_task = state["current_task"]
    
    # 처리 로직
    result = process_task(current_task)
    
    # 부분 상태 업데이트 반환
    return {
        "results": result,
        "messages": [AIMessage(content=f"Completed: {current_task}")]
    }

# 비동기 노드
async def async_development_node(
    state: WorkflowState, 
    config: RunnableConfig,
    runtime: Runtime
) -> dict:
    """비동기 노드 함수"""
    # Runtime 객체 활용
    store = runtime.store
    stream_writer = runtime.stream_writer
    
    # 비동기 처리
    result = await generate_code_async(state["requirements"])
    
    # 스트리밍 출력
    await stream_writer.write({"progress": "Code generation complete"})
    
    return {"generated_code": result}
```

#### Edge 정의
```python
from langgraph.graph import StateGraph, END

# 조건부 엣지
def route_by_task_type(state: WorkflowState) -> str:
    """태스크 타입에 따른 라우팅"""
    task_type = state.get("task_type")
    
    if task_type == "hotfix":
        return "fast_track"
    elif task_type == "feature":
        return "full_pipeline"
    else:
        return "planning"

# 그래프 구성
graph = StateGraph(WorkflowState)

# 노드 추가
graph.add_node("analyze", analyze_node)
graph.add_node("planning", planning_node)
graph.add_node("development", async_development_node)

# 엣지 추가
graph.add_edge("analyze", "planning")  # 고정 엣지
graph.add_conditional_edges(
    "planning",
    route_by_task_type,
    {
        "fast_track": "hotfix_node",
        "full_pipeline": "development",
        "planning": "detailed_planning"
    }
)
```

### 2. 실행 모델

#### 메시지 패싱 아키텍처
```python
# Pregel 기반 Super-step 실행
"""
Super-step 1: [analyze_node]
Super-step 2: [planning_node]
Super-step 3: [development_node, testing_node]  # 병렬 실행
Super-step 4: [deployment_node]
"""

# 병렬 실행을 위한 Send API
from langgraph.graph import Send

def orchestrator_node(state: WorkflowState) -> list[Send]:
    """오케스트레이터 노드 - 동적 워커 생성"""
    tasks = state["tasks"]
    
    # 각 태스크에 대해 워커 노드 생성
    return [
        Send("worker", {"task": task, "id": i}) 
        for i, task in enumerate(tasks)
    ]
```

#### 비동기 실행
```python
# 비동기 그래프 실행
from langgraph.graph import CompiledGraph

compiled_graph: CompiledGraph = graph.compile()

# 단일 입력 비동기 실행
result = await compiled_graph.ainvoke({
    "messages": [HumanMessage(content="Build a TODO app")],
    "task_type": "feature"
})

# 스트리밍 실행
async for chunk in compiled_graph.astream({
    "messages": [HumanMessage(content="Build a TODO app")]
}):
    print(f"Progress: {chunk}")

# 배치 실행
results = await compiled_graph.abatch([
    {"task": "task1"},
    {"task": "task2"},
    {"task": "task3"}
])
```

### 3. 상태 관리 및 지속성

#### Checkpointer 사용
```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver

# PostgreSQL 체크포인터
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/langgraph"
)

# 메모리 체크포인터 (개발용)
memory_checkpointer = MemorySaver()

# 체크포인터와 함께 컴파일
graph = graph.compile(checkpointer=checkpointer)

# 상태 저장과 함께 실행
config = {"configurable": {"thread_id": "user-123"}}
result = await graph.ainvoke(input_data, config=config)

# 상태 복원
state = await graph.aget_state(config)
print(f"Current state: {state.values}")

# 상태 히스토리
async for state in graph.aget_state_history(config):
    print(f"Historical state: {state}")
```

#### 상태 마이그레이션
```python
# 그래프 정의 변경 시 마이그레이션
# 1. 완료된 스레드: 전체 토폴로지 변경 가능
# 2. 중단된 스레드: 노드 이름 변경/제거 제외하고 모두 가능

# 마이그레이션 예시
def migrate_state(old_state: dict) -> dict:
    """이전 상태를 새 형식으로 마이그레이션"""
    new_state = {
        "messages": old_state.get("messages", []),
        "new_field": "default_value",  # 새 필드 추가
        # old_field 제거
    }
    return new_state
```

## 통합 아키텍처 심화

### 1. Claude Code + LangGraph 통합 패턴

```python
# MCP 서버로 LangGraph 노출
class LangGraphMCPServer:
    def __init__(self, graph: CompiledGraph):
        self.graph = graph
        
    async def handle_request(self, request: dict) -> dict:
        """MCP 요청 처리"""
        command = request["command"]
        
        if command == "execute_workflow":
            result = await self.graph.ainvoke(request["params"])
            return {"status": "success", "result": result}
            
        elif command == "get_state":
            state = await self.graph.aget_state(request["config"])
            return {"state": state.values}
```

### 2. 에러 처리 및 복구

```python
from langgraph.errors import GraphRecursionError
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientAgent:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def execute_with_retry(self, state: dict):
        """재시도 로직이 포함된 실행"""
        try:
            result = await self.graph.ainvoke(state)
            return result
        except GraphRecursionError:
            # 무한 루프 감지
            return {"error": "Recursion limit reached"}
        except Exception as e:
            # 상태 체크포인트로 롤백
            await self.rollback_to_checkpoint()
            raise
```

### 3. 성능 최적화

```python
# 노드 캐싱 설정
from langgraph.cache import NodeCache

cache = NodeCache(
    ttl=3600,  # 1시간 캐시
    max_size=1000  # 최대 1000개 항목
)

# 노드에 캐싱 적용
@cache.cached(key_func=lambda state: state["task_id"])
async def expensive_analysis_node(state: WorkflowState):
    """비용이 높은 분석 작업"""
    # 캐시된 결과가 있으면 즉시 반환
    result = await perform_expensive_analysis(state)
    return {"analysis_result": result}

# 병렬 처리 최적화
from concurrent.futures import ThreadPoolExecutor
import asyncio

async def parallel_processing_node(state: WorkflowState):
    """CPU 집약적 작업의 병렬 처리"""
    executor = ThreadPoolExecutor(max_workers=4)
    
    tasks = state["tasks"]
    loop = asyncio.get_event_loop()
    
    # CPU 바운드 작업을 스레드 풀에서 실행
    futures = [
        loop.run_in_executor(executor, process_task, task)
        for task in tasks
    ]
    
    results = await asyncio.gather(*futures)
    return {"processed_results": results}
```

## 구현 시 주의사항

### 1. Claude Code 관련

#### API 한계
- **토큰 제한**: 요청당 최대 200K 토큰
- **실행 시간**: 최대 실행 시간 제한 존재
- **파일 크기**: 대용량 파일 처리 시 청크 분할 필요

#### 보안 고려사항
```python
# MCP 서버 보안 설정
security_config = {
    "allowed_commands": ["read", "write", "execute"],
    "forbidden_paths": ["/etc", "/sys", "/proc"],
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "timeout": 300  # 5분
}
```

### 2. LangGraph 관련

#### 상태 크기 관리
```python
# 큰 상태 처리 시 외부 저장소 활용
class LargeStateHandler:
    def __init__(self, s3_client):
        self.s3 = s3_client
        
    async def save_large_data(self, state: dict, key: str):
        """큰 데이터는 S3에 저장하고 참조만 유지"""
        if len(str(state[key])) > 1024 * 1024:  # 1MB 이상
            s3_key = f"large_data/{state['thread_id']}/{key}"
            await self.s3.put_object(
                Bucket="langgraph-data",
                Key=s3_key,
                Body=json.dumps(state[key])
            )
            state[key] = {"__ref": s3_key}
        return state
```

#### 무한 루프 방지
```python
# 재귀 제한 설정
graph = graph.compile(
    checkpointer=checkpointer,
    recursion_limit=50  # 최대 50번 반복
)

# 사이클 감지
def detect_cycles(graph: StateGraph):
    """그래프 정의 시 사이클 감지"""
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.edges.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
                
        rec_stack.remove(node)
        return False
```

### 3. 통합 시 고려사항

#### 버전 호환성
```python
# 버전 체크
REQUIRED_VERSIONS = {
    "langgraph": ">=0.1.0",
    "claude-code": ">=1.0.0",
    "langchain": ">=0.2.0"
}

def check_compatibility():
    """버전 호환성 검사"""
    import pkg_resources
    
    for package, version_spec in REQUIRED_VERSIONS.items():
        try:
            pkg_resources.require(f"{package}{version_spec}")
        except pkg_resources.DistributionNotFound:
            raise ImportError(f"{package} not installed")
        except pkg_resources.VersionConflict as e:
            raise ImportError(f"Version conflict: {e}")
```

#### 리소스 관리
```python
# 리소스 정리
class ResourceManager:
    def __init__(self):
        self.resources = []
        
    def register(self, resource):
        self.resources.append(resource)
        
    async def cleanup(self):
        """모든 리소스 정리"""
        for resource in self.resources:
            if hasattr(resource, 'close'):
                await resource.close()
            elif hasattr(resource, 'cleanup'):
                await resource.cleanup()
                
# Context manager 패턴
from contextlib import asynccontextmanager

@asynccontextmanager
async def langgraph_session():
    """LangGraph 세션 관리"""
    graph = None
    try:
        graph = create_graph()
        yield graph
    finally:
        if graph:
            await graph.cleanup()
```

## 결론

Claude Code와 LangGraph는 각각:
- **Claude Code**: 터미널 기반 AI 코딩 어시스턴트로 MCP를 통한 도구 통합
- **LangGraph**: 상태 기반 그래프 워크플로우 엔진으로 복잡한 에이전트 시스템 구축

두 기술을 통합하면:
1. Claude Code가 사용자 인터페이스 역할
2. LangGraph가 백엔드 워크플로우 엔진 역할
3. MCP가 둘 사이의 통신 프로토콜 역할

이를 통해 강력하고 확장 가능한 AI 개발 파이프라인 구축이 가능합니다.