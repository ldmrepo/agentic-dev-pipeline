"""
모니터링 에이전트
성능 모니터링, 로그 분석, 알람 설정, 대시보드 생성
"""

import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
from pathlib import Path

from langchain.tools import Tool
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, AgentContext, AgentResult
from src.integrations.mcp.tools import MCPTools
from src.core.schemas import (
    MonitoringConfig, MetricData,
    AlertRule, DashboardConfig,
    ArtifactType
)
from src.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)

class MetricCollectionInput(BaseModel):
    """메트릭 수집 입력"""
    metric_type: str = Field(description="메트릭 타입 (cpu/memory/latency/error_rate)")
    duration: str = Field(description="수집 기간 (1h/24h/7d/30d)")
    aggregation: str = Field(description="집계 방법 (avg/max/min/p95)")

class AlertConfigInput(BaseModel):
    """알람 설정 입력"""
    metric: str = Field(description="모니터링할 메트릭")
    threshold: float = Field(description="임계값")
    condition: str = Field(description="조건 (above/below/equals)")
    duration: int = Field(description="지속 시간 (분)")

class LogAnalysisInput(BaseModel):
    """로그 분석 입력"""
    log_source: str = Field(description="로그 소스")
    time_range: str = Field(description="분석 기간")
    pattern: Optional[str] = Field(description="검색 패턴")

class MonitoringAgent(BaseAgent):
    """모니터링 AI 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="MonitoringAgent",
            description="애플리케이션 성능 모니터링 및 로그 분석을 수행하는 에이전트"
        )
        self.metrics: Dict[str, List[MetricData]] = {}
        self.alerts: List[AlertRule] = []
        self.dashboards: List[DashboardConfig] = []
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의"""
        return """You are a Monitoring Agent responsible for ensuring application health and performance.

Key responsibilities:
1. Collect and analyze performance metrics
2. Set up alerting rules and thresholds
3. Analyze logs for errors and patterns
4. Create monitoring dashboards
5. Generate performance reports
6. Identify bottlenecks and anomalies
7. Recommend optimization strategies

Monitoring expertise:
- Metrics: CPU, Memory, Disk, Network, Application-specific
- Logging: Centralized logging, Log aggregation, Pattern matching
- Alerting: Threshold-based, Anomaly detection, Escalation policies
- Visualization: Grafana, Prometheus, ELK stack
- APM: Application Performance Monitoring
- Distributed tracing: Jaeger, Zipkin
- Infrastructure: Cloud monitoring (AWS CloudWatch, GCP Monitoring)

Best practices:
- Define meaningful SLIs (Service Level Indicators)
- Set realistic SLOs (Service Level Objectives)
- Implement proper instrumentation
- Use structured logging
- Create actionable alerts
- Avoid alert fatigue
- Maintain runbooks for common issues

Focus on:
- Proactive monitoring over reactive
- Root cause analysis
- Continuous improvement
- Cost optimization
- Security monitoring"""
    
    def _get_specialized_tools(self) -> List[Tool]:
        """모니터링 전문 도구"""
        tools = []
        
        # 메트릭 수집 도구
        def collect_metrics(spec: str) -> str:
            """메트릭 수집"""
            return f"Collected metrics: {spec}"
        
        tools.append(Tool(
            name="collect_metrics",
            description="Collect performance metrics",
            func=collect_metrics
        ))
        
        # 로그 분석 도구
        def analyze_logs(query: str) -> str:
            """로그 분석"""
            return f"Log analysis for: {query}"
        
        tools.append(Tool(
            name="analyze_logs",
            description="Analyze application logs",
            func=analyze_logs
        ))
        
        # 알람 설정 도구
        def setup_alerts(config: str) -> str:
            """알람 설정"""
            return f"Alert configured: {config}"
        
        tools.append(Tool(
            name="setup_alerts",
            description="Configure monitoring alerts",
            func=setup_alerts
        ))
        
        # 파일 시스템 및 실행 도구 추가
        tools.extend([
            MCPTools.filesystem_read(),
            MCPTools.filesystem_write(),
            MCPTools.shell_execute(),
            MCPTools.prometheus_query()  # Prometheus 쿼리 도구
        ])
        
        return tools
    
    async def collect_metrics(
        self,
        metric_types: List[str],
        duration: str = "1h"
    ) -> Dict[str, List[MetricData]]:
        """메트릭 수집"""
        collected_metrics = {}
        
        for metric_type in metric_types:
            if metric_type == "cpu":
                metrics = await self._collect_cpu_metrics(duration)
            elif metric_type == "memory":
                metrics = await self._collect_memory_metrics(duration)
            elif metric_type == "latency":
                metrics = await self._collect_latency_metrics(duration)
            elif metric_type == "error_rate":
                metrics = await self._collect_error_rate_metrics(duration)
            else:
                logger.warning(f"Unknown metric type: {metric_type}")
                continue
            
            collected_metrics[metric_type] = metrics
        
        return collected_metrics
    
    async def _collect_cpu_metrics(self, duration: str) -> List[MetricData]:
        """CPU 메트릭 수집"""
        # Prometheus 쿼리 예시
        query = f'rate(process_cpu_seconds_total[{duration}])'
        
        # 시뮬레이션 데이터
        metrics = []
        now = datetime.now()
        
        for i in range(60):  # 60개 데이터 포인트
            timestamp = now - timedelta(minutes=i)
            value = 20 + (i % 20) * 2  # 20-60% 사이 변동
            
            metrics.append(MetricData(
                name="cpu_usage",
                value=value,
                timestamp=timestamp,
                labels={"instance": "app-server-1"}
            ))
        
        return metrics
    
    async def _collect_memory_metrics(self, duration: str) -> List[MetricData]:
        """메모리 메트릭 수집"""
        query = f'process_resident_memory_bytes'
        
        metrics = []
        now = datetime.now()
        
        for i in range(60):
            timestamp = now - timedelta(minutes=i)
            value = 512 * 1024 * 1024 + (i * 10 * 1024 * 1024)  # 512MB 베이스
            
            metrics.append(MetricData(
                name="memory_usage",
                value=value,
                timestamp=timestamp,
                labels={"instance": "app-server-1"}
            ))
        
        return metrics
    
    async def _collect_latency_metrics(self, duration: str) -> List[MetricData]:
        """레이턴시 메트릭 수집"""
        query = f'histogram_quantile(0.95, http_request_duration_seconds_bucket)'
        
        metrics = []
        now = datetime.now()
        
        for i in range(60):
            timestamp = now - timedelta(minutes=i)
            value = 100 + (i % 10) * 20  # 100-300ms 사이 변동
            
            metrics.append(MetricData(
                name="p95_latency",
                value=value,
                timestamp=timestamp,
                labels={"endpoint": "/api/v1/pipeline"}
            ))
        
        return metrics
    
    async def _collect_error_rate_metrics(self, duration: str) -> List[MetricData]:
        """에러율 메트릭 수집"""
        query = f'rate(http_requests_total{{status=~"5.."}}[{duration}])'
        
        metrics = []
        now = datetime.now()
        
        for i in range(60):
            timestamp = now - timedelta(minutes=i)
            value = 0.1 + (i % 5) * 0.1  # 0.1-0.5% 에러율
            
            metrics.append(MetricData(
                name="error_rate",
                value=value,
                timestamp=timestamp,
                labels={"service": "api"}
            ))
        
        return metrics
    
    async def analyze_logs(
        self,
        log_sources: List[str],
        time_range: str = "1h",
        patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """로그 분석"""
        analysis_results = {
            "total_logs": 0,
            "error_logs": 0,
            "warning_logs": 0,
            "patterns_found": {},
            "top_errors": [],
            "anomalies": []
        }
        
        for source in log_sources:
            # 로그 읽기 (시뮬레이션)
            logs = await self._read_logs(source, time_range)
            
            # 로그 분석
            for log in logs:
                analysis_results["total_logs"] += 1
                
                if "ERROR" in log:
                    analysis_results["error_logs"] += 1
                elif "WARNING" in log:
                    analysis_results["warning_logs"] += 1
                
                # 패턴 매칭
                if patterns:
                    for pattern in patterns:
                        if pattern in log:
                            if pattern not in analysis_results["patterns_found"]:
                                analysis_results["patterns_found"][pattern] = 0
                            analysis_results["patterns_found"][pattern] += 1
        
        # 상위 에러 추출
        analysis_results["top_errors"] = await self._extract_top_errors(logs)
        
        # 이상 탐지
        analysis_results["anomalies"] = await self._detect_anomalies(logs)
        
        return analysis_results
    
    async def _read_logs(self, source: str, time_range: str) -> List[str]:
        """로그 읽기 (시뮬레이션)"""
        sample_logs = [
            "[2024-01-29 10:00:00] INFO: Pipeline started - ID: pipe-123",
            "[2024-01-29 10:00:05] DEBUG: Agent execution started",
            "[2024-01-29 10:00:10] WARNING: High memory usage detected: 85%",
            "[2024-01-29 10:00:15] ERROR: Failed to connect to database: timeout",
            "[2024-01-29 10:00:20] INFO: Retrying database connection",
            "[2024-01-29 10:00:25] INFO: Database connection established",
            "[2024-01-29 10:00:30] ERROR: API rate limit exceeded",
            "[2024-01-29 10:00:35] WARNING: Slow query detected: 5.2s",
            "[2024-01-29 10:00:40] INFO: Pipeline completed successfully",
            "[2024-01-29 10:00:45] ERROR: Null pointer exception in module X"
        ]
        
        return sample_logs
    
    async def _extract_top_errors(self, logs: List[str]) -> List[Dict[str, Any]]:
        """상위 에러 추출"""
        error_counts = {}
        
        for log in logs:
            if "ERROR" in log:
                # 에러 메시지 추출
                error_msg = log.split("ERROR: ")[1] if "ERROR: " in log else "Unknown error"
                
                if error_msg not in error_counts:
                    error_counts[error_msg] = 0
                error_counts[error_msg] += 1
        
        # 상위 5개 에러
        top_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return [
            {"error": error, "count": count}
            for error, count in top_errors
        ]
    
    async def _detect_anomalies(self, logs: List[str]) -> List[Dict[str, Any]]:
        """로그 이상 탐지"""
        anomalies = []
        
        # 간단한 규칙 기반 이상 탐지
        error_threshold = 5
        error_count = sum(1 for log in logs if "ERROR" in log)
        
        if error_count > error_threshold:
            anomalies.append({
                "type": "high_error_rate",
                "description": f"Error rate exceeded threshold: {error_count} errors",
                "severity": "high"
            })
        
        # 특정 패턴 탐지
        if any("timeout" in log for log in logs):
            anomalies.append({
                "type": "timeout_issues",
                "description": "Multiple timeout errors detected",
                "severity": "medium"
            })
        
        return anomalies
    
    async def create_alert_rules(
        self,
        metrics: List[str],
        thresholds: Dict[str, float]
    ) -> List[AlertRule]:
        """알람 규칙 생성"""
        alert_rules = []
        
        for metric in metrics:
            if metric in thresholds:
                rule = AlertRule(
                    name=f"{metric}_alert",
                    metric=metric,
                    condition="above",
                    threshold=thresholds[metric],
                    duration_minutes=5,
                    severity="warning" if metric != "error_rate" else "critical",
                    notification_channels=["email", "slack"],
                    description=f"Alert when {metric} exceeds {thresholds[metric]}"
                )
                alert_rules.append(rule)
        
        self.alerts.extend(alert_rules)
        return alert_rules
    
    async def create_dashboard(
        self,
        name: str,
        metrics: List[str],
        layout: str = "grid"
    ) -> DashboardConfig:
        """모니터링 대시보드 생성"""
        panels = []
        
        for i, metric in enumerate(metrics):
            panel = {
                "id": i + 1,
                "title": metric.replace("_", " ").title(),
                "type": "graph",
                "datasource": "prometheus",
                "query": self._get_metric_query(metric),
                "gridPos": self._calculate_grid_position(i, layout)
            }
            panels.append(panel)
        
        dashboard = DashboardConfig(
            name=name,
            description=f"Monitoring dashboard for {name}",
            panels=panels,
            refresh_interval="10s",
            time_range="1h",
            tags=["monitoring", "performance"]
        )
        
        self.dashboards.append(dashboard)
        return dashboard
    
    def _get_metric_query(self, metric: str) -> str:
        """메트릭별 Prometheus 쿼리 생성"""
        queries = {
            "cpu_usage": 'rate(process_cpu_seconds_total[5m]) * 100',
            "memory_usage": 'process_resident_memory_bytes / 1024 / 1024',
            "latency": 'histogram_quantile(0.95, http_request_duration_seconds_bucket)',
            "error_rate": 'rate(http_requests_total{status=~"5.."}[5m])',
            "throughput": 'rate(http_requests_total[5m])'
        }
        
        return queries.get(metric, f'{metric}')
    
    def _calculate_grid_position(self, index: int, layout: str) -> Dict[str, int]:
        """대시보드 그리드 위치 계산"""
        if layout == "grid":
            # 2x2 그리드
            row = index // 2
            col = index % 2
            return {
                "x": col * 12,
                "y": row * 8,
                "w": 12,
                "h": 8
            }
        else:  # vertical
            return {
                "x": 0,
                "y": index * 8,
                "w": 24,
                "h": 8
            }
    
    async def generate_prometheus_config(
        self,
        targets: List[Dict[str, Any]]
    ) -> str:
        """Prometheus 설정 생성"""
        config = """# Prometheus Configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
      - targets:
        - alertmanager:9093

rule_files:
  - "alert_rules.yml"

scrape_configs:
"""
        
        for target in targets:
            config += f"""
  - job_name: '{target['job_name']}'
    static_configs:
      - targets: {target['targets']}
        labels:
          environment: '{target.get('environment', 'production')}'
          service: '{target.get('service', 'api')}'
"""
        
        return config
    
    async def generate_grafana_dashboard(
        self,
        dashboard_config: DashboardConfig
    ) -> Dict[str, Any]:
        """Grafana 대시보드 JSON 생성"""
        dashboard = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": dashboard_config.name,
                "tags": dashboard_config.tags,
                "timezone": "browser",
                "panels": [],
                "schemaVersion": 16,
                "version": 0,
                "refresh": dashboard_config.refresh_interval
            },
            "overwrite": True
        }
        
        # 패널 추가
        for panel in dashboard_config.panels:
            grafana_panel = {
                "id": panel["id"],
                "gridPos": panel["gridPos"],
                "type": panel["type"],
                "title": panel["title"],
                "datasource": panel["datasource"],
                "targets": [{
                    "expr": panel["query"],
                    "refId": "A"
                }],
                "options": {
                    "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom"
                    }
                }
            }
            dashboard["dashboard"]["panels"].append(grafana_panel)
        
        return dashboard
    
    async def generate_alert_rules_yaml(
        self,
        alert_rules: List[AlertRule]
    ) -> str:
        """Prometheus 알람 규칙 YAML 생성"""
        yaml_content = """groups:
  - name: application_alerts
    interval: 30s
    rules:
"""
        
        for rule in alert_rules:
            yaml_content += f"""
    - alert: {rule.name}
      expr: {self._generate_alert_expression(rule)}
      for: {rule.duration_minutes}m
      labels:
        severity: {rule.severity}
      annotations:
        summary: "{rule.description}"
        description: "{rule.metric} has exceeded threshold of {rule.threshold}"
"""
        
        return yaml_content
    
    def _generate_alert_expression(self, rule: AlertRule) -> str:
        """알람 표현식 생성"""
        metric_query = self._get_metric_query(rule.metric)
        
        if rule.condition == "above":
            return f"{metric_query} > {rule.threshold}"
        elif rule.condition == "below":
            return f"{metric_query} < {rule.threshold}"
        else:
            return f"{metric_query} == {rule.threshold}"
    
    async def generate_performance_report(
        self,
        metrics: Dict[str, List[MetricData]],
        analysis: Dict[str, Any]
    ) -> str:
        """성능 리포트 생성"""
        report = f"""# Performance Monitoring Report

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- Total monitoring period: Last 24 hours
- Systems monitored: API Server, Database, Cache
- Overall health status: {"Healthy" if analysis.get("error_logs", 0) < 10 else "Degraded"}

## Metrics Overview

### CPU Usage
- Average: {self._calculate_average(metrics.get('cpu_usage', [])):.1f}%
- Peak: {self._calculate_max(metrics.get('cpu_usage', [])):.1f}%
- Current: {metrics.get('cpu_usage', [{}])[-1].get('value', 0):.1f}%

### Memory Usage
- Average: {self._calculate_average(metrics.get('memory_usage', [])) / 1024 / 1024:.1f} MB
- Peak: {self._calculate_max(metrics.get('memory_usage', [])) / 1024 / 1024:.1f} MB
- Current: {metrics.get('memory_usage', [{}])[-1].get('value', 0) / 1024 / 1024:.1f} MB

### API Latency (P95)
- Average: {self._calculate_average(metrics.get('latency', [])):.1f} ms
- Peak: {self._calculate_max(metrics.get('latency', [])):.1f} ms
- Current: {metrics.get('latency', [{}])[-1].get('value', 0):.1f} ms

### Error Rate
- Average: {self._calculate_average(metrics.get('error_rate', [])) * 100:.2f}%
- Peak: {self._calculate_max(metrics.get('error_rate', [])) * 100:.2f}%
- Total errors: {analysis.get('error_logs', 0)}

## Log Analysis

- Total logs analyzed: {analysis.get('total_logs', 0)}
- Error logs: {analysis.get('error_logs', 0)}
- Warning logs: {analysis.get('warning_logs', 0)}

### Top Errors
"""
        
        for i, error in enumerate(analysis.get('top_errors', [])[:5]):
            report += f"{i+1}. {error['error']} - {error['count']} occurrences\n"
        
        report += """
## Anomalies Detected
"""
        
        for anomaly in analysis.get('anomalies', []):
            report += f"- **{anomaly['type']}**: {anomaly['description']} (Severity: {anomaly['severity']})\n"
        
        report += """
## Recommendations

1. **Performance Optimization**
   - Consider scaling horizontally if CPU usage consistently exceeds 70%
   - Implement caching for frequently accessed endpoints
   - Optimize database queries showing high latency

2. **Error Reduction**
   - Investigate and fix recurring errors
   - Implement circuit breakers for external service calls
   - Add retry logic with exponential backoff

3. **Monitoring Improvements**
   - Set up alerts for critical metrics
   - Implement distributed tracing for better visibility
   - Add custom metrics for business KPIs

## Next Steps

1. Review and address top errors
2. Implement recommended optimizations
3. Schedule follow-up monitoring review in 1 week
"""
        
        return report
    
    def _calculate_average(self, metrics: List[MetricData]) -> float:
        """평균 계산"""
        if not metrics:
            return 0.0
        
        values = [m.value for m in metrics if isinstance(m, MetricData)]
        return sum(values) / len(values) if values else 0.0
    
    def _calculate_max(self, metrics: List[MetricData]) -> float:
        """최대값 계산"""
        if not metrics:
            return 0.0
        
        values = [m.value for m in metrics if isinstance(m, MetricData)]
        return max(values) if values else 0.0
    
    async def _process_result(self, raw_result: Dict[str, Any], context: AgentContext) -> AgentResult:
        """결과 처리"""
        try:
            # 에이전트 출력에서 정보 추출
            output = raw_result.get("output", "")
            
            # 이전 결과에서 정보 가져오기
            deployment_result = context.previous_results.get("deployment_result", {})
            
            # 메트릭 수집
            metric_types = ["cpu_usage", "memory_usage", "latency", "error_rate"]
            collected_metrics = await self.collect_metrics(metric_types, "24h")
            
            # 로그 분석
            log_analysis = await self.analyze_logs(
                ["api.log", "error.log"],
                "24h",
                ["ERROR", "timeout", "exception"]
            )
            
            # 알람 규칙 생성
            thresholds = {
                "cpu_usage": 80.0,
                "memory_usage": 1024 * 1024 * 1024,  # 1GB
                "latency": 500.0,  # 500ms
                "error_rate": 0.05  # 5%
            }
            alert_rules = await self.create_alert_rules(metric_types, thresholds)
            
            # 대시보드 생성
            dashboard = await self.create_dashboard(
                "Application Performance",
                metric_types,
                "grid"
            )
            
            # 아티팩트 생성
            artifacts = []
            
            # 1. Prometheus 설정
            prometheus_config = await self.generate_prometheus_config([
                {
                    "job_name": "api_server",
                    "targets": ["localhost:8080"],
                    "environment": "production",
                    "service": "api"
                }
            ])
            artifacts.append({
                "name": "prometheus.yml",
                "type": ArtifactType.CONFIGURATION.value,
                "content": prometheus_config,
                "metadata": {"type": "prometheus"}
            })
            
            # 2. 알람 규칙
            alert_rules_yaml = await self.generate_alert_rules_yaml(alert_rules)
            artifacts.append({
                "name": "alert_rules.yml",
                "type": ArtifactType.CONFIGURATION.value,
                "content": alert_rules_yaml,
                "metadata": {"type": "prometheus_alerts"}
            })
            
            # 3. Grafana 대시보드
            grafana_dashboard = await self.generate_grafana_dashboard(dashboard)
            artifacts.append({
                "name": "grafana_dashboard.json",
                "type": ArtifactType.CONFIGURATION.value,
                "content": json.dumps(grafana_dashboard, indent=2),
                "metadata": {"type": "grafana"}
            })
            
            # 4. 성능 리포트
            performance_report = await self.generate_performance_report(
                collected_metrics,
                log_analysis
            )
            artifacts.append({
                "name": "performance_report.md",
                "type": ArtifactType.DOCUMENTATION.value,
                "content": performance_report,
                "metadata": {"format": "markdown"}
            })
            
            # 5. 모니터링 스크립트
            monitoring_script = self._generate_monitoring_script()
            artifacts.append({
                "name": "monitoring_setup.sh",
                "type": ArtifactType.CODE.value,
                "content": monitoring_script,
                "metadata": {"type": "shell"}
            })
            
            # 결과 구성
            result_data = {
                "monitoring_config": {
                    "metrics_collected": list(collected_metrics.keys()),
                    "alert_rules": len(alert_rules),
                    "dashboards": len(self.dashboards)
                },
                "analysis_summary": {
                    "total_logs": log_analysis["total_logs"],
                    "error_logs": log_analysis["error_logs"],
                    "anomalies": len(log_analysis["anomalies"]),
                    "top_errors": log_analysis["top_errors"][:3]
                },
                "metrics_summary": {
                    "cpu_average": self._calculate_average(collected_metrics.get("cpu_usage", [])),
                    "memory_average": self._calculate_average(collected_metrics.get("memory_usage", [])),
                    "latency_p95": self._calculate_average(collected_metrics.get("latency", [])),
                    "error_rate": self._calculate_average(collected_metrics.get("error_rate", []))
                }
            }
            
            return AgentResult(
                success=True,
                output=result_data,
                artifacts=artifacts,
                messages=[
                    f"Collected metrics for {len(metric_types)} metric types",
                    f"Analyzed {log_analysis['total_logs']} logs, found {log_analysis['error_logs']} errors",
                    f"Created {len(alert_rules)} alert rules",
                    f"Generated {len(self.dashboards)} monitoring dashboards",
                    "Created complete monitoring configuration"
                ],
                metrics={
                    "metrics_collected": len(collected_metrics),
                    "logs_analyzed": log_analysis["total_logs"],
                    "alerts_configured": len(alert_rules),
                    "dashboards_created": len(self.dashboards),
                    "artifacts_created": len(artifacts)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process monitoring result: {e}")
            return AgentResult(
                success=False,
                output=None,
                errors=[str(e)],
                metrics={"error_type": type(e).__name__}
            )
    
    def _generate_monitoring_script(self) -> str:
        """모니터링 설정 스크립트 생성"""
        return """#!/bin/bash

# Monitoring Setup Script

echo "Setting up monitoring infrastructure..."

# Install Prometheus
if ! command -v prometheus &> /dev/null; then
    echo "Installing Prometheus..."
    wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
    tar xvf prometheus-2.40.0.linux-amd64.tar.gz
    sudo cp prometheus-2.40.0.linux-amd64/prometheus /usr/local/bin/
    sudo cp prometheus-2.40.0.linux-amd64/promtool /usr/local/bin/
fi

# Install Grafana
if ! command -v grafana-server &> /dev/null; then
    echo "Installing Grafana..."
    sudo apt-get install -y adduser libfontconfig1
    wget https://dl.grafana.com/oss/release/grafana_9.3.0_amd64.deb
    sudo dpkg -i grafana_9.3.0_amd64.deb
fi

# Install Node Exporter
if ! command -v node_exporter &> /dev/null; then
    echo "Installing Node Exporter..."
    wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
    tar xvf node_exporter-1.5.0.linux-amd64.tar.gz
    sudo cp node_exporter-1.5.0.linux-amd64/node_exporter /usr/local/bin/
fi

# Create directories
sudo mkdir -p /etc/prometheus
sudo mkdir -p /var/lib/prometheus
sudo mkdir -p /etc/grafana/provisioning/dashboards
sudo mkdir -p /etc/grafana/provisioning/datasources

# Copy configuration files
sudo cp prometheus.yml /etc/prometheus/
sudo cp alert_rules.yml /etc/prometheus/
sudo cp grafana_dashboard.json /etc/grafana/provisioning/dashboards/

# Create Grafana datasource
cat > /tmp/prometheus-datasource.yaml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
EOF

sudo cp /tmp/prometheus-datasource.yaml /etc/grafana/provisioning/datasources/

# Create systemd services
# Prometheus service
sudo tee /etc/systemd/system/prometheus.service > /dev/null << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/prometheus \\
    --config.file=/etc/prometheus/prometheus.yml \\
    --storage.tsdb.path=/var/lib/prometheus/

[Install]
WantedBy=multi-user.target
EOF

# Node Exporter service
sudo tee /etc/systemd/system/node_exporter.service > /dev/null << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable prometheus node_exporter grafana-server
sudo systemctl start prometheus node_exporter grafana-server

echo "Monitoring setup complete!"
echo "Access Prometheus at: http://localhost:9090"
echo "Access Grafana at: http://localhost:3000 (admin/admin)"
"""
    
    async def _validate_specific_input(self, context: AgentContext) -> Optional[str]:
        """모니터링 특화 입력 검증"""
        # 배포 결과가 있는지 확인 (선택적)
        if "deployment_result" not in context.previous_results:
            logger.warning("No deployment result found, will create generic monitoring setup")
        
        return None
    
    async def _validate_specific_output(self, result: AgentResult) -> Optional[str]:
        """모니터링 특화 출력 검증"""
        if not result.output:
            return "No monitoring output generated"
        
        output = result.output
        if not isinstance(output, dict):
            return "Invalid output format"
        
        # 모니터링 설정 검증
        if "monitoring_config" not in output:
            return "Missing monitoring configuration"
        
        # 분석 요약 검증
        if "analysis_summary" not in output:
            return "Missing analysis summary"
        
        return None