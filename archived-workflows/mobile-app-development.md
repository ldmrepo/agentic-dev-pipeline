# 모바일 앱 개발 워크플로우

## 📱 크로스 플랫폼 모바일 앱 자동 개발

이 워크플로우는 React Native와 Flutter를 활용하여 iOS/Android 크로스 플랫폼 모바일 애플리케이션을 자동으로 개발합니다.

**목표 완료 시간: 3-5시간**

## 실행 방법
```bash
export REQUIREMENTS="소셜 미디어 모바일 앱 (사진 공유, 댓글, 좋아요)"
export PLATFORM="react-native" # 또는 "flutter"
export TARGET_DEVICES="ios,android"
claude -f workflows/mobile-app-development.md
```

## 워크플로우 단계

### 📐 1단계: 모바일 앱 설계 및 계획 (45분)

다음을 수행해줘:

#### UX/UI 설계 및 사용자 여정 매핑
- 앱 요구사항: ${REQUIREMENTS}
- 타겟 플랫폼: ${TARGET_DEVICES}
- 선택 기술: ${PLATFORM}

```
사용자 경험 설계:
1. 타겟 사용자 페르소나 정의
2. 핵심 사용자 여정 매핑 (User Journey)
3. 정보 아키텍처 구성
4. 와이어프레임 생성 (주요 화면 5-7개)
5. 사용성 원칙 적용 (접근성 포함)

UI 디자인 시스템:
- 컬러 팔레트 정의 (Primary, Secondary, Accent)
- 타이포그래피 스케일 (Heading, Body, Caption)
- 컴포넌트 라이브러리 (Button, Input, Card 등)
- 아이콘 시스템 (Material Design/SF Symbols)
- 스페이싱 시스템 (4pt/8pt grid)

플랫폼별 가이드라인 준수:
- iOS: Human Interface Guidelines
- Android: Material Design Guidelines
- 네이티브 UX 패턴 적용
- 플랫폼별 네비게이션 구조
```

#### 기술 아키텍처 설계
```
모바일 아키텍처 패턴:
- MVVM (Model-View-ViewModel) 패턴 적용
- 상태 관리: Redux Toolkit (RN) / Bloc (Flutter)
- 네비게이션: React Navigation / Flutter Navigator
- API 통신: Axios / Dio
- 로컬 저장소: AsyncStorage / SharedPreferences

성능 최적화 전략:
- 이미지 최적화 및 캐싱
- 지연 로딩 (Lazy Loading)
- 메모리 관리 최적화
- 배터리 효율성 고려
- 네트워크 최적화

보안 설계:
- 앱 서명 및 인증서 관리
- API 보안 (Token 기반 인증)
- 로컬 데이터 암호화
- 바이오메트릭 인증 지원
- 루팅/탈옥 탐지
```

**결과물**: 
- `docs/mobile-ux-design.md`
- `docs/mobile-architecture.md`
- `wireframes/` 폴더 (주요 화면 와이어프레임)

---

### 📱 2단계: 크로스 플랫폼 개발 (2-3시간)

선택된 플랫폼에 따라 개발을 진행해줘:

#### React Native 개발 경로
```
프로젝트 초기화:
# React Native CLI 또는 Expo 선택
npx react-native init MobileApp --template react-native-template-typescript

폴더 구조 생성:
src/
├── components/          # 재사용 가능한 UI 컴포넌트
│   ├── common/         # 공통 컴포넌트
│   ├── forms/          # 폼 관련 컴포넌트
│   └── navigation/     # 네비게이션 컴포넌트
├── screens/            # 화면 컴포넌트
│   ├── auth/          # 인증 관련 화면
│   ├── main/          # 메인 기능 화면
│   └── profile/       # 프로필 관련 화면
├── services/          # API 및 비즈니스 로직
├── store/             # Redux 상태 관리
├── utils/             # 유틸리티 함수
├── styles/            # 스타일 정의
└── types/             # TypeScript 타입 정의

핵심 기능 구현:
1. 네비게이션 설정 (Stack, Tab, Drawer Navigator)
2. 상태 관리 (Redux Toolkit + RTK Query)
3. 인증 시스템 (JWT + Biometric)
4. API 통신 및 데이터 관리
5. 푸시 알림 (@react-native-firebase/messaging)
6. 이미지 처리 (react-native-image-picker)
7. 카메라 통합 (react-native-vision-camera)
8. 지도 통합 (react-native-maps)

플랫폼별 최적화:
- iOS: CocoaPods 설정, iOS 특화 기능
- Android: Gradle 설정, Android 특화 기능
- 네이티브 모듈 통합 (필요시)
- 성능 최적화 (Flipper 활용)
```

#### Flutter 개발 경로
```
프로젝트 초기화:
flutter create mobile_app
cd mobile_app

폴더 구조 생성:
lib/
├── main.dart
├── app/               # 앱 설정 및 라우팅
├── core/              # 핵심 유틸리티
│   ├── constants/     # 상수 정의
│   ├── errors/        # 에러 처리
│   └── network/       # 네트워크 레이어
├── data/              # 데이터 레이어
│   ├── datasources/   # 데이터 소스
│   ├── models/        # 데이터 모델
│   └── repositories/  # 저장소 패턴
├── domain/            # 도메인 레이어
│   ├── entities/      # 엔티티
│   ├── repositories/  # 저장소 인터페이스
│   └── usecases/      # 비즈니스 로직
├── presentation/      # 프레젠테이션 레이어
│   ├── bloc/          # BLoC 상태 관리
│   ├── pages/         # 페이지 위젯
│   └── widgets/       # 재사용 위젯
└── shared/            # 공유 리소스

핵심 기능 구현:
1. Clean Architecture 패턴 적용
2. BLoC 상태 관리 패턴
3. Go Router를 이용한 네비게이션
4. Dio를 이용한 HTTP 통신
5. Hive/SharedPreferences 로컬 저장소
6. Firebase 통합 (인증, 푸시알림, 분석)
7. 이미지 처리 (image_picker, cached_network_image)
8. 카메라 통합 (camera package)
```

#### 공통 개발 요소
```
UI/UX 구현:
1. 디자인 시스템 구현
   - 컬러 테마 (Light/Dark 모드)
   - 컴포넌트 라이브러리
   - 반응형 레이아웃
   - 애니메이션 및 트랜지션

2. 핵심 화면 구현
   - 온보딩/튜토리얼 화면
   - 로그인/회원가입 화면
   - 메인 대시보드
   - 프로필 관리 화면
   - 설정 화면

3. 사용자 경험 최적화
   - 로딩 상태 처리
   - 에러 처리 및 사용자 피드백
   - 오프라인 지원
   - 접근성 기능 (Accessibility)

API 통합:
1. RESTful API 클라이언트
2. 실시간 통신 (WebSocket)
3. 파일 업로드/다운로드
4. 이미지 최적화 및 CDN 연동
5. 캐싱 전략 구현

네이티브 기능 통합:
1. 디바이스 센서 (가속도계, 자이로스코프)
2. 위치 서비스 (GPS)
3. 카메라 및 갤러리 접근
4. 연락처 및 캘린더 연동
5. 생체 인증 (지문, Face ID)
6. 푸시 알림
7. 앱 내 결제 (IAP)
```

---

### 🧪 3단계: 모바일 특화 테스팅 (1시간)

다음 모바일 전용 테스트를 수행해줘:

#### 단위 및 통합 테스트
```
React Native 테스트:
- Jest + React Native Testing Library
- API 통신 테스트 (MSW 활용)
- Redux 상태 관리 테스트
- 커스텀 훅 테스트

테스트 예시:
describe('LoginScreen', () => {
  test('should handle login successfully', async () => {
    const mockLogin = jest.fn().mockResolvedValue({
      token: 'mock-token',
      user: { id: 1, name: 'Test User' }
    });

    render(<LoginScreen onLogin={mockLogin} />);
    
    fireEvent.changeText(screen.getByPlaceholderText('Email'), 'test@example.com');
    fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
    fireEvent.press(screen.getByText('Login'));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });
});

Flutter 테스트:
- Flutter Test Framework
- Widget 테스트
- BLoC 테스트
- Golden 테스트 (스크린샷 비교)

테스트 예시:
testWidgets('Login form should validate input', (WidgetTester tester) async {
  await tester.pumpWidget(MaterialApp(home: LoginPage()));
  
  // 빈 폼 제출 시도
  await tester.tap(find.byType(ElevatedButton));
  await tester.pump();
  
  // 에러 메시지 확인
  expect(find.text('Email is required'), findsOneWidget);
  expect(find.text('Password is required'), findsOneWidget);
});
```

#### E2E 테스트 (End-to-End)
```
Detox (React Native) / Integration Test (Flutter):

주요 사용자 시나리오 테스트:
1. 앱 최초 실행 및 온보딩
2. 회원가입 → 이메일 인증 → 로그인
3. 메인 기능 사용 (데이터 생성/수정/삭제)
4. 푸시 알림 수신 및 처리
5. 앱 백그라운드/포그라운드 전환
6. 네트워크 연결 끊김 시 동작

Detox 테스트 예시:
describe('App E2E Tests', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should complete user registration flow', async () => {
    // 온보딩 건너뛰기
    await element(by.id('skip-onboarding')).tap();
    
    // 회원가입 화면으로 이동
    await element(by.id('signup-button')).tap();
    
    // 폼 작성
    await element(by.id('email-input')).typeText('newuser@example.com');
    await element(by.id('password-input')).typeText('SecurePassword123!');
    await element(by.id('confirm-password-input')).typeText('SecurePassword123!');
    
    // 회원가입 제출
    await element(by.id('submit-signup')).tap();
    
    // 성공 메시지 확인
    await expect(element(by.text('Registration successful!'))).toBeVisible();
  });
});
```

#### 디바이스별 테스트
```
물리 디바이스 테스트:
- iOS: iPhone (다양한 모델 및 iOS 버전)
- Android: Galaxy, Pixel (다양한 제조사 및 Android 버전)

화면 크기별 테스트:
- Phone: 소형(5"), 중형(6"), 대형(6.7"+)
- Tablet: iPad, Android Tablet
- 가로/세로 모드 전환 테스트

성능 테스트:
- 앱 시작 시간 측정 (< 3초 목표)
- 메모리 사용량 모니터링
- 배터리 소모량 측정
- CPU 사용률 확인
- 네트워크 사용량 최적화

접근성 테스트:
- Screen Reader 지원 (TalkBack, VoiceOver)
- 고대비 모드 지원
- 큰 글자 크기 지원
- 색상 구분 없는 정보 전달
```

---

### 📦 4단계: 빌드 및 배포 준비 (45분)

다음 배포 준비 작업을 수행해줘:

#### iOS 배포 준비
```
Apple Developer 계정 설정:
1. 개발자 계정 등록 확인
2. App ID 생성 및 설정
3. 프로비저닝 프로파일 생성
4. 푸시 알림 인증서 설정
5. App Store Connect 앱 등록

Xcode 프로젝트 설정:
- Bundle Identifier 설정
- App Icon 및 Launch Screen 구성
- Info.plist 권한 설정
- 코드 서명 설정 (Automatic Signing)
- 아카이브 빌드 테스트

fastlane 자동화 (선택사항):
# Fastfile
platform :ios do
  desc "Build and upload to TestFlight"
  lane :beta do
    build_app(scheme: "MobileApp")
    upload_to_testflight
  end
  
  desc "Upload to App Store"
  lane :release do
    build_app(scheme: "MobileApp")
    upload_to_app_store
  end
end
```

#### Android 배포 준비
```
Google Play Console 설정:
1. 개발자 계정 등록 확인
2. 앱 등록 및 스토어 정보 입력
3. 서명 키 생성 및 업로드
4. 앱 번들 최적화 설정
5. 내부 테스트 트랙 설정

Gradle 빌드 설정:
android {
  compileSdkVersion 33
  
  defaultConfig {
    applicationId "com.yourcompany.mobileapp"
    minSdkVersion 23
    targetSdkVersion 33
    versionCode 1
    versionName "1.0.0"
  }
  
  signingConfigs {
    release {
      keyAlias keystoreProperties['keyAlias']
      keyPassword keystoreProperties['keyPassword']
      storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
      storePassword keystoreProperties['storePassword']
    }
  }
  
  buildTypes {
    release {
      signingConfig signingConfigs.release
      minifyEnabled true
      proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
    }
  }
}

앱 번들 생성:
./gradlew bundleRelease
```

#### CI/CD 파이프라인 구성
```
GitHub Actions 워크플로우:
name: Mobile App CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Run E2E tests
        run: npm run test:e2e

  build-ios:
    needs: test
    runs-on: macos-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install CocoaPods
        run: cd ios && pod install
      
      - name: Build iOS
        run: |
          xcodebuild -workspace ios/MobileApp.xcworkspace \
                     -scheme MobileApp \
                     -configuration Release \
                     -archivePath MobileApp.xcarchive \
                     archive

  build-android:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '11'
      
      - name: Setup Android SDK
        uses: android-actions/setup-android@v2
      
      - name: Build Android
        run: |
          cd android
          ./gradlew assembleRelease
```

---

### 📊 5단계: 모바일 분석 및 모니터링 (30분)

다음 모바일 특화 모니터링을 설정해줘:

#### 앱 성능 모니터링
```
Firebase Performance Monitoring:
// React Native
import perf from '@react-native-firebase/perf';

const trace = perf().newTrace('user_registration');
await trace.start();

try {
  await registerUser(userData);
  trace.putAttribute('success', 'true');
} catch (error) {
  trace.putAttribute('success', 'false');
  trace.putAttribute('error', error.message);
} finally {
  await trace.stop();
}

// Flutter
import 'package:firebase_performance/firebase_performance.dart';

final trace = FirebasePerformance.instance.newTrace('user_registration');
await trace.start();

try {
  await registerUser(userData);
  trace.setMetric('success', 1);
} catch (error) {
  trace.setMetric('success', 0);
} finally {
  await trace.stop();
}

커스텀 메트릭:
- 앱 시작 시간
- 화면 로딩 시간
- API 응답 시간
- 이미지 로딩 시간
- 배터리 사용량
```

#### 크래시 리포팅
```
Firebase Crashlytics:
// React Native
import crashlytics from '@react-native-firebase/crashlytics';

// 사용자 정보 설정
crashlytics().setUserId(user.id);
crashlytics().setAttributes({
  role: user.role,
  plan: user.plan
});

// 커스텀 로그
crashlytics().log('User performed search');

// 비치명적 오류 기록
crashlytics().recordError(new Error('Non-fatal error occurred'));

// Flutter
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

// 앱 전체 오류 처리
FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;

PlatformDispatcher.instance.onError = (error, stack) {
  FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
  return true;
};
```

#### 사용자 행동 분석
```
Firebase Analytics:
// 주요 이벤트 추적
analytics().logEvent('screen_view', {
  screen_name: 'HomeScreen',
  screen_class: 'HomeScreen'
});

analytics().logEvent('user_engagement', {
  engagement_time_msec: 30000
});

analytics().logEvent('select_content', {
  content_type: 'product',
  content_id: 'prod_123',
  item_id: 'prod_123'
});

// 사용자 속성 설정
analytics().setUserProperty('user_type', 'premium');

커스텀 대시보드:
- DAU/MAU (일간/월간 활성 사용자)
- 세션 지속 시간
- 화면별 체류 시간
- 기능 사용률
- 이탈률 분석
- 코호트 분석
```

---

### 🚀 6단계: 앱 스토어 출시 준비 (30분)

다음 스토어 출시 준비를 완료해줘:

#### 앱 스토어 메타데이터
```
공통 준비사항:
1. 앱 이름 및 키워드 최적화 (ASO)
2. 앱 설명 작성 (다국어 지원)
3. 스크린샷 및 프리뷰 비디오 제작
4. 앱 아이콘 디자인 (다양한 크기)
5. 개인정보 처리방침 및 이용약관

iOS App Store:
- App Store Connect 메타데이터 입력
- 앱 리뷰 가이드라인 준수 확인
- TestFlight 내부 테스트 배포
- App Store Review 제출

Google Play Store:
- Play Console 스토어 등록정보 입력
- Play Console 정책 준수 확인
- 내부 테스트 트랙 배포
- 프로덕션 출시 신청

앱 스토어 최적화 (ASO):
{
  "app_name": "앱 이름 (키워드 포함)",
  "subtitle": "앱 부제목 (iOS)",
  "short_description": "짧은 설명 (Android)",
  "description": "상세 설명 (키워드 자연스럽게 포함)",
  "keywords": "관련 키워드 (iOS)",
  "category": "적절한 카테고리 선택",
  "age_rating": "연령 등급 설정"
}
```

#### 출시 후 모니터링 계획
```
KPI 설정:
1. 다운로드 수 및 설치율
2. 앱 스토어 평점 및 리뷰
3. 사용자 유지율 (1일, 7일, 30일)
4. 인앱 전환율 (해당시)
5. 크래시 없는 세션 비율 (>99.9%)

A/B 테스트 계획:
- 온보딩 플로우 최적화
- 주요 CTA 버튼 위치 테스트
- 푸시 알림 메시지 최적화
- 가격 정책 테스트 (유료 앱인 경우)

업데이트 계획:
1. 주간 단위 버그 수정 업데이트
2. 월간 단위 기능 추가 업데이트
3. 분기별 주요 기능 업데이트
4. 연간 디자인 리뉴얼 계획
```

## ✅ 완료 조건

### 필수 달성 목표
- [ ] 크로스 플랫폼 모바일 앱 구현 완료
- [ ] iOS/Android 네이티브 기능 통합
- [ ] 반응형 UI/UX 구현
- [ ] 오프라인 지원 기능
- [ ] 푸시 알림 시스템 구현
- [ ] 앱 스토어 배포 준비 완료
- [ ] E2E 테스트 통과
- [ ] 성능 최적화 완료 (앱 시작 < 3초)

### 품질 기준
- [ ] 테스트 커버리지 85% 이상
- [ ] 크래시 없는 세션 99.9% 이상
- [ ] 앱 스토어 정책 준수
- [ ] 접근성 기준 충족 (WCAG 2.1 AA)
- [ ] 다국어 지원 (최소 2개 언어)
- [ ] 다크 모드 지원
- [ ] 다양한 화면 크기 지원

### 성능 목표
- [ ] 앱 시작 시간 < 3초
- [ ] 화면 전환 시간 < 500ms
- [ ] 메모리 사용량 < 150MB
- [ ] 배터리 효율성 최적화
- [ ] 네트워크 사용량 최적화

### 보안 요구사항
- [ ] 데이터 암호화 (전송/저장)
- [ ] 생체 인증 지원
- [ ] API 보안 구현
- [ ] 앱 무결성 검증
- [ ] 개인정보 보호 준수

모든 조건이 충족되면 모바일 앱이 앱 스토어 출시 준비 완료됩니다.

**예상 총 소요시간: 3-5시간**
**결과물**: iOS/Android 크로스 플랫폼 모바일 앱 + 스토어 배포 패키지
