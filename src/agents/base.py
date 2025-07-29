"""
베이스 에이전트 클래스
모든 AI 에이전트의 기본 클래스
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime
from functools import wraps
import asyncio

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import Tool, StructuredTool
from langchain_core.utils.function_calling import convert_to_openai_function
from pydantic import BaseModel, Field

from src.integrations.claude import get_claude_client, ClaudeClient
from src.integrations.mcp.tools import MCPTools
from src.core.config import get_settings
from src.core.exceptions import AgentError, AgentExecutionError

logger = logging.getLogger(__name__)
settings = get_settings()

class AgentContext(BaseModel):
    """에이전트 실행 컨텍스트"""
    pipeline_id: str = Field(description="파이프라인 ID")
    task_id: str = Field(description="태스크 ID")
    requirements: str = Field(description="요구사항")
    constraints: List[str] = Field(default_factory=list, description="제약사항")
    previous_results: Dict[str, Any] = Field(default_factory=dict, description="이전 단계 결과")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

class AgentResult(BaseModel):
    """에이전트 실행 결과"""
    success: bool = Field(description="성공 여부")
    output: Any = Field(description="출력 데이터")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="생성된 아티팩트")
    messages: List[str] = Field(default_factory=list, description="실행 메시지")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="실행 메트릭")
    errors: List[str] = Field(default_factory=list, description="에러 메시지")

def track_agent_execution(agent_name: str):
    """에이전트 실행 추적 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()
            
            logger.info(f"[{agent_name}] Starting execution")
            
            try:
                result = await func(self, *args, **kwargs)
                
                execution_time = time.time() - start_time
                logger.info(f"[{agent_name}] Execution completed in {execution_time:.2f}s")
                
                # 메트릭 업데이트
                if isinstance(result, AgentResult):
                    result.metrics["execution_time"] = execution_time
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"[{agent_name}] Execution failed after {execution_time:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

class BaseAgent(ABC):
    """모든 AI 에이전트의 베이스 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agents.{name}")
        
        # Claude 클라이언트 (지연 초기화)
        self._claude_client: Optional[ClaudeClient] = None
        
        # 도구 초기화
        self.tools = self._initialize_tools()
        
        # 프롬프트 템플릿
        self.prompt = self._create_prompt_template()
        
        # 에이전트 실행기 (지연 초기화)
        self._agent_executor: Optional[AgentExecutor] = None
        
        # 실행 히스토리
        self.execution_history: List[Dict[str, Any]] = []
        
        # 토큰 사용량
        self.token_usage = {
            "input": 0,
            "output": 0,
            "total": 0
        }
    
    async def _get_claude_client(self) -> ClaudeClient:
        """Claude 클라이언트 지연 초기화"""
        if self._claude_client is None:
            self._claude_client = await get_claude_client()
        return self._claude_client
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의 (서브클래스에서 구현)"""
        pass
    
    @abstractmethod
    def _get_specialized_tools(self) -> List[Tool]:
        """에이전트 전문 도구 정의 (서브클래스에서 구현)"""
        pass
    
    def _get_common_tools(self) -> List[Tool]:
        """공통 도구 세트"""
        return MCPTools.get_common_tools()
    
    def _initialize_tools(self) -> List[Tool]:
        """도구 초기화"""
        common_tools = self._get_common_tools()
        specialized_tools = self._get_specialized_tools()
        
        # 중복 제거
        tool_names = set()
        unique_tools = []
        
        for tool in common_tools + specialized_tools:
            if tool.name not in tool_names:
                tool_names.add(tool.name)
                unique_tools.append(tool)
        
        self.logger.info(f"Initialized {len(unique_tools)} tools: {tool_names}")
        
        return unique_tools
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """프롬프트 템플릿 생성"""
        system_prompt = self._get_system_prompt()
        
        # 기본 에이전트 지침 추가
        base_instructions = """
You are an AI agent in an automated development pipeline.
Always:
1. Be precise and actionable in your responses
2. Use the provided tools to accomplish tasks
3. Validate your outputs before returning results
4. Report progress and any issues encountered
5. Follow best practices for your domain

Current timestamp: {timestamp}
Pipeline ID: {pipeline_id}
Task ID: {task_id}
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", base_instructions + "\n\n" + system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    async def _create_agent_executor(self) -> AgentExecutor:
        """에이전트 실행기 생성"""
        claude_client = await self._get_claude_client()
        
        # Claude를 LangChain과 통합하기 위한 래퍼
        class ClaudeLLMWrapper:
            def __init__(self, client: ClaudeClient):
                self.client = client
            
            async def agenerate(self, messages: List[BaseMessage], **kwargs):
                # LangChain 메시지를 Claude 형식으로 변환
                claude_messages = []
                system_message = None
                
                for msg in messages:
                    if isinstance(msg, SystemMessage):
                        system_message = msg.content
                    elif isinstance(msg, HumanMessage):
                        claude_messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        claude_messages.append({"role": "assistant", "content": msg.content})
                
                # Claude API 호출
                response = await self.client.create_message(
                    messages=claude_messages,
                    system=system_message,
                    max_tokens=settings.claude_max_tokens
                )
                
                # 응답 변환
                content = response["content"][0]["text"]
                return AIMessage(content=content)
        
        llm_wrapper = ClaudeLLMWrapper(claude_client)
        
        # OpenAI 함수 형식으로 도구 변환
        functions = [convert_to_openai_function(t) for t in self.tools]
        
        # 에이전트 체인 생성
        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
                "timestamp": lambda x: datetime.utcnow().isoformat(),
                "pipeline_id": lambda x: x.get("pipeline_id", "unknown"),
                "task_id": lambda x: x.get("task_id", "unknown"),
            }
            | self.prompt
            | llm_wrapper.agenerate
            | OpenAIFunctionsAgentOutputParser()
        )
        
        # 에이전트 실행기 생성
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=10,
            early_stopping_method="generate"
        )
    
    @track_agent_execution("BaseAgent")
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        에이전트 실행
        
        Args:
            context: 실행 컨텍스트
            
        Returns:
            실행 결과
        """
        try:
            # 입력 검증
            validation_error = await self.validate_input(context)
            if validation_error:
                raise AgentExecutionError(f"Input validation failed: {validation_error}")
            
            # 에이전트 실행기 초기화
            if self._agent_executor is None:
                self._agent_executor = await self._create_agent_executor()
            
            # 입력 준비
            agent_input = self._prepare_input(context)
            
            # 에이전트 실행
            self.logger.info(f"Executing agent with input: {agent_input[:200]}...")
            
            result = await self._agent_executor.ainvoke({
                "input": agent_input,
                "pipeline_id": context.pipeline_id,
                "task_id": context.task_id
            })
            
            # 결과 처리
            processed_result = await self._process_result(result, context)
            
            # 실행 히스토리 저장
            self._save_execution_history(context, processed_result)
            
            # 출력 검증
            validation_error = await self.validate_output(processed_result)
            if validation_error:
                processed_result.success = False
                processed_result.errors.append(f"Output validation failed: {validation_error}")
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            
            return AgentResult(
                success=False,
                output=None,
                errors=[str(e)],
                metrics={"error_type": type(e).__name__}
            )
    
    def _prepare_input(self, context: AgentContext) -> str:
        """에이전트 입력 준비"""
        input_parts = [
            f"Requirements: {context.requirements}"
        ]
        
        if context.constraints:
            input_parts.append(f"Constraints: {', '.join(context.constraints)}")
        
        if context.previous_results:
            input_parts.append(f"Previous Results: {context.previous_results}")
        
        if context.metadata:
            input_parts.append(f"Additional Context: {context.metadata}")
        
        return "\n\n".join(input_parts)
    
    @abstractmethod
    async def _process_result(self, raw_result: Dict[str, Any], context: AgentContext) -> AgentResult:
        """결과 처리 (서브클래스에서 구현)"""
        pass
    
    async def validate_input(self, context: AgentContext) -> Optional[str]:
        """입력 검증"""
        if not context.requirements:
            return "Requirements cannot be empty"
        
        if not context.pipeline_id:
            return "Pipeline ID is required"
        
        if not context.task_id:
            return "Task ID is required"
        
        # 서브클래스별 추가 검증
        return await self._validate_specific_input(context)
    
    async def _validate_specific_input(self, context: AgentContext) -> Optional[str]:
        """서브클래스별 입력 검증 (오버라이드 가능)"""
        return None
    
    async def validate_output(self, result: AgentResult) -> Optional[str]:
        """출력 검증"""
        if result.success and result.output is None:
            return "Successful result must have output"
        
        # 서브클래스별 추가 검증
        return await self._validate_specific_output(result)
    
    async def _validate_specific_output(self, result: AgentResult) -> Optional[str]:
        """서브클래스별 출력 검증 (오버라이드 가능)"""
        return None
    
    def _save_execution_history(self, context: AgentContext, result: AgentResult):
        """실행 히스토리 저장"""
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline_id": context.pipeline_id,
            "task_id": context.task_id,
            "success": result.success,
            "metrics": result.metrics,
            "errors": result.errors
        }
        
        self.execution_history.append(history_entry)
        
        # 최대 100개 유지
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """실행 통계 반환"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for h in self.execution_history if h["success"])
        
        execution_times = [
            h["metrics"].get("execution_time", 0)
            for h in self.execution_history
            if "execution_time" in h.get("metrics", {})
        ]
        
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_executions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_execution_time": avg_time,
            "recent_errors": [
                h["errors"] for h in self.execution_history[-5:]
                if h.get("errors")
            ]
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.execution_history.clear()
        self.token_usage = {
            "input": 0,
            "output": 0,
            "total": 0
        }