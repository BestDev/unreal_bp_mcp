# Security Features - UnrealBlueprintMCP

이 문서는 UnrealBlueprintMCP 프로젝트에 구현된 보안 기능과 수정된 취약점들을 설명합니다.

## 보안 취약점 수정 완료

### 1. OpenAI API 키 하드코딩 제거 ✅

**문제**: API 키가 소스코드에 직접 하드코딩되어 있었음
**수정사항**:
- 환경변수 사용으로 변경 (`OPENAI_API_KEY`)
- `.env` 파일 지원 추가 (python-dotenv)
- API 키 유효성 검증 구현
- 키 누락 시 명확한 에러 메시지 제공

**영향받은 파일**:
- `/examples/advanced/config.py`
- `/examples/advanced/langchain_integration/nl_blueprint_generator.py`
- `/requirements.txt` (python-dotenv 추가)
- `/.env.example` (새로 생성)

**구현된 보안 검증**:
```python
def validate_openai_api_key() -> bool:
    """Validate OpenAI API key format and presence"""
    if not OPENAI_API_KEY:
        return False
    if not OPENAI_API_KEY.startswith('sk-') or len(OPENAI_API_KEY) < 20:
        return False
    return True
```

### 2. 입력 검증 레이어 구현 ✅

**문제**: 사용자 입력값이 검증 없이 WebSocket으로 전송됨
**수정사항**:
- 포괄적인 보안 유틸리티 모듈 생성 (`security_utils.py`)
- Pydantic 모델에 보안 검증 통합
- JSON-RPC 매개변수 sanitization
- WebSocket 메시지 크기 제한

**새로 생성된 파일**:
- `/security_utils.py` - 보안 검증 유틸리티
- `/tests/test_security.py` - 보안 테스트 스위트

**구현된 보안 기능**:

#### Blueprint 이름 검증
```python
BLUEPRINT_NAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
```
- 영문자로 시작, 영숫자+언더스코어만 허용
- 최대 64자 길이 제한
- 예약어 방지

#### Asset 경로 검증
```python
ASSET_PATH_PATTERN = re.compile(r'^/Game/[A-Za-z0-9_/]+/$')
```
- `/Game/`으로 시작 강제
- 디렉토리 트래버설 방지 (`..` 탐지)
- 위험한 문자 차단 (`<`, `>`, `|`, `?`, `*` 등)

#### Property 값 sanitization
- HTML 이스케이핑으로 XSS 방지
- 위험한 패턴 탐지 (`<script>`, `javascript:`, `eval()` 등)
- 최대 길이 제한 (기본 1024자)

#### Parent 클래스 화이트리스트
```python
VALID_PARENT_CLASSES = {
    "Actor", "Pawn", "Character", "ActorComponent", "SceneComponent",
    "UserWidget", "Object", "StaticMeshActor", "GameModeBase",
    "PlayerController", "GameState", "PlayerState"
}
```

### 3. 추가 보안 강화 ✅

**WebSocket 메시지 크기 제한**:
- 기본 1MB 제한으로 DoS 공격 방지
- 사용자 정의 크기 제한 지원

**JSON-RPC 매개변수 Sanitization**:
- 모든 문자열 값에 HTML 이스케이핑 적용
- 키 이름 검증 (영숫자+언더스코어만 허용)
- 안전한 데이터 타입만 전송

**URL 검증**:
- WebSocket 프로토콜만 허용 (`ws://`, `wss://`)
- 유효한 hostname 검증

## 보안 테스트

### 테스트 실행
```bash
cd mcp_server_env
source bin/activate
python -m pytest tests/test_security.py -v
```

### 테스트 커버리지
- ✅ 22개 보안 테스트 통과
- Blueprint 이름 검증 (4개 테스트)
- Property 검증 (4개 테스트)
- Asset 경로 검증 (3개 테스트)
- Parent 클래스 검증 (2개 테스트)
- XSS 방지 (2개 테스트)
- Path traversal 방지 (1개 테스트)
- JSON-RPC sanitization (1개 테스트)
- WebSocket 보안 (2개 테스트)
- Pydantic 통합 (3개 테스트)

## 환경 설정

### .env 파일 설정
```bash
# .env.example을 .env로 복사
cp .env.example .env

# API 키 설정
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 의존성 설치
```bash
pip install python-dotenv
```

## 보안 가이드라인

### 개발자를 위한 권장사항

1. **API 키 관리**:
   - 절대 하드코딩하지 말 것
   - `.env` 파일을 `.gitignore`에 포함
   - 환경변수로만 관리

2. **입력 검증**:
   - 모든 사용자 입력은 `security_utils.py`의 함수로 검증
   - Pydantic 모델의 field_validator 사용
   - 화이트리스트 방식으로 허용 값 제한

3. **에러 처리**:
   - 보안 관련 에러는 명확한 메시지 제공
   - 민감한 정보 노출 방지
   - 적절한 로깅

4. **테스트**:
   - 새로운 입력 필드 추가 시 보안 테스트 작성
   - 공격 벡터를 고려한 테스트 케이스 포함

## 보안 체크리스트

### 배포 전 확인사항
- [ ] API 키가 하드코딩되지 않았는지 확인
- [ ] 모든 사용자 입력에 검증이 적용되는지 확인
- [ ] 보안 테스트가 통과하는지 확인
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 에러 메시지에 민감한 정보가 포함되지 않는지 확인

### 정기 보안 점검
- [ ] 의존성 취약점 스캔 (`pip audit`)
- [ ] 새로운 공격 벡터 확인
- [ ] 로그 모니터링
- [ ] 접근 패턴 분석

## 알려진 제한사항

1. **WebSocket Deprecation**:
   - 현재 websockets 라이브러리가 deprecated API 사용
   - 향후 업데이트에서 최신 API로 마이그레이션 필요

2. **Rate Limiting**:
   - 현재 구현되지 않음
   - 향후 버전에서 API 호출 빈도 제한 추가 예정

## 버전 히스토리

### v2.1.0 (2025-09-17)
- ✅ OpenAI API 키 하드코딩 제거
- ✅ 포괄적인 입력 검증 레이어 구현
- ✅ XSS 및 Path Traversal 방지
- ✅ 22개 보안 테스트 추가
- ✅ .env 파일 지원 추가

## 문의 및 신고

보안 취약점 발견 시:
1. GitHub Issues에 "Security" 라벨로 신고
2. 민감한 취약점은 비공개로 연락
3. 보안 패치는 최우선으로 처리

---

**보안은 지속적인 과정입니다. 정기적인 점검과 업데이트를 통해 안전한 개발 환경을 유지하세요.**