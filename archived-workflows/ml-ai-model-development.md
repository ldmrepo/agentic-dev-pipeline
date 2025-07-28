# ML/AI 모델 개발 워크플로우

## 🤖 End-to-End ML/AI 모델 개발 자동화

이 워크플로우는 데이터 준비부터 모델 배포까지 완전한 ML/AI 개발 파이프라인을 자동으로 구축합니다.

**목표 완료 시간: 3-4시간**

## 실행 방법
```bash
export REQUIREMENTS="고객 이탈 예측 모델 (정확도 90% 이상, 실시간 예측 API)"
export MODEL_TYPE="classification" # classification, regression, clustering, nlp, computer_vision
export DATASET_SOURCE="s3://data-lake/customer_data/"
export DEPLOYMENT_TYPE="real-time" # real-time, batch, edge
claude -f workflows/ml-ai-model-development.md
```

## 워크플로우 단계

### 🎯 1단계: ML 프로젝트 설계 및 요구사항 분석 (30분)

다음을 수행해줘:

#### 문제 정의 및 목표 설정
- ML 요구사항: ${REQUIREMENTS}
- 모델 타입: ${MODEL_TYPE}
- 데이터 소스: ${DATASET_SOURCE}
- 배포 방식: ${DEPLOYMENT_TYPE}

```
비즈니스 문제 분석:
1. 비즈니스 목표와 ML 목표 정렬
   - 예측하려는 타겟 정의
   - 성공 지표 설정 (정확도, 재현율, F1-score 등)
   - 비즈니스 임팩트 측정 방법

2. 제약사항 파악
   - 예측 지연시간 요구사항
   - 모델 해석가능성 필요 여부
   - 규제 준수 사항 (GDPR, 공정성)
   - 컴퓨팅 리소스 제한

3. 평가 전략 수립
   - Train/Validation/Test 분할 전략
   - Cross-validation 방법
   - A/B 테스트 계획
   - 모델 모니터링 지표

ML 시스템 아키텍처:
데이터 파이프라인:
- 데이터 수집 → 전처리 → 특성 엔지니어링 → 모델 학습

모델 서빙 아키텍처:
- 실시간: REST API / gRPC
- 배치: Airflow + Spark
- 엣지: TensorFlow Lite / ONNX

MLOps 인프라:
- 실험 추적: MLflow
- 모델 레지스트리: MLflow Model Registry
- 모니터링: Prometheus + Grafana
- CI/CD: GitLab CI / GitHub Actions
```

#### 데이터 탐색 및 분석 계획
```python
# EDA 체크리스트
1. 데이터 품질 평가
   - 결측치 분석
   - 이상치 탐지
   - 데이터 타입 검증
   - 중복 데이터 확인

2. 통계 분석
   - 기술 통계량
   - 분포 분석
   - 상관관계 분석
   - 타겟 변수 불균형 확인

3. 시각화
   - 히스토그램, 박스플롯
   - 산점도 매트릭스
   - 히트맵
   - 시계열 패턴 (시계열 데이터의 경우)

4. 특성 엔지니어링 기회
   - 파생 변수 생성 가능성
   - 차원 축소 필요성
   - 인코딩 전략
   - 스케일링 필요성
```

**결과물**:
- `docs/ml-project-charter.md`
- `docs/data-exploration-plan.md`
- `architecture/ml-system-design.yaml`

---

### 📊 2단계: 데이터 준비 및 특성 엔지니어링 (1시간)

다음 데이터 처리 파이프라인을 구현해줘:

#### 데이터 수집 및 검증
```python
# src/data/data_loader.py
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import great_expectations as ge
from sklearn.model_selection import train_test_split
import logging

class DataPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ge_context = ge.DataContext()
    
    def load_data(self, data_path: str) -> pd.DataFrame:
        """데이터 로드 및 초기 검증"""
        
        # 데이터 로드
        if data_path.startswith('s3://'):
            df = pd.read_parquet(data_path)
        elif data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        else:
            df = pd.read_sql(data_path, self.config['db_connection'])
        
        self.logger.info(f"Loaded {len(df)} records from {data_path}")
        
        # 데이터 품질 검증
        self._validate_data_quality(df)
        
        return df
    
    def _validate_data_quality(self, df: pd.DataFrame):
        """Great Expectations를 사용한 데이터 품질 검증"""
        
        # Expectation Suite 생성
        suite = self.ge_context.create_expectation_suite(
            "ml_data_quality_suite",
            overwrite_existing=True
        )
        
        # 기본 검증 규칙
        validator = self.ge_context.get_validator(
            batch_request={"dataset": df},
            expectation_suite_name="ml_data_quality_suite"
        )
        
        # 필수 컬럼 확인
        for column in self.config['required_columns']:
            validator.expect_column_to_exist(column)
            validator.expect_column_values_to_not_be_null(column)
        
        # 수치형 컬럼 범위 확인
        for column, bounds in self.config.get('numeric_bounds', {}).items():
            validator.expect_column_values_to_be_between(
                column, 
                min_value=bounds['min'], 
                max_value=bounds['max']
            )
        
        # 검증 실행
        results = validator.validate()
        
        if not results["success"]:
            raise ValueError(f"Data quality validation failed: {results}")
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """특성 엔지니어링"""
        
        # 시간 기반 특성
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # 집계 특성
        if 'user_id' in df.columns:
            user_stats = df.groupby('user_id').agg({
                'transaction_amount': ['sum', 'mean', 'std', 'count'],
                'session_duration': ['mean', 'max']
            })
            user_stats.columns = ['_'.join(col) for col in user_stats.columns]
            df = df.merge(user_stats, on='user_id', how='left')
        
        # 비율 특성
        if 'page_views' in df.columns and 'purchases' in df.columns:
            df['conversion_rate'] = df['purchases'] / (df['page_views'] + 1)
        
        # 카테고리 인코딩
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        for col in categorical_columns:
            if df[col].nunique() < 20:  # Low cardinality
                df = pd.get_dummies(df, columns=[col], prefix=col)
            else:  # High cardinality
                # Target encoding
                if 'target' in df.columns:
                    target_mean = df.groupby(col)['target'].mean()
                    df[f'{col}_target_encoded'] = df[col].map(target_mean)
        
        return df
    
    def create_ml_dataset(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """ML용 데이터셋 생성"""
        
        # 특성과 타겟 분리
        target_column = self.config['target_column']
        feature_columns = [col for col in df.columns if col != target_column]
        
        X = df[feature_columns]
        y = df[target_column]
        
        # 학습/검증/테스트 분할
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        self.logger.info(f"Dataset split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # 스케일링 (수치형 특성만)
        from sklearn.preprocessing import StandardScaler
        
        numeric_features = X_train.select_dtypes(include=[np.number]).columns
        scaler = StandardScaler()
        
        X_train[numeric_features] = scaler.fit_transform(X_train[numeric_features])
        X_val[numeric_features] = scaler.transform(X_val[numeric_features])
        X_test[numeric_features] = scaler.transform(X_test[numeric_features])
        
        # 스케일러 저장
        import joblib
        joblib.dump(scaler, 'models/scaler.pkl')
        
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)

# Feature Store 구현
class FeatureStore:
    def __init__(self, storage_backend='feast'):
        self.storage_backend = storage_backend
        
    def register_features(self, feature_df: pd.DataFrame, feature_group: str):
        """특성 저장소에 특성 등록"""
        
        if self.storage_backend == 'feast':
            from feast import FeatureStore, Entity, FeatureView, FileSource
            
            # Feast 설정
            fs = FeatureStore(repo_path="feature_repo")
            
            # 엔티티 정의
            user_entity = Entity(
                name="user_id",
                value_type="INT64",
                description="User identifier"
            )
            
            # 특성 뷰 정의
            user_features = FeatureView(
                name=feature_group,
                entities=["user_id"],
                ttl=timedelta(days=1),
                features=feature_df.columns.tolist(),
                online=True,
                source=FileSource(
                    path="data/user_features.parquet",
                    event_timestamp_column="timestamp"
                )
            )
            
            # 특성 등록
            fs.apply([user_entity, user_features])
            
        return f"Features registered in {feature_group}"
```

#### 자동화된 EDA 및 특성 선택
```python
# src/data/auto_eda.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas_profiling import ProfileReport
import shap
from sklearn.feature_selection import SelectKBest, chi2, f_classif, mutual_info_classif

class AutomatedEDA:
    def __init__(self, df: pd.DataFrame, target_column: str):
        self.df = df
        self.target_column = target_column
        self.numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_features = df.select_dtypes(include=['object']).columns.tolist()
        
    def generate_eda_report(self, output_path: str = 'reports/eda_report.html'):
        """포괄적인 EDA 리포트 생성"""
        
        profile = ProfileReport(
            self.df,
            title='Automated EDA Report',
            explorative=True,
            interactions={"continuous": True},
            missing_diagrams={"heatmap": True, "dendrogram": True}
        )
        
        profile.to_file(output_path)
        
        return output_path
    
    def analyze_target_distribution(self):
        """타겟 변수 분포 분석"""
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # 분포 플롯
        if self.target_column in self.numeric_features:
            self.df[self.target_column].hist(ax=axes[0], bins=50)
            axes[0].set_title('Target Distribution')
            
            # 로그 변환 분포
            if (self.df[self.target_column] > 0).all():
                np.log1p(self.df[self.target_column]).hist(ax=axes[1], bins=50)
                axes[1].set_title('Log-transformed Target Distribution')
        else:
            # 분류 문제
            self.df[self.target_column].value_counts().plot(kind='bar', ax=axes[0])
            axes[0].set_title('Target Class Distribution')
            
            # 클래스 불균형 비율
            class_ratios = self.df[self.target_column].value_counts(normalize=True)
            class_ratios.plot(kind='pie', ax=axes[1], autopct='%1.1f%%')
            axes[1].set_title('Class Balance')
        
        plt.tight_layout()
        plt.savefig('reports/target_analysis.png')
        
        return self.df[self.target_column].describe()
    
    def feature_importance_analysis(self, X, y, method='all'):
        """특성 중요도 분석"""
        
        importance_scores = {}
        
        # 1. 상관관계 분석 (수치형 타겟)
        if self.target_column in self.numeric_features:
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            importance_scores['correlation'] = correlations
        
        # 2. Mutual Information
        mi_scores = mutual_info_classif(X, y) if y.dtype == 'object' else mutual_info_classif(X, y)
        importance_scores['mutual_info'] = pd.Series(mi_scores, index=X.columns).sort_values(ascending=False)
        
        # 3. Chi-squared (범주형 타겟)
        if y.dtype == 'object':
            chi_scores = SelectKBest(chi2, k='all').fit(X, y).scores_
            importance_scores['chi2'] = pd.Series(chi_scores, index=X.columns).sort_values(ascending=False)
        
        # 4. Random Forest 특성 중요도
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        
        if y.dtype == 'object':
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
        
        rf.fit(X, y)
        importance_scores['random_forest'] = pd.Series(
            rf.feature_importances_, 
            index=X.columns
        ).sort_values(ascending=False)
        
        # 5. SHAP 값 (샘플링으로 속도 개선)
        sample_size = min(1000, len(X))
        X_sample = X.sample(n=sample_size, random_state=42)
        
        explainer = shap.TreeExplainer(rf)
        shap_values = explainer.shap_values(X_sample)
        
        if isinstance(shap_values, list):  # 다중 클래스
            shap_importance = np.abs(shap_values).mean(0).mean(0)
        else:
            shap_importance = np.abs(shap_values).mean(0)
            
        importance_scores['shap'] = pd.Series(
            shap_importance, 
            index=X.columns
        ).sort_values(ascending=False)
        
        # 종합 순위
        combined_ranks = pd.DataFrame(importance_scores)
        combined_ranks['mean_rank'] = combined_ranks.rank(ascending=False).mean(axis=1)
        combined_ranks = combined_ranks.sort_values('mean_rank')
        
        # 시각화
        fig, ax = plt.subplots(figsize=(10, 8))
        combined_ranks.head(20).plot(kind='barh', ax=ax)
        ax.set_title('Feature Importance Scores (Top 20)')
        plt.tight_layout()
        plt.savefig('reports/feature_importance.png')
        
        return combined_ranks
    
    def recommend_features(self, importance_df: pd.DataFrame, threshold: float = 0.95):
        """특성 선택 추천"""
        
        # 누적 중요도 계산
        cumsum_importance = importance_df['random_forest'].cumsum() / importance_df['random_forest'].sum()
        
        # 임계값을 만족하는 최소 특성 집합
        selected_features = cumsum_importance[cumsum_importance <= threshold].index.tolist()
        
        return {
            'selected_features': selected_features,
            'n_features': len(selected_features),
            'cumulative_importance': cumsum_importance[selected_features[-1]]
        }
```

---

### 🤖 3단계: 모델 개발 및 실험 (1시간 30분)

다음 ML 모델 개발 시스템을 구현해줘:

#### AutoML 파이프라인
```python
# src/models/automl_pipeline.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import optuna
from sklearn.model_selection import cross_val_score
import mlflow
import mlflow.sklearn
from datetime import datetime

class AutoMLPipeline:
    def __init__(self, task_type: str, config: Dict[str, Any]):
        self.task_type = task_type  # classification, regression
        self.config = config
        self.models = self._get_model_candidates()
        self.best_model = None
        self.best_params = None
        self.best_score = None
        
        # MLflow 설정
        mlflow.set_tracking_uri(config.get('mlflow_uri', 'http://localhost:5000'))
        mlflow.set_experiment(config.get('experiment_name', 'automl_experiment'))
    
    def _get_model_candidates(self) -> Dict[str, Any]:
        """태스크에 따른 모델 후보군 정의"""
        
        if self.task_type == 'classification':
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.svm import SVC
            from xgboost import XGBClassifier
            from lightgbm import LGBMClassifier
            
            return {
                'logistic_regression': {
                    'model': LogisticRegression,
                    'params': {
                        'C': ('float', 0.01, 100, 'log'),
                        'penalty': ('categorical', ['l1', 'l2']),
                        'solver': ('categorical', ['liblinear', 'saga'])
                    }
                },
                'random_forest': {
                    'model': RandomForestClassifier,
                    'params': {
                        'n_estimators': ('int', 50, 500),
                        'max_depth': ('int', 3, 20),
                        'min_samples_split': ('int', 2, 20),
                        'min_samples_leaf': ('int', 1, 10)
                    }
                },
                'xgboost': {
                    'model': XGBClassifier,
                    'params': {
                        'n_estimators': ('int', 50, 500),
                        'max_depth': ('int', 3, 10),
                        'learning_rate': ('float', 0.01, 0.3, 'log'),
                        'subsample': ('float', 0.6, 1.0),
                        'colsample_bytree': ('float', 0.6, 1.0)
                    }
                },
                'lightgbm': {
                    'model': LGBMClassifier,
                    'params': {
                        'n_estimators': ('int', 50, 500),
                        'num_leaves': ('int', 20, 300),
                        'learning_rate': ('float', 0.01, 0.3, 'log'),
                        'feature_fraction': ('float', 0.6, 1.0),
                        'bagging_fraction': ('float', 0.6, 1.0)
                    }
                }
            }
        else:  # regression
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.linear_model import LinearRegression, Ridge, Lasso
            from xgboost import XGBRegressor
            from lightgbm import LGBMRegressor
            
            return {
                'linear_regression': {
                    'model': Ridge,
                    'params': {
                        'alpha': ('float', 0.01, 100, 'log')
                    }
                },
                'random_forest': {
                    'model': RandomForestRegressor,
                    'params': {
                        'n_estimators': ('int', 50, 500),
                        'max_depth': ('int', 3, 20),
                        'min_samples_split': ('int', 2, 20)
                    }
                },
                'xgboost': {
                    'model': XGBRegressor,
                    'params': {
                        'n_estimators': ('int', 50, 500),
                        'max_depth': ('int', 3, 10),
                        'learning_rate': ('float', 0.01, 0.3, 'log'),
                        'subsample': ('float', 0.6, 1.0)
                    }
                },
                'lightgbm': {
                    'model': LGBMRegressor,
                    'params': {
                        'n_estimators': ('int', 50, 500),
                        'num_leaves': ('int', 20, 300),
                        'learning_rate': ('float', 0.01, 0.3, 'log')
                    }
                }
            }
    
    def optimize_model(self, model_name: str, X_train, y_train, X_val, y_val, n_trials: int = 50):
        """Optuna를 사용한 하이퍼파라미터 최적화"""
        
        model_config = self.models[model_name]
        
        def objective(trial):
            # 하이퍼파라미터 샘플링
            params = {}
            for param_name, param_config in model_config['params'].items():
                if param_config[0] == 'int':
                    params[param_name] = trial.suggest_int(param_name, param_config[1], param_config[2])
                elif param_config[0] == 'float':
                    if len(param_config) > 3 and param_config[3] == 'log':
                        params[param_name] = trial.suggest_float(param_name, param_config[1], param_config[2], log=True)
                    else:
                        params[param_name] = trial.suggest_float(param_name, param_config[1], param_config[2])
                elif param_config[0] == 'categorical':
                    params[param_name] = trial.suggest_categorical(param_name, param_config[1])
            
            # 모델 학습
            model = model_config['model'](**params)
            model.fit(X_train, y_train)
            
            # 검증 점수
            if self.task_type == 'classification':
                from sklearn.metrics import roc_auc_score
                y_pred_proba = model.predict_proba(X_val)[:, 1]
                score = roc_auc_score(y_val, y_pred_proba)
            else:
                from sklearn.metrics import mean_squared_error
                y_pred = model.predict(X_val)
                score = -mean_squared_error(y_val, y_pred)  # 최대화를 위해 음수
            
            return score
        
        # Optuna 스터디 생성 및 최적화
        study = optuna.create_study(
            direction='maximize',
            study_name=f'{model_name}_optimization'
        )
        
        study.optimize(objective, n_trials=n_trials)
        
        # 최적 파라미터로 최종 모델 학습
        best_params = study.best_params
        best_model = model_config['model'](**best_params)
        best_model.fit(X_train, y_train)
        
        return best_model, best_params, study.best_value
    
    def run_automl(self, X_train, y_train, X_val, y_val, time_budget_minutes: int = 60):
        """AutoML 실행"""
        
        import time
        start_time = time.time()
        results = {}
        
        with mlflow.start_run(run_name=f"automl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            
            for model_name in self.models.keys():
                if time.time() - start_time > time_budget_minutes * 60:
                    break
                
                print(f"\nOptimizing {model_name}...")
                
                # 각 모델에 대한 중첩 실행
                with mlflow.start_run(run_name=model_name, nested=True):
                    
                    # 하이퍼파라미터 최적화
                    model, params, score = self.optimize_model(
                        model_name, X_train, y_train, X_val, y_val
                    )
                    
                    # 결과 저장
                    results[model_name] = {
                        'model': model,
                        'params': params,
                        'score': score
                    }
                    
                    # MLflow 로깅
                    mlflow.log_params(params)
                    mlflow.log_metric('validation_score', score)
                    mlflow.sklearn.log_model(model, model_name)
                    
                    # 추가 메트릭 계산 및 로깅
                    self._log_additional_metrics(model, X_val, y_val)
            
            # 최고 모델 선택
            best_model_name = max(results, key=lambda x: results[x]['score'])
            self.best_model = results[best_model_name]['model']
            self.best_params = results[best_model_name]['params']
            self.best_score = results[best_model_name]['score']
            
            # 최고 모델 태그
            mlflow.set_tag('best_model', best_model_name)
            mlflow.log_metric('best_score', self.best_score)
        
        return results
    
    def _log_additional_metrics(self, model, X_val, y_val):
        """추가 평가 메트릭 로깅"""
        
        y_pred = model.predict(X_val)
        
        if self.task_type == 'classification':
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            mlflow.log_metric('accuracy', accuracy_score(y_val, y_pred))
            mlflow.log_metric('precision', precision_score(y_val, y_pred, average='weighted'))
            mlflow.log_metric('recall', recall_score(y_val, y_pred, average='weighted'))
            mlflow.log_metric('f1_score', f1_score(y_val, y_pred, average='weighted'))
            
            # Confusion Matrix
            from sklearn.metrics import confusion_matrix
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            cm = confusion_matrix(y_val, y_pred)
            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.title('Confusion Matrix')
            plt.savefig('confusion_matrix.png')
            mlflow.log_artifact('confusion_matrix.png')
            
        else:  # regression
            from sklearn.metrics import mean_absolute_error, r2_score
            
            mlflow.log_metric('mae', mean_absolute_error(y_val, y_pred))
            mlflow.log_metric('rmse', np.sqrt(mean_squared_error(y_val, y_pred)))
            mlflow.log_metric('r2_score', r2_score(y_val, y_pred))
            
            # Residual Plot
            plt.figure(figsize=(10, 6))
            plt.scatter(y_pred, y_val - y_pred, alpha=0.5)
            plt.axhline(y=0, color='r', linestyle='--')
            plt.xlabel('Predicted Values')
            plt.ylabel('Residuals')
            plt.title('Residual Plot')
            plt.savefig('residual_plot.png')
            mlflow.log_artifact('residual_plot.png')

# 딥러닝 모델 개발 (선택적)
class DeepLearningPipeline:
    def __init__(self, model_type: str, config: Dict[str, Any]):
        self.model_type = model_type
        self.config = config
        
    def build_neural_network(self, input_shape: int, output_shape: int):
        """신경망 아키텍처 구축"""
        
        import tensorflow as tf
        from tensorflow.keras import layers, models
        
        if self.model_type == 'classification':
            model = models.Sequential([
                layers.Dense(128, activation='relu', input_shape=(input_shape,)),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                
                layers.Dense(64, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                
                layers.Dense(32, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.2),
                
                layers.Dense(output_shape, activation='softmax' if output_shape > 1 else 'sigmoid')
            ])
            
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='sparse_categorical_crossentropy' if output_shape > 1 else 'binary_crossentropy',
                metrics=['accuracy']
            )
            
        elif self.model_type == 'regression':
            model = models.Sequential([
                layers.Dense(128, activation='relu', input_shape=(input_shape,)),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                
                layers.Dense(64, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                
                layers.Dense(32, activation='relu'),
                layers.BatchNormalization(),
                
                layers.Dense(1)  # 회귀는 출력이 1개
            ])
            
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
        elif self.model_type == 'nlp':
            # Transformer 기반 모델
            from transformers import TFAutoModelForSequenceClassification
            
            model = TFAutoModelForSequenceClassification.from_pretrained(
                'bert-base-uncased',
                num_labels=output_shape
            )
            
        elif self.model_type == 'computer_vision':
            # CNN 아키텍처
            model = models.Sequential([
                layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
                layers.MaxPooling2D((2, 2)),
                
                layers.Conv2D(64, (3, 3), activation='relu'),
                layers.MaxPooling2D((2, 2)),
                
                layers.Conv2D(128, (3, 3), activation='relu'),
                layers.MaxPooling2D((2, 2)),
                
                layers.Flatten(),
                layers.Dense(128, activation='relu'),
                layers.Dropout(0.5),
                layers.Dense(output_shape, activation='softmax')
            ])
            
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
        
        return model
    
    def train_with_callbacks(self, model, X_train, y_train, X_val, y_val):
        """콜백을 사용한 모델 학습"""
        
        import tensorflow as tf
        
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            ),
            tf.keras.callbacks.ModelCheckpoint(
                'best_model.h5',
                monitor='val_loss',
                save_best_only=True
            ),
            tf.keras.callbacks.TensorBoard(
                log_dir='./logs',
                histogram_freq=1
            )
        ]
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        return model, history
```

#### 모델 평가 및 해석
```python
# src/models/model_evaluation.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, roc_curve, auc
import shap
import lime
import lime.lime_tabular

class ModelEvaluator:
    def __init__(self, model, model_type: str):
        self.model = model
        self.model_type = model_type
        
    def comprehensive_evaluation(self, X_test, y_test, feature_names=None):
        """포괄적인 모델 평가"""
        
        evaluation_results = {}
        
        # 1. 기본 성능 메트릭
        y_pred = self.model.predict(X_test)
        
        if self.model_type == 'classification':
            # 분류 리포트
            report = classification_report(y_test, y_pred, output_dict=True)
            evaluation_results['classification_report'] = report
            
            # ROC 커브 (이진 분류)
            if len(np.unique(y_test)) == 2:
                y_pred_proba = self.model.predict_proba(X_test)[:, 1]
                fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
                roc_auc = auc(fpr, tpr)
                
                plt.figure(figsize=(8, 6))
                plt.plot(fpr, tpr, color='darkorange', lw=2, 
                        label=f'ROC curve (AUC = {roc_auc:.2f})')
                plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
                plt.xlim([0.0, 1.0])
                plt.ylim([0.0, 1.05])
                plt.xlabel('False Positive Rate')
                plt.ylabel('True Positive Rate')
                plt.title('ROC Curve')
                plt.legend(loc="lower right")
                plt.savefig('reports/roc_curve.png')
                
                evaluation_results['roc_auc'] = roc_auc
                
        else:  # regression
            from sklearn.metrics import mean_absolute_error, r2_score
            
            evaluation_results['mae'] = mean_absolute_error(y_test, y_pred)
            evaluation_results['rmse'] = np.sqrt(np.mean((y_test - y_pred) ** 2))
            evaluation_results['r2'] = r2_score(y_test, y_pred)
            
            # 예측 vs 실제 플롯
            plt.figure(figsize=(8, 6))
            plt.scatter(y_test, y_pred, alpha=0.5)
            plt.plot([y_test.min(), y_test.max()], 
                    [y_test.min(), y_test.max()], 'r--', lw=2)
            plt.xlabel('Actual Values')
            plt.ylabel('Predicted Values')
            plt.title('Predicted vs Actual')
            plt.savefig('reports/predicted_vs_actual.png')
        
        # 2. 특성 중요도 분석
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': feature_names or [f'feature_{i}' for i in range(X_test.shape[1])],
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            plt.figure(figsize=(10, 8))
            feature_importance.head(20).plot(x='feature', y='importance', kind='barh')
            plt.title('Top 20 Feature Importances')
            plt.tight_layout()
            plt.savefig('reports/feature_importance_model.png')
            
            evaluation_results['feature_importance'] = feature_importance
        
        return evaluation_results
    
    def explain_predictions(self, X_test, sample_indices=[0, 1, 2], feature_names=None):
        """개별 예측 설명"""
        
        explanations = {}
        
        # SHAP 설명
        if hasattr(self.model, 'predict'):
            # TreeExplainer for tree-based models
            try:
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(X_test)
                
                # SHAP Summary Plot
                plt.figure()
                shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
                plt.savefig('reports/shap_summary.png')
                plt.close()
                
                # Individual explanations
                for idx in sample_indices:
                    plt.figure()
                    shap.waterfall_plot(
                        shap.Explanation(
                            values=shap_values[idx] if len(shap_values.shape) == 2 else shap_values[0][idx],
                            base_values=explainer.expected_value if isinstance(explainer.expected_value, float) else explainer.expected_value[0],
                            data=X_test[idx],
                            feature_names=feature_names
                        ),
                        show=False
                    )
                    plt.savefig(f'reports/shap_waterfall_sample_{idx}.png')
                    plt.close()
                    
            except:
                # KernelExplainer for black-box models
                explainer = shap.KernelExplainer(self.model.predict, X_test[:100])
                shap_values = explainer.shap_values(X_test[sample_indices])
        
        # LIME 설명
        explainer_lime = lime.lime_tabular.LimeTabularExplainer(
            X_test,
            feature_names=feature_names,
            mode='classification' if self.model_type == 'classification' else 'regression'
        )
        
        for idx in sample_indices:
            exp = explainer_lime.explain_instance(
                X_test[idx], 
                self.model.predict_proba if self.model_type == 'classification' else self.model.predict,
                num_features=10
            )
            
            # LIME 플롯 저장
            fig = exp.as_pyplot_figure()
            fig.savefig(f'reports/lime_explanation_sample_{idx}.png')
            plt.close()
            
            explanations[f'sample_{idx}'] = exp.as_list()
        
        return explanations
    
    def fairness_evaluation(self, X_test, y_test, sensitive_features):
        """공정성 평가"""
        
        from fairlearn.metrics import MetricFrame
        from sklearn.metrics import accuracy_score, precision_score, recall_score
        
        y_pred = self.model.predict(X_test)
        
        # 민감한 특성별 성능 메트릭
        metrics = {
            'accuracy': accuracy_score,
            'precision': lambda y_t, y_p: precision_score(y_t, y_p, average='weighted'),
            'recall': lambda y_t, y_p: recall_score(y_t, y_p, average='weighted')
        }
        
        fairness_results = {}
        
        for feature in sensitive_features:
            mf = MetricFrame(
                metrics=metrics,
                y_true=y_test,
                y_pred=y_pred,
                sensitive_features=X_test[feature]
            )
            
            # 그룹별 성능 차이
            fairness_results[feature] = {
                'overall': mf.overall.to_dict(),
                'by_group': mf.by_group.to_dict(),
                'difference': mf.difference().to_dict(),
                'ratio': mf.ratio().to_dict()
            }
            
            # 시각화
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            for idx, (metric_name, metric_values) in enumerate(mf.by_group.items()):
                metric_values.plot(kind='bar', ax=axes[idx])
                axes[idx].set_title(f'{metric_name} by {feature}')
                axes[idx].set_ylabel(metric_name)
            
            plt.tight_layout()
            plt.savefig(f'reports/fairness_{feature}.png')
        
        return fairness_results
```

---

### 🚀 4단계: 모델 배포 준비 (45분)

다음 모델 배포 시스템을 구현해줘:

#### 모델 서빙 API
```python
# src/serving/model_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
import joblib
import logging
from typing import List, Dict, Any, Optional
import redis
import json
from prometheus_client import Counter, Histogram, generate_latest
import time

# Prometheus 메트릭
prediction_counter = Counter('model_predictions_total', 'Total number of predictions')
prediction_duration = Histogram('model_prediction_duration_seconds', 'Prediction duration')
prediction_errors = Counter('model_prediction_errors_total', 'Total prediction errors')

app = FastAPI(title="ML Model API", version="1.0.0")

# 모델 및 전처리기 로드
MODEL_PATH = "models/best_model.pkl"
SCALER_PATH = "models/scaler.pkl"
FEATURE_NAMES_PATH = "models/feature_names.json"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
with open(FEATURE_NAMES_PATH, 'r') as f:
    feature_names = json.load(f)

# Redis 캐시 설정
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionRequest(BaseModel):
    """예측 요청 스키마"""
    features: Dict[str, Any] = Field(..., example={
        "age": 35,
        "income": 75000,
        "credit_score": 720,
        "account_age_days": 365
    })
    request_id: Optional[str] = Field(None, description="Unique request ID for tracking")

class PredictionResponse(BaseModel):
    """예측 응답 스키마"""
    prediction: float
    probability: Optional[Dict[str, float]] = None
    confidence: float
    model_version: str
    request_id: Optional[str]
    processing_time_ms: float

class BatchPredictionRequest(BaseModel):
    """배치 예측 요청"""
    instances: List[Dict[str, Any]]
    
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return generate_latest()

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """단일 예측 엔드포인트"""
    
    start_time = time.time()
    prediction_counter.inc()
    
    try:
        # 캐시 확인
        cache_key = f"prediction:{hash(str(sorted(request.features.items())))}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # 특성 준비
        feature_vector = prepare_features(request.features)
        
        # 예측
        with prediction_duration.time():
            prediction = model.predict(feature_vector)[0]
            
            # 확률 계산 (분류 모델인 경우)
            probability = None
            confidence = 1.0
            
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(feature_vector)[0]
                probability = {f"class_{i}": float(p) for i, p in enumerate(proba)}
                confidence = float(max(proba))
        
        # 응답 생성
        response = PredictionResponse(
            prediction=float(prediction),
            probability=probability,
            confidence=confidence,
            model_version="1.0.0",
            request_id=request.request_id,
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        # 캐시 저장 (5분 TTL)
        redis_client.setex(cache_key, 300, response.json())
        
        # 로깅
        logger.info(f"Prediction completed: {response.dict()}")
        
        return response
        
    except Exception as e:
        prediction_errors.inc()
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_batch")
async def predict_batch(request: BatchPredictionRequest):
    """배치 예측 엔드포인트"""
    
    start_time = time.time()
    results = []
    
    for instance in request.instances:
        try:
            feature_vector = prepare_features(instance)
            prediction = model.predict(feature_vector)[0]
            
            results.append({
                "prediction": float(prediction),
                "status": "success"
            })
        except Exception as e:
            results.append({
                "prediction": None,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "predictions": results,
        "processing_time_ms": (time.time() - start_time) * 1000
    }

def prepare_features(raw_features: Dict[str, Any]) -> np.ndarray:
    """원시 특성을 모델 입력 형태로 변환"""
    
    # 특성 순서 맞추기
    feature_vector = []
    for feature_name in feature_names:
        if feature_name not in raw_features:
            raise ValueError(f"Missing required feature: {feature_name}")
        feature_vector.append(raw_features[feature_name])
    
    # NumPy 배열로 변환
    feature_array = np.array(feature_vector).reshape(1, -1)
    
    # 스케일링 적용
    feature_array = scaler.transform(feature_array)
    
    return feature_array

# A/B 테스트 지원
class ABTestConfig:
    def __init__(self):
        self.models = {
            'control': joblib.load('models/model_v1.pkl'),
            'treatment': joblib.load('models/model_v2.pkl')
        }
        self.traffic_split = {'control': 0.5, 'treatment': 0.5}
    
    def get_model_variant(self, user_id: str):
        """사용자 ID 기반 모델 변형 선택"""
        hash_value = hash(user_id) % 100
        if hash_value < self.traffic_split['control'] * 100:
            return 'control'
        return 'treatment'

# 모델 모니터링
class ModelMonitor:
    def __init__(self):
        self.prediction_log = []
        
    def log_prediction(self, features, prediction, actual=None):
        """예측 로깅"""
        self.prediction_log.append({
            'timestamp': time.time(),
            'features': features,
            'prediction': prediction,
            'actual': actual
        })
        
        # 드리프트 감지
        if len(self.prediction_log) % 1000 == 0:
            self.check_drift()
    
    def check_drift(self):
        """데이터 드리프트 감지"""
        recent_predictions = self.prediction_log[-1000:]
        # 드리프트 감지 로직 구현
        pass
```

#### 컨테이너화 및 배포 설정
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY src/ ./src/
COPY models/ ./models/

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 실행
CMD ["uvicorn", "src.serving.model_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# kubernetes/model-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-model-api
  labels:
    app: ml-model
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
      - name: model-api
        image: ml-model:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: MODEL_VERSION
          value: "1.0.0"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ml-model-service
spec:
  selector:
    app: ml-model
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-model-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-model-api
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

---

### 📊 5단계: MLOps 파이프라인 및 모니터링 (30분)

다음 MLOps 시스템을 구현해줘:

#### CI/CD 파이프라인
```yaml
# .github/workflows/ml-pipeline.yml
name: ML Model Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml

  train:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Download data
      run: |
        aws s3 cp s3://ml-data/train_data.parquet data/
    
    - name: Train model
      run: |
        python src/train.py --config config/model_config.yaml
    
    - name: Evaluate model
      run: |
        python src/evaluate.py --model models/latest_model.pkl
    
    - name: Upload model to registry
      if: success()
      run: |
        python src/register_model.py --model models/latest_model.pkl

  deploy:
    needs: train
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t ml-model:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        docker tag ml-model:${{ github.sha }} ${{ secrets.DOCKER_REGISTRY }}/ml-model:latest
        docker push ${{ secrets.DOCKER_REGISTRY }}/ml-model:latest
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/ml-model-api model-api=${{ secrets.DOCKER_REGISTRY }}/ml-model:latest
        kubectl rollout status deployment/ml-model-api

  monitor:
    needs: deploy
    runs-on: ubuntu-latest
    
    steps:
    - name: Run smoke tests
      run: |
        python tests/smoke_tests.py --endpoint https://api.example.com/predict
    
    - name: Check model metrics
      run: |
        python src/monitoring/check_metrics.py --threshold config/alert_thresholds.yaml
```

#### 모델 모니터링 시스템
```python
# src/monitoring/model_monitor.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
import requests
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
from prometheus_client import Gauge, Counter
import logging

# Prometheus 메트릭
model_accuracy_gauge = Gauge('model_accuracy', 'Current model accuracy')
drift_score_gauge = Gauge('data_drift_score', 'Data drift score')
prediction_latency_gauge = Gauge('prediction_latency_ms', 'Prediction latency in milliseconds')
daily_predictions_counter = Counter('daily_predictions_total', 'Total daily predictions')

class ModelMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reference_data = pd.read_parquet(config['reference_data_path'])
        
    def monitor_performance(self, production_data: pd.DataFrame):
        """모델 성능 모니터링"""
        
        # 실제 레이블이 있는 데이터만 사용
        labeled_data = production_data[production_data['actual_label'].notna()]
        
        if len(labeled_data) > 0:
            # 정확도 계산
            accuracy = (labeled_data['prediction'] == labeled_data['actual_label']).mean()
            model_accuracy_gauge.set(accuracy)
            
            # 성능 저하 알림
            if accuracy < self.config['accuracy_threshold']:
                self._send_alert({
                    'type': 'performance_degradation',
                    'metric': 'accuracy',
                    'current_value': accuracy,
                    'threshold': self.config['accuracy_threshold']
                })
        
        return accuracy
    
    def detect_data_drift(self, current_data: pd.DataFrame):
        """데이터 드리프트 감지"""
        
        # Evidently 리포트 생성
        data_drift_report = Report(metrics=[
            DataDriftPreset(),
        ])
        
        data_drift_report.run(
            reference_data=self.reference_data,
            current_data=current_data
        )
        
        # 드리프트 점수 추출
        drift_results = data_drift_report.as_dict()
        drift_score = drift_results['metrics'][0]['result']['drift_score']
        
        drift_score_gauge.set(drift_score)
        
        # 드리프트 알림
        if drift_score > self.config['drift_threshold']:
            self._send_alert({
                'type': 'data_drift',
                'drift_score': drift_score,
                'threshold': self.config['drift_threshold'],
                'drifted_features': self._get_drifted_features(drift_results)
            })
        
        return drift_results
    
    def monitor_prediction_distribution(self, predictions: List[float]):
        """예측 분포 모니터링"""
        
        pred_array = np.array(predictions)
        
        # 분포 통계
        stats = {
            'mean': np.mean(pred_array),
            'std': np.std(pred_array),
            'min': np.min(pred_array),
            'max': np.max(pred_array),
            'percentiles': {
                '25': np.percentile(pred_array, 25),
                '50': np.percentile(pred_array, 50),
                '75': np.percentile(pred_array, 75)
            }
        }
        
        # 이상 패턴 감지
        if stats['std'] < self.config['min_prediction_std']:
            self._send_alert({
                'type': 'prediction_pattern_anomaly',
                'issue': 'low_variance',
                'std': stats['std']
            })
        
        return stats
    
    def _send_alert(self, alert_data: Dict[str, Any]):
        """알림 전송"""
        
        alert_data['timestamp'] = datetime.now().isoformat()
        alert_data['model_version'] = self.config['model_version']
        
        # Slack 알림
        if self.config.get('slack_webhook'):
            requests.post(
                self.config['slack_webhook'],
                json={
                    'text': f"🚨 Model Alert: {alert_data['type']}",
                    'blocks': [
                        {
                            'type': 'section',
                            'text': {
                                'type': 'mrkdwn',
                                'text': f"*Alert Type:* {alert_data['type']}\n"
                                       f"*Details:* ```{alert_data}```"
                            }
                        }
                    ]
                }
            )
        
        # 로그 기록
        self.logger.warning(f"Model alert: {alert_data}")

# 실시간 모니터링 대시보드
def create_monitoring_dashboard():
    """Grafana 대시보드 설정"""
    
    dashboard_config = {
        "dashboard": {
            "title": "ML Model Monitoring",
            "panels": [
                {
                    "title": "Model Accuracy",
                    "targets": [{"expr": "model_accuracy"}],
                    "type": "graph"
                },
                {
                    "title": "Data Drift Score",
                    "targets": [{"expr": "data_drift_score"}],
                    "type": "gauge",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 0.1},
                            {"color": "red", "value": 0.3}
                        ]
                    }
                },
                {
                    "title": "Prediction Latency",
                    "targets": [{"expr": "histogram_quantile(0.95, prediction_latency_ms)"}],
                    "type": "graph"
                },
                {
                    "title": "Daily Predictions",
                    "targets": [{"expr": "rate(daily_predictions_total[1d])"}],
                    "type": "stat"
                }
            ]
        }
    }
    
    return dashboard_config
```

---

### 📋 6단계: 문서화 및 모델 거버넌스 (15분)

다음 문서와 거버넌스 체계를 생성해줘:

#### 모델 카드 및 문서화
```markdown
# Model Card: 고객 이탈 예측 모델

## 모델 개요
- **모델명**: Customer Churn Predictor v1.0
- **개발일**: 2024-03-15
- **개발팀**: ML Engineering Team
- **모델 유형**: Binary Classification (XGBoost)
- **프레임워크**: scikit-learn 1.2.0, xgboost 1.7.0

## 사용 목적
- **주요 목적**: 고객 이탈 가능성 예측
- **사용 사례**: 
  - 고위험 고객 식별
  - 맞춤형 리텐션 캠페인
  - 고객 생애가치 최적화

## 데이터
- **학습 데이터**: 
  - 기간: 2022-01-01 ~ 2023-12-31
  - 크기: 1.2M 고객 레코드
  - 특성: 45개 (인구통계, 행동, 거래)
- **검증 데이터**: 2024-01-01 ~ 2024-02-28

## 성능 메트릭
| 메트릭 | 값 |
|--------|-----|
| Accuracy | 0.92 |
| Precision | 0.89 |
| Recall | 0.85 |
| F1-Score | 0.87 |
| AUC-ROC | 0.94 |

## 한계 및 편향
- **알려진 한계**:
  - 신규 고객 (< 30일) 예측 정확도 낮음
  - 계절성 패턴 완전히 포착 못함
- **편향 분석**:
  - 연령대별 성능 차이 < 5%
  - 지역별 성능 균일

## 윤리적 고려사항
- 개인정보 보호 준수 (GDPR, CCPA)
- 설명 가능한 AI 원칙 적용
- 공정성 메트릭 모니터링

## 사용 가이드
```python
# 예측 API 호출
response = requests.post(
    "https://api.example.com/predict",
    json={
        "features": {
            "account_age_days": 365,
            "total_transactions": 42,
            "avg_transaction_value": 125.50
        }
    }
)
```

## 모니터링 및 유지보수
- 일일 성능 모니터링
- 주간 데이터 드리프트 검사
- 월간 재학습 평가
```

#### 모델 거버넌스 프로세스
```python
# src/governance/model_registry.py
from typing import Dict, Any, Optional
import mlflow
from datetime import datetime
import json

class ModelRegistry:
    def __init__(self, registry_uri: str):
        self.registry_uri = registry_uri
        mlflow.set_registry_uri(registry_uri)
        
    def register_model(self, model_path: str, model_metadata: Dict[str, Any]):
        """모델 등록 및 승인 프로세스"""
        
        # 모델 등록
        model_uri = f"runs:/{model_metadata['run_id']}/model"
        model_version = mlflow.register_model(
            model_uri,
            model_metadata['model_name']
        )
        
        # 메타데이터 추가
        client = mlflow.tracking.MlflowClient()
        
        # 모델 버전 태그
        client.set_model_version_tag(
            model_metadata['model_name'],
            model_version.version,
            "developer",
            model_metadata['developer']
        )
        
        client.set_model_version_tag(
            model_metadata['model_name'],
            model_version.version,
            "performance_metrics",
            json.dumps(model_metadata['metrics'])
        )
        
        # 승인 워크플로우
        self._approval_workflow(
            model_metadata['model_name'],
            model_version.version,
            model_metadata
        )
        
        return model_version
    
    def _approval_workflow(self, model_name: str, version: str, metadata: Dict[str, Any]):
        """모델 승인 워크플로우"""
        
        client = mlflow.tracking.MlflowClient()
        
        # 1단계: 개발 환경
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Staging"
        )
        
        # 2단계: 자동 검증
        validation_passed = self._run_validation_checks(model_name, version, metadata)
        
        if validation_passed:
            # 3단계: 프로덕션 승인 요청
            client.set_model_version_tag(
                model_name,
                version,
                "approval_status",
                "pending_review"
            )
            
            # 승인자에게 알림
            self._notify_approvers(model_name, version, metadata)
        else:
            client.set_model_version_tag(
                model_name,
                version,
                "approval_status",
                "failed_validation"
            )
    
    def _run_validation_checks(self, model_name: str, version: str, metadata: Dict[str, Any]) -> bool:
        """자동 검증 체크"""
        
        checks = {
            "performance_threshold": metadata['metrics']['accuracy'] > 0.85,
            "fairness_check": all(bias < 0.1 for bias in metadata.get('bias_metrics', {}).values()),
            "security_scan": self._security_scan_passed(model_name, version),
            "documentation_complete": all(k in metadata for k in ['description', 'limitations', 'ethics'])
        }
        
        return all(checks.values())
    
    def promote_to_production(self, model_name: str, version: str, approver: str):
        """프로덕션 배포 승인"""
        
        client = mlflow.tracking.MlflowClient()
        
        # 프로덕션으로 전환
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production"
        )
        
        # 승인 기록
        client.set_model_version_tag(
            model_name,
            version,
            "approved_by",
            approver
        )
        
        client.set_model_version_tag(
            model_name,
            version,
            "approval_timestamp",
            datetime.now().isoformat()
        )
        
        # 이전 프로덕션 모델 아카이브
        self._archive_previous_production_models(model_name, version)
        
        return True
```

**결과물**:
- 완전한 ML/AI 개발 파이프라인
- AutoML 및 딥러닝 지원
- 모델 서빙 API 및 인프라
- MLOps CI/CD 파이프라인
- 실시간 모니터링 시스템
- 모델 거버넌스 체계

---

이 워크플로우를 실행하면 데이터 준비부터 프로덕션 배포까지 완전한 ML/AI 시스템이 자동으로 구축됩니다!