# ML/AI 모델 개발 워크플로우

## 🤖 End-to-End ML/AI 모델 개발 자동화
**목표 완료 시간: 3-4시간**

다음의 ML/AI 모델을 개발해주세요: $ARGUMENTS

## 워크플로우 단계

### 1단계: 문제 정의 및 데이터 분석 (30분)

다음을 수행해줘:

#### 문제 정의
- 비즈니스 목표 명확화
- ML 문제 유형 결정 (분류/회귀/클러스터링/추천)
- 성공 메트릭 정의 (정확도, F1, AUC, RMSE 등)
- 제약사항 파악 (레이턴시, 모델 크기, 설명가능성)

#### 데이터 탐색 (EDA)
```python
# notebooks/eda.ipynb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ydata_profiling import ProfileReport

# 데이터 프로파일링
profile = ProfileReport(df, title="데이터 분석 리포트")
profile.to_file("reports/data_profile.html")

# 시각화 및 통계 분석
# 결측치 분석
# 이상치 탐지
# 특성 분포 분석
# 상관관계 분석
```

#### 데이터 품질 평가
- 데이터 완전성 검사
- 레이블 불균형 분석
- 데이터 누수 검사
- 시간적 일관성 검증

docs/ml-project/ 디렉토리에 생성:
- problem_definition.md
- data_analysis_report.md
- ml_requirements.md

### 2단계: 데이터 준비 및 특성 공학 (45분)

다음을 수행해줘:

#### 데이터 전처리
```python
# src/preprocessing/data_preprocessor.py
class DataPreprocessor:
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
    
    def clean_data(self, df):
        # 결측치 처리
        # 이상치 제거/변환
        # 데이터 타입 변환
        pass
    
    def handle_missing_values(self, df):
        # 수치형: 평균/중앙값/보간
        # 범주형: 최빈값/새 카테고리
        pass
    
    def remove_outliers(self, df):
        # IQR 방법
        # Z-score 방법
        # Isolation Forest
        pass
```

#### 특성 공학
```python
# src/features/feature_engineering.py
class FeatureEngineer:
    def create_features(self, df):
        # 상호작용 특성
        # 다항식 특성
        # 도메인 특화 특성
        # 시계열 특성 (lag, rolling)
        pass
    
    def encode_categorical(self, df):
        # One-hot encoding
        # Target encoding
        # Ordinal encoding
        # Embedding
        pass
    
    def scale_features(self, df):
        # StandardScaler
        # MinMaxScaler
        # RobustScaler
        # Normalizer
        pass
```

#### 특성 선택
```python
# src/features/feature_selection.py
from sklearn.feature_selection import (
    SelectKBest, RFE, SelectFromModel
)

class FeatureSelector:
    def select_features(self, X, y):
        # 통계적 방법 (chi2, ANOVA)
        # 모델 기반 (Lasso, Random Forest)
        # 순차적 선택
        # 중요도 기반
        pass
```

### 3단계: 모델 개발 및 실험 (60분)

다음을 수행해줘:

#### AutoML 구현
```python
# src/models/automl.py
import optuna
from sklearn.model_selection import cross_val_score

class AutoMLPipeline:
    def __init__(self):
        self.best_model = None
        self.best_params = None
        self.study = None
    
    def objective(self, trial):
        # 모델 선택
        model_name = trial.suggest_categorical(
            'model', ['rf', 'xgb', 'lgb', 'nn']
        )
        
        # 하이퍼파라미터 탐색
        if model_name == 'rf':
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20)
            }
        # ... 다른 모델들
        
        # 교차 검증
        score = cross_val_score(model, X, y, cv=5).mean()
        return score
    
    def run_automl(self, X, y, n_trials=100):
        self.study = optuna.create_study(direction='maximize')
        self.study.optimize(
            lambda trial: self.objective(trial), 
            n_trials=n_trials
        )
```

#### 딥러닝 모델 (PyTorch/TensorFlow)
```python
# src/models/deep_learning.py
import torch
import torch.nn as nn

class NeuralNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dims, output_dim):
        super().__init__()
        layers = []
        
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, output_dim))
        self.model = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.model(x)

# 트레이닝 루프
class Trainer:
    def train(self, model, train_loader, val_loader, epochs=100):
        optimizer = torch.optim.Adam(model.parameters())
        criterion = nn.CrossEntropyLoss()
        
        for epoch in range(epochs):
            # 트레이닝
            # 검증
            # Early stopping
            # 체크포인트 저장
            pass
```

#### 앙상블 방법
```python
# src/models/ensemble.py
class EnsembleModel:
    def __init__(self):
        self.models = []
        self.weights = []
    
    def add_model(self, model, weight=1.0):
        self.models.append(model)
        self.weights.append(weight)
    
    def predict(self, X):
        # Voting
        # Averaging
        # Stacking
        # Blending
        pass
```

### 4단계: 모델 평가 및 검증 (30분)

다음을 수행해줘:

#### 평가 메트릭
```python
# src/evaluation/metrics.py
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    roc_auc_score, confusion_matrix, mean_squared_error
)

class ModelEvaluator:
    def evaluate_classification(self, y_true, y_pred):
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1': f1_score(y_true, y_pred, average='weighted'),
            'auc_roc': roc_auc_score(y_true, y_pred_proba)
        }
        
        # 혼동 행렬
        cm = confusion_matrix(y_true, y_pred)
        
        # 클래스별 성능
        per_class = precision_recall_fscore_support(y_true, y_pred)
        
        return metrics, cm, per_class
    
    def evaluate_regression(self, y_true, y_pred):
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
        return metrics
```

#### 교차 검증
```python
# src/evaluation/cross_validation.py
from sklearn.model_selection import (
    KFold, StratifiedKFold, TimeSeriesSplit
)

class CrossValidator:
    def validate(self, model, X, y, cv_strategy='stratified'):
        if cv_strategy == 'stratified':
            cv = StratifiedKFold(n_splits=5, shuffle=True)
        elif cv_strategy == 'time_series':
            cv = TimeSeriesSplit(n_splits=5)
        else:
            cv = KFold(n_splits=5, shuffle=True)
        
        scores = []
        for train_idx, val_idx in cv.split(X, y):
            # 훈련 및 평가
            pass
        
        return scores
```

#### 모델 해석
```python
# src/interpretation/explainability.py
import shap
import lime

class ModelInterpreter:
    def explain_with_shap(self, model, X):
        explainer = shap.Explainer(model)
        shap_values = explainer(X)
        
        # SHAP 시각화
        shap.summary_plot(shap_values, X)
        shap.waterfall_plot(shap_values[0])
        
        return shap_values
    
    def explain_with_lime(self, model, X, instance):
        explainer = lime.tabular.LimeTabularExplainer(
            X.values,
            feature_names=X.columns,
            mode='classification'
        )
        
        explanation = explainer.explain_instance(
            instance, 
            model.predict_proba
        )
        
        return explanation
```

### 5단계: MLOps 파이프라인 구축 (45분)

다음을 수행해줘:

#### MLflow 실험 추적
```python
# src/mlops/experiment_tracking.py
import mlflow
import mlflow.sklearn

class ExperimentTracker:
    def __init__(self, experiment_name):
        mlflow.set_experiment(experiment_name)
    
    def log_experiment(self, model, params, metrics, artifacts):
        with mlflow.start_run():
            # 파라미터 로깅
            mlflow.log_params(params)
            
            # 메트릭 로깅
            mlflow.log_metrics(metrics)
            
            # 모델 로깅
            mlflow.sklearn.log_model(model, "model")
            
            # 아티팩트 로깅
            for artifact in artifacts:
                mlflow.log_artifact(artifact)
            
            # 태그 추가
            mlflow.set_tags({
                "model_type": type(model).__name__,
                "version": "1.0"
            })
```

#### DVC 데이터 버전 관리
```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python src/prepare_data.py
    deps:
      - src/prepare_data.py
      - data/raw
    outs:
      - data/processed
    params:
      - prepare.split_ratio
      - prepare.seed
  
  train:
    cmd: python src/train_model.py
    deps:
      - src/train_model.py
      - data/processed
    outs:
      - models/model.pkl
    metrics:
      - metrics/scores.json
    params:
      - train.n_estimators
      - train.max_depth
```

#### 모델 레지스트리
```python
# src/mlops/model_registry.py
class ModelRegistry:
    def __init__(self):
        self.client = mlflow.tracking.MlflowClient()
    
    def register_model(self, run_id, model_name):
        # 모델 등록
        model_uri = f"runs:/{run_id}/model"
        model_version = mlflow.register_model(
            model_uri, 
            model_name
        )
        
        # 스테이지 전환
        self.client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage="Staging"
        )
        
        return model_version
    
    def promote_to_production(self, model_name, version):
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production"
        )
```

### 6단계: 모델 배포 (30분)

다음을 수행해줘:

#### REST API 서버
```python
# src/serving/api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib

app = FastAPI()

# 모델 로드
model = joblib.load("models/production_model.pkl")

class PredictionRequest(BaseModel):
    features: list

class PredictionResponse(BaseModel):
    prediction: float
    confidence: float

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        prediction = model.predict([request.features])[0]
        confidence = model.predict_proba([request.features]).max()
        
        return PredictionResponse(
            prediction=prediction,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

#### Docker 컨테이너화
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "src.serving.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Kubernetes 배포
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-model-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-model
  template:
    metadata:
      labels:
        app: ml-model
    spec:
      containers:
      - name: ml-model
        image: ml-model:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### 7단계: 모니터링 및 유지보수 (30분)

다음을 수행해줘:

#### 모델 모니터링
```python
# src/monitoring/model_monitor.py
from evidently import Dashboard
from evidently.tabs import DataDriftTab, CatTargetDriftTab

class ModelMonitor:
    def __init__(self):
        self.dashboard = Dashboard(tabs=[
            DataDriftTab(),
            CatTargetDriftTab()
        ])
    
    def detect_drift(self, reference_data, current_data):
        self.dashboard.calculate(
            reference_data, 
            current_data
        )
        
        # 드리프트 감지
        drift_report = self.dashboard.json()
        
        # 알림 발송
        if drift_report['data_drift']['dataset_drift']:
            self.send_alert("Data drift detected!")
        
        return drift_report
    
    def monitor_performance(self, predictions, actuals):
        # 실시간 성능 추적
        # 정확도 하락 감지
        # 예측 분포 모니터링
        pass
```

#### A/B 테스팅
```python
# src/deployment/ab_testing.py
class ABTestManager:
    def __init__(self):
        self.model_a = None
        self.model_b = None
        self.traffic_split = 0.5
    
    def route_request(self, request):
        if random.random() < self.traffic_split:
            return self.model_a.predict(request)
        else:
            return self.model_b.predict(request)
    
    def analyze_results(self):
        # 성능 비교
        # 통계적 유의성 검정
        # 승자 결정
        pass
```

#### 재학습 파이프라인
```python
# src/retraining/auto_retrain.py
class AutoRetrainer:
    def __init__(self):
        self.performance_threshold = 0.8
        self.drift_threshold = 0.1
    
    def should_retrain(self, current_performance, drift_score):
        return (
            current_performance < self.performance_threshold or
            drift_score > self.drift_threshold
        )
    
    def retrain_pipeline(self):
        # 새 데이터 수집
        # 데이터 전처리
        # 모델 학습
        # 검증
        # 배포
        pass
```

### 8단계: 문서화 및 인수인계 (20분)

다음을 수행해줘:

#### 모델 문서
- 모델 카드 생성
- 성능 벤치마크
- 한계점 및 편향성
- 사용 가이드

#### API 문서
- OpenAPI 스펙
- 예제 요청/응답
- 에러 처리
- 인증 방법

#### 운영 가이드
- 배포 절차
- 모니터링 대시보드
- 트러블슈팅
- 롤백 절차

최종 산출물:
- 프로덕션 준비된 ML 모델
- 완전한 MLOps 파이프라인
- 모니터링 대시보드
- API 서버 및 문서
- 재학습 자동화

각 단계별로 진행 상황을 보고하고, 모든 코드와 설정을 생성해줘.