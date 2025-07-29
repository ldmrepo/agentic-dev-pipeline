"""
Claude API 클라이언트
Anthropic Claude API와의 통합을 담당
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from datetime import datetime
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_retry_log
)

from src.core.config import get_settings
from src.core.exceptions import APIError, RateLimitError, TokenLimitError

logger = logging.getLogger(__name__)
settings = get_settings()

class ClaudeClient:
    """Claude API 클라이언트"""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.temperature = settings.claude_temperature
        
        # HTTP 클라이언트 설정
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            timeout=httpx.Timeout(60.0, read=300.0)  # 긴 응답 대기
        )
        
        # 토큰 사용량 추적
        self.token_usage = {
            "input": 0,
            "output": 0,
            "total": 0
        }
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_retry=before_retry_log(logger, logging.WARNING)
    )
    async def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Claude API 메시지 생성
        
        Args:
            messages: 대화 메시지 리스트
            system: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 생성 온도
            stream: 스트리밍 여부
            metadata: 추가 메타데이터
        
        Returns:
            API 응답 또는 스트리밍 제너레이터
        """
        # 요청 데이터 구성
        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": stream
        }
        
        if system:
            request_data["system"] = system
        
        if metadata:
            request_data["metadata"] = {"user_id": metadata.get("user_id", "system")}
        
        try:
            # API 요청
            response = await self.client.post(
                "/messages",
                json=request_data
            )
            
            # 에러 처리
            if response.status_code == 429:
                raise RateLimitError("Claude API rate limit exceeded")
            elif response.status_code == 400:
                error_data = response.json()
                if "max_tokens" in error_data.get("error", {}).get("message", ""):
                    raise TokenLimitError("Token limit exceeded")
                raise APIError(f"Bad request: {error_data}")
            elif response.status_code != 200:
                raise APIError(f"API request failed: {response.status_code} - {response.text}")
            
            # 스트리밍 응답 처리
            if stream:
                return self._handle_stream_response(response)
            
            # 일반 응답 처리
            result = response.json()
            
            # 토큰 사용량 업데이트
            self._update_token_usage(result.get("usage", {}))
            
            return result
            
        except httpx.TimeoutException:
            logger.error("Claude API request timeout")
            raise APIError("Request timeout")
        except httpx.ConnectError:
            logger.error("Failed to connect to Claude API")
            raise APIError("Connection failed")
        except Exception as e:
            logger.error(f"Unexpected error in Claude API call: {str(e)}")
            raise
    
    async def _handle_stream_response(self, response: httpx.Response) -> AsyncGenerator[Dict[str, Any], None]:
        """스트리밍 응답 처리"""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # "data: " 제거
                
                if data == "[DONE]":
                    break
                
                try:
                    event = json.loads(data)
                    yield event
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse streaming event: {data}")
    
    def _update_token_usage(self, usage: Dict[str, int]):
        """토큰 사용량 업데이트"""
        self.token_usage["input"] += usage.get("input_tokens", 0)
        self.token_usage["output"] += usage.get("output_tokens", 0)
        self.token_usage["total"] = self.token_usage["input"] + self.token_usage["output"]
    
    async def analyze(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        output_format: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """
        분석 작업 수행
        
        Args:
            prompt: 분석 프롬프트
            context: 추가 컨텍스트
            output_format: 출력 형식 (json, text)
        
        Returns:
            분석 결과
        """
        system_prompt = """You are an AI assistant specialized in software development analysis.
Always provide structured, actionable insights based on the given requirements.
When asked to format output as JSON, ensure valid JSON syntax."""
        
        messages = [{"role": "user", "content": prompt}]
        
        if context:
            messages[0]["content"] = f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}"
        
        response = await self.create_message(
            messages=messages,
            system=system_prompt
        )
        
        content = response["content"][0]["text"]
        
        # JSON 형식 요청 시 파싱
        if output_format == "json":
            try:
                # JSON 블록 추출 (```json ... ``` 형식 처리)
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                else:
                    json_str = content.strip()
                
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                # 폴백: 텍스트로 반환
                return content
        
        return content
    
    async def generate_code(
        self,
        specification: Dict[str, Any],
        language: str,
        framework: Optional[str] = None,
        style_guide: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        코드 생성
        
        Args:
            specification: 코드 사양
            language: 프로그래밍 언어
            framework: 사용할 프레임워크
            style_guide: 코딩 스타일 가이드
        
        Returns:
            생성된 코드와 메타데이터
        """
        system_prompt = f"""You are an expert {language} developer.
Generate clean, maintainable, and well-documented code.
Follow best practices and design patterns.
{f'Use {framework} framework.' if framework else ''}
{f'Follow this style guide: {style_guide}' if style_guide else ''}"""
        
        prompt = f"""Generate {language} code for the following specification:

{json.dumps(specification, indent=2)}

Provide the code with appropriate comments and structure.
Include any necessary imports and dependencies."""
        
        response = await self.create_message(
            messages=[{"role": "user", "content": prompt}],
            system=system_prompt
        )
        
        content = response["content"][0]["text"]
        
        # 코드 블록 추출
        code_blocks = self._extract_code_blocks(content)
        
        return {
            "code": code_blocks[0] if code_blocks else content,
            "explanation": content,
            "language": language,
            "framework": framework,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _extract_code_blocks(self, content: str) -> List[str]:
        """마크다운 코드 블록 추출"""
        import re
        
        # ```언어\n코드\n``` 패턴 찾기
        pattern = r"```(?:\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        return matches
    
    async def review_code(
        self,
        code: str,
        language: str,
        review_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        코드 리뷰
        
        Args:
            code: 리뷰할 코드
            language: 프로그래밍 언어
            review_criteria: 리뷰 기준
        
        Returns:
            리뷰 결과
        """
        default_criteria = [
            "Code quality and readability",
            "Performance considerations",
            "Security vulnerabilities",
            "Error handling",
            "Best practices adherence",
            "Test coverage suggestions"
        ]
        
        criteria = review_criteria or default_criteria
        
        system_prompt = f"""You are an expert code reviewer for {language}.
Provide constructive feedback focusing on improvement opportunities.
Be specific with line numbers and code examples when suggesting changes."""
        
        prompt = f"""Review the following {language} code:

```{language}
{code}
```

Review criteria:
{chr(10).join(f'- {criterion}' for criterion in criteria)}

Provide a structured review with:
1. Overall assessment
2. Specific issues found
3. Improvement suggestions
4. Security concerns if any
5. Performance optimization opportunities"""
        
        response = await self.create_message(
            messages=[{"role": "user", "content": prompt}],
            system=system_prompt
        )
        
        return {
            "review": response["content"][0]["text"],
            "language": language,
            "criteria": criteria,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def create_test_cases(
        self,
        code: str,
        language: str,
        test_framework: Optional[str] = None,
        coverage_target: int = 80
    ) -> Dict[str, Any]:
        """
        테스트 케이스 생성
        
        Args:
            code: 테스트할 코드
            language: 프로그래밍 언어
            test_framework: 테스트 프레임워크
            coverage_target: 목표 커버리지
        
        Returns:
            생성된 테스트 케이스
        """
        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "go": "testing"
        }
        
        framework = test_framework or framework_map.get(language.lower(), "default")
        
        system_prompt = f"""You are an expert in writing comprehensive test cases.
Generate test cases that achieve at least {coverage_target}% code coverage.
Use {framework} as the testing framework.
Include edge cases, error scenarios, and happy path tests."""
        
        prompt = f"""Generate comprehensive test cases for the following {language} code:

```{language}
{code}
```

Include:
1. Unit tests for all functions/methods
2. Edge case testing
3. Error handling tests
4. Integration tests if applicable
5. Test data setup and teardown"""
        
        response = await self.create_message(
            messages=[{"role": "user", "content": prompt}],
            system=system_prompt
        )
        
        content = response["content"][0]["text"]
        test_code = self._extract_code_blocks(content)
        
        return {
            "tests": test_code[0] if test_code else content,
            "explanation": content,
            "framework": framework,
            "coverage_target": coverage_target,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_token_usage(self) -> Dict[str, int]:
        """현재 토큰 사용량 반환"""
        return self.token_usage.copy()
    
    def reset_token_usage(self):
        """토큰 사용량 초기화"""
        self.token_usage = {
            "input": 0,
            "output": 0,
            "total": 0
        }

# 싱글톤 인스턴스
_claude_client: Optional[ClaudeClient] = None

async def get_claude_client() -> ClaudeClient:
    """Claude 클라이언트 싱글톤 인스턴스 반환"""
    global _claude_client
    
    if _claude_client is None:
        _claude_client = ClaudeClient()
    
    return _claude_client

# 편의 함수들
async def analyze_requirements(requirements: str) -> Dict[str, Any]:
    """요구사항 분석 편의 함수"""
    client = await get_claude_client()
    return await client.analyze(
        f"Analyze these software requirements and provide a structured analysis:\n{requirements}",
        output_format="json"
    )

async def generate_architecture(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """아키텍처 설계 편의 함수"""
    client = await get_claude_client()
    return await client.analyze(
        "Design a system architecture based on these requirements:",
        context=requirements,
        output_format="json"
    )

async def estimate_effort(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """작업 시간 추정 편의 함수"""
    client = await get_claude_client()
    return await client.analyze(
        "Estimate the effort required for these tasks in hours:",
        context={"tasks": tasks},
        output_format="json"
    )