# UnrealBlueprintMCP 설치 가이드 (Installation Guide)

> **언어**: 한국어 / English
> **대상**: Unreal Engine 개발자, AI 개발자, 기술 연구자
> **난이도**: 중급 (Intermediate)

## 📋 목차 (Table of Contents)

1. [시스템 요구사항](#시스템-요구사항)
2. [전체 설치 프로세스](#전체-설치-프로세스)
3. [Unreal Engine 플러그인 설치](#unreal-engine-플러그인-설치)
4. [Python MCP 서버 설치](#python-mcp-서버-설치)
5. [AI 클라이언트 연동](#ai-클라이언트-연동)
6. [테스트 및 검증](#테스트-및-검증)
7. [문제 해결](#문제-해결)

---

## 🔧 시스템 요구사항 (System Requirements)

### 필수 소프트웨어 (Required Software)
- **Unreal Engine 5.3+** - Blueprint 에디터 및 WebSocket 모듈 지원
- **Visual Studio 2022** - C++ 컴파일러 (Windows)
- **Python 3.8+** - MCP 서버 실행 환경 (비동기 처리 지원)
- **Node.js 18+** - MCP Inspector 실행 (선택사항)

### 지원 플랫폼 (Supported Platforms)
- ✅ **Windows 10/11** (주 개발 플랫폼)
- ✅ **Linux Ubuntu 20.04+** (서버 환경)
- ⚠️ **macOS** (실험적 지원)

### 하드웨어 권장사항 (Hardware Recommendations)
- **RAM**: 16GB 이상 (Unreal Editor + MCP 서버 동시 실행)
- **Storage**: 10GB 여유 공간
- **CPU**: 4코어 이상 권장

---

## 🚀 전체 설치 프로세스 (Complete Installation Process)

### 단계별 설치 순서
```
1. 프로젝트 다운로드
2. Unreal Engine 플러그인 설치
3. Python MCP 서버 설정
4. AI 클라이언트 연동 (선택)
5. 테스트 및 검증
```

### 예상 설치 시간
- **신규 설치**: 30-45분
- **기존 환경 업데이트**: 15-20분

---

## 🎮 Unreal Engine 플러그인 설치

### 1단계: 프로젝트 준비

#### 방법 A: 기존 프로젝트에 추가
```bash
# 1. 기존 Unreal 프로젝트 폴더로 이동
cd /path/to/your/unreal/project

# 2. Plugins 폴더 생성 (없는 경우)
mkdir -p Plugins

# 3. UnrealBlueprintMCP 플러그인 복사
cp -r /path/to/unreal_bp_mcp/Source/UnrealBlueprintMCP Plugins/
cp /path/to/unreal_bp_mcp/UnrealBlueprintMCP.uplugin Plugins/UnrealBlueprintMCP/
```

#### 방법 B: 새 프로젝트 생성
```bash
# 1. 새 C++ 프로젝트 생성 (Unreal Editor에서)
# - Template: Third Person (C++)
# - Project Name: MCPTestProject
# - Location: 원하는 경로

# 2. 프로젝트 폴더에 플러그인 복사
cd MCPTestProject
mkdir Plugins
cp -r /path/to/unreal_bp_mcp/Source/UnrealBlueprintMCP Plugins/
```

### 2단계: 플러그인 컴파일

#### Windows (Visual Studio)
```cmd
# 1. .uproject 파일을 우클릭하여 "Generate Visual Studio project files" 선택
# 2. .sln 파일을 Visual Studio로 열기
# 3. Build > Build Solution 실행
# 4. Development Editor 구성으로 빌드
```

#### Linux
```bash
# 1. Unreal Build Tool 사용
/path/to/UnrealEngine/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe \
  YourProjectNameEditor Linux Development \
  -Project="/path/to/YourProject.uproject" \
  -WaitMutex -FromMsBuild
```

### 3단계: 플러그인 활성화

```bash
# 1. Unreal Editor 실행
# 2. Edit > Plugins 메뉴 열기
# 3. "Project" 탭에서 "Custom" 카테고리 확인
# 4. "UnrealBlueprintMCP" 플러그인 체크박스 활성화
# 5. "Restart Now" 클릭하여 에디터 재시작
```

### 4단계: 플러그인 동작 확인

```bash
# 1. 에디터 재시작 후 메뉴바 확인
# 2. Window > Developer Tools > MCP Status 메뉴 존재 확인
# 3. MCP Status 창 열기
# 4. 기본 UI 요소들 정상 표시 확인:
#    - Server Address 입력필드
#    - Connect/Disconnect 버튼
#    - Connection Status 표시
#    - Operation Logs 영역
```

---

## 🐍 Python MCP 서버 설치

### 1단계: Python 환경 확인

```bash
# Python 버전 확인 (3.8+ 필요)
python --version
# 또는
python3 --version

# pip 설치 확인
pip --version
```

### 2단계: 프로젝트 다운로드 및 설정

```bash
# 1. 프로젝트 클론 또는 다운로드
git clone <repository-url> unreal_bp_mcp
cd unreal_bp_mcp

# 또는 압축파일 다운로드 후 압축 해제
# unzip unreal_bp_mcp.zip
# cd unreal_bp_mcp
```

### 3단계: Python 가상환경 생성

#### Windows
```cmd
# 1. 가상환경 생성
python -m venv mcp_server_env

# 2. 가상환경 활성화
mcp_server_env\Scripts\activate

# 3. 활성화 확인 (프롬프트에 (mcp_server_env) 표시됨)
```

#### Linux/macOS
```bash
# 1. 가상환경 생성
python3 -m venv mcp_server_env

# 2. 가상환경 활성화
source mcp_server_env/bin/activate

# 3. 활성화 확인 (프롬프트에 (mcp_server_env) 표시됨)
```

### 4단계: 종속성 패키지 설치

```bash
# 가상환경이 활성화된 상태에서 실행
pip install --upgrade pip
pip install fastmcp pydantic websockets asyncio

# 설치 확인
pip list
# fastmcp, pydantic, websockets 패키지 확인
```

### 5단계: MCP 서버 실행 테스트

```bash
# 개발 모드로 서버 실행 (WebSocket 서버가 ws://localhost:8080에서 자동 시작됨)
fastmcp dev unreal_blueprint_mcp_server.py

# 성공 시 출력 예시:
# ⚙️ Proxy server listening on localhost:6277
# 🚀 MCP Inspector is up and running at: http://localhost:6274/...
# 🌐 WebSocket server started on ws://localhost:8080
# ✅ UnrealBlueprintMCP Server ready for connections
```

### 6단계: MCP 도구 확인

```bash
# 웹 브라우저에서 MCP Inspector 열기
# http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>

# 확인할 항목:
# ✅ 6개 도구 목록 표시
# ✅ create_blueprint 도구
# ✅ set_blueprint_property 도구
# ✅ get_server_status 도구
# ✅ list_supported_blueprint_classes 도구
# ✅ create_test_actor_blueprint 도구
# ✅ test_unreal_connection 도구
```

---

## 🤖 AI 클라이언트 연동

### Claude Code 연동

#### 1단계: MCP 설정 파일 생성
```json
// ~/.config/claude-code/mcp.json
{
  "servers": {
    "unreal_blueprint": {
      "command": "fastmcp",
      "args": ["run", "/absolute/path/to/unreal_blueprint_mcp_server.py"],
      "env": {
        "PATH": "/absolute/path/to/mcp_server_env/bin:$PATH"
      }
    }
  }
}
```

#### 2단계: 연동 테스트
```bash
# Claude Code에서 다음 명령어 테스트:
# "Create an Actor blueprint named TestActor"
# "Set the location of TestActor to 100, 200, 300"
```

### 직접 MCP 클라이언트 구현

```python
# example_mcp_client.py
import asyncio
import websockets
import json

async def test_mcp_tools():
    uri = "ws://localhost:6277"

    async with websockets.connect(uri) as websocket:
        # create_blueprint 도구 호출
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_blueprint",
                "arguments": {
                    "blueprint_name": "MyActor",
                    "parent_class": "Actor",
                    "asset_path": "/Game/Blueprints/"
                }
            }
        }

        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        print(f"Response: {response}")

# 실행
asyncio.run(test_mcp_tools())
```

---

## 🧪 테스트 및 검증

### 통합 테스트 프로세스

#### 1단계: 개별 컴포넌트 테스트

```bash
# A. MCP 서버 단독 테스트
cd unreal_bp_mcp
source mcp_server_env/bin/activate  # Linux/macOS
# 또는 mcp_server_env\Scripts\activate  # Windows
fastmcp dev unreal_blueprint_mcp_server.py

# B. Unreal 플러그인 단독 테스트
# 1. Unreal Editor 실행
# 2. Window > Developer Tools > MCP Status 열기
# 3. UI 요소들 정상 표시 확인
```

#### 2단계: WebSocket 통신 테스트

```bash
# 테스트 스크립트 실행
python test_unreal_connection.py

# 예상 결과:
# ❌ Connection refused (Unreal Editor 미실행 시 - 정상)
# ✅ Connected to Unreal Engine WebSocket server (연결 성공 시)
```

#### 3단계: End-to-End 테스트

```bash
# 1. MCP 서버 실행 (터미널 1)
fastmcp dev unreal_blueprint_mcp_server.py

# 2. Unreal Editor 실행 및 MCP Status 창 열기
# Window > Developer Tools > MCP Status

# 3. MCP Status 창에서 "Connect" 버튼 클릭
# 연결 상태가 "Connected"로 변경되는지 확인

# 4. MCP Inspector에서 도구 테스트 (선택사항)
# http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>

# 5. create_blueprint 도구 실행
# Parameters:
# - blueprint_name: "TestActor"
# - parent_class: "Actor"
# - asset_path: "/Game/Blueprints/"

# 6. Unreal Editor Content Browser에서 실제 생성된 블루프린트 확인
# /Game/Blueprints/TestActor.uasset 파일이 실제로 생성됨
```

### 테스트 체크리스트

- [ ] **MCP 서버 시작**: `fastmcp dev` 명령으로 서버 정상 실행
- [ ] **MCP Inspector 접근**: 웹 인터페이스 정상 로드
- [ ] **6개 도구 확인**: 모든 도구가 도구 목록에 표시
- [ ] **Unreal 플러그인 로드**: 플러그인이 Unreal Editor에서 활성화
- [ ] **MCP Status UI**: MCP 상태 창이 정상 표시
- [ ] **WebSocket 통신**: Unreal ↔ Python 서버 간 통신 테스트
- [ ] **Blueprint 생성**: 실제 블루프린트 생성 확인
- [ ] **Property 수정**: CDO 속성 변경 확인

---

## 🔧 문제 해결 (Troubleshooting)

### 일반적인 문제 및 해결방법

#### 1. Unreal Engine 플러그인 문제

**문제**: 플러그인이 플러그인 목록에 나타나지 않음
```bash
해결방법:
1. .uplugin 파일이 올바른 위치에 있는지 확인
   위치: [ProjectName]/Plugins/UnrealBlueprintMCP/UnrealBlueprintMCP.uplugin
2. 프로젝트를 닫고 "Generate Visual Studio project files" 재실행
3. 프로젝트 재컴파일
```

**문제**: 컴파일 에러 - WebSockets 모듈을 찾을 수 없음
```bash
해결방법:
1. Build.cs 파일에서 "WebSockets" 모듈이 추가되었는지 확인
2. Unreal Engine 5.6+ 사용 확인 (이전 버전은 모듈명이 다를 수 있음)
```

**문제**: MCP Status 메뉴가 나타나지 않음
```bash
해결방법:
1. 플러그인이 정상적으로 로드되었는지 확인 (Output Log 확인)
2. Editor 전용 모듈이므로 PIE가 아닌 Editor에서 확인
3. Unreal Editor 재시작
```

#### 2. Python MCP 서버 문제

**문제**: `ModuleNotFoundError: No module named 'fastmcp'`
```bash
해결방법:
1. 가상환경이 활성화되었는지 확인
2. pip install fastmcp 재실행
3. Python 버전 확인 (3.8+ 필요)
```

**문제**: MCP 서버가 시작되지 않음
```bash
해결방법:
1. 포트 6277이 이미 사용 중인지 확인
   - Windows: netstat -an | findstr 6277
   - Linux/macOS: lsof -i :6277
2. 방화벽 설정 확인
3. fastmcp 최신 버전 설치 확인
```

**문제**: MCP Inspector에 도구가 표시되지 않음
```bash
해결방법:
1. unreal_blueprint_mcp_server.py 파일에 구문 오류가 없는지 확인
2. @mcp.tool() 데코레이터가 모든 함수에 적용되었는지 확인
3. 서버 재시작 후 재확인
```

#### 3. 통신 문제

**문제**: Unreal ↔ MCP 서버 간 연결 실패
```bash
해결방법:
1. 포트 설정 확인:
   - MCP 서버: 6277 (기본값)
   - Unreal 플러그인: 8080 (기본값)
2. 로컬호스트 연결 테스트
3. 네트워크 방화벽 설정 확인
```

**문제**: WebSocket 연결 거부됨
```bash
해결방법:
1. Unreal Editor가 실행 중인지 확인
2. MCP Status 창이 열려있고 "Connect" 버튼을 눌렀는지 확인
3. MCP 플러그인이 정상적으로 로드되었는지 확인 (Output Log 확인)
4. 포트 8080이 사용 가능한지 확인:
   - Linux/macOS: lsof -i :8080
   - Windows: netstat -an | findstr 8080
5. 방화벽에서 포트 8080 허용 여부 확인
```

### 로그 및 디버깅

#### Unreal Engine 로그 확인
```bash
# Output Log 창에서 다음 키워드 검색:
- "MCPClient"
- "MCPBlueprintManager"
- "WebSocket"
- "MCP"
```

#### Python MCP 서버 로그 확인
```bash
# 터미널에서 실행 중인 서버 로그 확인
# 일반적인 로그 메시지:
- "Starting MCP inspector..."
- "Proxy server listening on localhost:6277"
- "WebSocket server started on ws://localhost:8080"
- "New STDIO connection request"
- "WebSocket connection established with Unreal Engine"
- "Received JSON-RPC request: create_blueprint"
```

### 성능 최적화

#### 메모리 사용량 최적화
- Unreal Editor: 불필요한 플러그인 비활성화
- Python: 가상환경 사용으로 격리된 환경 유지

#### 응답 속도 개선
- MCP 서버: SSD 스토리지 사용 권장
- 네트워크: 로컬 연결 사용 (원격 연결 시 지연 증가)

---

## 📚 추가 리소스

### 공식 문서
- [Unreal Engine 5.6 Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-6-documentation)
- [MCP Protocol Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

### 커뮤니티 지원
- **Issues**: GitHub Issues 페이지에서 문제 보고
- **Discussions**: 기능 제안 및 사용법 문의
- **Discord**: 실시간 지원 및 커뮤니티 채팅

### 예제 프로젝트
- `examples/` 폴더: 기본 사용법 예제
- `tests/` 폴더: 단위 테스트 및 통합 테스트
- `docs/` 폴더: 추가 기술 문서

---

## 🎯 다음 단계

설치가 완료되면:

1. **기본 튜토리얼**: README.md의 Quick Start 가이드 따라하기
2. **API 문서**: 각 MCP 도구의 상세 사용법 학습
3. **커스터마이제이션**: 프로젝트 요구사항에 맞게 도구 확장
4. **프로덕션 배포**: 실제 개발 워크플로우에 통합

**Happy Coding! 🚀**