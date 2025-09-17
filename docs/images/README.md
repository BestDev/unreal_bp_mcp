# 이미지 및 다이어그램

이 폴더에는 프로젝트 문서에 사용되는 스크린샷과 다이어그램이 포함됩니다.

## 필요한 이미지

### 스크린샷
- `mcp-status-dashboard.png` - Unreal Editor의 MCP Status 창
- `mcp-inspector.png` - 웹 브라우저의 MCP Inspector 인터페이스
- `content-browser-blueprints.png` - 생성된 블루프린트들이 표시된 Content Browser
- `blueprint-editor-properties.png` - Blueprint Editor에서 설정된 속성들

### 애니메이션
- `blueprint-creation-demo.gif` - 블루프린트 생성 과정 데모
- `property-setting-demo.gif` - 속성 설정 과정 데모

### 다이어그램
- `architecture-diagram.png` - 전체 시스템 아키텍처
- `communication-flow.png` - AI 클라이언트 → MCP 서버 → Unreal 플러그인 통신 흐름
- `mcp-protocol-diagram.png` - MCP 프로토콜 메시지 흐름

## 이미지 캡처 가이드

### MCP Status Dashboard 스크린샷
1. Unreal Editor 실행
2. Window → Developer Tools → MCP Status
3. 연결 상태, 로그, 버튼들이 모두 보이도록 캡처

### MCP Inspector 스크린샷
1. MCP 서버 실행 후 웹 인터페이스 접속
2. 도구 목록이 표시된 화면 캡처
3. 도구 실행 결과 화면도 별도 캡처

### Blueprint Creation Demo
1. MCP Inspector에서 create_blueprint 도구 실행
2. Unreal Editor Content Browser에서 생성된 블루프린트 확인
3. 전체 과정을 화면 녹화로 GIF 생성

## 파일 명명 규칙

- 스크린샷: `feature-name-screenshot.png`
- 다이어그램: `feature-name-diagram.png`
- 애니메이션: `feature-name-demo.gif`
- 해상도: 최소 1200px 너비 권장