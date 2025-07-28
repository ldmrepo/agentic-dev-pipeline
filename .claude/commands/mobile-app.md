# 모바일 앱 개발 워크플로우

## 📱 크로스플랫폼 모바일 앱 자동 개발
**목표 완료 시간: 3-4시간**

다음의 모바일 앱을 개발해주세요: $ARGUMENTS

## 워크플로우 단계

### 1단계: 앱 요구사항 분석 및 설계 (30분)

다음을 수행해줘:

#### 요구사항 분석
- 타겟 플랫폼 결정 (iOS/Android/Both)
- 주요 기능 리스트 작성
- 사용자 스토리 정의
- 비기능적 요구사항 (성능, 보안, 오프라인 지원)

#### UI/UX 설계
- 와이어프레임 작성
- 화면 플로우 다이어그램
- 디자인 시스템 정의
- 프로토타입 생성

#### 기술 스택 선정
- 프레임워크: React Native / Flutter / Ionic
- 상태 관리: Redux / MobX / Provider
- 백엔드: Firebase / AWS Amplify / Custom API
- 데이터베이스: SQLite / Realm / AsyncStorage

docs/mobile-app/ 디렉토리에 생성:
- requirements.md
- ui-design-system.md
- technical-architecture.md

### 2단계: 프로젝트 초기화 및 환경 설정 (30분)

다음을 수행해줘:

#### React Native 프로젝트 설정
```bash
# 프로젝트 생성
npx react-native init MobileApp --template react-native-template-typescript

# 필수 패키지 설치
npm install @react-navigation/native @react-navigation/stack
npm install react-native-vector-icons
npm install redux react-redux @reduxjs/toolkit
npm install react-native-async-storage/async-storage
```

#### 프로젝트 구조
```
mobile-app/
├── src/
│   ├── components/
│   ├── screens/
│   ├── navigation/
│   ├── store/
│   ├── services/
│   ├── utils/
│   └── types/
├── assets/
│   ├── images/
│   ├── fonts/
│   └── icons/
├── ios/
├── android/
└── __tests__/
```

#### 개발 환경 설정
```javascript
// .eslintrc.js
module.exports = {
  root: true,
  extends: [
    '@react-native-community',
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  rules: {
    'react-native/no-inline-styles': 'off',
  },
};

// prettier.config.js
module.exports = {
  bracketSpacing: true,
  singleQuote: true,
  trailingComma: 'all',
  arrowParens: 'avoid',
};
```

### 3단계: 네비게이션 및 라우팅 구현 (30분)

다음을 수행해줘:

#### 네비게이션 구조
```typescript
// src/navigation/AppNavigator.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Auth" component={AuthNavigator} />
        <Stack.Screen name="Main" component={MainTabs} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

#### 딥링킹 설정
```typescript
// src/navigation/linking.ts
const linking = {
  prefixes: ['myapp://', 'https://myapp.com'],
  config: {
    screens: {
      Home: 'home',
      Profile: 'profile/:id',
      Settings: 'settings',
    },
  },
};
```

### 4단계: UI 컴포넌트 개발 (45분)

다음을 수행해줘:

#### 재사용 가능한 컴포넌트
```typescript
// src/components/Button.tsx
import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
}) => {
  return (
    <TouchableOpacity
      style={[
        styles.button,
        styles[variant],
        disabled && styles.disabled,
      ]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={styles.text}>{title}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  primary: {
    backgroundColor: '#007AFF',
  },
  secondary: {
    backgroundColor: '#E0E0E0',
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});
```

#### 폼 컴포넌트
```typescript
// src/components/Input.tsx
import React from 'react';
import { TextInput, View, Text, StyleSheet } from 'react-native';

interface InputProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  value,
  onChangeText,
  placeholder,
  secureTextEntry,
  error,
}) => {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, error && styles.inputError]}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        secureTextEntry={secureTextEntry}
      />
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
};
```

#### 리스트 컴포넌트
```typescript
// src/components/List.tsx
import React from 'react';
import { FlatList, RefreshControl } from 'react-native';

interface ListProps<T> {
  data: T[];
  renderItem: (item: T) => React.ReactElement;
  onRefresh?: () => void;
  onEndReached?: () => void;
  refreshing?: boolean;
}

export function List<T>({
  data,
  renderItem,
  onRefresh,
  onEndReached,
  refreshing = false,
}: ListProps<T>) {
  return (
    <FlatList
      data={data}
      renderItem={({ item }) => renderItem(item)}
      keyExtractor={(item, index) => index.toString()}
      refreshControl={
        onRefresh ? (
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        ) : undefined
      }
      onEndReached={onEndReached}
      onEndReachedThreshold={0.5}
    />
  );
}
```

### 5단계: 상태 관리 구현 (30분)

다음을 수행해줘:

#### Redux Toolkit 설정
```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import userReducer from './userSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    user: userReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

#### Auth Slice
```typescript
// src/store/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }) => {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    const data = await response.json();
    await AsyncStorage.setItem('token', data.token);
    return data;
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    isAuthenticated: false,
    token: null,
    loading: false,
    error: null,
  } as AuthState,
  reducers: {
    logout: (state) => {
      state.isAuthenticated = false;
      state.token = null;
      AsyncStorage.removeItem('token');
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Login failed';
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
```

### 6단계: API 통신 및 데이터 서비스 (30분)

다음을 수행해줘:

#### API 클라이언트
```typescript
// src/services/api.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await AsyncStorage.getItem('token');
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  get<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data: any) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put<T>(endpoint: string, data: any) {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient('https://api.example.com');
```

#### 오프라인 지원
```typescript
// src/services/offline.ts
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';

class OfflineManager {
  private queue: any[] = [];

  constructor() {
    this.loadQueue();
    this.setupNetworkListener();
  }

  async loadQueue() {
    const saved = await AsyncStorage.getItem('offline_queue');
    if (saved) {
      this.queue = JSON.parse(saved);
    }
  }

  async saveQueue() {
    await AsyncStorage.setItem('offline_queue', JSON.stringify(this.queue));
  }

  setupNetworkListener() {
    NetInfo.addEventListener(state => {
      if (state.isConnected) {
        this.processQueue();
      }
    });
  }

  async addToQueue(request: any) {
    this.queue.push(request);
    await this.saveQueue();
  }

  async processQueue() {
    while (this.queue.length > 0) {
      const request = this.queue.shift();
      try {
        await this.executeRequest(request);
      } catch (error) {
        this.queue.unshift(request);
        break;
      }
    }
    await this.saveQueue();
  }

  private async executeRequest(request: any) {
    // API 요청 실행
  }
}

export const offlineManager = new OfflineManager();
```

### 7단계: 네이티브 기능 통합 (30분)

다음을 수행해줘:

#### 카메라 및 갤러리
```typescript
// src/services/media.ts
import ImagePicker from 'react-native-image-crop-picker';

export const MediaService = {
  async takePhoto() {
    try {
      const image = await ImagePicker.openCamera({
        width: 300,
        height: 400,
        cropping: true,
      });
      return image;
    } catch (error) {
      console.error('Camera error:', error);
      throw error;
    }
  },

  async selectFromGallery() {
    try {
      const image = await ImagePicker.openPicker({
        width: 300,
        height: 400,
        cropping: true,
        multiple: false,
      });
      return image;
    } catch (error) {
      console.error('Gallery error:', error);
      throw error;
    }
  },
};
```

#### 위치 서비스
```typescript
// src/services/location.ts
import Geolocation from 'react-native-geolocation-service';
import { PermissionsAndroid, Platform } from 'react-native';

export const LocationService = {
  async requestPermission() {
    if (Platform.OS === 'ios') {
      const auth = await Geolocation.requestAuthorization('whenInUse');
      return auth === 'granted';
    }

    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }

    return false;
  },

  async getCurrentLocation() {
    const hasPermission = await this.requestPermission();
    
    if (!hasPermission) {
      throw new Error('Location permission denied');
    }

    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        position => resolve(position),
        error => reject(error),
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
      );
    });
  },
};
```

#### 푸시 알림
```typescript
// src/services/notifications.ts
import messaging from '@react-native-firebase/messaging';
import PushNotification from 'react-native-push-notification';

export const NotificationService = {
  async initialize() {
    // FCM 토큰 가져오기
    const token = await messaging().getToken();
    console.log('FCM Token:', token);

    // 알림 채널 생성 (Android)
    PushNotification.createChannel({
      channelId: 'default',
      channelName: 'Default Channel',
      importance: 4,
    });

    // 메시지 리스너
    messaging().onMessage(async remoteMessage => {
      PushNotification.localNotification({
        title: remoteMessage.notification?.title,
        message: remoteMessage.notification?.body || '',
      });
    });
  },

  async requestPermission() {
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    return enabled;
  },
};
```

### 8단계: 테스트 구현 (30분)

다음을 수행해줘:

#### 단위 테스트
```typescript
// __tests__/components/Button.test.tsx
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { Button } from '../src/components/Button';

describe('Button Component', () => {
  it('renders correctly', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={() => {}} />
    );
    expect(getByText('Test Button')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <Button title="Test Button" onPress={onPress} />
    );
    
    fireEvent.press(getByText('Test Button'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <Button title="Test Button" onPress={onPress} disabled />
    );
    
    fireEvent.press(getByText('Test Button'));
    expect(onPress).not.toHaveBeenCalled();
  });
});
```

#### 통합 테스트
```typescript
// __tests__/screens/Login.test.tsx
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Provider } from 'react-redux';
import { store } from '../src/store';
import LoginScreen from '../src/screens/LoginScreen';

describe('Login Screen', () => {
  it('shows error on invalid credentials', async () => {
    const { getByPlaceholderText, getByText } = render(
      <Provider store={store}>
        <LoginScreen />
      </Provider>
    );

    fireEvent.changeText(getByPlaceholderText('Email'), 'test@test.com');
    fireEvent.changeText(getByPlaceholderText('Password'), 'wrong');
    fireEvent.press(getByText('Login'));

    await waitFor(() => {
      expect(getByText('Invalid credentials')).toBeTruthy();
    });
  });
});
```

#### E2E 테스트 (Detox)
```javascript
// e2e/login.e2e.js
describe('Login Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should login successfully', async () => {
    await element(by.id('email-input')).typeText('user@example.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();
    
    await expect(element(by.id('home-screen'))).toBeVisible();
  });
});
```

### 9단계: 성능 최적화 (30분)

다음을 수행해줘:

#### 이미지 최적화
```typescript
// src/components/OptimizedImage.tsx
import FastImage from 'react-native-fast-image';
import React from 'react';

interface OptimizedImageProps {
  source: { uri: string };
  style?: any;
  resizeMode?: 'contain' | 'cover' | 'stretch';
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  source,
  style,
  resizeMode = 'cover',
}) => {
  return (
    <FastImage
      style={style}
      source={{
        uri: source.uri,
        priority: FastImage.priority.normal,
        cache: FastImage.cacheControl.immutable,
      }}
      resizeMode={FastImage.resizeMode[resizeMode]}
    />
  );
};
```

#### 리스트 최적화
```typescript
// src/components/OptimizedList.tsx
import React, { useCallback } from 'react';
import { FlatList, View } from 'react-native';

export const OptimizedList = ({ data, renderItem }) => {
  const keyExtractor = useCallback((item) => item.id.toString(), []);
  
  const getItemLayout = useCallback(
    (data, index) => ({
      length: ITEM_HEIGHT,
      offset: ITEM_HEIGHT * index,
      index,
    }),
    []
  );

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      getItemLayout={getItemLayout}
      removeClippedSubviews={true}
      maxToRenderPerBatch={10}
      updateCellsBatchingPeriod={50}
      initialNumToRender={10}
      windowSize={10}
    />
  );
};
```

#### 메모리 최적화
```typescript
// src/hooks/useMemoryOptimization.ts
import { useEffect } from 'react';
import { AppState } from 'react-native';

export const useMemoryOptimization = () => {
  useEffect(() => {
    const handleAppStateChange = (nextAppState: string) => {
      if (nextAppState === 'background') {
        // 캐시 정리
        clearImageCache();
        // 불필요한 데이터 정리
        cleanupTempData();
      }
    };

    const subscription = AppState.addEventListener(
      'change',
      handleAppStateChange
    );

    return () => {
      subscription.remove();
    };
  }, []);
};
```

### 10단계: 빌드 및 배포 (30분)

다음을 수행해줘:

#### iOS 빌드 설정
```ruby
# ios/Podfile
platform :ios, '11.0'

target 'MobileApp' do
  config = use_native_modules!
  
  use_react_native!(
    :path => config[:reactNativePath],
    :hermes_enabled => true
  )
  
  # 추가 pods
  pod 'Firebase/Analytics'
  pod 'Firebase/Crashlytics'
end
```

#### Android 빌드 설정
```gradle
// android/app/build.gradle
android {
  defaultConfig {
    applicationId "com.mycompany.mobileapp"
    minSdkVersion 21
    targetSdkVersion 31
    versionCode 1
    versionName "1.0"
  }
  
  signingConfigs {
    release {
      storeFile file(MYAPP_RELEASE_STORE_FILE)
      storePassword MYAPP_RELEASE_STORE_PASSWORD
      keyAlias MYAPP_RELEASE_KEY_ALIAS
      keyPassword MYAPP_RELEASE_KEY_PASSWORD
    }
  }
  
  buildTypes {
    release {
      signingConfig signingConfigs.release
      minifyEnabled true
      proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
    }
  }
}
```

#### CI/CD 파이프라인 (GitHub Actions)
```yaml
# .github/workflows/mobile-deploy.yml
name: Mobile App Deploy

on:
  push:
    branches: [main]

jobs:
  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '16'
      
      - name: Install dependencies
        run: |
          npm install
          cd ios && pod install
      
      - name: Build iOS
        run: |
          cd ios
          xcodebuild -workspace MobileApp.xcworkspace \
            -scheme MobileApp \
            -configuration Release \
            -archivePath MobileApp.xcarchive \
            archive
      
      - name: Upload to TestFlight
        run: |
          xcrun altool --upload-app \
            -f MobileApp.ipa \
            -u ${{ secrets.APPLE_ID }} \
            -p ${{ secrets.APPLE_APP_PASSWORD }}

  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '16'
      
      - name: Install dependencies
        run: npm install
      
      - name: Build Android
        run: |
          cd android
          ./gradlew assembleRelease
      
      - name: Upload to Play Store
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_JSON }}
          packageName: com.mycompany.mobileapp
          releaseFiles: android/app/build/outputs/apk/release/app-release.apk
          track: internal
```

최종 산출물:
- 완전히 작동하는 크로스플랫폼 모바일 앱
- iOS/Android 빌드
- 자동화된 테스트
- CI/CD 파이프라인
- 앱스토어 배포 준비 완료

각 단계별로 진행 상황을 보고하고, 모든 코드를 생성해줘.