# Monitoring & Observability Setup

This document describes how to set up monitoring, alerting, and observability for the World Cup Betting Insights CLI/API.

---

## Table of Contents

1. [Prometheus Metrics](#prometheus-metrics)
2. [Sentry Error Tracking](#sentry-error-tracking)
3. [Alerting Setup](#alerting-setup)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Log Aggregation](#log-aggregation)

---

## Prometheus Metrics

### Enabling Metrics

Metrics are exposed at `/metrics` endpoint. To enable:

```bash
# Set environment variable
export ENABLE_METRICS=true
export PROMETHEUS_PORT=9090
```

### Available Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `http_requests_total` | Counter | Total HTTP requests | method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency | method, endpoint |
| `http_requests_active` | Gauge | Currently active requests | - |
| `http_errors_total` | Counter | Total errors | method, endpoint, error_type |

### Example Queries

```promql
# Request rate per second
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m]))

# Active requests
http_requests_active
```

---

## Sentry Error Tracking

### Installation

```bash
pip install sentry-sdk[fastapi]
```

### Configuration

```bash
# Required
export SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Optional
export SENTRY_TRACES_SAMPLE_RATE=0.1
export SENTRY_PROFILES_SAMPLE_RATE=0.1
export SENTRY_RELEASE=world-cup-betting-cli@0.1.0
```

### Initialization

In your application startup:

```python
from src.utils.sentry import init_sentry

init_sentry(environment="production")
```

---

## Alerting Setup

### Prometheus Alert Rules

Create `monitoring/alerts.yml`:

```yaml
groups:
  - name: worldcup-alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s"

      # Service down
      - alert: ServiceDown
        expr: up{job="worldcup-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "World Cup API is down"
          description: "Service has been down for more than 1 minute"

      # Rate limit exceeded
      - alert: RateLimitExceeded
        expr: increase(http_errors_total{error_type="client_error"}[5m]) > 100
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "High rate of rate-limit errors"
          description: "Many clients hitting rate limits"
```

### Alertmanager Configuration

Create `monitoring/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-receiver'
  
  routes:
    - match:
        severity: critical
      receiver: 'critical-receiver'

receivers:
  - name: 'default-receiver'
    email_configs:
      - to: 'team@example.com'
        
  - name: 'critical-receiver'
    email_configs:
      - to: 'oncall@example.com'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
```

---

## Grafana Dashboards

### Import Dashboard

1. Access Grafana at `http://localhost:3000` (default credentials: admin/admin)
2. Go to Dashboards → Import
3. Use dashboard ID or upload JSON

### Sample Dashboard JSON

Create `monitoring/grafana/dashboards/worldcup.json`:

```json
{
  "dashboard": {
    "title": "World Cup Betting Insights",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Latency (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m]))"
          }
        ]
      }
    ]
  }
}
```

---

## Log Aggregation

### Structured Logging

Enable JSON logging for log aggregation:

```bash
export LOG_STRUCTURED=true
export LOG_FILE=/var/log/worldcup/app.log
```

### Example Log Entry

```json
{
  "timestamp": "2026-06-11T22:00:00.000Z",
  "level": "INFO",
  "logger": "worldcup.api",
  "message": "Request processed successfully"
}
```

### ELK Stack Integration

For Elasticsearch + Logstash + Kibana:

1. Configure Filebeat to ship logs:

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/worldcup/*.log
    json.keys_under_root: true
    
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "worldcup-logs-%{+YYYY.MM.dd}"
```

2. Create Kibana index pattern: `worldcup-logs-*`

3. Build dashboards in Kibana

---

## Health Checks

### Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": 1718143200.0
}
```

### Docker Health Check

Already configured in Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

---

## Quick Start with Docker Compose

Start full monitoring stack:

```bash
docker-compose --profile monitoring up -d
```

Access points:
- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## Troubleshooting

### Metrics Not Showing

1. Check `ENABLE_METRICS=true` is set
2. Verify `/metrics` endpoint returns data
3. Check Prometheus target status at http://localhost:9090/targets

### Sentry Not Receiving Events

1. Verify `SENTRY_DSN` is correct
2. Check network connectivity to Sentry
3. Enable debug: `SENTRY_DEBUG=true`

### Alerts Not Firing

1. Check Prometheus alert rules at http://localhost:9090/alerts
2. Verify Alertmanager configuration
3. Check notification channel credentials
