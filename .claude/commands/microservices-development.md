# 마이크로서비스 개발 워크플로우

## 🎯 마이크로서비스 아키텍처 자동 구축
**목표 완료 시간: 4-5시간**

다음의 마이크로서비스 시스템을 개발해주세요: $ARGUMENTS

## 워크플로우 단계

### 1단계: 시스템 설계 및 서비스 분해 (45분)

다음을 수행해줘:

#### 도메인 분석
- 비즈니스 도메인 모델링
- Bounded Context 정의
- 서비스 경계 식별
- 데이터 흐름 매핑

#### 마이크로서비스 설계
```yaml
# architecture/services.yaml
services:
  - name: user-service
    description: 사용자 관리 및 인증
    port: 8001
    database: postgresql
    
  - name: product-service
    description: 상품 카탈로그 관리
    port: 8002
    database: mongodb
    
  - name: order-service
    description: 주문 처리 및 관리
    port: 8003
    database: postgresql
    
  - name: payment-service
    description: 결제 처리
    port: 8004
    database: postgresql
    
  - name: notification-service
    description: 알림 전송
    port: 8005
    database: redis
```

#### 통신 패턴 정의
- 동기 통신: REST/gRPC
- 비동기 통신: 메시지 큐/이벤트 스트리밍
- 서비스 메시 고려사항
- API Gateway 설계

docs/architecture/ 디렉토리에 생성:
- domain-model.md
- service-boundaries.md
- communication-patterns.md
- data-management-strategy.md

### 2단계: 인프라 및 개발 환경 구성 (30분)

다음을 수행해줘:

#### Docker Compose 설정
```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Gateway
  api-gateway:
    build: ./api-gateway
    ports:
      - "8080:8080"
    environment:
      - SERVICE_DISCOVERY_URL=http://consul:8500
    depends_on:
      - consul
    networks:
      - microservices

  # Service Discovery
  consul:
    image: consul:latest
    ports:
      - "8500:8500"
      - "8600:8600/udp"
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0
    networks:
      - microservices

  # Message Broker
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=admin
    networks:
      - microservices

  # Distributed Tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - microservices

  # Metrics Collection
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - microservices

  # Visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
    networks:
      - microservices

networks:
  microservices:
    driver: bridge
```

#### 프로젝트 구조
```
microservices-system/
├── api-gateway/
├── services/
│   ├── user-service/
│   ├── product-service/
│   ├── order-service/
│   ├── payment-service/
│   └── notification-service/
├── shared/
│   ├── proto/
│   ├── contracts/
│   └── libraries/
├── infrastructure/
│   ├── kubernetes/
│   ├── terraform/
│   └── scripts/
└── docker-compose.yml
```

### 3단계: 공통 라이브러리 및 계약 정의 (30분)

다음을 수행해줘:

#### Protocol Buffers 정의
```protobuf
// shared/proto/user.proto
syntax = "proto3";

package user;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(DeleteUserRequest) returns (Empty);
}

message User {
  string id = 1;
  string email = 2;
  string name = 3;
  string role = 4;
  int64 created_at = 5;
  int64 updated_at = 6;
}

message GetUserRequest {
  string id = 1;
}

message CreateUserRequest {
  string email = 1;
  string password = 2;
  string name = 3;
}
```

#### 이벤트 스키마
```json
// shared/contracts/events/user-events.json
{
  "UserCreated": {
    "type": "object",
    "properties": {
      "eventId": { "type": "string" },
      "timestamp": { "type": "string" },
      "userId": { "type": "string" },
      "email": { "type": "string" },
      "name": { "type": "string" }
    }
  },
  "UserUpdated": {
    "type": "object",
    "properties": {
      "eventId": { "type": "string" },
      "timestamp": { "type": "string" },
      "userId": { "type": "string" },
      "changes": { "type": "object" }
    }
  }
}
```

#### 공통 라이브러리
```go
// shared/libraries/go/middleware/tracing.go
package middleware

import (
    "github.com/opentracing/opentracing-go"
    "github.com/uber/jaeger-client-go"
    "github.com/gin-gonic/gin"
)

func TracingMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        tracer := opentracing.GlobalTracer()
        
        spanContext, _ := tracer.Extract(
            opentracing.HTTPHeaders,
            opentracing.HTTPHeadersCarrier(c.Request.Header),
        )
        
        span := tracer.StartSpan(
            c.Request.URL.Path,
            opentracing.ChildOf(spanContext),
        )
        defer span.Finish()
        
        c.Set("span", span)
        c.Next()
    }
}
```

### 4단계: API Gateway 구현 (30분)

다음을 수행해줘:

#### Kong API Gateway 설정
```yaml
# api-gateway/kong.yml
_format_version: "2.1"

services:
  - name: user-service
    url: http://user-service:8001
    routes:
      - name: user-routes
        paths:
          - /api/v1/users
        strip_path: false
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: jwt
      - name: cors

  - name: product-service
    url: http://product-service:8002
    routes:
      - name: product-routes
        paths:
          - /api/v1/products
        strip_path: false
    plugins:
      - name: rate-limiting
        config:
          minute: 200
      - name: request-transformer
        config:
          add:
            headers:
              - X-Service:product

  - name: order-service
    url: http://order-service:8003
    routes:
      - name: order-routes
        paths:
          - /api/v1/orders
        strip_path: false
    plugins:
      - name: jwt
      - name: request-size-limiting
        config:
          allowed_payload_size: 8
```

#### Custom Gateway (Node.js)
```typescript
// api-gateway/src/index.ts
import express from 'express';
import httpProxy from 'http-proxy-middleware';
import consul from 'consul';
import jwt from 'jsonwebtoken';
import rateLimit from 'express-rate-limit';
import { CircuitBreaker } from 'opossum';

const app = express();
const consulClient = consul({ host: 'consul', port: 8500 });

// Rate Limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100
});

// JWT Verification
const verifyToken = (req, res, next) => {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).send('No token provided');
  
  jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
    if (err) return res.status(403).send('Invalid token');
    req.userId = decoded.id;
    next();
  });
};

// Service Discovery
const getServiceUrl = async (serviceName: string) => {
  const services = await consulClient.health.service(serviceName);
  if (services.length === 0) throw new Error('Service not found');
  
  const service = services[0];
  return `http://${service.Service.Address}:${service.Service.Port}`;
};

// Circuit Breaker
const createCircuitBreaker = (serviceUrl: string) => {
  return new CircuitBreaker(
    async (req, res) => {
      return httpProxy.createProxyMiddleware({
        target: serviceUrl,
        changeOrigin: true,
      })(req, res);
    },
    {
      timeout: 3000,
      errorThresholdPercentage: 50,
      resetTimeout: 30000
    }
  );
};

// Dynamic Routing
const services = ['user', 'product', 'order', 'payment', 'notification'];

services.forEach(service => {
  app.use(`/api/v1/${service}s`, limiter, verifyToken, async (req, res) => {
    try {
      const serviceUrl = await getServiceUrl(`${service}-service`);
      const breaker = createCircuitBreaker(serviceUrl);
      await breaker.fire(req, res);
    } catch (error) {
      res.status(503).json({ error: 'Service unavailable' });
    }
  });
});

app.listen(8080, () => {
  console.log('API Gateway running on port 8080');
});
```

### 5단계: 마이크로서비스 구현 (90분)

다음을 수행해줘:

#### User Service (Go)
```go
// services/user-service/main.go
package main

import (
    "github.com/gin-gonic/gin"
    "github.com/jinzhu/gorm"
    _ "github.com/lib/pq"
    "github.com/nats-io/nats.go"
)

type User struct {
    ID        string `json:"id" gorm:"primary_key"`
    Email     string `json:"email" gorm:"unique"`
    Name      string `json:"name"`
    Password  string `json:"-"`
    CreatedAt int64  `json:"created_at"`
    UpdatedAt int64  `json:"updated_at"`
}

type UserService struct {
    db   *gorm.DB
    nats *nats.Conn
}

func (s *UserService) CreateUser(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    
    // Hash password
    user.Password = hashPassword(user.Password)
    
    // Save to database
    if err := s.db.Create(&user).Error; err != nil {
        c.JSON(500, gin.H{"error": "Failed to create user"})
        return
    }
    
    // Publish event
    event := map[string]interface{}{
        "eventType": "UserCreated",
        "userId":    user.ID,
        "email":     user.Email,
        "name":      user.Name,
        "timestamp": time.Now().Unix(),
    }
    
    eventData, _ := json.Marshal(event)
    s.nats.Publish("user.created", eventData)
    
    c.JSON(201, user)
}

func main() {
    // Database connection
    db, err := gorm.Open("postgres", "host=postgres user=user dbname=users password=pass")
    if err != nil {
        panic("Failed to connect to database")
    }
    defer db.Close()
    
    // Migrate schema
    db.AutoMigrate(&User{})
    
    // NATS connection
    nc, err := nats.Connect("nats://nats:4222")
    if err != nil {
        panic("Failed to connect to NATS")
    }
    defer nc.Close()
    
    service := &UserService{db: db, nats: nc}
    
    // Setup routes
    r := gin.Default()
    
    // Middleware
    r.Use(TracingMiddleware())
    r.Use(MetricsMiddleware())
    
    // Routes
    r.POST("/users", service.CreateUser)
    r.GET("/users/:id", service.GetUser)
    r.PUT("/users/:id", service.UpdateUser)
    r.DELETE("/users/:id", service.DeleteUser)
    
    // Health check
    r.GET("/health", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "healthy"})
    })
    
    // Service registration
    registerService("user-service", "8001")
    
    r.Run(":8001")
}
```

#### Order Service (Node.js)
```javascript
// services/order-service/index.js
const express = require('express');
const { Sequelize, DataTypes } = require('sequelize');
const amqp = require('amqplib');
const { Kafka } = require('kafkajs');
const opentracing = require('opentracing');
const jaeger = require('jaeger-client');

// Initialize tracer
const tracer = jaeger.initTracer({
  serviceName: 'order-service',
  reporter: {
    agentHost: 'jaeger',
    agentPort: 6832,
  },
  sampler: {
    type: 'const',
    param: 1,
  },
});

// Database
const sequelize = new Sequelize('orders', 'user', 'pass', {
  host: 'postgres',
  dialect: 'postgres',
});

// Order Model
const Order = sequelize.define('Order', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  userId: {
    type: DataTypes.UUID,
    allowNull: false,
  },
  items: {
    type: DataTypes.JSONB,
    allowNull: false,
  },
  totalAmount: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false,
  },
  status: {
    type: DataTypes.ENUM('pending', 'paid', 'shipped', 'delivered', 'cancelled'),
    defaultValue: 'pending',
  },
  paymentId: DataTypes.UUID,
  shippingAddress: DataTypes.JSONB,
});

// Kafka setup
const kafka = new Kafka({
  clientId: 'order-service',
  brokers: ['kafka:9092'],
});

const producer = kafka.producer();
const consumer = kafka.consumer({ groupId: 'order-service-group' });

class OrderService {
  async createOrder(orderData, span) {
    const childSpan = tracer.startSpan('create-order', { childOf: span });
    
    try {
      // Validate inventory (call product service)
      const inventoryValid = await this.checkInventory(orderData.items);
      if (!inventoryValid) {
        throw new Error('Insufficient inventory');
      }
      
      // Create order
      const order = await Order.create(orderData);
      
      // Send order created event
      await producer.send({
        topic: 'order-events',
        messages: [{
          key: order.id,
          value: JSON.stringify({
            eventType: 'OrderCreated',
            orderId: order.id,
            userId: order.userId,
            totalAmount: order.totalAmount,
            timestamp: new Date().toISOString(),
          }),
        }],
      });
      
      childSpan.finish();
      return order;
    } catch (error) {
      childSpan.setTag('error', true);
      childSpan.log({ event: 'error', message: error.message });
      childSpan.finish();
      throw error;
    }
  }
  
  async processPayment(orderId, paymentId) {
    const order = await Order.findByPk(orderId);
    if (!order) throw new Error('Order not found');
    
    order.paymentId = paymentId;
    order.status = 'paid';
    await order.save();
    
    // Send order paid event
    await producer.send({
      topic: 'order-events',
      messages: [{
        key: orderId,
        value: JSON.stringify({
          eventType: 'OrderPaid',
          orderId: orderId,
          paymentId: paymentId,
          timestamp: new Date().toISOString(),
        }),
      }],
    });
  }
}

// Express app
const app = express();
app.use(express.json());

const orderService = new OrderService();

// Middleware for tracing
app.use((req, res, next) => {
  const span = tracer.extract(opentracing.FORMAT_HTTP_HEADERS, req.headers);
  req.span = tracer.startSpan(req.path, {
    childOf: span,
  });
  next();
});

// Routes
app.post('/orders', async (req, res) => {
  try {
    const order = await orderService.createOrder(req.body, req.span);
    res.status(201).json(order);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
  req.span.finish();
});

app.get('/orders/:id', async (req, res) => {
  const order = await Order.findByPk(req.params.id);
  if (!order) {
    res.status(404).json({ error: 'Order not found' });
  } else {
    res.json(order);
  }
  req.span.finish();
});

// Event consumers
async function startConsumer() {
  await consumer.connect();
  await consumer.subscribe({ topic: 'payment-events', fromBeginning: true });
  
  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const event = JSON.parse(message.value.toString());
      
      if (event.eventType === 'PaymentCompleted') {
        await orderService.processPayment(event.orderId, event.paymentId);
      }
    },
  });
}

// Start server
async function start() {
  await sequelize.sync();
  await producer.connect();
  await startConsumer();
  
  app.listen(8003, () => {
    console.log('Order service running on port 8003');
  });
}

start().catch(console.error);
```

#### Payment Service (Python)
```python
# services/payment-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
import stripe
import redis
import json
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@postgres/payments'
db = SQLAlchemy(app)

# Celery configuration
celery = Celery('payment-service', broker='redis://redis:6379')

# Redis client
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Stripe configuration
stripe.api_key = 'sk_test_...'

# Tracing setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

class Payment(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    order_id = db.Column(db.String(36), nullable=False)
    amount = db.Column(db.Decimal(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='pending')
    stripe_payment_intent_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/payments', methods=['POST'])
def create_payment():
    with tracer.start_as_current_span("create_payment"):
        data = request.json
        
        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(data['amount'] * 100),  # Convert to cents
            currency=data.get('currency', 'usd'),
            metadata={
                'order_id': data['order_id']
            }
        )
        
        # Save payment record
        payment = Payment(
            id=str(uuid.uuid4()),
            order_id=data['order_id'],
            amount=data['amount'],
            stripe_payment_intent_id=intent.id
        )
        db.session.add(payment)
        db.session.commit()
        
        # Send payment created event
        publish_event('payment.created', {
            'eventType': 'PaymentCreated',
            'paymentId': payment.id,
            'orderId': payment.order_id,
            'amount': float(payment.amount),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'paymentId': payment.id,
            'clientSecret': intent.client_secret
        }), 201

@app.route('/payments/<payment_id>/confirm', methods=['POST'])
def confirm_payment(payment_id):
    with tracer.start_as_current_span("confirm_payment"):
        payment = Payment.query.get_or_404(payment_id)
        
        # Confirm payment with Stripe
        intent = stripe.PaymentIntent.confirm(
            payment.stripe_payment_intent_id
        )
        
        if intent.status == 'succeeded':
            payment.status = 'completed'
            db.session.commit()
            
            # Send payment completed event
            publish_event('payment.completed', {
                'eventType': 'PaymentCompleted',
                'paymentId': payment.id,
                'orderId': payment.order_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Process refund if needed (async)
            process_payment.delay(payment.id)
        
        return jsonify({'status': payment.status})

@celery.task
def process_payment(payment_id):
    """Async payment processing tasks"""
    # Additional payment processing logic
    pass

def publish_event(channel, event):
    redis_client.publish(channel, json.dumps(event))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8004)
```

### 6단계: 서비스 간 통신 구현 (30분)

다음을 수행해줘:

#### gRPC 통신
```go
// services/shared/grpc/client.go
package grpc

import (
    "google.golang.org/grpc"
    "google.golang.org/grpc/balancer/roundrobin"
    "github.com/grpc-ecosystem/go-grpc-middleware/retry"
)

func NewServiceClient(serviceName string) (*grpc.ClientConn, error) {
    opts := []grpc.DialOption{
        grpc.WithInsecure(),
        grpc.WithBalancerName(roundrobin.Name),
        grpc.WithUnaryInterceptor(
            grpc_retry.UnaryClientInterceptor(
                grpc_retry.WithMax(3),
                grpc_retry.WithBackoff(grpc_retry.BackoffExponential(100)),
            ),
        ),
    }
    
    // Service discovery integration
    target := fmt.Sprintf("consul://%s/%s", consulAddr, serviceName)
    
    return grpc.Dial(target, opts...)
}
```

#### Event Sourcing
```javascript
// services/shared/event-store.js
const { EventStoreDBClient } = require('@eventstore/db-client');

class EventStore {
  constructor() {
    this.client = new EventStoreDBClient({
      endpoint: 'esdb://eventstore:2113',
    });
  }
  
  async appendEvent(streamName, eventType, data) {
    const event = {
      type: eventType,
      data: data,
      metadata: {
        timestamp: new Date().toISOString(),
        version: '1.0',
      },
    };
    
    await this.client.appendToStream(streamName, [event]);
  }
  
  async readEvents(streamName, fromPosition = 0) {
    const events = [];
    const stream = this.client.readStream(streamName, {
      fromRevision: fromPosition,
      direction: 'forwards',
    });
    
    for await (const { event } of stream) {
      events.push({
        type: event.type,
        data: event.data,
        metadata: event.metadata,
        position: event.revision,
      });
    }
    
    return events;
  }
}

module.exports = EventStore;
```

#### Saga Pattern
```python
# services/shared/saga.py
from abc import ABC, abstractmethod
import asyncio
from typing import List, Dict, Any

class SagaStep(ABC):
    @abstractmethod
    async def execute(self, context: Dict[str, Any]):
        pass
    
    @abstractmethod
    async def compensate(self, context: Dict[str, Any]):
        pass

class Saga:
    def __init__(self, name: str):
        self.name = name
        self.steps: List[SagaStep] = []
        self.completed_steps: List[SagaStep] = []
    
    def add_step(self, step: SagaStep):
        self.steps.append(step)
    
    async def execute(self, context: Dict[str, Any]):
        try:
            for step in self.steps:
                await step.execute(context)
                self.completed_steps.append(step)
        except Exception as e:
            # Compensate in reverse order
            for step in reversed(self.completed_steps):
                try:
                    await step.compensate(context)
                except Exception as comp_error:
                    # Log compensation error
                    print(f"Compensation failed: {comp_error}")
            raise e

# Example: Order Saga
class CreateOrderStep(SagaStep):
    async def execute(self, context):
        # Create order logic
        order = await create_order(context['order_data'])
        context['order_id'] = order.id
    
    async def compensate(self, context):
        # Cancel order
        await cancel_order(context['order_id'])

class ReserveInventoryStep(SagaStep):
    async def execute(self, context):
        # Reserve inventory
        reservation = await reserve_inventory(context['items'])
        context['reservation_id'] = reservation.id
    
    async def compensate(self, context):
        # Release inventory
        await release_inventory(context['reservation_id'])

class ProcessPaymentStep(SagaStep):
    async def execute(self, context):
        # Process payment
        payment = await process_payment(context['payment_data'])
        context['payment_id'] = payment.id
    
    async def compensate(self, context):
        # Refund payment
        await refund_payment(context['payment_id'])
```

### 7단계: 관측성 및 모니터링 (30분)

다음을 수행해줘:

#### Distributed Tracing
```yaml
# infrastructure/tracing/jaeger-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: jaeger-config
data:
  sampling-strategies.json: |
    {
      "service_strategies": [
        {
          "service": "user-service",
          "type": "probabilistic",
          "param": 0.5
        },
        {
          "service": "order-service",
          "type": "probabilistic",
          "param": 1.0
        }
      ],
      "default_strategy": {
        "type": "probabilistic",
        "param": 0.1
      }
    }
```

#### Prometheus Metrics
```go
// services/shared/metrics/metrics.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    RequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "microservice_requests_total",
            Help: "Total number of requests",
        },
        []string{"service", "method", "status"},
    )
    
    RequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "microservice_request_duration_seconds",
            Help: "Request duration in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"service", "method"},
    )
    
    ActiveConnections = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "microservice_active_connections",
            Help: "Number of active connections",
        },
        []string{"service"},
    )
)
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Microservices Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(microservice_requests_total[5m])) by (service)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(microservice_requests_total{status=~\"5..\"}[5m])) by (service)"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(microservice_request_duration_seconds_bucket[5m])) by (service)"
          }
        ]
      }
    ]
  }
}
```

#### Centralized Logging
```yaml
# infrastructure/logging/fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type forward
      port 24224
    </source>
    
    <filter **>
      @type parser
      format json
      key_name log
      reserve_data true
    </filter>
    
    <filter **>
      @type record_transformer
      <record>
        service ${tag}
        hostname ${hostname}
      </record>
    </filter>
    
    <match **>
      @type elasticsearch
      host elasticsearch
      port 9200
      logstash_format true
      logstash_prefix microservices
      <buffer>
        @type file
        path /var/log/fluentd-buffers/microservices.buffer
        flush_mode interval
        flush_interval 10s
      </buffer>
    </match>
```

### 8단계: 보안 구현 (30분)

다음을 수행해줘:

#### Service Mesh (Istio)
```yaml
# infrastructure/istio/service-mesh.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: microservices
spec:
  mtls:
    mode: STRICT

---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: user-service-policy
  namespace: microservices
spec:
  selector:
    matchLabels:
      app: user-service
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/microservices/sa/api-gateway"]
    to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]

---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: user-service
spec:
  hosts:
  - user-service
  http:
  - timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
    route:
    - destination:
        host: user-service
        subset: v1
      weight: 90
    - destination:
        host: user-service
        subset: v2
      weight: 10
```

#### Secrets Management
```yaml
# infrastructure/secrets/vault-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vault-config
data:
  vault.hcl: |
    ui = true
    
    listener "tcp" {
      address = "0.0.0.0:8200"
      tls_disable = 0
      tls_cert_file = "/vault/certs/server.crt"
      tls_key_file = "/vault/certs/server.key"
    }
    
    storage "consul" {
      address = "consul:8500"
      path = "vault/"
    }
    
    api_addr = "https://vault:8200"
```

#### OAuth2/OIDC
```javascript
// services/auth-service/oauth.js
const express = require('express');
const { Issuer } = require('openid-client');
const jose = require('jose');

class AuthService {
  constructor() {
    this.privateKey = null;
    this.publicKey = null;
    this.clients = new Map();
  }
  
  async initialize() {
    // Generate key pair
    const { publicKey, privateKey } = await jose.generateKeyPair('RS256');
    this.publicKey = publicKey;
    this.privateKey = privateKey;
  }
  
  async issueToken(userId, clientId, scope) {
    const jwt = await new jose.SignJWT({
      sub: userId,
      client_id: clientId,
      scope: scope,
    })
    .setProtectedHeader({ alg: 'RS256' })
    .setIssuedAt()
    .setIssuer('https://auth.microservices.local')
    .setAudience(clientId)
    .setExpirationTime('1h')
    .sign(this.privateKey);
    
    return jwt;
  }
  
  async verifyToken(token) {
    try {
      const { payload } = await jose.jwtVerify(token, this.publicKey, {
        issuer: 'https://auth.microservices.local',
      });
      return payload;
    } catch (error) {
      throw new Error('Invalid token');
    }
  }
  
  // OIDC Discovery endpoint
  getDiscoveryDocument() {
    return {
      issuer: 'https://auth.microservices.local',
      authorization_endpoint: 'https://auth.microservices.local/authorize',
      token_endpoint: 'https://auth.microservices.local/token',
      userinfo_endpoint: 'https://auth.microservices.local/userinfo',
      jwks_uri: 'https://auth.microservices.local/.well-known/jwks.json',
      response_types_supported: ['code', 'token', 'id_token'],
      subject_types_supported: ['public'],
      id_token_signing_alg_values_supported: ['RS256'],
    };
  }
}
```

### 9단계: 배포 자동화 (30분)

다음을 수행해줘:

#### Kubernetes Manifests
```yaml
# infrastructure/kubernetes/microservices-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: microservices
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        version: v1
    spec:
      serviceAccountName: user-service
      containers:
      - name: user-service
        image: microservices/user-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DB_CONNECTION
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: user-db-connection
        - name: JAEGER_AGENT_HOST
          value: jaeger-agent.istio-system
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: microservices
spec:
  selector:
    app: user-service
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
  namespace: microservices
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
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
```

#### Helm Charts
```yaml
# infrastructure/helm/microservices/values.yaml
global:
  namespace: microservices
  domain: microservices.local
  
services:
  userService:
    enabled: true
    replicaCount: 3
    image:
      repository: microservices/user-service
      tag: latest
      pullPolicy: Always
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
    
  orderService:
    enabled: true
    replicaCount: 3
    image:
      repository: microservices/order-service
      tag: latest
    
  paymentService:
    enabled: true
    replicaCount: 2
    image:
      repository: microservices/payment-service
      tag: latest

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
  jaeger:
    enabled: true

security:
  istio:
    enabled: true
  vault:
    enabled: true
```

#### CI/CD Pipeline
```yaml
# .github/workflows/microservices-deploy.yml
name: Microservices CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [user-service, order-service, payment-service]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Run tests
      run: |
        cd services/${{ matrix.service }}
        make test
    
    - name: Run integration tests
      run: |
        docker-compose -f docker-compose.test.yml up -d
        make integration-test
        docker-compose -f docker-compose.test.yml down

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [user-service, order-service, payment-service]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push Docker image
      env:
        DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
      run: |
        cd services/${{ matrix.service }}
        docker build -t $DOCKER_REGISTRY/${{ matrix.service }}:${{ github.sha }} .
        docker push $DOCKER_REGISTRY/${{ matrix.service }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Helm
      uses: azure/setup-helm@v1
      with:
        version: '3.7.0'
    
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        
        helm upgrade --install microservices \
          ./infrastructure/helm/microservices \
          --namespace microservices \
          --create-namespace \
          --set-string global.imageTag=${{ github.sha }}
```

### 10단계: 문서화 및 완료 (20분)

다음을 수행해줘:

#### API 문서 (OpenAPI)
```yaml
# docs/api/user-service-api.yaml
openapi: 3.0.0
info:
  title: User Service API
  version: 1.0.0
  description: Microservice for user management

servers:
  - url: https://api.microservices.local/v1

paths:
  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
```

#### 운영 가이드
```markdown
# Microservices 운영 가이드

## 서비스 목록
- User Service (Port 8001)
- Product Service (Port 8002)
- Order Service (Port 8003)
- Payment Service (Port 8004)
- Notification Service (Port 8005)

## 모니터링
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686

## 트러블슈팅
### 서비스 재시작
```bash
kubectl rollout restart deployment/user-service -n microservices
```

### 로그 확인
```bash
kubectl logs -f deployment/user-service -n microservices
```

### 스케일링
```bash
kubectl scale deployment/user-service --replicas=5 -n microservices
```
```

최종 산출물:
- 완전한 마이크로서비스 시스템
- Service Mesh 통합
- 분산 추적 및 모니터링
- 자동화된 CI/CD
- 프로덕션 준비 완료

각 단계별로 진행 상황을 보고하고, 모든 코드와 설정을 생성해줘.