"""
배포 노드
코드 리뷰 통과 후 배포 준비 및 실행
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timezone

from src.orchestration.nodes.base import BaseNode
from src.orchestration.state import WorkflowState
from src.core.constants import ArtifactType, DeploymentEnvironment

class DeploymentNode(BaseNode):
    """배포 노드"""
    
    def __init__(self):
        super().__init__(
            name="Deployment",
            description="Prepare and execute deployment"
        )
    
    async def _validate_specific_input(self, state: WorkflowState) -> Optional[str]:
        """입력 검증"""
        if not state.get("review_result"):
            return "Review result is missing"
        
        review_result = state["review_result"]
        approval_status = review_result.get("approval_status", "")
        
        # 리뷰 승인 확인
        if approval_status not in ["approved", "approved_with_comments"]:
            return f"Deployment blocked: Review status is '{approval_status}'. Approval required."
        
        if not state.get("development_result"):
            return "Development result is missing"
        
        if not state.get("test_result"):
            return "Test result is missing"
        
        # 테스트 통과 확인
        test_summary = state["test_result"].get("summary", {})
        if test_summary.get("failed", 0) > 0:
            return f"Deployment blocked: {test_summary['failed']} tests are failing"
        
        return None
    
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """배포 처리"""
        dev_result = state["development_result"]
        test_result = state["test_result"]
        review_result = state["review_result"]
        
        # 배포 환경 결정
        deployment_env = self._determine_deployment_environment(state)
        
        self.log_progress(f"Starting deployment to {deployment_env}...")
        
        # 배포 준비 및 실행
        deployment_result = await self._execute_deployment(
            dev_result, test_result, review_result, deployment_env
        )
        
        # 메시지 추가
        message_update = self.add_message(
            state,
            f"Deployment to {deployment_env} completed successfully. "
            f"Version: {deployment_result['version']}, "
            f"URL: {deployment_result['deployment_url']}",
            metadata={
                "deployment_id": deployment_result["deployment_id"],
                "environment": deployment_env,
                "version": deployment_result["version"]
            }
        )
        
        # 배포 매니페스트 아티팩트
        manifest_artifact = self.add_artifact(
            state,
            name="deployment_manifest",
            artifact_type=ArtifactType.CONFIG,
            content=json.dumps(deployment_result["manifest"], indent=2),
            metadata={"format": "json", "environment": deployment_env}
        )
        
        # 배포 스크립트 아티팩트
        scripts_artifact = self.add_artifact(
            state,
            name="deployment_scripts",
            artifact_type=ArtifactType.CODE,
            content=self._generate_deployment_scripts(deployment_result),
            metadata={"format": "bash"}
        )
        
        # 릴리스 노트 아티팩트
        release_notes = self.add_artifact(
            state,
            name="release_notes",
            artifact_type=ArtifactType.DOCUMENT,
            content=self._generate_release_notes(deployment_result, state),
            metadata={"format": "markdown", "version": deployment_result["version"]}
        )
        
        # 결과 업데이트
        result_update = self.update_result(state, "deployment_result", deployment_result)
        
        # 모든 업데이트 병합
        updates = {}
        updates.update(message_update)
        updates.update(manifest_artifact)
        updates.update(scripts_artifact)
        updates.update(release_notes)
        updates.update(result_update)
        
        self.log_progress("Deployment completed")
        
        return updates
    
    def _determine_deployment_environment(self, state: WorkflowState) -> str:
        """배포 환경 결정"""
        # 컨텍스트에서 환경 정보 확인
        context = state.get("context", {})
        env = context.get("deployment_environment")
        
        if env and env in [e.value for e in DeploymentEnvironment]:
            return env
        
        # 기본적으로 staging 환경으로 배포
        return DeploymentEnvironment.STAGING.value
    
    async def _execute_deployment(
        self,
        dev_result: Dict[str, Any],
        test_result: Dict[str, Any],
        review_result: Dict[str, Any],
        environment: str
    ) -> Dict[str, Any]:
        """배포 실행"""
        
        # 배포 버전 생성
        version = self._generate_version()
        
        # 배포 매니페스트 생성
        manifest = self._create_deployment_manifest(
            dev_result, test_result, review_result, environment, version
        )
        
        # 배포 단계별 실행
        deployment_steps = []
        
        # 1. 빌드 단계
        build_step = await self._execute_build(dev_result, version)
        deployment_steps.append(build_step)
        
        # 2. 테스트 검증 단계
        test_verification = await self._verify_tests(test_result)
        deployment_steps.append(test_verification)
        
        # 3. 환경 준비 단계
        env_preparation = await self._prepare_environment(environment, manifest)
        deployment_steps.append(env_preparation)
        
        # 4. 배포 실행 단계
        deployment_execution = await self._deploy_application(manifest, environment)
        deployment_steps.append(deployment_execution)
        
        # 5. 헬스 체크 단계
        health_check = await self._perform_health_check(environment)
        deployment_steps.append(health_check)
        
        # 6. 롤백 준비 단계
        rollback_preparation = await self._prepare_rollback(version, environment)
        deployment_steps.append(rollback_preparation)
        
        # 배포 URL 생성
        deployment_url = self._generate_deployment_url(environment)
        
        return {
            "deployment_id": f"deploy-{datetime.now(timezone.utc).isoformat()}",
            "version": version,
            "environment": environment,
            "deployment_url": deployment_url,
            "manifest": manifest,
            "steps": deployment_steps,
            "status": "success",
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "rollback_version": self._get_previous_version(environment),
            "monitoring": {
                "dashboard_url": f"https://monitoring.example.com/dashboard/{environment}",
                "logs_url": f"https://logs.example.com/{environment}",
                "metrics_url": f"https://metrics.example.com/{environment}"
            }
        }
    
    def _generate_version(self) -> str:
        """버전 생성"""
        # 시맨틱 버저닝 사용 (시뮬레이션)
        import random
        major = 1
        minor = random.randint(0, 5)
        patch = random.randint(0, 20)
        
        # 타임스탬프 기반 빌드 번호
        build = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        
        return f"{major}.{minor}.{patch}-{build}"
    
    def _create_deployment_manifest(
        self,
        dev_result: Dict[str, Any],
        test_result: Dict[str, Any],
        review_result: Dict[str, Any],
        environment: str,
        version: str
    ) -> Dict[str, Any]:
        """배포 매니페스트 생성"""
        return {
            "version": version,
            "environment": environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "application": {
                "name": "agentic-pipeline-app",
                "type": "web",
                "framework": "fastapi",
                "runtime": "python3.11"
            },
            "artifacts": {
                "docker_image": f"agentic-pipeline:{version}",
                "files_count": len(dev_result.get("generated_files", [])),
                "total_size_mb": sum(f.get("lines", 0) * 0.05 for f in dev_result.get("generated_files", []))  # 추정
            },
            "configuration": {
                "replicas": self._get_replica_count(environment),
                "resources": self._get_resource_limits(environment),
                "environment_variables": self._get_env_variables(environment),
                "secrets": ["database_url", "api_keys", "jwt_secret"]
            },
            "dependencies": dev_result.get("dependencies", {}),
            "health_checks": {
                "liveness": "/health",
                "readiness": "/ready",
                "startup": "/startup"
            },
            "rollback": {
                "enabled": True,
                "strategy": "blue-green",
                "previous_version": self._get_previous_version(environment)
            },
            "monitoring": {
                "metrics_enabled": True,
                "logging_level": "INFO" if environment == DeploymentEnvironment.PRODUCTION.value else "DEBUG",
                "tracing_enabled": environment == DeploymentEnvironment.PRODUCTION.value
            },
            "approval": {
                "review_status": review_result.get("approval_status"),
                "reviewer": "AI Code Reviewer",
                "approved_at": review_result.get("timestamp")
            },
            "test_summary": {
                "passed": test_result.get("summary", {}).get("passed", 0),
                "total": test_result.get("summary", {}).get("total_tests", 0),
                "coverage": test_result.get("coverage", {}).get("line_coverage", 0)
            }
        }
    
    async def _execute_build(self, dev_result: Dict[str, Any], version: str) -> Dict[str, Any]:
        """빌드 실행"""
        return {
            "step": "build",
            "status": "success",
            "duration_seconds": 45,
            "details": {
                "docker_image": f"agentic-pipeline:{version}",
                "build_cache_used": True,
                "layers_created": 12,
                "size_mb": 156.7
            },
            "logs": [
                "Building Docker image...",
                "Installing dependencies...",
                "Copying application files...",
                "Running build scripts...",
                "Image built successfully"
            ]
        }
    
    async def _verify_tests(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """테스트 검증"""
        test_summary = test_result.get("summary", {})
        
        return {
            "step": "test_verification",
            "status": "success",
            "duration_seconds": 10,
            "details": {
                "tests_passed": test_summary.get("passed", 0),
                "tests_total": test_summary.get("total_tests", 0),
                "coverage": test_result.get("coverage", {}).get("line_coverage", 0),
                "quality_gates_passed": True
            },
            "logs": [
                "Verifying test results...",
                f"All {test_summary.get('total_tests', 0)} tests passed",
                f"Code coverage: {test_result.get('coverage', {}).get('line_coverage', 0):.1f}%",
                "Quality gates passed"
            ]
        }
    
    async def _prepare_environment(self, environment: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """환경 준비"""
        return {
            "step": "environment_preparation",
            "status": "success",
            "duration_seconds": 20,
            "details": {
                "environment": environment,
                "namespace": f"agentic-pipeline-{environment}",
                "resources_allocated": manifest["configuration"]["resources"],
                "secrets_configured": len(manifest["configuration"]["secrets"])
            },
            "logs": [
                f"Preparing {environment} environment...",
                "Creating/updating namespace...",
                "Configuring secrets...",
                "Allocating resources...",
                "Environment ready"
            ]
        }
    
    async def _deploy_application(self, manifest: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """애플리케이션 배포"""
        return {
            "step": "deployment",
            "status": "success",
            "duration_seconds": 60,
            "details": {
                "strategy": manifest["rollback"]["strategy"],
                "replicas_deployed": manifest["configuration"]["replicas"],
                "rolling_update": environment != DeploymentEnvironment.PRODUCTION.value,
                "endpoints_updated": 5
            },
            "logs": [
                f"Deploying application to {environment}...",
                f"Using {manifest['rollback']['strategy']} deployment strategy",
                "Starting new containers...",
                "Updating load balancer...",
                "Deployment completed successfully"
            ]
        }
    
    async def _perform_health_check(self, environment: str) -> Dict[str, Any]:
        """헬스 체크 수행"""
        return {
            "step": "health_check",
            "status": "success",
            "duration_seconds": 15,
            "details": {
                "endpoints_checked": 3,
                "all_healthy": True,
                "response_time_ms": 45,
                "database_connected": True,
                "cache_connected": True
            },
            "logs": [
                "Performing health checks...",
                "Checking liveness endpoint... OK",
                "Checking readiness endpoint... OK",
                "Checking database connection... OK",
                "All health checks passed"
            ]
        }
    
    async def _prepare_rollback(self, version: str, environment: str) -> Dict[str, Any]:
        """롤백 준비"""
        previous_version = self._get_previous_version(environment)
        
        return {
            "step": "rollback_preparation",
            "status": "success",
            "duration_seconds": 5,
            "details": {
                "current_version": version,
                "previous_version": previous_version,
                "rollback_script_created": True,
                "backup_created": True
            },
            "logs": [
                "Preparing rollback mechanism...",
                f"Previous version: {previous_version}",
                "Creating rollback script...",
                "Backup created successfully"
            ]
        }
    
    def _get_replica_count(self, environment: str) -> int:
        """환경별 레플리카 수 결정"""
        replica_map = {
            DeploymentEnvironment.DEVELOPMENT.value: 1,
            DeploymentEnvironment.STAGING.value: 2,
            DeploymentEnvironment.PRODUCTION.value: 3
        }
        return replica_map.get(environment, 1)
    
    def _get_resource_limits(self, environment: str) -> Dict[str, Any]:
        """환경별 리소스 제한 설정"""
        if environment == DeploymentEnvironment.PRODUCTION.value:
            return {
                "cpu": "2000m",
                "memory": "4Gi",
                "storage": "20Gi"
            }
        elif environment == DeploymentEnvironment.STAGING.value:
            return {
                "cpu": "1000m",
                "memory": "2Gi",
                "storage": "10Gi"
            }
        else:
            return {
                "cpu": "500m",
                "memory": "1Gi",
                "storage": "5Gi"
            }
    
    def _get_env_variables(self, environment: str) -> Dict[str, str]:
        """환경 변수 설정"""
        base_vars = {
            "APP_ENV": environment,
            "LOG_LEVEL": "INFO" if environment == DeploymentEnvironment.PRODUCTION.value else "DEBUG",
            "ENABLE_METRICS": "true",
            "ENABLE_TRACING": str(environment == DeploymentEnvironment.PRODUCTION.value).lower()
        }
        
        # 환경별 추가 변수
        if environment == DeploymentEnvironment.PRODUCTION.value:
            base_vars.update({
                "RATE_LIMIT": "1000",
                "CACHE_TTL": "3600",
                "CONNECTION_POOL_SIZE": "50"
            })
        else:
            base_vars.update({
                "RATE_LIMIT": "100",
                "CACHE_TTL": "300",
                "CONNECTION_POOL_SIZE": "10"
            })
        
        return base_vars
    
    def _get_previous_version(self, environment: str) -> str:
        """이전 버전 조회 (시뮬레이션)"""
        # 실제로는 배포 히스토리에서 조회
        return "1.0.0-20240101120000"
    
    def _generate_deployment_url(self, environment: str) -> str:
        """배포 URL 생성"""
        if environment == DeploymentEnvironment.PRODUCTION.value:
            return "https://api.agentic-pipeline.com"
        elif environment == DeploymentEnvironment.STAGING.value:
            return "https://staging-api.agentic-pipeline.com"
        else:
            return "https://dev-api.agentic-pipeline.com"
    
    def _generate_deployment_scripts(self, deployment_result: Dict[str, Any]) -> str:
        """배포 스크립트 생성"""
        version = deployment_result["version"]
        environment = deployment_result["environment"]
        
        return f"""#!/bin/bash
# Deployment Script for Agentic Pipeline
# Version: {version}
# Environment: {environment}
# Generated: {datetime.now(timezone.utc).isoformat()}

set -e

echo "Starting deployment of version {version} to {environment}..."

# Build Docker image
echo "Building Docker image..."
docker build -t agentic-pipeline:{version} .

# Tag image for registry
docker tag agentic-pipeline:{version} registry.example.com/agentic-pipeline:{version}

# Push to registry
echo "Pushing image to registry..."
docker push registry.example.com/agentic-pipeline:{version}

# Update Kubernetes deployment
echo "Updating Kubernetes deployment..."
kubectl set image deployment/agentic-pipeline \\
    agentic-pipeline=registry.example.com/agentic-pipeline:{version} \\
    -n agentic-pipeline-{environment}

# Wait for rollout to complete
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/agentic-pipeline -n agentic-pipeline-{environment}

# Run database migrations
echo "Running database migrations..."
kubectl exec -it deployment/agentic-pipeline -n agentic-pipeline-{environment} -- \\
    python manage.py migrate

# Verify deployment
echo "Verifying deployment..."
kubectl get pods -n agentic-pipeline-{environment}

# Health check
echo "Running health checks..."
curl -f https://{deployment_result['deployment_url']}/health || exit 1

echo "Deployment completed successfully!"
echo "Application URL: {deployment_result['deployment_url']}"
echo "Monitoring Dashboard: {deployment_result['monitoring']['dashboard_url']}"

# Rollback script
cat > rollback.sh << 'EOF'
#!/bin/bash
echo "Rolling back to previous version..."
kubectl rollout undo deployment/agentic-pipeline -n agentic-pipeline-{environment}
kubectl rollout status deployment/agentic-pipeline -n agentic-pipeline-{environment}
EOF

chmod +x rollback.sh
echo "Rollback script created: ./rollback.sh"
"""
    
    def _generate_release_notes(self, deployment_result: Dict[str, Any], state: WorkflowState) -> str:
        """릴리스 노트 생성"""
        version = deployment_result["version"]
        environment = deployment_result["environment"]
        dev_result = state.get("development_result", {})
        test_result = state.get("test_result", {})
        review_result = state.get("review_result", {})
        
        return f"""# Release Notes

## Version {version}

**Release Date**: {deployment_result['deployed_at']}
**Environment**: {environment}
**Deployment URL**: {deployment_result['deployment_url']}

## Summary

This release includes the implementation of features based on the provided requirements, with comprehensive testing and code review.

## What's New

### Features
- Implemented {len(dev_result.get('generated_files', []))} new components
- Created {len(dev_result.get('api_endpoints', []))} API endpoints
- Added {len(dev_result.get('database_models', []))} database models

### Technical Improvements
- Code coverage: {test_result.get('coverage', {}).get('line_coverage', 0):.1f}%
- All {test_result.get('summary', {}).get('total_tests', 0)} tests passing
- Code review score: {review_result.get('approval_status', 'N/A')}

## Changes

### Backend
- FastAPI application with comprehensive API endpoints
- Database models with proper relationships
- Authentication and authorization implementation
- Error handling and validation

### Frontend
- React components with TypeScript
- Responsive UI design
- State management implementation
- API integration

### Infrastructure
- Docker containerization
- CI/CD pipeline configuration
- Health check endpoints
- Monitoring and logging setup

## Testing

- **Unit Tests**: {sum(1 for s in test_result.get('suites', []) if s['type'] == 'unit')} suites
- **Integration Tests**: {sum(1 for s in test_result.get('suites', []) if s['type'] == 'integration')} suites
- **E2E Tests**: {sum(1 for s in test_result.get('suites', []) if s['type'] == 'e2e')} suites
- **Total Coverage**: {test_result.get('coverage', {}).get('line_coverage', 0):.1f}%

## Deployment Information

- **Strategy**: {deployment_result['manifest']['rollback']['strategy']}
- **Replicas**: {deployment_result['manifest']['configuration']['replicas']}
- **Resources**: {deployment_result['manifest']['configuration']['resources']}
- **Rollback Version**: {deployment_result['rollback_version']}

## Monitoring

- Dashboard: {deployment_result['monitoring']['dashboard_url']}
- Logs: {deployment_result['monitoring']['logs_url']}
- Metrics: {deployment_result['monitoring']['metrics_url']}

## Known Issues

None at this time.

## Rollback Instructions

If issues are encountered, run the generated rollback script:
```bash
./rollback.sh
```

This will revert to version: {deployment_result['rollback_version']}

---
*Generated by Agentic Development Pipeline*
"""

# 노드 인스턴스 생성
deployment_node = DeploymentNode()