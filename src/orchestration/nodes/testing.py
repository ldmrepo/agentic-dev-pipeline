"""
테스트 노드
생성된 코드에 대한 테스트 수행
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from src.orchestration.nodes.base import BaseNode
from src.orchestration.state import WorkflowState
from src.core.constants import ArtifactType, TestType

class TestingNode(BaseNode):
    """테스트 실행 노드"""
    
    def __init__(self):
        super().__init__(
            name="Testing",
            description="Execute tests on generated code"
        )
    
    async def _validate_specific_input(self, state: WorkflowState) -> Optional[str]:
        """입력 검증"""
        if not state.get("development_result"):
            return "Development result is missing"
        
        dev_result = state["development_result"]
        if "generated_files" not in dev_result or not dev_result["generated_files"]:
            return "No generated files found to test"
        
        return None
    
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """테스트 실행"""
        dev_result = state["development_result"]
        planning_result = state.get("planning_result", {})
        
        self.log_progress("Starting test execution...")
        
        # 테스트 실행
        test_result = await self._execute_tests(dev_result, planning_result)
        
        # 메시지 추가
        message_update = self.add_message(
            state,
            f"Testing completed: {test_result['summary']['total_tests']} tests, "
            f"{test_result['summary']['passed']} passed, {test_result['summary']['failed']} failed",
            metadata={
                "test_summary": test_result["summary"],
                "coverage": test_result["coverage"]
            }
        )
        
        # 테스트 보고서 아티팩트
        test_report = self.add_artifact(
            state,
            name="test_report",
            artifact_type=ArtifactType.DOCUMENT,
            content=self._generate_test_report(test_result),
            metadata={"format": "markdown", "test_run_id": test_result["test_run_id"]}
        )
        
        # 커버리지 보고서 아티팩트
        coverage_report = self.add_artifact(
            state,
            name="coverage_report",
            artifact_type=ArtifactType.DOCUMENT,
            content=json.dumps(test_result["coverage"], indent=2),
            metadata={"format": "json"}
        )
        
        # 결과 업데이트
        result_update = self.update_result(state, "test_result", test_result)
        
        # 모든 업데이트 병합
        updates = {}
        updates.update(message_update)
        updates.update(test_report)
        updates.update(coverage_report)
        updates.update(result_update)
        
        self.log_progress("Testing completed")
        
        return updates
    
    async def _execute_tests(self, dev_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """테스트 실행"""
        generated_files = dev_result.get("generated_files", [])
        
        # 테스트 유형별 분류
        test_suites = self._create_test_suites(generated_files, planning_result)
        
        # 테스트 실행 결과 초기화
        test_results = {
            "test_run_id": f"test-run-{datetime.utcnow().isoformat()}",
            "suites": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_ms": 0
            },
            "coverage": {
                "line_coverage": 0.0,
                "branch_coverage": 0.0,
                "function_coverage": 0.0,
                "statement_coverage": 0.0,
                "files": []
            },
            "issues": []
        }
        
        # 각 테스트 스위트 실행
        for suite in test_suites:
            suite_result = await self._run_test_suite(suite, generated_files)
            test_results["suites"].append(suite_result)
            
            # 요약 업데이트
            test_results["summary"]["total_tests"] += suite_result["total_tests"]
            test_results["summary"]["passed"] += suite_result["passed"]
            test_results["summary"]["failed"] += suite_result["failed"]
            test_results["summary"]["skipped"] += suite_result["skipped"]
            test_results["summary"]["duration_ms"] += suite_result["duration_ms"]
        
        # 커버리지 계산
        test_results["coverage"] = self._calculate_coverage(generated_files, test_results["suites"])
        
        # 이슈 수집
        test_results["issues"] = self._collect_issues(test_results["suites"])
        
        return test_results
    
    def _create_test_suites(self, generated_files: List[Dict[str, Any]], planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """테스트 스위트 생성"""
        suites = []
        
        # 단위 테스트 스위트
        unit_test_files = [f for f in generated_files if "test" in f["path"].lower() or "spec" in f["path"].lower()]
        if unit_test_files or any("backend" in f["path"] for f in generated_files):
            suites.append({
                "name": "Unit Tests",
                "type": TestType.UNIT.value,
                "test_files": unit_test_files,
                "target_files": [f for f in generated_files if "backend" in f["path"] and "test" not in f["path"]]
            })
        
        # 통합 테스트 스위트
        if any("api" in f["path"].lower() for f in generated_files):
            suites.append({
                "name": "Integration Tests",
                "type": TestType.INTEGRATION.value,
                "test_files": [],
                "target_files": [f for f in generated_files if "api" in f["path"].lower()]
            })
        
        # E2E 테스트 스위트
        if any("frontend" in f["path"] for f in generated_files):
            suites.append({
                "name": "E2E Tests",
                "type": TestType.E2E.value,
                "test_files": [],
                "target_files": [f for f in generated_files if "frontend" in f["path"]]
            })
        
        # 성능 테스트 스위트 (복잡한 프로젝트인 경우)
        if planning_result.get("overview", {}).get("complexity") in ["complex", "very_complex"]:
            suites.append({
                "name": "Performance Tests",
                "type": TestType.PERFORMANCE.value,
                "test_files": [],
                "target_files": generated_files
            })
        
        return suites
    
    async def _run_test_suite(self, suite: Dict[str, Any], generated_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """테스트 스위트 실행 (시뮬레이션)"""
        suite_type = suite["type"]
        target_files = suite["target_files"]
        
        # 테스트 케이스 생성
        test_cases = self._generate_test_cases(suite_type, target_files)
        
        # 테스트 실행 결과
        suite_result = {
            "name": suite["name"],
            "type": suite_type,
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_ms": 0,
            "test_cases": []
        }
        
        # 각 테스트 케이스 실행
        for test_case in test_cases:
            test_result = await self._run_test_case(test_case, suite_type)
            suite_result["test_cases"].append(test_result)
            
            # 결과 집계
            if test_result["status"] == "passed":
                suite_result["passed"] += 1
            elif test_result["status"] == "failed":
                suite_result["failed"] += 1
            else:
                suite_result["skipped"] += 1
            
            suite_result["duration_ms"] += test_result["duration_ms"]
        
        return suite_result
    
    def _generate_test_cases(self, test_type: str, target_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """테스트 케이스 생성"""
        test_cases = []
        
        if test_type == TestType.UNIT.value:
            # 단위 테스트 케이스
            for file in target_files:
                if "models" in file["path"]:
                    test_cases.extend([
                        {"name": "test_user_model_creation", "target": file["path"]},
                        {"name": "test_user_model_validation", "target": file["path"]},
                        {"name": "test_task_model_relationships", "target": file["path"]}
                    ])
                elif "api" in file["path"]:
                    test_cases.extend([
                        {"name": "test_endpoint_authentication", "target": file["path"]},
                        {"name": "test_endpoint_validation", "target": file["path"]},
                        {"name": "test_endpoint_error_handling", "target": file["path"]}
                    ])
        
        elif test_type == TestType.INTEGRATION.value:
            # 통합 테스트 케이스
            test_cases.extend([
                {"name": "test_api_database_integration", "target": "backend/api"},
                {"name": "test_api_cache_integration", "target": "backend/api"},
                {"name": "test_api_external_service_integration", "target": "backend/api"}
            ])
        
        elif test_type == TestType.E2E.value:
            # E2E 테스트 케이스
            test_cases.extend([
                {"name": "test_user_registration_flow", "target": "frontend"},
                {"name": "test_task_creation_flow", "target": "frontend"},
                {"name": "test_navigation_flow", "target": "frontend"}
            ])
        
        elif test_type == TestType.PERFORMANCE.value:
            # 성능 테스트 케이스
            test_cases.extend([
                {"name": "test_api_response_time", "target": "backend/api"},
                {"name": "test_database_query_performance", "target": "backend/models"},
                {"name": "test_frontend_load_time", "target": "frontend"}
            ])
        
        return test_cases
    
    async def _run_test_case(self, test_case: Dict[str, Any], test_type: str) -> Dict[str, Any]:
        """개별 테스트 케이스 실행 (시뮬레이션)"""
        import random
        
        # 테스트 실행 시뮬레이션
        duration_ms = random.randint(10, 500)
        
        # 성공/실패 결정 (90% 성공률)
        passed = random.random() < 0.9
        
        result = {
            "name": test_case["name"],
            "status": "passed" if passed else "failed",
            "duration_ms": duration_ms,
            "target": test_case["target"]
        }
        
        # 실패한 경우 에러 정보 추가
        if not passed:
            result["error"] = {
                "message": self._generate_error_message(test_case["name"]),
                "stack_trace": self._generate_stack_trace(test_case),
                "expected": "Expected behavior",
                "actual": "Actual behavior"
            }
        
        # 성능 테스트인 경우 메트릭 추가
        if test_type == TestType.PERFORMANCE.value:
            result["metrics"] = {
                "response_time_ms": random.randint(50, 200),
                "throughput_rps": random.randint(100, 1000),
                "cpu_usage_percent": random.randint(20, 80),
                "memory_usage_mb": random.randint(100, 500)
            }
        
        return result
    
    def _generate_error_message(self, test_name: str) -> str:
        """에러 메시지 생성"""
        error_templates = [
            f"Assertion failed in {test_name}: Expected value does not match actual",
            f"Timeout occurred in {test_name}: Operation took longer than expected",
            f"Null reference exception in {test_name}: Object not initialized",
            f"Validation error in {test_name}: Invalid input provided"
        ]
        
        import random
        return random.choice(error_templates)
    
    def _generate_stack_trace(self, test_case: Dict[str, Any]) -> str:
        """스택 트레이스 생성"""
        return f"""
  at {test_case['name']} ({test_case['target']}:42)
  at TestRunner.execute (test_runner.py:156)
  at TestSuite.run (test_suite.py:89)
  at main (main.py:23)
"""
    
    def _calculate_coverage(self, generated_files: List[Dict[str, Any]], test_suites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """코드 커버리지 계산"""
        import random
        
        # 전체 커버리지 (테스트 성공률에 기반)
        total_tests = sum(s["total_tests"] for s in test_suites)
        passed_tests = sum(s["passed"] for s in test_suites)
        
        base_coverage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        coverage = {
            "line_coverage": min(95, base_coverage + random.uniform(-5, 5)),
            "branch_coverage": min(90, base_coverage + random.uniform(-10, 0)),
            "function_coverage": min(98, base_coverage + random.uniform(-2, 8)),
            "statement_coverage": min(95, base_coverage + random.uniform(-5, 5)),
            "files": []
        }
        
        # 파일별 커버리지
        for file in generated_files:
            if file.get("language") in ["python", "typescript", "javascript"]:
                file_coverage = {
                    "path": file["path"],
                    "lines_covered": random.randint(80, 95),
                    "lines_total": file.get("lines", 100),
                    "branches_covered": random.randint(70, 90),
                    "branches_total": random.randint(10, 30),
                    "functions_covered": random.randint(90, 100),
                    "functions_total": random.randint(5, 20)
                }
                coverage["files"].append(file_coverage)
        
        return coverage
    
    def _collect_issues(self, test_suites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """테스트에서 발견된 이슈 수집"""
        issues = []
        
        for suite in test_suites:
            for test_case in suite.get("test_cases", []):
                if test_case["status"] == "failed":
                    issues.append({
                        "severity": "high" if "error" in test_case["name"] else "medium",
                        "type": "test_failure",
                        "test_name": test_case["name"],
                        "suite": suite["name"],
                        "message": test_case.get("error", {}).get("message", "Test failed"),
                        "file": test_case["target"]
                    })
        
        # 커버리지 관련 이슈
        if any(suite["name"] == "Unit Tests" for suite in test_suites):
            unit_suite = next(s for s in test_suites if s["name"] == "Unit Tests")
            coverage_percent = (unit_suite["passed"] / unit_suite["total_tests"] * 100) if unit_suite["total_tests"] > 0 else 0
            
            if coverage_percent < 80:
                issues.append({
                    "severity": "medium",
                    "type": "low_coverage",
                    "message": f"Code coverage is below 80% ({coverage_percent:.1f}%)",
                    "recommendation": "Add more unit tests to increase coverage"
                })
        
        return issues
    
    def _generate_test_report(self, test_result: Dict[str, Any]) -> str:
        """테스트 보고서 생성"""
        summary = test_result["summary"]
        coverage = test_result["coverage"]
        
        report = f"""# Test Report

## Summary
- **Test Run ID**: {test_result['test_run_id']}
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed']} ✅
- **Failed**: {summary['failed']} ❌
- **Skipped**: {summary['skipped']} ⏭️
- **Duration**: {summary['duration_ms']}ms

## Coverage
- **Line Coverage**: {coverage['line_coverage']:.1f}%
- **Branch Coverage**: {coverage['branch_coverage']:.1f}%
- **Function Coverage**: {coverage['function_coverage']:.1f}%
- **Statement Coverage**: {coverage['statement_coverage']:.1f}%

## Test Suites
"""
        
        for suite in test_result["suites"]:
            report += f"\n### {suite['name']}\n"
            report += f"- Type: {suite['type']}\n"
            report += f"- Tests: {suite['total_tests']} (✅ {suite['passed']}, ❌ {suite['failed']}, ⏭️ {suite['skipped']})\n"
            report += f"- Duration: {suite['duration_ms']}ms\n"
            
            # 실패한 테스트 나열
            failed_tests = [tc for tc in suite.get('test_cases', []) if tc['status'] == 'failed']
            if failed_tests:
                report += "\n#### Failed Tests:\n"
                for test in failed_tests:
                    report += f"- **{test['name']}**\n"
                    if 'error' in test:
                        report += f"  - Error: {test['error']['message']}\n"
                        report += f"  - File: {test['target']}\n"
        
        # 이슈 섹션
        if test_result["issues"]:
            report += "\n## Issues Found\n"
            for issue in test_result["issues"]:
                report += f"- **[{issue['severity'].upper()}]** {issue['message']}\n"
                if 'recommendation' in issue:
                    report += f"  - Recommendation: {issue['recommendation']}\n"
        
        report += f"\n---\n*Generated on: {datetime.utcnow().isoformat()}*\n"
        
        return report

# 노드 인스턴스 생성
testing_node = TestingNode()