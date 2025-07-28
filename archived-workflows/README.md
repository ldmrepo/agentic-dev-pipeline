# 아카이브된 워크플로우

이 디렉토리에는 이전 버전의 워크플로우 파일들이 보관되어 있습니다.

## 중요 안내

**⚠️ 이 파일들은 더 이상 사용되지 않습니다!**

v1.1부터 모든 워크플로우는 slash commands로 변경되었습니다.

### 새로운 사용 방법

이전 방식:
```bash
claude -f workflows/basic-development.md
```

새로운 방식:
```bash
claude /basic-development "요구사항 설명"
```

### 사용 가능한 명령어

- `/basic-development` - 기본 웹 애플리케이션 개발
- `/data-pipeline` - 데이터 파이프라인 구축
- `/ml-ai-model` - ML/AI 모델 개발
- `/mobile-app` - 모바일 앱 개발
- `/microservices-development` - 마이크로서비스 구축
- `/hotfix` - 긴급 버그 수정

### 커스텀 명령어 생성

새로운 워크플로우를 추가하려면 `.claude/commands/` 디렉토리에 마크다운 파일을 생성하세요.

예시:
```bash
# 새로운 명령어 생성
touch .claude/commands/my-workflow.md

# 사용
claude /my-workflow "설명"
```