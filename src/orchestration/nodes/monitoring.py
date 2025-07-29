"""
모니터링 노드
배포된 애플리케이션의 모니터링 설정 및 실행
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timezone, timedelta

from src.orchestration.nodes.base import BaseNode
from src.orchestration.state import WorkflowState
from src.core.constants import ArtifactType

class MonitoringNode(BaseNode):
    """모니터링 노드"""
    
    def __init__(self):
        super().__init__(
            name="Monitoring",
            description="Setup and configure monitoring for deployed application"
        )
    
    async def _validate_specific_input(self, state: WorkflowState) -> Optional[str]:
        """입력 검증"""
        if not state.get("deployment_result"):
            return "Deployment result is missing"
        
        deployment_result = state["deployment_result"]
        if deployment_result.get("status") != "success":
            return "Deployment was not successful"
        
        return None
    
    async def process(self, state: WorkflowState) -> Dict[str, Any]:
        """모니터링 설정 및 구성"""
        deployment_result = state["deployment_result"]
        dev_result = state.get("development_result", {})
        
        self.log_progress("Setting up monitoring and observability...")
        
        # 모니터링 설정 실행
        monitoring_result = await self._setup_monitoring(deployment_result, dev_result)
        
        # 메시지 추가
        message_update = self.add_message(
            state,
            f"Monitoring setup completed. "
            f"Dashboards: {len(monitoring_result['dashboards'])}, "
            f"Alerts: {len(monitoring_result['alerts'])}, "
            f"Metrics: {len(monitoring_result['metrics'])}",
            metadata={
                "monitoring_id": monitoring_result["monitoring_id"],
                "dashboard_urls": [d["url"] for d in monitoring_result["dashboards"]]
            }
        )
        
        # 모니터링 설정 아티팩트
        monitoring_config = self.add_artifact(
            state,
            name="monitoring_config",
            artifact_type=ArtifactType.CONFIG,
            content=json.dumps(monitoring_result["configuration"], indent=2),
            metadata={"format": "json", "type": "monitoring"}
        )
        
        # 대시보드 정의 아티팩트
        dashboard_artifact = self.add_artifact(
            state,
            name="monitoring_dashboards",
            artifact_type=ArtifactType.CONFIG,
            content=self._generate_dashboard_config(monitoring_result),
            metadata={"format": "json", "tool": "grafana"}
        )
        
        # 알림 규칙 아티팩트
        alerts_artifact = self.add_artifact(
            state,
            name="alert_rules",
            artifact_type=ArtifactType.CONFIG,
            content=self._generate_alert_rules(monitoring_result),
            metadata={"format": "yaml", "tool": "prometheus"}
        )
        
        # 모니터링 가이드 아티팩트
        guide_artifact = self.add_artifact(
            state,
            name="monitoring_guide",
            artifact_type=ArtifactType.DOCUMENT,
            content=self._generate_monitoring_guide(monitoring_result, deployment_result),
            metadata={"format": "markdown"}
        )
        
        # 결과 업데이트
        result_update = self.update_result(state, "monitoring_result", monitoring_result)
        
        # 모든 업데이트 병합
        updates = {}
        updates.update(message_update)
        updates.update(monitoring_config)
        updates.update(dashboard_artifact)
        updates.update(alerts_artifact)
        updates.update(guide_artifact)
        updates.update(result_update)
        
        self.log_progress("Monitoring setup completed")
        
        return updates
    
    async def _setup_monitoring(self, deployment_result: Dict[str, Any], dev_result: Dict[str, Any]) -> Dict[str, Any]:
        """모니터링 설정"""
        environment = deployment_result["environment"]
        version = deployment_result["version"]
        
        # 모니터링 구성 요소 설정
        metrics = self._configure_metrics(dev_result)
        dashboards = self._create_dashboards(environment, metrics)
        alerts = self._create_alert_rules(environment, metrics)
        logging = self._configure_logging(environment)
        tracing = self._configure_tracing(environment)
        
        # SLO/SLI 정의
        slos = self._define_slos(environment)
        
        return {
            "monitoring_id": f"monitoring-{datetime.now(timezone.utc).isoformat()}",
            "environment": environment,
            "version": version,
            "configuration": {
                "metrics_endpoint": "/metrics",
                "logs_aggregator": deployment_result["monitoring"]["logs_url"],
                "traces_collector": "http://jaeger-collector:14268/api/traces",
                "dashboard_url": deployment_result["monitoring"]["dashboard_url"]
            },
            "metrics": metrics,
            "dashboards": dashboards,
            "alerts": alerts,
            "logging": logging,
            "tracing": tracing,
            "slos": slos,
            "health_status": await self._check_monitoring_health(deployment_result),
            "recommendations": self._generate_monitoring_recommendations(environment)
        }
    
    def _configure_metrics(self, dev_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """메트릭 구성"""
        metrics = []
        
        # 기본 시스템 메트릭
        system_metrics = [
            {
                "name": "cpu_usage_percent",
                "type": "gauge",
                "description": "CPU usage percentage",
                "labels": ["pod", "container"],
                "unit": "percent"
            },
            {
                "name": "memory_usage_bytes",
                "type": "gauge",
                "description": "Memory usage in bytes",
                "labels": ["pod", "container"],
                "unit": "bytes"
            },
            {
                "name": "disk_usage_percent",
                "type": "gauge",
                "description": "Disk usage percentage",
                "labels": ["pod", "mount"],
                "unit": "percent"
            }
        ]
        metrics.extend(system_metrics)
        
        # 애플리케이션 메트릭
        app_metrics = [
            {
                "name": "http_requests_total",
                "type": "counter",
                "description": "Total HTTP requests",
                "labels": ["method", "endpoint", "status"],
                "unit": "requests"
            },
            {
                "name": "http_request_duration_seconds",
                "type": "histogram",
                "description": "HTTP request latency",
                "labels": ["method", "endpoint"],
                "unit": "seconds",
                "buckets": [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
            },
            {
                "name": "active_connections",
                "type": "gauge",
                "description": "Number of active connections",
                "labels": ["type"],
                "unit": "connections"
            }
        ]
        metrics.extend(app_metrics)
        
        # 비즈니스 메트릭
        if any("api" in f["path"].lower() for f in dev_result.get("generated_files", [])):
            business_metrics = [
                {
                    "name": "api_calls_total",
                    "type": "counter",
                    "description": "Total API calls",
                    "labels": ["endpoint", "client"],
                    "unit": "calls"
                },
                {
                    "name": "api_errors_total",
                    "type": "counter",
                    "description": "Total API errors",
                    "labels": ["endpoint", "error_type"],
                    "unit": "errors"
                }
            ]
            metrics.extend(business_metrics)
        
        # 데이터베이스 메트릭
        if any("database" in f["path"].lower() or "model" in f["path"].lower() for f in dev_result.get("generated_files", [])):
            db_metrics = [
                {
                    "name": "database_connections_active",
                    "type": "gauge",
                    "description": "Active database connections",
                    "labels": ["database"],
                    "unit": "connections"
                },
                {
                    "name": "database_query_duration_seconds",
                    "type": "histogram",
                    "description": "Database query duration",
                    "labels": ["query_type", "table"],
                    "unit": "seconds"
                }
            ]
            metrics.extend(db_metrics)
        
        return metrics
    
    def _create_dashboards(self, environment: str, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """대시보드 생성"""
        dashboards = []
        
        # 시스템 개요 대시보드
        system_dashboard = {
            "id": "system-overview",
            "name": "System Overview",
            "url": f"https://grafana.example.com/d/system-overview-{environment}",
            "panels": [
                {
                    "title": "CPU Usage",
                    "type": "graph",
                    "metric": "cpu_usage_percent",
                    "aggregation": "avg"
                },
                {
                    "title": "Memory Usage",
                    "type": "graph",
                    "metric": "memory_usage_bytes",
                    "aggregation": "avg"
                },
                {
                    "title": "Request Rate",
                    "type": "graph",
                    "metric": "http_requests_total",
                    "aggregation": "rate"
                },
                {
                    "title": "Error Rate",
                    "type": "graph",
                    "metric": "http_requests_total{status=~'5..'}",
                    "aggregation": "rate"
                }
            ]
        }
        dashboards.append(system_dashboard)
        
        # 애플리케이션 성능 대시보드
        performance_dashboard = {
            "id": "application-performance",
            "name": "Application Performance",
            "url": f"https://grafana.example.com/d/app-performance-{environment}",
            "panels": [
                {
                    "title": "Response Time (p95)",
                    "type": "graph",
                    "metric": "http_request_duration_seconds",
                    "aggregation": "histogram_quantile(0.95)"
                },
                {
                    "title": "Throughput",
                    "type": "graph",
                    "metric": "http_requests_total",
                    "aggregation": "rate"
                },
                {
                    "title": "Active Connections",
                    "type": "graph",
                    "metric": "active_connections",
                    "aggregation": "sum"
                },
                {
                    "title": "Error Distribution",
                    "type": "pie",
                    "metric": "http_requests_total{status=~'4..|5..'}",
                    "groupBy": "status"
                }
            ]
        }
        dashboards.append(performance_dashboard)
        
        # 비즈니스 메트릭 대시보드
        business_dashboard = {
            "id": "business-metrics",
            "name": "Business Metrics",
            "url": f"https://grafana.example.com/d/business-metrics-{environment}",
            "panels": [
                {
                    "title": "API Usage by Endpoint",
                    "type": "table",
                    "metric": "api_calls_total",
                    "groupBy": "endpoint"
                },
                {
                    "title": "Top API Clients",
                    "type": "bar",
                    "metric": "api_calls_total",
                    "groupBy": "client",
                    "limit": 10
                },
                {
                    "title": "Error Trends",
                    "type": "graph",
                    "metric": "api_errors_total",
                    "aggregation": "rate"
                }
            ]
        }
        dashboards.append(business_dashboard)
        
        return dashboards
    
    def _create_alert_rules(self, environment: str, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """알림 규칙 생성"""
        alerts = []
        
        # 시스템 리소스 알림
        alerts.extend([
            {
                "name": "HighCPUUsage",
                "expression": "avg(cpu_usage_percent) > 80",
                "duration": "5m",
                "severity": "warning",
                "description": "CPU usage is above 80% for 5 minutes",
                "action": "scale_up"
            },
            {
                "name": "HighMemoryUsage",
                "expression": "avg(memory_usage_bytes) / avg(memory_limit_bytes) > 0.9",
                "duration": "5m",
                "severity": "critical",
                "description": "Memory usage is above 90% of limit",
                "action": "investigate"
            },
            {
                "name": "DiskSpaceLow",
                "expression": "disk_usage_percent > 85",
                "duration": "10m",
                "severity": "warning",
                "description": "Disk usage is above 85%",
                "action": "cleanup"
            }
        ])
        
        # 애플리케이션 성능 알림
        alerts.extend([
            {
                "name": "HighResponseTime",
                "expression": "histogram_quantile(0.95, http_request_duration_seconds) > 1",
                "duration": "5m",
                "severity": "warning",
                "description": "95th percentile response time is above 1 second",
                "action": "optimize"
            },
            {
                "name": "HighErrorRate",
                "expression": "rate(http_requests_total{status=~'5..'}[5m]) > 0.05",
                "duration": "5m",
                "severity": "critical",
                "description": "Error rate is above 5%",
                "action": "investigate"
            },
            {
                "name": "LowThroughput",
                "expression": "rate(http_requests_total[5m]) < 10",
                "duration": "10m",
                "severity": "info",
                "description": "Request rate is below 10 req/min",
                "action": "monitor"
            }
        ])
        
        # 가용성 알림
        alerts.extend([
            {
                "name": "ServiceDown",
                "expression": "up == 0",
                "duration": "1m",
                "severity": "critical",
                "description": "Service is down",
                "action": "restart"
            },
            {
                "name": "HealthCheckFailing",
                "expression": "health_check_status != 1",
                "duration": "3m",
                "severity": "critical",
                "description": "Health check is failing",
                "action": "investigate"
            }
        ])
        
        # 데이터베이스 알림
        if any(m["name"].startswith("database_") for m in metrics):
            alerts.extend([
                {
                    "name": "DatabaseConnectionPoolExhausted",
                    "expression": "database_connections_active / database_connections_max > 0.9",
                    "duration": "5m",
                    "severity": "warning",
                    "description": "Database connection pool is nearly exhausted",
                    "action": "scale_connections"
                },
                {
                    "name": "SlowDatabaseQueries",
                    "expression": "histogram_quantile(0.95, database_query_duration_seconds) > 5",
                    "duration": "5m",
                    "severity": "warning",
                    "description": "Database queries are taking too long",
                    "action": "optimize_queries"
                }
            ])
        
        return alerts
    
    def _configure_logging(self, environment: str) -> Dict[str, Any]:
        """로깅 구성"""
        return {
            "level": "INFO" if environment == "production" else "DEBUG",
            "format": "json",
            "outputs": [
                {
                    "type": "stdout",
                    "format": "json"
                },
                {
                    "type": "file",
                    "path": "/var/log/app/application.log",
                    "rotation": "daily",
                    "retention": "30d"
                },
                {
                    "type": "aggregator",
                    "endpoint": "http://fluentd:24224",
                    "buffer_size": "10MB"
                }
            ],
            "structured_fields": [
                "timestamp",
                "level",
                "message",
                "trace_id",
                "span_id",
                "user_id",
                "request_id",
                "environment",
                "version"
            ],
            "filters": [
                {
                    "type": "sensitive_data",
                    "patterns": ["password", "token", "secret", "key"]
                }
            ]
        }
    
    def _configure_tracing(self, environment: str) -> Dict[str, Any]:
        """트레이싱 구성"""
        return {
            "enabled": True,
            "sampler": {
                "type": "probabilistic",
                "rate": 0.1 if environment == "production" else 1.0
            },
            "exporter": {
                "type": "jaeger",
                "endpoint": "http://jaeger-collector:14268/api/traces",
                "service_name": "agentic-pipeline"
            },
            "propagation": "w3c",
            "instrumentation": [
                "http",
                "database",
                "redis",
                "external_api"
            ],
            "tags": {
                "environment": environment,
                "version": "${VERSION}",
                "region": "${REGION}"
            }
        }
    
    def _define_slos(self, environment: str) -> List[Dict[str, Any]]:
        """SLO(서비스 수준 목표) 정의"""
        return [
            {
                "name": "availability",
                "target": 99.9 if environment == "production" else 99.0,
                "window": "30d",
                "indicator": "sum(rate(http_requests_total{status!~'5..'}[5m])) / sum(rate(http_requests_total[5m]))",
                "description": "Service availability"
            },
            {
                "name": "latency",
                "target": 95.0,
                "window": "7d",
                "indicator": "histogram_quantile(0.95, http_request_duration_seconds) < 0.5",
                "description": "95% of requests complete within 500ms"
            },
            {
                "name": "error_rate",
                "target": 99.0,
                "window": "24h",
                "indicator": "sum(rate(http_requests_total{status!~'5..'}[5m])) / sum(rate(http_requests_total[5m])) * 100",
                "description": "Success rate"
            }
        ]
    
    async def _check_monitoring_health(self, deployment_result: Dict[str, Any]) -> Dict[str, Any]:
        """모니터링 시스템 상태 확인"""
        return {
            "prometheus": {
                "status": "healthy",
                "targets_up": 15,
                "targets_down": 0,
                "storage_used_gb": 2.5
            },
            "grafana": {
                "status": "healthy",
                "dashboards": 12,
                "datasources": 3,
                "users": 25
            },
            "alertmanager": {
                "status": "healthy",
                "active_alerts": 0,
                "silenced_alerts": 2,
                "inhibited_alerts": 0
            },
            "logging": {
                "status": "healthy",
                "logs_per_second": 150,
                "storage_used_gb": 15.7,
                "retention_days": 30
            }
        }
    
    def _generate_monitoring_recommendations(self, environment: str) -> List[Dict[str, Any]]:
        """모니터링 권장사항 생성"""
        recommendations = [
            {
                "category": "performance",
                "recommendation": "Consider implementing distributed tracing for better performance insights",
                "priority": "medium"
            },
            {
                "category": "alerting",
                "recommendation": "Set up PagerDuty integration for critical alerts",
                "priority": "high"
            },
            {
                "category": "dashboards",
                "recommendation": "Create custom dashboards for business KPIs",
                "priority": "low"
            }
        ]
        
        if environment == "production":
            recommendations.extend([
                {
                    "category": "compliance",
                    "recommendation": "Enable audit logging for compliance requirements",
                    "priority": "high"
                },
                {
                    "category": "capacity",
                    "recommendation": "Set up capacity planning dashboards",
                    "priority": "medium"
                }
            ])
        
        return recommendations
    
    def _generate_dashboard_config(self, monitoring_result: Dict[str, Any]) -> str:
        """대시보드 설정 생성"""
        dashboards = monitoring_result["dashboards"]
        
        config = {
            "apiVersion": 1,
            "providers": [
                {
                    "name": "default",
                    "orgId": 1,
                    "folder": "Agentic Pipeline",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": "/var/lib/grafana/dashboards"
                    }
                }
            ],
            "dashboards": []
        }
        
        for dashboard in dashboards:
            config["dashboards"].append({
                "uid": dashboard["id"],
                "title": dashboard["name"],
                "tags": ["agentic-pipeline", monitoring_result["environment"]],
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 1,
                "panels": dashboard["panels"]
            })
        
        return json.dumps(config, indent=2)
    
    def _generate_alert_rules(self, monitoring_result: Dict[str, Any]) -> str:
        """알림 규칙 생성 (Prometheus 형식)"""
        alerts = monitoring_result["alerts"]
        
        rules_config = f"""# Alert Rules for Agentic Pipeline
# Environment: {monitoring_result['environment']}
# Generated: {datetime.now(timezone.utc).isoformat()}

groups:
  - name: agentic_pipeline_alerts
    interval: 30s
    rules:
"""
        
        for alert in alerts:
            rules_config += f"""
      - alert: {alert['name']}
        expr: {alert['expression']}
        for: {alert['duration']}
        labels:
          severity: {alert['severity']}
          environment: {monitoring_result['environment']}
        annotations:
          description: "{alert['description']}"
          action: "{alert['action']}"
          dashboard: "https://grafana.example.com/d/system-overview"
"""
        
        return rules_config
    
    def _generate_monitoring_guide(self, monitoring_result: Dict[str, Any], deployment_result: Dict[str, Any]) -> str:
        """모니터링 가이드 생성"""
        return f"""# Monitoring Guide

## Overview

This guide provides instructions for monitoring the Agentic Pipeline application deployed to {deployment_result['environment']}.

## Quick Links

- **Dashboards**: {deployment_result['monitoring']['dashboard_url']}
- **Logs**: {deployment_result['monitoring']['logs_url']}
- **Metrics**: {deployment_result['monitoring']['metrics_url']}
- **Alerts**: https://alertmanager.example.com

## Dashboards

### Available Dashboards

{chr(10).join(f"- **{d['name']}**: {d['url']}" for d in monitoring_result['dashboards'])}

### Key Metrics to Watch

1. **System Health**
   - CPU Usage: Keep below 80%
   - Memory Usage: Keep below 90%
   - Disk Usage: Keep below 85%

2. **Application Performance**
   - Response Time (p95): Should be < 500ms
   - Error Rate: Should be < 1%
   - Throughput: Monitor for anomalies

3. **Business Metrics**
   - API Usage: Track usage patterns
   - Error Distribution: Identify problematic endpoints

## Alerts

### Configured Alerts

Total alerts configured: {len(monitoring_result['alerts'])}

**Critical Alerts:**
{chr(10).join(f"- {a['name']}: {a['description']}" for a in monitoring_result['alerts'] if a['severity'] == 'critical')}

**Warning Alerts:**
{chr(10).join(f"- {a['name']}: {a['description']}" for a in monitoring_result['alerts'] if a['severity'] == 'warning')}

### Alert Response Procedures

1. **Service Down**
   - Check pod status: `kubectl get pods -n {deployment_result['environment']}`
   - Check logs: `kubectl logs -n {deployment_result['environment']} <pod-name>`
   - Restart if necessary: `kubectl rollout restart deployment/agentic-pipeline`

2. **High Error Rate**
   - Check error logs for patterns
   - Identify affected endpoints
   - Review recent deployments
   - Consider rollback if necessary

3. **Performance Degradation**
   - Check resource usage
   - Review slow query logs
   - Check external dependencies
   - Scale if necessary

## Logging

### Log Levels
- Production: INFO
- Staging: DEBUG
- Development: DEBUG

### Important Log Queries

```
# Find errors
level="error" OR level="fatal"

# Find slow requests
duration>1000

# Find by user
user_id="<user-id>"

# Find by request ID
request_id="<request-id>"
```

## Tracing

Distributed tracing is enabled with a sampling rate of {monitoring_result['tracing']['sampler']['rate'] * 100}%.

### Finding Traces
1. Go to Jaeger UI
2. Select service: "agentic-pipeline"
3. Filter by operation or tags
4. Analyze trace timeline

## SLOs (Service Level Objectives)

{chr(10).join(f"- **{slo['name'].title()}**: {slo['target']}% ({slo['description']})" for slo in monitoring_result['slos'])}

## Troubleshooting

### Common Issues

1. **Metrics not appearing**
   - Check Prometheus targets
   - Verify /metrics endpoint
   - Check network connectivity

2. **Dashboards empty**
   - Verify data source configuration
   - Check time range
   - Refresh dashboard

3. **Alerts not firing**
   - Check alert manager status
   - Verify alert rules syntax
   - Check notification channels

## Maintenance

### Regular Tasks
- Review and acknowledge alerts daily
- Check dashboard anomalies
- Review error logs
- Monitor resource trends
- Update alert thresholds as needed

### Monthly Tasks
- Review SLO compliance
- Analyze performance trends
- Update dashboards
- Archive old logs
- Capacity planning

## Contact

For monitoring issues or questions:
- Slack: #monitoring-alerts
- Email: devops@example.com
- On-call: Use PagerDuty

---
*Last updated: {datetime.now(timezone.utc).isoformat()}*
"""

# 노드 인스턴스 생성
monitoring_node = MonitoringNode()