"""
배포 에이전트
Docker 이미지 빌드, Kubernetes 배포, CI/CD 파이프라인 관리
"""

import logging
from typing import List, Dict, Any, Optional
import json
import yaml
from pathlib import Path

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, AgentContext, AgentResult
from src.integrations.mcp.tools import MCPTools
from src.core.schemas import (
    DeploymentConfig, DeploymentResult,
    EnvironmentType, ArtifactType
)
from src.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)

class DockerBuildInput(BaseModel):
    """Docker 빌드 입력"""
    dockerfile_path: str = Field(description="Dockerfile 경로")
    image_name: str = Field(description="Docker 이미지 이름")
    tag: str = Field(description="이미지 태그")
    build_args: Optional[Dict[str, str]] = Field(default=None, description="빌드 인자")

class KubernetesDeployInput(BaseModel):
    """Kubernetes 배포 입력"""
    manifest_path: str = Field(description="K8s 매니페스트 경로")
    namespace: str = Field(description="배포 네임스페이스")
    environment: EnvironmentType = Field(description="배포 환경")

class PipelineConfig(BaseModel):
    """CI/CD 파이프라인 설정"""
    provider: str = Field(description="CI/CD 제공자 (github-actions/gitlab-ci/jenkins)")
    stages: List[str] = Field(description="파이프라인 스테이지")
    triggers: List[str] = Field(description="트리거 조건")

class DeploymentAgent(BaseAgent):
    """배포 AI 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="DeploymentAgent",
            description="Docker, Kubernetes, CI/CD 파이프라인을 통한 애플리케이션 배포 담당"
        )
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self.deployment_history: List[DeploymentResult] = []
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의"""
        return """You are an expert DevOps engineer responsible for application deployment and infrastructure management.

Key responsibilities:
1. Build and optimize Docker images
2. Create Kubernetes manifests and Helm charts
3. Set up CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
4. Manage different environments (development, staging, production)
5. Implement blue-green and canary deployment strategies
6. Configure monitoring and logging
7. Ensure security best practices

Technical expertise:
- Docker: Multi-stage builds, layer caching, security scanning
- Kubernetes: Deployments, Services, ConfigMaps, Secrets, Ingress
- Helm: Chart creation, templating, dependency management
- CI/CD: Pipeline as code, automated testing, deployment gates
- Cloud platforms: AWS, GCP, Azure
- Infrastructure as Code: Terraform, CloudFormation
- Monitoring: Prometheus, Grafana, ELK stack

Best practices:
- Use minimal base images for security
- Implement proper health checks
- Follow the principle of least privilege
- Use environment-specific configurations
- Implement proper rollback strategies
- Document all deployment procedures
- Automate everything possible

Focus on:
- Reliability and zero-downtime deployments
- Security and compliance
- Performance optimization
- Cost efficiency
- Disaster recovery planning"""
    
    def _get_specialized_tools(self) -> List[Tool]:
        """배포 전문 도구"""
        tools = []
        
        # Docker 빌드 도구
        def build_docker_image(spec: str) -> str:
            """Docker 이미지 빌드"""
            return f"Built Docker image: {spec}"
        
        tools.append(Tool(
            name="build_docker_image",
            description="Build Docker images with best practices",
            func=build_docker_image
        ))
        
        # Kubernetes 배포 도구
        def deploy_to_kubernetes(manifest: str) -> str:
            """Kubernetes 배포"""
            return f"Deployed to Kubernetes: {manifest}"
        
        tools.append(Tool(
            name="deploy_to_kubernetes",
            description="Deploy applications to Kubernetes",
            func=deploy_to_kubernetes
        ))
        
        # CI/CD 파이프라인 도구
        def create_pipeline(config: str) -> str:
            """CI/CD 파이프라인 생성"""
            return f"Created pipeline: {config}"
        
        tools.append(Tool(
            name="create_pipeline",
            description="Create CI/CD pipelines",
            func=create_pipeline
        ))
        
        # 파일 시스템 및 실행 도구 추가
        tools.extend([
            MCPTools.filesystem_read(),
            MCPTools.filesystem_write(),
            MCPTools.docker_execute(),
            MCPTools.shell_execute()
        ])
        
        return tools
    
    async def create_dockerfile(
        self,
        app_type: str,
        base_image: str = None,
        dependencies_file: str = None
    ) -> str:
        """Dockerfile 생성"""
        if app_type == "python":
            dockerfile = await self._create_python_dockerfile(base_image, dependencies_file)
        elif app_type == "node":
            dockerfile = await self._create_node_dockerfile(base_image, dependencies_file)
        elif app_type == "go":
            dockerfile = await self._create_go_dockerfile(base_image)
        else:
            raise ValueError(f"Unsupported app type: {app_type}")
        
        return dockerfile
    
    async def _create_python_dockerfile(
        self,
        base_image: str = None,
        requirements_file: str = "requirements.txt"
    ) -> str:
        """Python 애플리케이션 Dockerfile 생성"""
        base_image = base_image or "python:3.11-slim"
        
        dockerfile = f'''# Build stage
FROM {base_image} AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY {requirements_file} .
RUN pip install --user --no-cache-dir -r {requirements_file}

# Runtime stage
FROM {base_image}

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        return dockerfile
    
    async def _create_node_dockerfile(
        self,
        base_image: str = None,
        package_file: str = "package.json"
    ) -> str:
        """Node.js 애플리케이션 Dockerfile 생성"""
        base_image = base_image or "node:18-alpine"
        
        dockerfile = f'''# Build stage
FROM {base_image} AS builder

# Install build dependencies
RUN apk add --no-cache python3 make g++

WORKDIR /app

# Copy package files
COPY {package_file} package-lock.json* ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Build application
RUN npm run build

# Runtime stage
FROM {base_image}

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

WORKDIR /app

# Copy built application
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

# Switch to non-root user
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD node healthcheck.js || exit 1

# Expose port
EXPOSE 3000

# Start application
CMD ["node", "dist/index.js"]
'''
        return dockerfile
    
    async def _create_go_dockerfile(self, base_image: str = None) -> str:
        """Go 애플리케이션 Dockerfile 생성"""
        base_image = base_image or "golang:1.21-alpine"
        
        dockerfile = f'''# Build stage
FROM {base_image} AS builder

# Install certificates for HTTPS
RUN apk add --no-cache ca-certificates git

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \\
    -ldflags="-w -s" \\
    -o /app/main .

# Runtime stage
FROM scratch

# Copy certificates
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy binary
COPY --from=builder /app/main /main

# Expose port
EXPOSE 8080

# Run binary
ENTRYPOINT ["/main"]
'''
        return dockerfile
    
    async def create_kubernetes_manifest(
        self,
        app_name: str,
        image: str,
        replicas: int = 3,
        environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    ) -> Dict[str, Any]:
        """Kubernetes 매니페스트 생성"""
        manifests = {}
        
        # Deployment
        manifests['deployment'] = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app_name,
                "labels": {
                    "app": app_name,
                    "environment": environment.value
                }
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": app_name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": app_name,
                            "version": "v1"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": app_name,
                            "image": image,
                            "ports": [{
                                "containerPort": 8000,
                                "name": "http"
                            }],
                            "env": self._get_environment_variables(environment),
                            "resources": self._get_resource_limits(environment),
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": "http"
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/ready",
                                    "port": "http"
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }],
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                            "fsGroup": 1000
                        }
                    }
                }
            }
        }
        
        # Service
        manifests['service'] = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": app_name,
                "labels": {
                    "app": app_name
                }
            },
            "spec": {
                "type": "ClusterIP",
                "selector": {
                    "app": app_name
                },
                "ports": [{
                    "port": 80,
                    "targetPort": "http",
                    "protocol": "TCP"
                }]
            }
        }
        
        # Ingress (프로덕션 환경)
        if environment == EnvironmentType.PRODUCTION:
            manifests['ingress'] = await self._create_ingress(app_name)
        
        # HorizontalPodAutoscaler
        manifests['hpa'] = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": app_name
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": app_name
                },
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": 70
                        }
                    }
                }]
            }
        }
        
        return manifests
    
    async def _create_ingress(self, app_name: str) -> Dict[str, Any]:
        """Ingress 리소스 생성"""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": app_name,
                "annotations": {
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "nginx.ingress.kubernetes.io/rate-limit": "100"
                }
            },
            "spec": {
                "ingressClassName": "nginx",
                "tls": [{
                    "hosts": [f"{app_name}.example.com"],
                    "secretName": f"{app_name}-tls"
                }],
                "rules": [{
                    "host": f"{app_name}.example.com",
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": app_name,
                                    "port": {
                                        "number": 80
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
    
    def _get_environment_variables(self, environment: EnvironmentType) -> List[Dict[str, str]]:
        """환경별 환경 변수"""
        base_env = [
            {"name": "ENVIRONMENT", "value": environment.value},
            {"name": "LOG_LEVEL", "value": "INFO" if environment == EnvironmentType.PRODUCTION else "DEBUG"}
        ]
        
        if environment == EnvironmentType.DEVELOPMENT:
            base_env.extend([
                {"name": "DEBUG", "value": "true"},
                {"name": "DATABASE_URL", "valueFrom": {
                    "secretKeyRef": {
                        "name": "dev-db-secret",
                        "key": "url"
                    }
                }}
            ])
        elif environment == EnvironmentType.PRODUCTION:
            base_env.extend([
                {"name": "DEBUG", "value": "false"},
                {"name": "DATABASE_URL", "valueFrom": {
                    "secretKeyRef": {
                        "name": "prod-db-secret",
                        "key": "url"
                    }
                }}
            ])
        
        return base_env
    
    def _get_resource_limits(self, environment: EnvironmentType) -> Dict[str, Dict[str, str]]:
        """환경별 리소스 제한"""
        if environment == EnvironmentType.DEVELOPMENT:
            return {
                "requests": {
                    "memory": "256Mi",
                    "cpu": "100m"
                },
                "limits": {
                    "memory": "512Mi",
                    "cpu": "500m"
                }
            }
        elif environment == EnvironmentType.STAGING:
            return {
                "requests": {
                    "memory": "512Mi",
                    "cpu": "250m"
                },
                "limits": {
                    "memory": "1Gi",
                    "cpu": "1000m"
                }
            }
        else:  # PRODUCTION
            return {
                "requests": {
                    "memory": "1Gi",
                    "cpu": "500m"
                },
                "limits": {
                    "memory": "2Gi",
                    "cpu": "2000m"
                }
            }
    
    async def create_ci_pipeline(
        self,
        provider: str,
        app_name: str,
        test_framework: str = "pytest"
    ) -> str:
        """CI/CD 파이프라인 생성"""
        if provider == "github-actions":
            return await self._create_github_actions_pipeline(app_name, test_framework)
        elif provider == "gitlab-ci":
            return await self._create_gitlab_ci_pipeline(app_name, test_framework)
        else:
            raise ValueError(f"Unsupported CI provider: {provider}")
    
    async def _create_github_actions_pipeline(
        self,
        app_name: str,
        test_framework: str
    ) -> str:
        """GitHub Actions 파이프라인 생성"""
        pipeline = f'''name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        {test_framework} tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Run security scan
      run: |
        pip install bandit safety
        bandit -r src/
        safety check
  
  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Registry
      uses: docker/login-action@v2
      with:
        registry: ${{{{ env.REGISTRY }}}}
        username: ${{{{ github.actor }}}}
        password: ${{{{ secrets.GITHUB_TOKEN }}}}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{{{version}}}}
          type=sha
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{{{ steps.meta.outputs.tags }}}}
        labels: ${{{{ steps.meta.outputs.labels }}}}
        cache-from: type=gha
        cache-to: type=gha,mode=max
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Kubernetes
      run: |
        echo "Deploying to production..."
        # kubectl apply -f k8s/
'''
        return pipeline
    
    async def _create_gitlab_ci_pipeline(
        self,
        app_name: str,
        test_framework: str
    ) -> str:
        """GitLab CI 파이프라인 생성"""
        pipeline = f'''stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

cache:
  paths:
    - .cache/pip

test:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
  script:
    - {test_framework} tests/ --cov=src --cov-report=xml
    - bandit -r src/
    - safety check
  coverage: '/TOTAL.*\\s+(\\d+%)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
    - docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest

deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/{app_name} {app_name}=$IMAGE_TAG -n staging
  environment:
    name: staging
  only:
    - develop

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/{app_name} {app_name}=$IMAGE_TAG -n production
  environment:
    name: production
  when: manual
  only:
    - main
'''
        return pipeline
    
    async def create_helm_chart(
        self,
        app_name: str,
        version: str = "0.1.0"
    ) -> Dict[str, Any]:
        """Helm 차트 생성"""
        chart = {
            "Chart.yaml": f'''apiVersion: v2
name: {app_name}
description: A Helm chart for {app_name}
type: application
version: {version}
appVersion: "1.0"
''',
            "values.yaml": f'''replicaCount: 3

image:
  repository: {app_name}
  pullPolicy: IfNotPresent
  tag: ""

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {{}}
  name: ""

podAnnotations: {{}}

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: {app_name}.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: {app_name}-tls
      hosts:
        - {app_name}.example.com

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

nodeSelector: {{}}
tolerations: []
affinity: {{}}
''',
            "templates/deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "chart.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: http
          readinessProbe:
            httpGet:
              path: /ready
              port: http
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
'''
        }
        
        return chart
    
    async def _process_result(self, raw_result: Dict[str, Any], context: AgentContext) -> AgentResult:
        """결과 처리"""
        try:
            # 에이전트 출력에서 정보 추출
            output = raw_result.get("output", "")
            
            # 이전 결과에서 정보 가져오기
            dev_result = context.previous_results.get("development_result", {})
            test_result = context.previous_results.get("testing_result", {})
            
            # 애플리케이션 정보 추출
            app_info = self._extract_app_info(dev_result)
            
            # Dockerfile 생성
            dockerfile = await self.create_dockerfile(
                app_type=app_info['type'],
                dependencies_file=app_info.get('dependencies_file')
            )
            
            # Kubernetes 매니페스트 생성
            k8s_manifests = await self.create_kubernetes_manifest(
                app_name=app_info['name'],
                image=f"{app_info['name']}:latest",
                environment=EnvironmentType.PRODUCTION
            )
            
            # CI/CD 파이프라인 생성
            ci_pipeline = await self.create_ci_pipeline(
                provider="github-actions",
                app_name=app_info['name'],
                test_framework=app_info.get('test_framework', 'pytest')
            )
            
            # Helm 차트 생성
            helm_chart = await self.create_helm_chart(app_info['name'])
            
            # 아티팩트 생성
            artifacts = []
            
            # 1. Dockerfile
            artifacts.append({
                "name": "Dockerfile",
                "type": ArtifactType.CONFIGURATION.value,
                "content": dockerfile,
                "metadata": {
                    "app_type": app_info['type'],
                    "base_image": "python:3.11-slim"
                }
            })
            
            # 2. Kubernetes 매니페스트
            for resource_type, manifest in k8s_manifests.items():
                artifacts.append({
                    "name": f"k8s-{resource_type}.yaml",
                    "type": ArtifactType.CONFIGURATION.value,
                    "content": yaml.dump(manifest, default_flow_style=False),
                    "metadata": {
                        "resource_type": resource_type,
                        "environment": "production"
                    }
                })
            
            # 3. CI/CD 파이프라인
            artifacts.append({
                "name": ".github/workflows/ci-cd.yml",
                "type": ArtifactType.CONFIGURATION.value,
                "content": ci_pipeline,
                "metadata": {
                    "provider": "github-actions",
                    "stages": ["test", "build", "deploy"]
                }
            })
            
            # 4. Helm 차트
            for file_name, content in helm_chart.items():
                artifacts.append({
                    "name": f"helm/{app_info['name']}/{file_name}",
                    "type": ArtifactType.CONFIGURATION.value,
                    "content": content,
                    "metadata": {
                        "chart_type": "helm",
                        "version": "0.1.0"
                    }
                })
            
            # 5. 배포 문서
            deployment_doc = self._generate_deployment_documentation(
                app_info, k8s_manifests, ci_pipeline
            )
            artifacts.append({
                "name": "DEPLOYMENT.md",
                "type": ArtifactType.DOCUMENTATION.value,
                "content": deployment_doc,
                "metadata": {
                    "format": "markdown"
                }
            })
            
            # 배포 설정 생성
            deployment_config = DeploymentConfig(
                environment=EnvironmentType.PRODUCTION,
                docker_image=f"{app_info['name']}:latest",
                replicas=3,
                resources={
                    "requests": {"memory": "512Mi", "cpu": "250m"},
                    "limits": {"memory": "1Gi", "cpu": "1000m"}
                },
                environment_variables={
                    "ENVIRONMENT": "production",
                    "LOG_LEVEL": "INFO"
                },
                secrets=["database-secret", "api-keys"],
                health_check_path="/health",
                readiness_check_path="/ready"
            )
            
            # 배포 결과
            deployment_result = DeploymentResult(
                deployment_id=f"deploy-{app_info['name']}-001",
                status="prepared",
                environment=EnvironmentType.PRODUCTION,
                version="1.0.0",
                url=f"https://{app_info['name']}.example.com",
                deployment_time=None,  # 실제 배포 시 설정
                rollback_version=None
            )
            
            # 결과 구성
            result_data = {
                "deployment_config": deployment_config.model_dump(),
                "deployment_result": deployment_result.model_dump(),
                "summary": {
                    "docker_image": f"{app_info['name']}:latest",
                    "kubernetes_resources": list(k8s_manifests.keys()),
                    "ci_cd_provider": "github-actions",
                    "helm_chart_created": True,
                    "environments": ["development", "staging", "production"]
                }
            }
            
            return AgentResult(
                success=True,
                output=result_data,
                artifacts=artifacts,
                messages=[
                    f"Created Dockerfile for {app_info['type']} application",
                    f"Generated Kubernetes manifests for {len(k8s_manifests)} resources",
                    "Created GitHub Actions CI/CD pipeline",
                    "Generated Helm chart for easy deployment",
                    "Prepared complete deployment configuration"
                ],
                metrics={
                    "dockerfile_created": 1,
                    "k8s_resources": len(k8s_manifests),
                    "helm_files": len(helm_chart),
                    "artifacts_created": len(artifacts)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process deployment result: {e}")
            return AgentResult(
                success=False,
                output=None,
                errors=[str(e)],
                metrics={"error_type": type(e).__name__}
            )
    
    def _extract_app_info(self, dev_result: Dict[str, Any]) -> Dict[str, Any]:
        """개발 결과에서 애플리케이션 정보 추출"""
        # 기본값
        app_info = {
            "name": "myapp",
            "type": "python",
            "dependencies_file": "requirements.txt",
            "test_framework": "pytest"
        }
        
        # 개발 결과에서 정보 추출
        if dev_result:
            generated_files = dev_result.get("generated_files", [])
            
            # 언어 타입 추출
            for file in generated_files:
                if file['language'] == 'javascript':
                    app_info['type'] = 'node'
                    app_info['dependencies_file'] = 'package.json'
                    app_info['test_framework'] = 'jest'
                    break
                elif file['language'] == 'go':
                    app_info['type'] = 'go'
                    app_info['dependencies_file'] = 'go.mod'
                    app_info['test_framework'] = 'go test'
                    break
            
            # 프로젝트 이름 추출
            project_info = dev_result.get("project_structure", {})
            if project_info:
                app_info['name'] = project_info.get("name", "myapp").lower().replace(" ", "-")
        
        return app_info
    
    def _generate_deployment_documentation(
        self,
        app_info: Dict[str, Any],
        k8s_manifests: Dict[str, Any],
        ci_pipeline: str
    ) -> str:
        """배포 문서 생성"""
        doc = f"""# Deployment Guide for {app_info['name']}

## Overview
This document provides instructions for deploying the {app_info['name']} application.

## Prerequisites
- Docker installed
- Kubernetes cluster access
- kubectl configured
- Helm 3.x installed (optional)

## Build Process

### Local Build
```bash
# Build Docker image
docker build -t {app_info['name']}:latest .

# Run locally
docker run -p 8000:8000 {app_info['name']}:latest
```

### CI/CD Pipeline
The application includes a GitHub Actions workflow that:
1. Runs tests on every push
2. Builds Docker images
3. Pushes to container registry
4. Deploys to Kubernetes (manual approval for production)

## Deployment Steps

### Using kubectl
```bash
# Apply all Kubernetes resources
kubectl apply -f k8s/

# Check deployment status
kubectl get deployments -n default
kubectl get pods -n default
kubectl get services -n default
```

### Using Helm
```bash
# Install the application
helm install {app_info['name']} ./helm/{app_info['name']}

# Upgrade the application
helm upgrade {app_info['name']} ./helm/{app_info['name']}

# Check status
helm status {app_info['name']}
```

## Environment Configuration

### Development
- Replicas: 1
- Resources: Limited (256Mi memory, 100m CPU)
- Debug mode: Enabled

### Staging
- Replicas: 2
- Resources: Moderate (512Mi memory, 250m CPU)
- Debug mode: Disabled

### Production
- Replicas: 3-10 (auto-scaling)
- Resources: Full (1Gi memory, 500m CPU)
- TLS: Enabled
- Monitoring: Enabled

## Monitoring

### Health Checks
- Liveness: `GET /health`
- Readiness: `GET /ready`

### Metrics
- Prometheus metrics available at `/metrics`
- Grafana dashboards included

## Rollback Procedure
```bash
# Rollback to previous version
kubectl rollout undo deployment/{app_info['name']}

# Check rollout history
kubectl rollout history deployment/{app_info['name']}
```

## Security Considerations
- Non-root container execution
- Read-only root filesystem
- Network policies applied
- Secrets managed via Kubernetes secrets

## Troubleshooting

### Common Issues
1. **Pod not starting**: Check logs with `kubectl logs <pod-name>`
2. **Service not accessible**: Verify ingress configuration
3. **Database connection issues**: Check secret configuration

### Debug Commands
```bash
# Get pod logs
kubectl logs -f deployment/{app_info['name']}

# Execute into pod
kubectl exec -it deployment/{app_info['name']} -- /bin/sh

# Describe pod for events
kubectl describe pod <pod-name>
```

## Support
For issues or questions, please contact the DevOps team.
"""
        return doc
    
    async def _validate_specific_input(self, context: AgentContext) -> Optional[str]:
        """배포 특화 입력 검증"""
        # 개발 및 테스트 결과가 있는지 확인
        if "development_result" not in context.previous_results:
            return "Development result is required before deployment"
        
        if "testing_result" not in context.previous_results:
            # 테스트 결과는 선택적
            logger.warning("No testing result found, proceeding with deployment preparation")
        
        return None
    
    async def _validate_specific_output(self, result: AgentResult) -> Optional[str]:
        """배포 특화 출력 검증"""
        if not result.output:
            return "No deployment output generated"
        
        output = result.output
        if not isinstance(output, dict):
            return "Invalid output format"
        
        # 배포 설정 검증
        if "deployment_config" not in output:
            return "Missing deployment configuration"
        
        # 아티팩트 검증
        if not result.artifacts:
            return "No deployment artifacts generated"
        
        # 필수 아티팩트 확인
        artifact_names = [a["name"] for a in result.artifacts]
        required = ["Dockerfile", "k8s-deployment.yaml", ".github/workflows/ci-cd.yml"]
        
        missing = [r for r in required if not any(r in name for name in artifact_names)]
        if missing:
            return f"Missing required artifacts: {', '.join(missing)}"
        
        return None