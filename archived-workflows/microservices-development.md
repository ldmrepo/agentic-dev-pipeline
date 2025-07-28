# 마이크로서비스 개발 워크플로우

## 🏗️ 마이크로서비스 아키텍처 자동 개발

이 워크플로우는 마이크로서비스 아키텍처 기반 분산 시스템을 자동으로 개발합니다.

**목표 완료 시간: 3-4시간**

## 실행 방법
```bash
export REQUIREMENTS="사용자 관리, 주문 처리, 결제 시스템 마이크로서비스"
export SERVICES="user-service,order-service,payment-service"
claude -f workflows/microservices-development.md
```

## 워크플로우 단계

### 🎯 1단계: 마이크로서비스 아키텍처 설계 (30분)

다음을 수행해줘:

#### 서비스 분해 및 경계 정의
- 요구사항: ${REQUIREMENTS}
- 서비스 목록: ${SERVICES}

```
도메인 분석:
1. 비즈니스 도메인별 서비스 경계 명확히 정의
2. 서비스 간 통신 인터페이스 설계
3. 데이터 일관성 및 트랜잭션 경계 결정
4. 공유 데이터와 서비스별 전용 데이터 구분

서비스별 책임 정의:
- User Service: 사용자 인증, 프로필 관리, 권한 관리
- Order Service: 주문 생성, 상태 관리, 주문 히스토리
- Payment Service: 결제 처리, 결제 검증, 환불 처리

데이터 설계:
- 서비스별 독립적인 데이터베이스 설계
- Event Sourcing 패턴 적용 (필요시)
- CQRS 패턴 고려
- 데이터 동기화 전략 수립
```

#### API 게이트웨이 및 서비스 메시 설계
```
API Gateway 설계:
- 라우팅 규칙 정의 (/api/users/*, /api/orders/*, /api/payments/*)
- 인증/인가 통합 지점
- Rate Limiting 및 Circuit Breaker 패턴
- API 버전 관리 전략

Service Mesh 구성:
- Istio 또는 Linkerd 선택 및 설정
- 서비스 간 mTLS 통신
- 트래픽 관리 및 로드 밸런싱
- 분산 추적 (Jaeger) 설정
```

**결과물**: 
- `docs/microservices-architecture.md`
- `docs/service-boundaries.md`
- `docs/api-gateway-design.md`

---

### 🔨 2단계: 병렬 서비스 개발 (2-2.5시간)

다음 서비스들을 동시에 개발해줘:

#### User Service 개발
```
프로젝트 구조:
services/user-service/
├── src/
│   ├── controllers/     # API 컨트롤러
│   ├── services/        # 비즈니스 로직
│   ├── models/          # 데이터 모델
│   ├── middleware/      # 인증, 로깅 등
│   └── utils/           # 유틸리티
├── tests/
├── Dockerfile
├── docker-compose.yml
└── package.json

핵심 기능 구현:
1. 사용자 등록/로그인 API
2. JWT 토큰 기반 인증
3. 사용자 프로필 CRUD
4. 권한 관리 (RBAC)
5. 이메일 인증 기능

데이터베이스:
- PostgreSQL 사용
- User, Role, Permission 테이블
- 인덱스 최적화
- 마이그레이션 스크립트

API 엔드포인트:
- POST /auth/register
- POST /auth/login  
- GET /users/profile
- PUT /users/profile
- GET /users/{id}
- POST /users/{id}/roles
```

#### Order Service 개발
```
프로젝트 구조:
services/order-service/
├── src/
│   ├── controllers/
│   ├── services/
│   └── events/          # 이벤트 핸들러
├── tests/
├── Dockerfile
└── package.json

핵심 기능 구현:
1. 주문 생성 및 관리 API
2. 주문 상태 머신 구현
3. 재고 확인 (외부 서비스 연동)
4. 이벤트 기반 아키텍처 적용
5. 주문 히스토리 관리

데이터베이스:
- MongoDB 사용 (유연한 스키마)
- Order, OrderItem, OrderHistory 컬렉션
- 인덱스 최적화

이벤트 처리:
- Order Created 이벤트 발행
- Payment Processed 이벤트 구독
- Inventory Updated 이벤트 구독

API 엔드포인트:
- POST /orders
- GET /orders/{id}
- GET /orders/user/{userId}
- PUT /orders/{id}/status
- DELETE /orders/{id}
```

#### Payment Service 개발
```
프로젝트 구조:
services/payment-service/
├── src/
│   ├── controllers/
│   ├── services/
│   ├── gateways/        # 외부 결제 게이트웨이
│   └── security/        # 보안 관련
├── tests/
├── Dockerfile
└── package.json

핵심 기능 구현:
1. 결제 처리 API
2. 다중 결제 게이트웨이 지원 (Stripe, PayPal)
3. PCI DSS 준수 보안 구현
4. 결제 상태 관리
5. 환불 처리 기능

데이터베이스:
- PostgreSQL 사용 (ACID 보장)
- Payment, Transaction, Refund 테이블
- 암호화 적용 (민감 정보)

보안 구현:
- 카드 정보 토큰화
- PCI DSS Level 1 준수
- 암호화 키 관리
- 감사 로그 기록

API 엔드포인트:
- POST /payments/process
- GET /payments/{id}
- POST /payments/{id}/refund
- GET /payments/order/{orderId}
```

#### API Gateway 구현
```
기술 스택: Kong 또는 Express Gateway

설정 구현:
1. 서비스 라우팅 규칙
2. 로드 밸런싱 전략
3. Circuit Breaker 패턴
4. Rate Limiting 정책
5. CORS 설정

보안 기능:
- JWT 토큰 검증
- API 키 관리
- OAuth2 통합
- 로깅 및 모니터링

kong.yml 설정:
_format_version: "3.0"
services:
  - name: user-service
    url: http://user-service:3001
    routes:
      - name: user-routes
        paths: ["/api/users", "/api/auth"]
  
  - name: order-service  
    url: http://order-service:3002
    routes:
      - name: order-routes
        paths: ["/api/orders"]
        
  - name: payment-service
    url: http://payment-service:3003
    routes:
      - name: payment-routes
        paths: ["/api/payments"]
```

---

### 🔗 3단계: 서비스 간 통신 구현 (45분)

다음 통신 패턴을 구현해줘:

#### 동기 통신 (HTTP REST)
```
서비스 디스커버리:
- Consul 또는 etcd 설정
- 서비스 등록/해제 자동화
- 헬스체크 구성

HTTP 클라이언트 구현:
- Axios 기반 서비스 클라이언트
- Retry 정책 및 Circuit Breaker
- 타임아웃 설정
- 로깅 및 모니터링

예시 - Order Service에서 User Service 호출:
class UserServiceClient {
  async getUserById(userId) {
    const response = await this.httpClient.get(`/users/${userId}`);
    return response.data;
  }
  
  async validateUser(token) {
    const response = await this.httpClient.post('/auth/validate', { token });
    return response.data;
  }
}
```

#### 비동기 통신 (Event-Driven)
```
메시지 브로커: Apache Kafka 또는 RabbitMQ

이벤트 정의:
- UserRegistered: 사용자 등록 완료
- OrderCreated: 주문 생성 완료  
- PaymentProcessed: 결제 처리 완료
- OrderStatusChanged: 주문 상태 변경

Event Publisher 구현:
class EventPublisher {
  async publishOrderCreated(orderData) {
    await this.kafka.send({
      topic: 'order-events',
      messages: [{
        key: orderData.id,
        value: JSON.stringify({
          eventType: 'OrderCreated',
          data: orderData,
          timestamp: new Date().toISOString()
        })
      }]
    });
  }
}

Event Consumer 구현:
class PaymentEventConsumer {
  async handleOrderCreated(event) {
    const { orderId, amount, userId } = event.data;
    // 결제 준비 로직
    await this.paymentService.preparePayment(orderId, amount, userId);
  }
}
```

#### 데이터 일관성 보장
```
Saga 패턴 구현:
1. Order Creation Saga
   - Create Order → Reserve Inventory → Process Payment
   - 실패 시 보상 트랜잭션 실행

2. Payment Processing Saga
   - Validate Payment → Charge Card → Update Order → Send Confirmation
   
Saga Orchestrator:
class OrderCreationSaga {
  async execute(orderData) {
    try {
      const order = await this.orderService.createOrder(orderData);
      const inventory = await this.inventoryService.reserve(order.items);
      const payment = await this.paymentService.process(order.payment);
      
      await this.orderService.confirmOrder(order.id);
      await this.notificationService.sendConfirmation(order);
      
    } catch (error) {
      await this.compensate(order, inventory, payment);
    }
  }
}
```

---

### 🧪 4단계: 통합 테스트 및 End-to-End 테스트 (30분)

다음 테스트를 구현해줘:

#### 서비스별 단위 테스트
```
각 서비스별 테스트:
- Controller 테스트 (API 엔드포인트)
- Service 테스트 (비즈니스 로직)
- Repository 테스트 (데이터 접근)
- Integration 테스트 (외부 의존성)

테스트 커버리지: 각 서비스 85% 이상

예시 - User Service 테스트:
describe('UserController', () => {
  test('POST /auth/register should create new user', async () => {
    const userData = {
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User'
    };
    
    const response = await request(app)
      .post('/auth/register')
      .send(userData)
      .expect(201);
      
    expect(response.body.user.email).toBe(userData.email);
    expect(response.body.token).toBeDefined();
  });
});
```

#### 서비스 간 통합 테스트
```
Contract Testing (Pact):
- User Service ↔ Order Service 계약 테스트
- Order Service ↔ Payment Service 계약 테스트
- API Gateway ↔ 모든 서비스 계약 테스트

예시 - Order Service에서 User Service 호출 테스트:
describe('Order Service → User Service Integration', () => {
  test('should validate user before creating order', async () => {
    // Given: Valid user token
    const userToken = 'valid-jwt-token';
    
    // When: Creating order
    const orderData = {
      userId: 'user123',
      items: [{ productId: 'prod1', quantity: 2 }]
    };
    
    // Then: User validation should succeed and order created
    const response = await request(orderService)
      .post('/orders')
      .set('Authorization', `Bearer ${userToken}`)
      .send(orderData)
      .expect(201);
  });
});
```

#### End-to-End 시나리오 테스트
```
전체 비즈니스 플로우 테스트:

시나리오 1: 완전한 주문 프로세스
1. 사용자 등록 → User Service
2. 로그인 → User Service  
3. 주문 생성 → Order Service
4. 결제 처리 → Payment Service
5. 주문 확인 → Order Service

시나리오 2: 결제 실패 시 롤백
1. 주문 생성 → Order Service
2. 결제 실패 → Payment Service
3. 주문 취소 → Order Service
4. 재고 복원 → Inventory Service

E2E 테스트 구현:
describe('Complete Order Flow', () => {
  test('user can register, login, and complete order', async () => {
    // 1. Register user
    const user = await registerUser({
      email: 'customer@example.com',
      password: 'password123'
    });
    
    // 2. Login
    const { token } = await loginUser(user.email, user.password);
    
    // 3. Create order
    const order = await createOrder(token, {
      items: [{ productId: 'prod1', quantity: 1, price: 100 }]
    });
    
    // 4. Process payment
    const payment = await processPayment(token, {
      orderId: order.id,
      amount: 100,
      cardToken: 'test-card-token'
    });
    
    // 5. Verify order completion
    expect(payment.status).toBe('completed');
    expect(order.status).toBe('confirmed');
  });
});
```

---

### 🚀 5단계: 컨테이너화 및 오케스트레이션 (45분)

다음을 구현해줘:

#### Docker 컨테이너화
```
각 서비스별 Dockerfile:

# user-service/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY src/ ./src/
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3001/health || exit 1
CMD ["node", "src/index.js"]

Docker Compose 통합:
version: '3.8'
services:
  user-service:
    build: ./services/user-service
    ports:
      - "3001:3001"
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
      
  order-service:
    build: ./services/order-service
    ports:
      - "3002:3002"
    environment:
      - MONGO_URI=mongodb://mongodb:27017/orders
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - mongodb
      - kafka
      
  payment-service:
    build: ./services/payment-service
    ports:
      - "3003:3003"
    environment:
      - DB_HOST=postgres-payment
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - postgres-payment
```

#### Kubernetes 배포
```
Kubernetes 매니페스트 생성:

# user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        ports:
        - containerPort: 3001
        env:
        - name: DB_HOST
          value: "postgres-service"
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
            port: 3001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3001
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 3001
  type: ClusterIP

Istio Service Mesh 설정:
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: microservices-vs
spec:
  http:
  - match:
    - uri:
        prefix: /api/users
    route:
    - destination:
        host: user-service
  - match:
    - uri:
        prefix: /api/orders
    route:
    - destination:
        host: order-service
  - match:
    - uri:
        prefix: /api/payments
    route:
    - destination:
        host: payment-service
```

---

### 📊 6단계: 모니터링 및 관찰성 (30분)

다음을 설정해줘:

#### 분산 추적 (Jaeger)
```
각 서비스에 OpenTelemetry 통합:

// tracing.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-node');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');

const provider = new NodeTracerProvider();

provider.addSpanProcessor(
  new BatchSpanProcessor(
    new JaegerExporter({
      endpoint: 'http://jaeger:14268/api/traces',
    })
  )
);

provider.register();

Express 미들웨어:
app.use((req, res, next) => {
  const span = tracer.startSpan(`${req.method} ${req.path}`);
  req.span = span;
  
  res.on('finish', () => {
    span.setAttributes({
      'http.method': req.method,
      'http.url': req.url,
      'http.status_code': res.statusCode,
    });
    span.end();
  });
  
  next();
});
```

#### 메트릭 수집 (Prometheus)
```
각 서비스에 메트릭 엔드포인트 추가:

const prometheus = require('prom-client');

// 비즈니스 메트릭
const orderCreated = new prometheus.Counter({
  name: 'orders_created_total',
  help: 'Total number of orders created'
});

const paymentProcessed = new prometheus.Counter({
  name: 'payments_processed_total',
  help: 'Total number of payments processed'
});

const responseTime = new prometheus.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status']
});

// /metrics 엔드포인트
app.get('/metrics', (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(prometheus.register.metrics());
});
```

#### 중앙 로깅 (ELK Stack)
```
구조화된 로깅 설정:

const winston = require('winston');

const logger = winston.createLogger({
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'user-service',
    version: process.env.APP_VERSION
  },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/app.log' })
  ]
});

// 요청 로깅 미들웨어
app.use((req, res, next) => {
  logger.info('Request received', {
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    ip: req.ip,
    traceId: req.span?.spanContext().traceId
  });
  next();
});
```

## ✅ 완료 조건

### 필수 달성 목표
- [ ] 3개 이상의 마이크로서비스 구현 완료
- [ ] API Gateway를 통한 통합 라우팅
- [ ] 서비스 간 동기/비동기 통신 구현
- [ ] 각 서비스별 독립적인 데이터베이스
- [ ] Docker 컨테이너화 및 Kubernetes 배포 설정
- [ ] 분산 추적 및 중앙 로깅 구현
- [ ] End-to-End 테스트 통과
- [ ] 서비스별 테스트 커버리지 85% 이상

### 품질 기준
- [ ] 각 서비스 독립 배포 가능
- [ ] Circuit Breaker 패턴 적용
- [ ] 데이터 일관성 보장 (Saga 패턴)
- [ ] 모니터링 대시보드 구성
- [ ] 자동 스케일링 설정 (HPA)
- [ ] 보안 정책 적용 (mTLS, RBAC)

### 성능 목표
- [ ] API 응답시간 < 100ms (95%ile)
- [ ] 서비스 가용성 > 99.9%
- [ ] 동시 사용자 1000명 처리 가능
- [ ] 트랜잭션 처리량 > 100 TPS

모든 조건이 충족되면 마이크로서비스 아키텍처 구현이 완료됩니다. 

**예상 총 소요시간: 3-4시간**
