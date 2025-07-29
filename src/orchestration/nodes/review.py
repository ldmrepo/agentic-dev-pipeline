"""
코드 리뷰 노드
생성된 코드와 테스트 결과를 리뷰
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from src.orchestration.nodes.base import BaseNode
from src.orchestration.state import WorkflowState
from src.core.constants import ArtifactType, ReviewSeverity

class ReviewNode(BaseNode):
    """코드 리뷰 노드"""
    
    def __init__(self):
        super().__init__(
            name="Review",
            description="Review generated code and test results"
        )
    
    async def _validate_specific_input(self, state: WorkflowState) -> Optional[str]:
        """입력 검증"""
        if not state.get("development_result"):
            return "Development result is missing"
        
        if not state.get("test_result"):
            return "Test result is missing"
        
        return None
    
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """코드 리뷰 수행"""
        dev_result = state["development_result"]
        test_result = state["test_result"]
        planning_result = state.get("planning_result", {})
        
        self.log_progress("Starting code review...")
        
        # 코드 리뷰 실행
        review_result = await self._perform_review(dev_result, test_result, planning_result)
        
        # 메시지 추가
        message_update = self.add_message(
            state,
            f"Code review completed: {review_result['summary']['total_issues']} issues found "
            f"({review_result['summary']['critical']} critical, "
            f"{review_result['summary']['major']} major, "
            f"{review_result['summary']['minor']} minor)",
            metadata={
                "review_summary": review_result["summary"],
                "approval_status": review_result["approval_status"]
            }
        )
        
        # 리뷰 보고서 아티팩트
        review_report = self.add_artifact(
            state,
            name="review_report",
            artifact_type=ArtifactType.DOCUMENT,
            content=self._generate_review_report(review_result),
            metadata={"format": "markdown", "review_id": review_result["review_id"]}
        )
        
        # 개선 제안 아티팩트
        if review_result["suggestions"]:
            suggestions_artifact = self.add_artifact(
                state,
                name="improvement_suggestions",
                artifact_type=ArtifactType.DOCUMENT,
                content=json.dumps(review_result["suggestions"], indent=2),
                metadata={"format": "json"}
            )
        else:
            suggestions_artifact = {}
        
        # 결과 업데이트
        result_update = self.update_result(state, "review_result", review_result)
        
        # 모든 업데이트 병합
        updates = {}
        updates.update(message_update)
        updates.update(review_report)
        updates.update(suggestions_artifact)
        updates.update(result_update)
        
        self.log_progress("Code review completed")
        
        return updates
    
    async def _perform_review(self, dev_result: Dict[str, Any], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """코드 리뷰 수행"""
        generated_files = dev_result.get("generated_files", [])
        test_summary = test_result.get("summary", {})
        coverage = test_result.get("coverage", {})
        
        # 리뷰 결과 초기화
        review_result = {
            "review_id": f"review-{datetime.utcnow().isoformat()}",
            "timestamp": datetime.utcnow().isoformat(),
            "files_reviewed": len(generated_files),
            "categories": [],
            "issues": [],
            "suggestions": [],
            "metrics": {},
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "major": 0,
                "minor": 0,
                "info": 0
            },
            "approval_status": "pending"
        }
        
        # 카테고리별 리뷰
        categories = [
            ("code_quality", self._review_code_quality),
            ("architecture", self._review_architecture),
            ("security", self._review_security),
            ("performance", self._review_performance),
            ("testing", self._review_testing),
            ("documentation", self._review_documentation)
        ]
        
        for category_name, review_func in categories:
            category_result = await review_func(generated_files, test_result, planning_result)
            review_result["categories"].append(category_result)
            
            # 이슈 수집
            review_result["issues"].extend(category_result.get("issues", []))
            
            # 제안 수집
            review_result["suggestions"].extend(category_result.get("suggestions", []))
        
        # 메트릭 계산
        review_result["metrics"] = self._calculate_metrics(generated_files, test_result)
        
        # 요약 업데이트
        for issue in review_result["issues"]:
            severity = issue.get("severity", "info")
            if severity == ReviewSeverity.CRITICAL.value:
                review_result["summary"]["critical"] += 1
            elif severity == ReviewSeverity.MAJOR.value:
                review_result["summary"]["major"] += 1
            elif severity == ReviewSeverity.MINOR.value:
                review_result["summary"]["minor"] += 1
            else:
                review_result["summary"]["info"] += 1
        
        review_result["summary"]["total_issues"] = len(review_result["issues"])
        
        # 승인 상태 결정
        review_result["approval_status"] = self._determine_approval_status(review_result)
        
        return review_result
    
    async def _review_code_quality(self, files: List[Dict[str, Any]], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """코드 품질 리뷰"""
        issues = []
        suggestions = []
        
        for file in files:
            if file.get("language") in ["python", "typescript", "javascript"]:
                # 파일 크기 체크
                lines = file.get("lines", 0)
                if lines > 500:
                    issues.append({
                        "file": file["path"],
                        "line": None,
                        "severity": ReviewSeverity.MAJOR.value,
                        "category": "code_quality",
                        "message": f"File is too large ({lines} lines). Consider splitting into smaller modules.",
                        "rule": "file-size"
                    })
                
                # 복잡도 체크 (시뮬레이션)
                if "backend" in file["path"] and lines > 200:
                    issues.append({
                        "file": file["path"],
                        "line": 50,
                        "severity": ReviewSeverity.MINOR.value,
                        "category": "code_quality",
                        "message": "High cyclomatic complexity detected. Consider refactoring.",
                        "rule": "complexity"
                    })
                
                # 네이밍 컨벤션 체크
                if file.get("language") == "python" and "API" in file["path"]:
                    suggestions.append({
                        "file": file["path"],
                        "suggestion": "Python file names should use snake_case instead of PascalCase",
                        "category": "naming"
                    })
        
        return {
            "category": "code_quality",
            "score": 85,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "average_file_size": sum(f.get("lines", 0) for f in files) / len(files) if files else 0,
                "total_lines": sum(f.get("lines", 0) for f in files)
            }
        }
    
    async def _review_architecture(self, files: List[Dict[str, Any]], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """아키텍처 리뷰"""
        issues = []
        suggestions = []
        
        # 계층 분리 확인
        has_frontend = any("frontend" in f["path"] for f in files)
        has_backend = any("backend" in f["path"] for f in files)
        
        if has_frontend and has_backend:
            # API 계약 확인
            api_files = [f for f in files if "api" in f["path"].lower()]
            if not api_files:
                issues.append({
                    "file": None,
                    "line": None,
                    "severity": ReviewSeverity.MAJOR.value,
                    "category": "architecture",
                    "message": "No clear API contract found between frontend and backend",
                    "rule": "api-contract"
                })
        
        # 디자인 패턴 제안
        if len(files) > 10:
            suggestions.append({
                "file": None,
                "suggestion": "Consider implementing a service layer to separate business logic from controllers",
                "category": "design-pattern"
            })
        
        # 모듈화 체크
        module_count = len(set(f["path"].split("/")[0] for f in files if "/" in f["path"]))
        if module_count < 3 and len(files) > 15:
            issues.append({
                "file": None,
                "line": None,
                "severity": ReviewSeverity.MINOR.value,
                "category": "architecture",
                "message": "Low module count. Consider better separation of concerns",
                "rule": "modularity"
            })
        
        return {
            "category": "architecture",
            "score": 80,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "module_count": module_count,
                "layer_separation": has_frontend and has_backend
            }
        }
    
    async def _review_security(self, files: List[Dict[str, Any]], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """보안 리뷰"""
        issues = []
        suggestions = []
        
        # 보안 관련 키워드 검색
        security_keywords = ["password", "secret", "key", "token", "api_key"]
        
        for file in files:
            content = file.get("content", "")
            
            # 하드코딩된 시크릿 검사
            for keyword in security_keywords:
                if keyword in content.lower() and "=" in content:
                    # 실제 하드코딩 체크 (시뮬레이션)
                    if file["path"] not in [".env", "config.py", "settings.py"]:
                        issues.append({
                            "file": file["path"],
                            "line": 10,
                            "severity": ReviewSeverity.CRITICAL.value,
                            "category": "security",
                            "message": f"Potential hardcoded {keyword} detected",
                            "rule": "hardcoded-secrets"
                        })
            
            # SQL 인젝션 취약점 체크
            if "sql" in content.lower() and "format" in content:
                issues.append({
                    "file": file["path"],
                    "line": 50,
                    "severity": ReviewSeverity.CRITICAL.value,
                    "category": "security",
                    "message": "Potential SQL injection vulnerability. Use parameterized queries",
                    "rule": "sql-injection"
                })
        
        # 보안 헤더 체크
        if any("api" in f["path"].lower() for f in files):
            suggestions.append({
                "file": None,
                "suggestion": "Implement security headers: CORS, CSP, X-Frame-Options",
                "category": "security-headers"
            })
        
        # 인증/인가 체크
        auth_files = [f for f in files if "auth" in f["path"].lower()]
        if not auth_files and len(files) > 10:
            issues.append({
                "file": None,
                "line": None,
                "severity": ReviewSeverity.MAJOR.value,
                "category": "security",
                "message": "No authentication mechanism found",
                "rule": "missing-auth"
            })
        
        return {
            "category": "security",
            "score": 75,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "auth_implemented": len(auth_files) > 0,
                "security_issues": len([i for i in issues if i["severity"] == ReviewSeverity.CRITICAL.value])
            }
        }
    
    async def _review_performance(self, files: List[Dict[str, Any]], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """성능 리뷰"""
        issues = []
        suggestions = []
        
        # 데이터베이스 쿼리 최적화
        db_files = [f for f in files if "model" in f["path"].lower() or "database" in f["path"].lower()]
        if db_files:
            suggestions.append({
                "file": None,
                "suggestion": "Consider adding database indexes for frequently queried fields",
                "category": "database-optimization"
            })
        
        # 캐싱 체크
        has_caching = any("cache" in f.get("content", "").lower() or "redis" in f.get("content", "").lower() for f in files)
        if not has_caching and len(files) > 15:
            issues.append({
                "file": None,
                "line": None,
                "severity": ReviewSeverity.MINOR.value,
                "category": "performance",
                "message": "No caching mechanism detected. Consider implementing caching for better performance",
                "rule": "missing-cache"
            })
        
        # 프론트엔드 번들 크기
        frontend_files = [f for f in files if "frontend" in f["path"]]
        if frontend_files:
            total_frontend_lines = sum(f.get("lines", 0) for f in frontend_files)
            if total_frontend_lines > 5000:
                issues.append({
                    "file": None,
                    "line": None,
                    "severity": ReviewSeverity.MINOR.value,
                    "category": "performance",
                    "message": "Large frontend bundle size. Consider code splitting",
                    "rule": "bundle-size"
                })
        
        # 비동기 처리
        async_count = sum(1 for f in files if "async" in f.get("content", "") or "await" in f.get("content", ""))
        if async_count == 0 and any("api" in f["path"].lower() for f in files):
            suggestions.append({
                "file": None,
                "suggestion": "Consider using async/await for I/O operations",
                "category": "async-operations"
            })
        
        return {
            "category": "performance",
            "score": 82,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "has_caching": has_caching,
                "async_usage": async_count > 0,
                "frontend_size": sum(f.get("lines", 0) for f in frontend_files)
            }
        }
    
    async def _review_testing(self, files: List[Dict[str, Any]], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """테스트 리뷰"""
        issues = []
        suggestions = []
        
        # 테스트 커버리지 체크
        coverage = test_result.get("coverage", {})
        line_coverage = coverage.get("line_coverage", 0)
        
        if line_coverage < 80:
            issues.append({
                "file": None,
                "line": None,
                "severity": ReviewSeverity.MAJOR.value,
                "category": "testing",
                "message": f"Test coverage ({line_coverage:.1f}%) is below 80% threshold",
                "rule": "low-coverage"
            })
        
        # 테스트 실패 체크
        test_summary = test_result.get("summary", {})
        if test_summary.get("failed", 0) > 0:
            issues.append({
                "file": None,
                "line": None,
                "severity": ReviewSeverity.CRITICAL.value,
                "category": "testing",
                "message": f"{test_summary['failed']} tests are failing",
                "rule": "failing-tests"
            })
        
        # 테스트 타입 체크
        test_suites = test_result.get("suites", [])
        test_types = [s["type"] for s in test_suites]
        
        if "unit" not in test_types:
            suggestions.append({
                "file": None,
                "suggestion": "Add unit tests for better code coverage",
                "category": "test-types"
            })
        
        if "integration" not in test_types and len(files) > 10:
            suggestions.append({
                "file": None,
                "suggestion": "Add integration tests to verify component interactions",
                "category": "test-types"
            })
        
        return {
            "category": "testing",
            "score": 78,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "line_coverage": line_coverage,
                "test_pass_rate": (test_summary.get("passed", 0) / test_summary.get("total_tests", 1) * 100) if test_summary.get("total_tests", 0) > 0 else 0,
                "test_types": len(set(test_types))
            }
        }
    
    async def _review_documentation(self, files: List[Dict[str, Any]], test_result: Dict[str, Any], planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """문서화 리뷰"""
        issues = []
        suggestions = []
        
        # README 체크
        has_readme = any("readme" in f["path"].lower() for f in files)
        if not has_readme:
            issues.append({
                "file": None,
                "line": None,
                "severity": ReviewSeverity.MAJOR.value,
                "category": "documentation",
                "message": "No README file found",
                "rule": "missing-readme"
            })
        
        # API 문서화 체크
        api_files = [f for f in files if "api" in f["path"].lower()]
        if api_files:
            # OpenAPI/Swagger 체크
            has_api_docs = any("swagger" in f.get("content", "").lower() or "openapi" in f.get("content", "").lower() for f in files)
            if not has_api_docs:
                suggestions.append({
                    "file": None,
                    "suggestion": "Add OpenAPI/Swagger documentation for API endpoints",
                    "category": "api-docs"
                })
        
        # 코드 주석 체크 (시뮬레이션)
        for file in files:
            if file.get("language") in ["python", "typescript", "javascript"]:
                content = file.get("content", "")
                # 간단한 주석 비율 체크
                comment_lines = content.count("#") + content.count("//") + content.count("/*")
                total_lines = file.get("lines", 1)
                comment_ratio = comment_lines / total_lines
                
                if comment_ratio < 0.1:  # 10% 미만
                    issues.append({
                        "file": file["path"],
                        "line": None,
                        "severity": ReviewSeverity.MINOR.value,
                        "category": "documentation",
                        "message": "Low comment density. Consider adding more inline documentation",
                        "rule": "low-comments"
                    })
        
        return {
            "category": "documentation",
            "score": 70,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "has_readme": has_readme,
                "has_api_docs": len(api_files) > 0
            }
        }
    
    def _calculate_metrics(self, files: List[Dict[str, Any]], test_result: Dict[str, Any]) -> Dict[str, Any]:
        """전체 메트릭 계산"""
        return {
            "total_lines": sum(f.get("lines", 0) for f in files),
            "file_count": len(files),
            "language_distribution": self._get_language_distribution(files),
            "test_coverage": test_result.get("coverage", {}).get("line_coverage", 0),
            "test_pass_rate": self._calculate_test_pass_rate(test_result),
            "complexity_score": self._calculate_complexity_score(files)
        }
    
    def _get_language_distribution(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """언어별 파일 분포"""
        distribution = {}
        for file in files:
            lang = file.get("language", "unknown")
            distribution[lang] = distribution.get(lang, 0) + 1
        return distribution
    
    def _calculate_test_pass_rate(self, test_result: Dict[str, Any]) -> float:
        """테스트 통과율 계산"""
        summary = test_result.get("summary", {})
        total = summary.get("total_tests", 0)
        passed = summary.get("passed", 0)
        
        return (passed / total * 100) if total > 0 else 0
    
    def _calculate_complexity_score(self, files: List[Dict[str, Any]]) -> float:
        """복잡도 점수 계산 (시뮬레이션)"""
        # 간단한 복잡도 계산: 파일 크기와 수를 기반으로
        avg_file_size = sum(f.get("lines", 0) for f in files) / len(files) if files else 0
        
        if avg_file_size < 100:
            return 1.0  # Low complexity
        elif avg_file_size < 300:
            return 2.0  # Medium complexity
        else:
            return 3.0  # High complexity
    
    def _determine_approval_status(self, review_result: Dict[str, Any]) -> str:
        """승인 상태 결정"""
        summary = review_result["summary"]
        
        # Critical 이슈가 있으면 거부
        if summary["critical"] > 0:
            return "rejected"
        
        # Major 이슈가 3개 이상이면 수정 필요
        if summary["major"] >= 3:
            return "needs_changes"
        
        # 전체 점수 계산 (카테고리 평균)
        category_scores = [cat["score"] for cat in review_result["categories"]]
        avg_score = sum(category_scores) / len(category_scores) if category_scores else 0
        
        if avg_score >= 80:
            return "approved"
        elif avg_score >= 70:
            return "approved_with_comments"
        else:
            return "needs_changes"
    
    def _generate_review_report(self, review_result: Dict[str, Any]) -> str:
        """리뷰 보고서 생성"""
        report = f"""# Code Review Report

## Summary
- **Review ID**: {review_result['review_id']}
- **Files Reviewed**: {review_result['files_reviewed']}
- **Approval Status**: **{review_result['approval_status'].upper().replace('_', ' ')}**

## Issues Summary
- **Critical**: {review_result['summary']['critical']} 🔴
- **Major**: {review_result['summary']['major']} 🟠
- **Minor**: {review_result['summary']['minor']} 🟡
- **Info**: {review_result['summary']['info']} 🔵
- **Total**: {review_result['summary']['total_issues']}

## Category Scores
"""
        
        for category in review_result["categories"]:
            report += f"### {category['category'].replace('_', ' ').title()}\n"
            report += f"- **Score**: {category['score']}/100\n"
            report += f"- **Issues**: {len(category.get('issues', []))}\n"
            report += f"- **Suggestions**: {len(category.get('suggestions', []))}\n\n"
        
        # 상세 이슈
        if review_result["issues"]:
            report += "## Detailed Issues\n"
            
            # 심각도별로 그룹화
            for severity in [ReviewSeverity.CRITICAL.value, ReviewSeverity.MAJOR.value, ReviewSeverity.MINOR.value]:
                severity_issues = [i for i in review_result["issues"] if i.get("severity") == severity]
                if severity_issues:
                    report += f"\n### {severity.title()} Issues\n"
                    for issue in severity_issues:
                        report += f"- **[{issue['category']}]** {issue['message']}\n"
                        if issue.get("file"):
                            report += f"  - File: `{issue['file']}`"
                            if issue.get("line"):
                                report += f" (line {issue['line']})"
                            report += "\n"
                        report += f"  - Rule: `{issue['rule']}`\n"
        
        # 개선 제안
        if review_result["suggestions"]:
            report += "\n## Improvement Suggestions\n"
            for suggestion in review_result["suggestions"]:
                report += f"- {suggestion['suggestion']}\n"
                if suggestion.get("file"):
                    report += f"  - File: `{suggestion['file']}`\n"
                report += f"  - Category: `{suggestion['category']}`\n"
        
        # 메트릭
        metrics = review_result["metrics"]
        report += f"\n## Metrics\n"
        report += f"- **Total Lines**: {metrics['total_lines']:,}\n"
        report += f"- **File Count**: {metrics['file_count']}\n"
        report += f"- **Test Coverage**: {metrics['test_coverage']:.1f}%\n"
        report += f"- **Test Pass Rate**: {metrics['test_pass_rate']:.1f}%\n"
        report += f"- **Complexity Score**: {metrics['complexity_score']:.1f}/3.0\n"
        
        # 언어 분포
        if metrics.get("language_distribution"):
            report += "\n### Language Distribution\n"
            for lang, count in metrics["language_distribution"].items():
                report += f"- {lang}: {count} files\n"
        
        report += f"\n---\n*Generated on: {review_result['timestamp']}*\n"
        
        return report

# 노드 인스턴스 생성
review_node = ReviewNode()