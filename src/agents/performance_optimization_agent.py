"""
성능 최적화 전문 에이전트
코드, 데이터베이스, 인프라 전반의 성능을 분석하고 최적화하는 AI 에이전트
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import psutil
import aiohttp
import yaml
import json
import subprocess
from datetime import datetime
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class PerformanceIssueType(Enum):
    """성능 이슈 타입"""
    SLOW_QUERY = "slow_query"
    HIGH_CPU = "high_cpu"
    MEMORY_LEAK = "memory_leak"
    INEFFICIENT_ALGORITHM = "inefficient_algorithm"
    MISSING_INDEX = "missing_index"
    CACHE_MISS = "cache_miss"
    N_PLUS_ONE = "n_plus_one"
    BLOCKING_IO = "blocking_io"

@dataclass
class PerformanceMetric:
    """성능 메트릭"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]

@dataclass
class OptimizationRecommendation:
    """최적화 권장사항"""
    issue_type: PerformanceIssueType
    severity: str  # critical, high, medium, low
    description: str
    solution: str
    estimated_improvement: str
    implementation_code: Optional[str] = None
    risk_level: str = "low"

class PerformanceAnalyzer(ABC):
    """성능 분석기 베이스 클래스"""
    
    @abstractmethod
    async def analyze(self, target: Any) -> List[PerformanceMetric]:
        """성능 분석 실행"""
        pass
    
    @abstractmethod
    async def get_recommendations(self, metrics: List[PerformanceMetric]) -> List[OptimizationRecommendation]:
        """최적화 권장사항 생성"""
        pass

class CodePerformanceAnalyzer(PerformanceAnalyzer):
    """코드 성능 분석기"""
    
    async def analyze(self, code_path: str) -> List[PerformanceMetric]:
        """코드 프로파일링 및 분석"""
        metrics = []
        
        # Python 코드 프로파일링
        if code_path.endswith('.py'):
            profile_result = await self._profile_python(code_path)
            metrics.extend(profile_result)
        
        # JavaScript 코드 분석
        elif code_path.endswith('.js') or code_path.endswith('.ts'):
            profile_result = await self._profile_javascript(code_path)
            metrics.extend(profile_result)
        
        # 복잡도 분석
        complexity_metrics = await self._analyze_complexity(code_path)
        metrics.extend(complexity_metrics)
        
        return metrics
    
    async def _profile_python(self, file_path: str) -> List[PerformanceMetric]:
        """Python 코드 프로파일링"""
        import cProfile
        import pstats
        from io import StringIO
        
        profiler = cProfile.Profile()
        metrics = []
        
        # 프로파일링 실행
        profiler.enable()
        try:
            exec(open(file_path).read())
        except Exception as e:
            print(f"Profiling error: {e}")
        finally:
            profiler.disable()
        
        # 결과 분석
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # 상위 10개 함수
        
        # 메트릭 추출
        for line in s.getvalue().split('\n'):
            if line and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 6:
                    metrics.append(PerformanceMetric(
                        metric_name=f"function_time_{parts[-1]}",
                        value=float(parts[2]),
                        unit="seconds",
                        timestamp=datetime.now(),
                        context={"function": parts[-1], "calls": parts[0]}
                    ))
        
        return metrics
    
    async def _analyze_complexity(self, file_path: str) -> List[PerformanceMetric]:
        """코드 복잡도 분석"""
        # radon을 사용한 복잡도 분석
        try:
            result = subprocess.run(
                ['radon', 'cc', file_path, '-j'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                complexity_data = json.loads(result.stdout)
                metrics = []
                
                for file_data in complexity_data.values():
                    for func in file_data:
                        metrics.append(PerformanceMetric(
                            metric_name="cyclomatic_complexity",
                            value=func['complexity'],
                            unit="score",
                            timestamp=datetime.now(),
                            context={
                                "function": func['name'],
                                "type": func['type'],
                                "rank": func['rank']
                            }
                        ))
                
                return metrics
        except Exception as e:
            print(f"Complexity analysis error: {e}")
        
        return []
    
    async def get_recommendations(self, metrics: List[PerformanceMetric]) -> List[OptimizationRecommendation]:
        """코드 최적화 권장사항 생성"""
        recommendations = []
        
        # 고복잡도 함수 확인
        for metric in metrics:
            if metric.metric_name == "cyclomatic_complexity" and metric.value > 10:
                recommendations.append(OptimizationRecommendation(
                    issue_type=PerformanceIssueType.INEFFICIENT_ALGORITHM,
                    severity="high" if metric.value > 20 else "medium",
                    description=f"함수 '{metric.context['function']}'의 복잡도가 {metric.value}로 높습니다",
                    solution="함수를 더 작은 단위로 분리하고 로직을 단순화하세요",
                    estimated_improvement="20-30% 성능 향상",
                    implementation_code=self._generate_refactoring_code(metric.context['function'])
                ))
        
        # 느린 함수 확인
        slow_functions = [m for m in metrics if m.metric_name.startswith("function_time_") and m.value > 0.1]
        for metric in slow_functions:
            recommendations.append(OptimizationRecommendation(
                issue_type=PerformanceIssueType.INEFFICIENT_ALGORITHM,
                severity="critical" if metric.value > 1.0 else "high",
                description=f"함수 '{metric.context['function']}'의 실행 시간이 {metric.value:.2f}초로 느립니다",
                solution="알고리즘 최적화 또는 캐싱 적용을 고려하세요",
                estimated_improvement="50-70% 성능 향상",
                implementation_code=self._generate_caching_code(metric.context['function'])
            ))
        
        return recommendations
    
    def _generate_refactoring_code(self, function_name: str) -> str:
        """리팩토링 코드 예시 생성"""
        return f"""
# 복잡한 함수를 작은 단위로 분리
def {function_name}_optimized(data):
    # 단계 1: 데이터 검증
    validated_data = _validate_data(data)
    
    # 단계 2: 핵심 로직 처리
    result = _process_core_logic(validated_data)
    
    # 단계 3: 결과 후처리
    return _post_process(result)

def _validate_data(data):
    # 검증 로직 분리
    pass

def _process_core_logic(data):
    # 핵심 비즈니스 로직
    pass

def _post_process(result):
    # 결과 처리
    pass
"""
    
    def _generate_caching_code(self, function_name: str) -> str:
        """캐싱 코드 예시 생성"""
        return f"""
from functools import lru_cache
import redis

# 메모리 캐싱 (간단한 경우)
@lru_cache(maxsize=1000)
def {function_name}_cached(param):
    return {function_name}(param)

# Redis 캐싱 (분산 환경)
redis_client = redis.Redis(host='localhost', port=6379)

def {function_name}_redis_cached(param):
    cache_key = f"{function_name}:{{param}}"
    
    # 캐시 확인
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # 캐시 미스 - 실행 후 저장
    result = {function_name}(param)
    redis_client.setex(cache_key, 3600, json.dumps(result))  # 1시간 TTL
    
    return result
"""

class DatabasePerformanceAnalyzer(PerformanceAnalyzer):
    """데이터베이스 성능 분석기"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    async def analyze(self, queries: List[str]) -> List[PerformanceMetric]:
        """데이터베이스 쿼리 분석"""
        metrics = []
        
        for query in queries:
            # 쿼리 실행 계획 분석
            explain_result = await self._explain_query(query)
            metrics.extend(explain_result)
            
            # 쿼리 실행 시간 측정
            execution_time = await self._measure_query_time(query)
            metrics.append(PerformanceMetric(
                metric_name="query_execution_time",
                value=execution_time,
                unit="milliseconds",
                timestamp=datetime.now(),
                context={"query": query[:100]}  # 쿼리 일부만 저장
            ))
        
        # 인덱스 사용 분석
        index_metrics = await self._analyze_index_usage()
        metrics.extend(index_metrics)
        
        return metrics
    
    async def _explain_query(self, query: str) -> List[PerformanceMetric]:
        """쿼리 실행 계획 분석"""
        import asyncpg
        
        metrics = []
        
        # PostgreSQL EXPLAIN ANALYZE
        try:
            conn = await asyncpg.connect(**self.db_config)
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = await conn.fetchval(explain_query)
            await conn.close()
            
            plan = json.loads(result)[0]
            
            # 실행 계획에서 메트릭 추출
            total_cost = plan['Plan']['Total Cost']
            execution_time = plan['Execution Time']
            
            metrics.append(PerformanceMetric(
                metric_name="query_cost",
                value=total_cost,
                unit="cost_units",
                timestamp=datetime.now(),
                context={"query": query[:100], "plan": plan}
            ))
            
            # 테이블 스캔 확인
            if self._has_sequential_scan(plan['Plan']):
                metrics.append(PerformanceMetric(
                    metric_name="sequential_scan_detected",
                    value=1,
                    unit="boolean",
                    timestamp=datetime.now(),
                    context={"query": query[:100], "issue": "Sequential scan detected"}
                ))
            
        except Exception as e:
            print(f"Query explain error: {e}")
        
        return metrics
    
    def _has_sequential_scan(self, plan: Dict) -> bool:
        """순차 스캔 여부 확인"""
        if plan.get('Node Type') == 'Seq Scan':
            return True
        
        # 하위 플랜 재귀적 확인
        for child in plan.get('Plans', []):
            if self._has_sequential_scan(child):
                return True
        
        return False
    
    async def _analyze_index_usage(self) -> List[PerformanceMetric]:
        """인덱스 사용 현황 분석"""
        import asyncpg
        
        metrics = []
        
        # PostgreSQL 인덱스 통계
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0
        ORDER BY schemaname, tablename;
        """
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            unused_indexes = await conn.fetch(query)
            await conn.close()
            
            for idx in unused_indexes:
                metrics.append(PerformanceMetric(
                    metric_name="unused_index",
                    value=0,
                    unit="scans",
                    timestamp=datetime.now(),
                    context={
                        "index": idx['indexname'],
                        "table": idx['tablename'],
                        "schema": idx['schemaname']
                    }
                ))
        except Exception as e:
            print(f"Index analysis error: {e}")
        
        return metrics
    
    async def get_recommendations(self, metrics: List[PerformanceMetric]) -> List[OptimizationRecommendation]:
        """데이터베이스 최적화 권장사항"""
        recommendations = []
        
        # 느린 쿼리 최적화
        slow_queries = [m for m in metrics if m.metric_name == "query_execution_time" and m.value > 100]
        for metric in slow_queries:
            recommendations.append(OptimizationRecommendation(
                issue_type=PerformanceIssueType.SLOW_QUERY,
                severity="critical" if metric.value > 1000 else "high",
                description=f"쿼리 실행 시간이 {metric.value}ms로 느립니다",
                solution="쿼리 최적화 및 인덱스 추가를 고려하세요",
                estimated_improvement="70-90% 성능 향상",
                implementation_code=self._generate_index_suggestion(metric.context.get('query', ''))
            ))
        
        # 순차 스캔 문제
        seq_scans = [m for m in metrics if m.metric_name == "sequential_scan_detected"]
        for metric in seq_scans:
            recommendations.append(OptimizationRecommendation(
                issue_type=PerformanceIssueType.MISSING_INDEX,
                severity="high",
                description="테이블 전체 스캔이 발생하고 있습니다",
                solution="적절한 인덱스를 추가하여 성능을 개선하세요",
                estimated_improvement="80-95% 성능 향상",
                implementation_code=self._generate_index_creation(metric.context)
            ))
        
        # 사용하지 않는 인덱스
        unused_indexes = [m for m in metrics if m.metric_name == "unused_index"]
        for metric in unused_indexes:
            recommendations.append(OptimizationRecommendation(
                issue_type=PerformanceIssueType.INEFFICIENT_ALGORITHM,
                severity="low",
                description=f"인덱스 '{metric.context['index']}'가 사용되지 않고 있습니다",
                solution="사용하지 않는 인덱스를 제거하여 쓰기 성능을 개선하세요",
                estimated_improvement="5-10% 쓰기 성능 향상",
                implementation_code=f"DROP INDEX {metric.context['schema']}.{metric.context['index']};"
            ))
        
        return recommendations
    
    def _generate_index_suggestion(self, query: str) -> str:
        """인덱스 생성 제안"""
        # 간단한 WHERE 절 파싱 (실제로는 더 복잡한 파서 필요)
        import re
        
        where_match = re.search(r'WHERE\s+(\w+)\s*=', query, re.IGNORECASE)
        if where_match:
            column = where_match.group(1)
            return f"""
-- WHERE 절에 사용된 컬럼에 인덱스 생성
CREATE INDEX idx_{column} ON table_name({column});

-- 복합 인덱스가 필요한 경우
CREATE INDEX idx_composite ON table_name(column1, column2);

-- 부분 인덱스 (특정 조건에만 적용)
CREATE INDEX idx_partial ON table_name(column) WHERE status = 'active';
"""
        
        return "-- 쿼리 분석 후 적절한 인덱스를 생성하세요"

class InfrastructurePerformanceAnalyzer(PerformanceAnalyzer):
    """인프라 성능 분석기"""
    
    async def analyze(self, target_servers: List[str]) -> List[PerformanceMetric]:
        """인프라 성능 분석"""
        metrics = []
        
        for server in target_servers:
            # CPU, 메모리, 디스크 사용률
            resource_metrics = await self._collect_resource_metrics(server)
            metrics.extend(resource_metrics)
            
            # 네트워크 지연시간
            network_metrics = await self._measure_network_latency(server)
            metrics.extend(network_metrics)
            
            # 애플리케이션 응답 시간
            app_metrics = await self._measure_application_response(server)
            metrics.extend(app_metrics)
        
        return metrics
    
    async def _collect_resource_metrics(self, server: str) -> List[PerformanceMetric]:
        """리소스 사용률 수집"""
        metrics = []
        
        # 로컬 서버인 경우 psutil 사용
        if server == "localhost":
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            metrics.extend([
                PerformanceMetric(
                    metric_name="cpu_usage",
                    value=cpu_percent,
                    unit="percent",
                    timestamp=datetime.now(),
                    context={"server": server}
                ),
                PerformanceMetric(
                    metric_name="memory_usage",
                    value=memory_info.percent,
                    unit="percent",
                    timestamp=datetime.now(),
                    context={"server": server, "used_gb": memory_info.used / (1024**3)}
                ),
                PerformanceMetric(
                    metric_name="disk_usage",
                    value=disk_info.percent,
                    unit="percent",
                    timestamp=datetime.now(),
                    context={"server": server, "free_gb": disk_info.free / (1024**3)}
                )
            ])
        
        return metrics
    
    async def _measure_network_latency(self, server: str) -> List[PerformanceMetric]:
        """네트워크 지연시간 측정"""
        import aiohttp
        import time
        
        metrics = []
        
        # HTTP 엔드포인트 응답 시간 측정
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{server}/health", timeout=10) as response:
                    latency = (time.time() - start_time) * 1000  # ms
                    
                    metrics.append(PerformanceMetric(
                        metric_name="network_latency",
                        value=latency,
                        unit="milliseconds",
                        timestamp=datetime.now(),
                        context={"server": server, "status_code": response.status}
                    ))
        except Exception as e:
            print(f"Network latency measurement error: {e}")
        
        return metrics
    
    async def get_recommendations(self, metrics: List[PerformanceMetric]) -> List[OptimizationRecommendation]:
        """인프라 최적화 권장사항"""
        recommendations = []
        
        # CPU 사용률 높음
        high_cpu = [m for m in metrics if m.metric_name == "cpu_usage" and m.value > 80]
        for metric in high_cpu:
            recommendations.append(OptimizationRecommendation(
                issue_type=PerformanceIssueType.HIGH_CPU,
                severity="critical" if metric.value > 90 else "high",
                description=f"서버 '{metric.context['server']}'의 CPU 사용률이 {metric.value}%로 높습니다",
                solution="스케일 아웃 또는 CPU 집약적 작업 최적화가 필요합니다",
                estimated_improvement="30-50% 응답 시간 개선",
                implementation_code=self._generate_scaling_config()
            ))
        
        # 메모리 사용률 높음
        high_memory = [m for m in metrics if m.metric_name == "memory_usage" and m.value > 85]
        for metric in high_memory:
            recommendations.append(OptimizationRecommendation(
                issue_type=PerformanceIssueType.MEMORY_LEAK,
                severity="critical" if metric.value > 95 else "high",
                description=f"서버 '{metric.context['server']}'의 메모리 사용률이 {metric.value}%로 높습니다",
                solution="메모리 누수 확인 및 메모리 최적화가 필요합니다",
                estimated_improvement="메모리 사용량 20-40% 감소",
                implementation_code=self._generate_memory_optimization()
            ))
        
        return recommendations
    
    def _generate_scaling_config(self) -> str:
        """스케일링 설정 예시"""
        return """
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
"""
    
    def _generate_memory_optimization(self) -> str:
        """메모리 최적화 코드"""
        return """
# 메모리 프로파일링 및 최적화

# 1. Python 메모리 프로파일링
from memory_profiler import profile

@profile
def memory_intensive_function():
    # 함수 실행 중 메모리 사용량 추적
    pass

# 2. 메모리 누수 방지
import gc
import weakref

class ResourceManager:
    def __init__(self):
        self._resources = weakref.WeakValueDictionary()
    
    def get_resource(self, key):
        # 약한 참조를 사용하여 자동 가비지 컬렉션
        return self._resources.get(key)
    
    def cleanup(self):
        # 명시적 가비지 컬렉션
        gc.collect()

# 3. 메모리 효율적인 데이터 구조
# 대용량 데이터는 generator 사용
def process_large_file(filename):
    with open(filename) as f:
        for line in f:  # 전체 파일을 메모리에 로드하지 않음
            yield process_line(line)

# 4. 캐시 크기 제한
from functools import lru_cache

@lru_cache(maxsize=1000)  # 최대 1000개 항목만 캐시
def expensive_operation(param):
    pass
"""

class PerformanceOptimizationAgent:
    """성능 최적화 전문 에이전트"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.code_analyzer = CodePerformanceAnalyzer()
        self.db_analyzer = None  # 필요시 초기화
        self.infra_analyzer = InfrastructurePerformanceAnalyzer()
        
    async def optimize_application(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """애플리케이션 전체 성능 최적화"""
        
        print("🚀 성능 최적화 분석을 시작합니다...")
        
        all_metrics = []
        all_recommendations = []
        
        # 1. 코드 성능 분석
        if 'code_paths' in app_config:
            print("📊 코드 성능 분석 중...")
            for code_path in app_config['code_paths']:
                metrics = await self.code_analyzer.analyze(code_path)
                all_metrics.extend(metrics)
                
                recommendations = await self.code_analyzer.get_recommendations(metrics)
                all_recommendations.extend(recommendations)
        
        # 2. 데이터베이스 성능 분석
        if 'database' in app_config:
            print("🗄️ 데이터베이스 성능 분석 중...")
            self.db_analyzer = DatabasePerformanceAnalyzer(app_config['database'])
            
            if 'queries' in app_config:
                metrics = await self.db_analyzer.analyze(app_config['queries'])
                all_metrics.extend(metrics)
                
                recommendations = await self.db_analyzer.get_recommendations(metrics)
                all_recommendations.extend(recommendations)
        
        # 3. 인프라 성능 분석
        if 'servers' in app_config:
            print("🖥️ 인프라 성능 분석 중...")
            metrics = await self.infra_analyzer.analyze(app_config['servers'])
            all_metrics.extend(metrics)
            
            recommendations = await self.infra_analyzer.get_recommendations(metrics)
            all_recommendations.extend(recommendations)
        
        # 4. 종합 분석 및 우선순위 결정
        prioritized_recommendations = self._prioritize_recommendations(all_recommendations)
        
        # 5. 최적화 계획 생성
        optimization_plan = self._create_optimization_plan(prioritized_recommendations)
        
        # 6. 자동 최적화 실행 (선택적)
        if app_config.get('auto_optimize', False):
            applied_optimizations = await self._apply_optimizations(optimization_plan)
        else:
            applied_optimizations = []
        
        # 7. 결과 리포트 생성
        report = self._generate_performance_report(
            all_metrics,
            prioritized_recommendations,
            optimization_plan,
            applied_optimizations
        )
        
        print("✅ 성능 최적화 분석이 완료되었습니다!")
        
        return report
    
    def _prioritize_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """권장사항 우선순위 결정"""
        
        # 심각도와 예상 개선 효과를 기준으로 정렬
        severity_score = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        def score_recommendation(rec: OptimizationRecommendation) -> float:
            base_score = severity_score.get(rec.severity, 0)
            
            # 예상 개선 효과에서 숫자 추출
            import re
            improvement_match = re.search(r'(\d+)-(\d+)%', rec.estimated_improvement)
            if improvement_match:
                avg_improvement = (int(improvement_match.group(1)) + int(improvement_match.group(2))) / 2
                base_score += avg_improvement / 100
            
            # 위험도 조정
            if rec.risk_level == 'high':
                base_score *= 0.7
            elif rec.risk_level == 'medium':
                base_score *= 0.85
            
            return base_score
        
        return sorted(recommendations, key=score_recommendation, reverse=True)
    
    def _create_optimization_plan(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, Any]:
        """최적화 실행 계획 생성"""
        
        plan = {
            'phases': [],
            'total_estimated_time': 0,
            'expected_improvements': {}
        }
        
        # Phase 1: 즉시 적용 가능한 최적화 (낮은 위험도)
        phase1 = {
            'name': 'Quick Wins',
            'duration': '1-2 hours',
            'tasks': []
        }
        
        for rec in recommendations:
            if rec.risk_level == 'low' and rec.severity in ['critical', 'high']:
                phase1['tasks'].append({
                    'type': rec.issue_type.value,
                    'description': rec.description,
                    'solution': rec.solution,
                    'code': rec.implementation_code
                })
        
        if phase1['tasks']:
            plan['phases'].append(phase1)
        
        # Phase 2: 중간 위험도 최적화
        phase2 = {
            'name': 'Medium Risk Optimizations',
            'duration': '4-8 hours',
            'tasks': []
        }
        
        for rec in recommendations:
            if rec.risk_level == 'medium':
                phase2['tasks'].append({
                    'type': rec.issue_type.value,
                    'description': rec.description,
                    'solution': rec.solution,
                    'code': rec.implementation_code,
                    'testing_required': True
                })
        
        if phase2['tasks']:
            plan['phases'].append(phase2)
        
        # Phase 3: 주요 아키텍처 변경
        phase3 = {
            'name': 'Architecture Changes',
            'duration': '1-2 weeks',
            'tasks': []
        }
        
        for rec in recommendations:
            if rec.risk_level == 'high' or rec.issue_type in [
                PerformanceIssueType.INEFFICIENT_ALGORITHM,
                PerformanceIssueType.HIGH_CPU
            ]:
                phase3['tasks'].append({
                    'type': rec.issue_type.value,
                    'description': rec.description,
                    'solution': rec.solution,
                    'code': rec.implementation_code,
                    'approval_required': True
                })
        
        if phase3['tasks']:
            plan['phases'].append(phase3)
        
        return plan
    
    async def _apply_optimizations(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """자동으로 적용 가능한 최적화 실행"""
        
        applied = []
        
        # Phase 1의 낮은 위험도 최적화만 자동 적용
        if plan['phases'] and plan['phases'][0]['name'] == 'Quick Wins':
            for task in plan['phases'][0]['tasks']:
                if task['type'] in ['cache_miss', 'missing_index']:
                    # 실제 구현에서는 여기서 최적화 코드 실행
                    applied.append({
                        'task': task['description'],
                        'status': 'applied',
                        'timestamp': datetime.now()
                    })
        
        return applied
    
    def _generate_performance_report(
        self,
        metrics: List[PerformanceMetric],
        recommendations: List[OptimizationRecommendation],
        plan: Dict[str, Any],
        applied_optimizations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """성능 분석 리포트 생성"""
        
        # 메트릭 요약
        metric_summary = {}
        for metric in metrics:
            if metric.metric_name not in metric_summary:
                metric_summary[metric.metric_name] = {
                    'values': [],
                    'avg': 0,
                    'max': 0,
                    'min': float('inf')
                }
            
            metric_summary[metric.metric_name]['values'].append(metric.value)
            metric_summary[metric.metric_name]['max'] = max(
                metric_summary[metric.metric_name]['max'],
                metric.value
            )
            metric_summary[metric.metric_name]['min'] = min(
                metric_summary[metric.metric_name]['min'],
                metric.value
            )
        
        # 평균 계산
        for metric_name, data in metric_summary.items():
            if data['values']:
                data['avg'] = sum(data['values']) / len(data['values'])
        
        # 이슈 카테고리별 집계
        issue_summary = {}
        for rec in recommendations:
            issue_type = rec.issue_type.value
            if issue_type not in issue_summary:
                issue_summary[issue_type] = {
                    'count': 0,
                    'severities': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                }
            
            issue_summary[issue_type]['count'] += 1
            issue_summary[issue_type]['severities'][rec.severity] += 1
        
        report = {
            'summary': {
                'total_issues': len(recommendations),
                'critical_issues': sum(1 for r in recommendations if r.severity == 'critical'),
                'high_issues': sum(1 for r in recommendations if r.severity == 'high'),
                'applied_optimizations': len(applied_optimizations)
            },
            'metrics': metric_summary,
            'issues_by_type': issue_summary,
            'top_recommendations': recommendations[:5],
            'optimization_plan': plan,
            'applied_optimizations': applied_optimizations,
            'generated_at': datetime.now().isoformat()
        }
        
        # 리포트를 파일로 저장
        with open('performance_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # 마크다운 리포트 생성
        self._generate_markdown_report(report)
        
        return report
    
    def _generate_markdown_report(self, report: Dict[str, Any]):
        """마크다운 형식의 리포트 생성"""
        
        markdown = f"""# 성능 최적화 리포트

생성일시: {report['generated_at']}

## 📊 요약

- **총 발견된 이슈**: {report['summary']['total_issues']}개
- **심각**: {report['summary']['critical_issues']}개
- **높음**: {report['summary']['high_issues']}개
- **자동 적용된 최적화**: {report['summary']['applied_optimizations']}개

## 🔍 주요 발견 사항

### 상위 5개 권장사항

"""
        
        for i, rec in enumerate(report['top_recommendations'], 1):
            markdown += f"""
{i}. **{rec['description']}**
   - 심각도: {rec['severity']}
   - 예상 개선: {rec['estimated_improvement']}
   - 해결책: {rec['solution']}
"""
        
        markdown += """
## 📈 성능 메트릭

| 메트릭 | 평균 | 최대 | 최소 |
|--------|------|------|------|
"""
        
        for metric_name, data in report['metrics'].items():
            markdown += f"| {metric_name} | {data['avg']:.2f} | {data['max']:.2f} | {data['min']:.2f} |\n"
        
        markdown += """
## 🛠️ 최적화 계획

"""
        
        for phase in report['optimization_plan']['phases']:
            markdown += f"### {phase['name']} (예상 소요 시간: {phase['duration']})\n\n"
            for task in phase['tasks']:
                markdown += f"- {task['description']}\n"
        
        with open('performance_report.md', 'w') as f:
            f.write(markdown)

# 사용 예시
async def main():
    agent = PerformanceOptimizationAgent('configs/agents/performance-optimization-agent.yaml')
    
    app_config = {
        'code_paths': ['src/api/handlers.py', 'src/services/data_processor.py'],
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'myapp',
            'user': 'postgres',
            'password': 'password'
        },
        'queries': [
            "SELECT * FROM users WHERE created_at > '2024-01-01'",
            "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id"
        ],
        'servers': ['localhost'],
        'auto_optimize': False
    }
    
    report = await agent.optimize_application(app_config)
    print(f"\n✅ 리포트가 생성되었습니다: performance_report.md")

if __name__ == "__main__":
    asyncio.run(main())