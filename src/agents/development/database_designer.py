"""
데이터베이스 설계 관련 기능
"""

import logging
from typing import Dict, Any, List, Optional
import json

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)


class DatabaseSchemaSpec(BaseModel):
    """데이터베이스 스키마 명세"""
    table_name: str = Field(description="테이블 이름")
    columns: List[Dict[str, Any]] = Field(description="컬럼 정의")
    indexes: Optional[List[str]] = Field(default_factory=list)
    relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class DatabaseDesigner:
    """데이터베이스 설계 도구"""
    
    @staticmethod
    def get_tools(llm, mcp_tools) -> List[Tool]:
        """데이터베이스 설계 관련 도구 반환"""
        return [
            Tool(
                name="design_database_schema",
                description="데이터베이스 스키마 설계 및 ERD 생성",
                func=lambda input: DatabaseDesigner._design_database_schema(llm, mcp_tools, input)
            ),
            Tool(
                name="generate_migrations",
                description="데이터베이스 마이그레이션 스크립트 생성",
                func=lambda input: DatabaseDesigner._generate_migrations(llm, mcp_tools, input)
            ),
            Tool(
                name="optimize_database_queries",
                description="데이터베이스 쿼리 최적화",
                func=lambda input: DatabaseDesigner._optimize_queries(llm, mcp_tools, input)
            ),
        ]
    
    @staticmethod
    def _design_database_schema(llm, mcp_tools, input_str: str) -> str:
        """데이터베이스 스키마 설계"""
        try:
            specs = json.loads(input_str)
            
            prompt = f"""
            Design a database schema based on the following requirements:
            {json.dumps(specs, indent=2)}
            
            Generate:
            1. Complete entity relationship diagram (ERD)
            2. Table definitions with appropriate data types
            3. Primary keys, foreign keys, and indexes
            4. Normalization to 3NF where appropriate
            5. Performance optimization considerations
            
            Output format: SQL DDL statements and diagram description
            """
            
            response = llm.invoke(prompt)
            
            # SQL 스키마 파일 생성
            schema_file = "database/schema.sql"
            mcp_tools.call_tool(
                server="filesystem",
                tool="write_file",
                arguments={
                    "path": schema_file,
                    "content": response.content
                }
            )
            
            # SQLAlchemy 모델 생성
            if specs.get("orm") == "sqlalchemy":
                models_content = DatabaseDesigner._generate_sqlalchemy_models(specs)
                mcp_tools.call_tool(
                    server="filesystem",
                    tool="write_file",
                    arguments={
                        "path": "src/models/database.py",
                        "content": models_content
                    }
                )
            
            return f"Successfully designed database schema with {len(specs.get('entities', []))} tables"
            
        except Exception as e:
            logger.error(f"Error designing database schema: {e}")
            raise AgentExecutionError(f"Failed to design database schema: {str(e)}")
    
    @staticmethod
    def _generate_migrations(llm, mcp_tools, input_str: str) -> str:
        """마이그레이션 스크립트 생성"""
        try:
            specs = json.loads(input_str)
            
            prompt = f"""
            Generate database migration scripts for:
            {json.dumps(specs, indent=2)}
            
            Create:
            1. Initial schema creation migration
            2. Data migration scripts if needed
            3. Rollback scripts for each migration
            4. Index creation optimized for performance
            5. Seed data scripts
            """
            
            response = llm.invoke(prompt)
            
            # Alembic 마이그레이션 파일 생성
            migration_file = f"alembic/versions/{specs.get('version', '001')}_initial_schema.py"
            mcp_tools.call_tool(
                server="filesystem",
                tool="write_file",
                arguments={
                    "path": migration_file,
                    "content": response.content
                }
            )
            
            return "Successfully generated database migrations"
            
        except Exception as e:
            logger.error(f"Error generating migrations: {e}")
            raise AgentExecutionError(f"Failed to generate migrations: {str(e)}")
    
    @staticmethod
    def _optimize_queries(llm, mcp_tools, input_str: str) -> str:
        """쿼리 최적화"""
        try:
            specs = json.loads(input_str)
            
            prompt = f"""
            Optimize the following database queries:
            {json.dumps(specs, indent=2)}
            
            Provide:
            1. Optimized query versions
            2. Index recommendations
            3. Query execution plan analysis
            4. Performance benchmarks
            5. Caching strategy recommendations
            """
            
            response = llm.invoke(prompt)
            
            # 최적화된 쿼리 파일 생성
            optimized_file = "database/optimized_queries.sql"
            mcp_tools.call_tool(
                server="filesystem",
                tool="write_file",
                arguments={
                    "path": optimized_file,
                    "content": response.content
                }
            )
            
            return "Successfully optimized database queries"
            
        except Exception as e:
            logger.error(f"Error optimizing queries: {e}")
            raise AgentExecutionError(f"Failed to optimize queries: {str(e)}")
    
    @staticmethod
    def _generate_sqlalchemy_models(specs: Dict[str, Any]) -> str:
        """SQLAlchemy 모델 생성"""
        models = []
        for entity in specs.get("entities", []):
            model_code = f"""
class {entity['name']}(Base):
    __tablename__ = '{entity['table_name']}'
    
"""
            for column in entity.get("columns", []):
                model_code += f"    {column['name']} = Column({column['type']})\n"
            
            models.append(model_code)
        
        return """
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

""" + "\n\n".join(models)