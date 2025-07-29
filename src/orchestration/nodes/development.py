"""
개발 노드
계획에 따라 실제 코드 구현
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from src.orchestration.nodes.base import BaseNode
from src.orchestration.state import WorkflowState
from src.core.constants import ArtifactType, ProgrammingLanguage, Framework

class DevelopmentNode(BaseNode):
    """개발 구현 노드"""
    
    def __init__(self):
        super().__init__(
            name="Development",
            description="Implement code based on planning"
        )
    
    async def _validate_specific_input(self, state: WorkflowState) -> Optional[str]:
        """입력 검증"""
        if not state.get("planning_result"):
            return "Planning result is missing"
        
        plan = state["planning_result"]
        if "tasks" not in plan or not plan["tasks"]:
            return "No tasks found in planning result"
        
        return None
    
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """코드 개발 처리"""
        plan = state["planning_result"]
        requirements = state["requirements"]
        
        self.log_progress("Starting development implementation...")
        
        # 개발 실행
        dev_result = await self._implement_development(plan, requirements)
        
        # 메시지 추가
        message_update = self.add_message(
            state,
            f"Development completed: {len(dev_result['generated_files'])} files generated, "
            f"{len(dev_result['api_endpoints'])} API endpoints created",
            metadata={
                "files_count": len(dev_result['generated_files']),
                "endpoints_count": len(dev_result['api_endpoints']),
                "total_lines": sum(f.get("lines", 0) for f in dev_result['generated_files'])
            }
        )
        
        # 생성된 파일들을 아티팩트로 추가
        artifacts_updates = {}
        for file_info in dev_result['generated_files']:
            artifact = self.add_artifact(
                state,
                name=file_info['path'],
                artifact_type=ArtifactType.CODE,
                content=file_info['content'],
                metadata={
                    "language": file_info.get("language", "unknown"),
                    "lines": file_info.get("lines", 0),
                    "purpose": file_info.get("description", "")
                }
            )
            # 아티팩트 업데이트 병합
            if "artifacts" in artifact:
                if "artifacts" not in artifacts_updates:
                    artifacts_updates["artifacts"] = []
                artifacts_updates["artifacts"].extend(artifact["artifacts"])
        
        # API 문서 아티팩트
        if dev_result['api_endpoints']:
            api_doc = self.add_artifact(
                state,
                name="api_documentation",
                artifact_type=ArtifactType.DOCUMENT,
                content=json.dumps(dev_result['api_endpoints'], indent=2),
                metadata={"format": "openapi", "version": "3.0"}
            )
            if "artifacts" in api_doc:
                artifacts_updates["artifacts"].extend(api_doc["artifacts"])
        
        # 결과 업데이트
        result_update = self.update_result(state, "development_result", dev_result)
        
        # 모든 업데이트 병합
        updates = {}
        updates.update(message_update)
        updates.update(artifacts_updates)
        updates.update(result_update)
        
        self.log_progress("Development implementation completed")
        
        return updates
    
    async def _implement_development(self, plan: Dict[str, Any], requirements: str) -> Dict[str, Any]:
        """개발 구현 실행"""
        tasks = plan.get("tasks", [])
        architecture = plan.get("architecture", {})
        
        # 카테고리별 태스크 분류
        frontend_tasks = [t for t in tasks if t.get("category") == "frontend"]
        backend_tasks = [t for t in tasks if t.get("category") == "backend"]
        infra_tasks = [t for t in tasks if t.get("category") == "infrastructure"]
        
        # 개발 결과 생성
        generated_files = []
        api_endpoints = []
        database_models = []
        
        # 백엔드 개발
        if backend_tasks:
            backend_files = await self._develop_backend(backend_tasks, architecture)
            generated_files.extend(backend_files["files"])
            api_endpoints.extend(backend_files["endpoints"])
            database_models.extend(backend_files["models"])
        
        # 프론트엔드 개발
        if frontend_tasks:
            frontend_files = await self._develop_frontend(frontend_tasks, architecture)
            generated_files.extend(frontend_files)
        
        # 인프라 설정
        if infra_tasks:
            infra_files = await self._develop_infrastructure(infra_tasks)
            generated_files.extend(infra_files)
        
        # 의존성 정리
        dependencies = self._collect_dependencies(generated_files)
        
        return {
            "generated_files": generated_files,
            "api_endpoints": api_endpoints,
            "database_models": database_models,
            "dependencies": dependencies,
            "documentation": self._generate_documentation(generated_files, api_endpoints),
            "summary": {
                "total_files": len(generated_files),
                "total_endpoints": len(api_endpoints),
                "total_models": len(database_models),
                "languages_used": list(set(f.get("language", "") for f in generated_files))
            }
        }
    
    async def _develop_backend(self, tasks: List[Dict[str, Any]], architecture: Dict[str, Any]) -> Dict[str, Any]:
        """백엔드 개발"""
        files = []
        endpoints = []
        models = []
        
        # FastAPI 애플리케이션 생성
        main_app = self._generate_fastapi_app()
        files.append({
            "path": "backend/main.py",
            "content": main_app,
            "language": ProgrammingLanguage.PYTHON.value,
            "lines": len(main_app.split("\n")),
            "description": "Main FastAPI application"
        })
        
        # 데이터베이스 모델
        if any("database" in t.get("name", "").lower() for t in tasks):
            model_code = self._generate_database_models()
            files.append({
                "path": "backend/models.py",
                "content": model_code,
                "language": ProgrammingLanguage.PYTHON.value,
                "lines": len(model_code.split("\n")),
                "description": "Database models"
            })
            models.extend([
                {"name": "User", "fields": ["id", "email", "name", "created_at"]},
                {"name": "Task", "fields": ["id", "title", "description", "status", "user_id"]}
            ])
        
        # API 엔드포인트
        for task in tasks:
            if "api" in task.get("name", "").lower():
                endpoint_code = self._generate_api_endpoint(task["name"])
                endpoint_name = task["name"].replace(" ", "_").lower()
                
                files.append({
                    "path": f"backend/routes/{endpoint_name}.py",
                    "content": endpoint_code,
                    "language": ProgrammingLanguage.PYTHON.value,
                    "lines": len(endpoint_code.split("\n")),
                    "description": f"API endpoint for {task['name']}"
                })
                
                endpoints.append({
                    "path": f"/api/v1/{endpoint_name}",
                    "method": "POST",
                    "description": f"Endpoint for {task['name']}",
                    "request_body": {"type": "object"},
                    "response": {"type": "object", "status_code": 200}
                })
        
        return {
            "files": files,
            "endpoints": endpoints,
            "models": models
        }
    
    async def _develop_frontend(self, tasks: List[Dict[str, Any]], architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """프론트엔드 개발"""
        files = []
        
        # React 애플리케이션 구조
        app_component = self._generate_react_app()
        files.append({
            "path": "frontend/src/App.tsx",
            "content": app_component,
            "language": ProgrammingLanguage.TYPESCRIPT.value,
            "lines": len(app_component.split("\n")),
            "description": "Main React application component"
        })
        
        # 컴포넌트 생성
        for task in tasks:
            if "ui" in task.get("name", "").lower():
                component_name = task["name"].replace(" ", "").replace("Implement", "")
                component_code = self._generate_react_component(component_name)
                
                files.append({
                    "path": f"frontend/src/components/{component_name}.tsx",
                    "content": component_code,
                    "language": ProgrammingLanguage.TYPESCRIPT.value,
                    "lines": len(component_code.split("\n")),
                    "description": f"React component for {task['name']}"
                })
        
        # 스타일 파일
        styles = self._generate_styles()
        files.append({
            "path": "frontend/src/styles/main.css",
            "content": styles,
            "language": "css",
            "lines": len(styles.split("\n")),
            "description": "Main stylesheet"
        })
        
        return files
    
    async def _develop_infrastructure(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """인프라 설정 개발"""
        files = []
        
        # Docker 설정
        dockerfile = self._generate_dockerfile()
        files.append({
            "path": "Dockerfile",
            "content": dockerfile,
            "language": "dockerfile",
            "lines": len(dockerfile.split("\n")),
            "description": "Docker container configuration"
        })
        
        # Docker Compose
        compose = self._generate_docker_compose()
        files.append({
            "path": "docker-compose.yml",
            "content": compose,
            "language": ProgrammingLanguage.YAML.value,
            "lines": len(compose.split("\n")),
            "description": "Docker Compose configuration"
        })
        
        # CI/CD 파이프라인
        for task in tasks:
            if "ci/cd" in task.get("name", "").lower():
                pipeline = self._generate_ci_pipeline()
                files.append({
                    "path": ".github/workflows/main.yml",
                    "content": pipeline,
                    "language": ProgrammingLanguage.YAML.value,
                    "lines": len(pipeline.split("\n")),
                    "description": "CI/CD pipeline configuration"
                })
        
        return files
    
    def _generate_fastapi_app(self) -> str:
        """FastAPI 애플리케이션 코드 생성"""
        return '''"""
Main FastAPI application
Generated by Agentic Development Pipeline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="Generated API",
    version="1.0.0",
    description="API generated by Agentic Development Pipeline"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Generated API",
        "version": "1.0.0"
    }

# Example model
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    created_at: datetime
    
# Example endpoint
@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Create a new task"""
    # Implementation would go here
    return TaskResponse(
        id=1,
        title=task.title,
        description=task.description,
        created_at=datetime.utcnow()
    )
'''
    
    def _generate_database_models(self) -> str:
        """데이터베이스 모델 코드 생성"""
        return '''"""
Database models
Generated by Agentic Development Pipeline
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
'''
    
    def _generate_api_endpoint(self, endpoint_name: str) -> str:
        """API 엔드포인트 코드 생성"""
        return f'''"""
API endpoint for {endpoint_name}
Generated by Agentic Development Pipeline
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/")
async def list_items():
    """List all items"""
    return {{"items": [], "total": 0}}

@router.post("/")
async def create_item(data: dict):
    """Create a new item"""
    return {{"id": 1, "data": data, "created_at": datetime.utcnow().isoformat()}}

@router.get("/{{item_id}}")
async def get_item(item_id: int):
    """Get item by ID"""
    return {{"id": item_id, "data": {{}}, "created_at": datetime.utcnow().isoformat()}}

@router.put("/{{item_id}}")
async def update_item(item_id: int, data: dict):
    """Update item"""
    return {{"id": item_id, "data": data, "updated_at": datetime.utcnow().isoformat()}}

@router.delete("/{{item_id}}")
async def delete_item(item_id: int):
    """Delete item"""
    return {{"message": "Item deleted successfully"}}
'''
    
    def _generate_react_app(self) -> str:
        """React 애플리케이션 코드 생성"""
        return '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Generated Application</h1>
        <p>Built with Agentic Development Pipeline</p>
      </header>
      <main>
        <section className="features">
          <h2>Features</h2>
          <ul>
            <li>Automated Development</li>
            <li>AI-Powered Code Generation</li>
            <li>Best Practices Implementation</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

export default App;
'''
    
    def _generate_react_component(self, component_name: str) -> str:
        """React 컴포넌트 코드 생성"""
        return f'''import React, {{ useState, useEffect }} from 'react';

interface {component_name}Props {{
  title?: string;
  onAction?: () => void;
}}

const {component_name}: React.FC<{component_name}Props> = ({{ title = "{component_name}", onAction }}) => {{
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  
  useEffect(() => {{
    // Component initialization
  }}, []);
  
  const handleClick = () => {{
    setIsLoading(true);
    if (onAction) {{
      onAction();
    }}
    setIsLoading(false);
  }};
  
  return (
    <div className="{component_name.toLowerCase()}">
      <h3>{{title}}</h3>
      <button onClick={{handleClick}} disabled={{isLoading}}>
        {{isLoading ? 'Loading...' : 'Action'}}
      </button>
      {{data && <pre>{{JSON.stringify(data, null, 2)}}</pre>}}
    </div>
  );
}};

export default {component_name};
'''
    
    def _generate_styles(self) -> str:
        """CSS 스타일 생성"""
        return '''/* Generated Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
}

.App {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.App-header {
  background-color: #282c34;
  padding: 2rem;
  color: white;
  text-align: center;
}

.App-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.features {
  background: #f4f4f4;
  padding: 2rem;
  border-radius: 8px;
}

.features h2 {
  margin-bottom: 1rem;
  color: #282c34;
}

.features ul {
  list-style: none;
  padding-left: 0;
}

.features li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #ddd;
}

button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

button:hover {
  background-color: #0056b3;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
'''
    
    def _generate_dockerfile(self) -> str:
        """Dockerfile 생성"""
        return '''# Multi-stage build for production
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./static

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def _generate_docker_compose(self) -> str:
        """Docker Compose 설정 생성"""
        return '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
'''
    
    def _generate_ci_pipeline(self) -> str:
        """CI/CD 파이프라인 설정 생성"""
        return '''name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov
        
    - name: Run tests
      run: |
        pytest backend/tests --cov=backend --cov-report=xml
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      
  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t app:${{ github.sha }} .
      
    - name: Push to registry
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Push to container registry"
'''
    
    def _collect_dependencies(self, files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """의존성 수집"""
        dependencies = {
            "python": [
                "fastapi==0.104.1",
                "uvicorn[standard]==0.24.0",
                "sqlalchemy==2.0.23",
                "psycopg2-binary==2.9.9",
                "redis==5.0.1",
                "pydantic==2.5.0"
            ],
            "javascript": [
                "react@18.2.0",
                "typescript@5.3.2",
                "vite@5.0.0",
                "@types/react@18.2.0"
            ],
            "docker": [
                "docker-compose@2.23.0"
            ]
        }
        
        return dependencies
    
    def _generate_documentation(self, files: List[Dict[str, Any]], endpoints: List[Dict[str, Any]]) -> str:
        """문서 생성"""
        doc = f"""# Generated Application Documentation

## Overview
This application was automatically generated by the Agentic Development Pipeline.

## Structure
- **Backend**: FastAPI application with {len([f for f in files if 'backend' in f['path']])} files
- **Frontend**: React application with {len([f for f in files if 'frontend' in f['path']])} files
- **Infrastructure**: Docker and CI/CD configuration

## API Endpoints
Total endpoints: {len(endpoints)}

### Available Endpoints:
"""
        
        for endpoint in endpoints:
            doc += f"\n- **{endpoint['method']} {endpoint['path']}**: {endpoint['description']}"
        
        doc += """

## Getting Started

1. Install dependencies:
   ```bash
   # Backend
   cd backend && pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   ```

2. Run with Docker:
   ```bash
   docker-compose up
   ```

3. Access the application:
   - API: http://localhost:8000
   - Frontend: http://localhost:3000

## Development

Generated on: {datetime.utcnow().isoformat()}
"""
        
        return doc

# 노드 인스턴스 생성
development_node = DevelopmentNode()