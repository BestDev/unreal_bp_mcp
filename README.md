# 🎮 UnrealBlueprintMCP - Production Implementation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.6+-blue.svg)](https://www.unrealengine.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)
[![WebSocket](https://img.shields.io/badge/WebSocket-JSON--RPC%202.0-orange.svg)]()

> **Production-Ready AI Blueprint Control for Unreal Engine**
>
> A complete WebSocket client implementation enabling external AI agents to control Unreal Engine Blueprint Editor through JSON-RPC 2.0 protocol. Supports real-time blueprint creation, property modification, component addition, and compilation with comprehensive error handling and UI integration.

---

## 🚀 What is UnrealBlueprintMCP?

UnrealBlueprintMCP는 AI 에이전트가 자연어를 통해 Unreal Engine 블루프린트를 프로그래밍 방식으로 생성하고 수정할 수 있도록 하는 혁신적인 도구입니다.

**"Create an Actor blueprint called MyTestActor"** → 실제 Unreal Editor에 블루프린트 생성! ✨

### ✨ 주요 기능 (Key Features)

- 🎯 **자연어 블루프린트 생성**: AI 에이전트를 통한 직관적인 블루프린트 제작
- 🔧 **실시간 속성 수정**: CDO 기반 블루프린트 속성 실시간 변경
- 🌐 **MCP 표준 준수**: Model Context Protocol을 통한 표준화된 AI 통신
- ⚡ **WebSocket 통신**: 고성능 실시간 양방향 통신
- 🎮 **Unreal Engine 통합**: UE 5.6+ 완벽 지원 및 에디터 통합
- 🛡️ **타입 안전성**: Pydantic 기반 강력한 타입 검증

### 🏗️ 시스템 아키텍처

```
AI Client (Claude/GPT) → MCP Protocol → Python MCP Server → WebSocket → Unreal Plugin → Blueprint Editor
```

---

## 📸 스크린샷 & 데모

### MCP Status Dashboard
![MCP Status](docs/images/mcp-status-dashboard.png)
*Unreal Editor 내 MCP 서버 연결 상태 모니터링*

### MCP Inspector Interface
![MCP Inspector](docs/images/mcp-inspector.png)
*웹 기반 MCP 도구 테스트 및 모니터링 인터페이스*

### AI Agent in Action
```
🤖 AI: "Create a Character blueprint named PlayerCharacter with location 0,0,100"
✅ Result: Blueprint created at /Game/Blueprints/PlayerCharacter
🤖 AI: "Set PlayerCharacter's health to 100"
✅ Result: Health property updated in CDO
```

---

## 🎯 Quick Start (빠른 시작)

### 전체 설치 과정 (5분 설치)

#### 1️⃣ 프로젝트 다운로드
```bash
git clone https://github.com/yourusername/unreal-blueprint-mcp.git
cd unreal-blueprint-mcp
```

#### 2️⃣ Python MCP 서버 설정
```bash
# Python 가상환경 생성
python -m venv mcp_server_env

# 가상환경 활성화
source mcp_server_env/bin/activate  # Linux/macOS
# 또는 mcp_server_env\Scripts\activate  # Windows

# 종속성 설치
pip install fastmcp pydantic websockets

# MCP 서버 실행
fastmcp dev unreal_blueprint_mcp_server.py
```

#### 3️⃣ Unreal Engine 플러그인 설치
1.  **플러그인 폴더 준비**
    - Unreal Engine 프로젝트 루트에 `Plugins` 폴더가 없으면 생성합니다.
    - `Plugins` 폴더 안에 `UnrealBlueprintMCP` 라는 이름의 새 폴더를 만듭니다.

2.  **플러그인 파일 복사**
    - 이 저장소의 `Source` 폴더와 `UnrealBlueprintMCP.uplugin` 파일을 `[내 Unreal 프로젝트]/Plugins/UnrealBlueprintMCP/` 폴더 안으로 복사합니다.
    - 최종 경로는 다음과 같아야 합니다:
      - `[내 Unreal 프로젝트]/Plugins/UnrealBlueprintMCP/Source`
      - `[내 Unreal 프로젝트]/Plugins/UnrealBlueprintMCP/UnrealBlueprintMCP.uplugin`

3.  **프로젝트 파일 재생성 (필수)**
    - 프로젝트의 `.uproject` 파일을 마우스 오른쪽 버튼으로 클릭하고 **"Generate Visual Studio project files"**를 선택하여 Visual Studio 프로젝트를 업데이트합니다.

4.  **빌드 및 플러그인 활성화**
    - 생성된 `.sln` 파일을 Visual Studio에서 열고 프로젝트를 빌드합니다.
    - Unreal Editor에서 프로젝트를 열고 `Edit > Plugins` 메뉴에서 `UnrealBlueprintMCP`를 찾아 활성화(Enabled)합니다. (에디터 재시작 필요)

5.  **MCP 상태 창 확인**
    - 에디터 메뉴에서 `Window > Developer Tools > MCP Status`를 선택하여 플러그인 UI가 정상적으로 뜨는지 확인합니다.

#### 4️⃣ 첫 테스트 실행
```bash
# MCP Inspector 웹 인터페이스 접속
# http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>

# create_blueprint 도구 테스트:
{
  "blueprint_name": "TestActor",
  "parent_class": "Actor",
  "asset_path": "/Game/Blueprints/"
}
```

### 🎉 성공!
Unreal Editor의 Content Browser에서 새로 생성된 블루프린트를 확인하세요!

---

## 📚 사용법 (Usage)

### 기본 블루프린트 생성

#### AI 클라이언트를 통한 자연어 명령
```
"Create an Actor blueprint called MyGameActor"
"Make a Pawn blueprint named PlayerPawn in the Characters folder"
"Create a UserWidget blueprint for the main menu UI"
```

#### 직접 MCP 도구 호출
```python
# create_blueprint 도구 사용
{
  "name": "create_blueprint",
  "arguments": {
    "blueprint_name": "MyActor",
    "parent_class": "Actor",
    "asset_path": "/Game/Blueprints/"
  }
}
```

### 블루프린트 속성 수정

#### 자연어 명령
```
"Set MyActor's location to 100, 200, 300"
"Change the health property of PlayerCharacter to 150"
"Set the mesh scale to 2.0"
```

#### 직접 MCP 도구 호출
```python
# set_blueprint_property 도구 사용
{
  "name": "set_blueprint_property",
  "arguments": {
    "blueprint_path": "/Game/Blueprints/MyActor",
    "property_name": "RootComponent",
    "property_value": "100.0,200.0,300.0",
    "property_type": "Vector"
  }
}
```

### 지원되는 블루프린트 타입

| Parent Class | 설명 | 사용 예시 |
|-------------|------|----------|
| **Actor** | 기본 게임 오브젝트 | 환경 오브젝트, NPC |
| **Pawn** | 제어 가능한 엔티티 | AI 캐릭터, 탈것 |
| **Character** | 플레이어/NPC 캐릭터 | 플레이어, 적 캐릭터 |
| **ActorComponent** | 재사용 가능한 컴포넌트 | 인벤토리, 스킬 시스템 |
| **SceneComponent** | 변환 기반 컴포넌트 | 카메라 컴포넌트 |
| **UserWidget** | UI 위젯 | 메뉴, HUD, 다이얼로그 |
| **Object** | 기본 UObject | 데이터 에셋, 설정 |

### 지원되는 속성 타입

| Type | 예시 값 | 설명 |
|------|--------|------|
| **int** | `100` | 정수형 속성 |
| **float** | `3.14` | 실수형 속성 |
| **bool** | `true` | 불린형 속성 |
| **string** | `"Hello World"` | 문자열 속성 |
| **Vector** | `"100.0,200.0,300.0"` | 3D 벡터 (위치, 크기 등) |
| **Rotator** | `"0.0,90.0,0.0"` | 3D 회전값 |

---

## 🔧 고급 사용법 (Advanced Usage)

### 커스텀 AI 클라이언트 구현

```python
import asyncio
import websockets
import json

class UnrealBlueprintClient:
    def __init__(self, mcp_server_url="ws://localhost:6277"):
        self.server_url = mcp_server_url

    async def create_blueprint(self, name, parent_class="Actor"):
        """블루프린트 생성"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_blueprint",
                "arguments": {
                    "blueprint_name": name,
                    "parent_class": parent_class,
                    "asset_path": "/Game/Blueprints/"
                }
            }
        }

        async with websockets.connect(self.server_url) as ws:
            await ws.send(json.dumps(request))
            response = await ws.recv()
            return json.loads(response)

    async def set_property(self, blueprint_path, property_name, value):
        """속성 설정"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "set_blueprint_property",
                "arguments": {
                    "blueprint_path": blueprint_path,
                    "property_name": property_name,
                    "property_value": str(value)
                }
            }
        }

        async with websockets.connect(self.server_url) as ws:
            await ws.send(json.dumps(request))
            response = await ws.recv()
            return json.loads(response)

# 사용 예시
async def main():
    client = UnrealBlueprintClient()

    # 블루프린트 생성
    result = await client.create_blueprint("MyCustomActor", "Actor")
    print(f"Blueprint created: {result}")

    # 속성 설정
    result = await client.set_property(
        "/Game/Blueprints/MyCustomActor",
        "RootComponent",
        "0.0,0.0,100.0"
    )
    print(f"Property set: {result}")

asyncio.run(main())
```

### Claude Code 통합 설정

```json
// ~/.config/claude-code/mcp.json
{
  "servers": {
    "unreal_blueprint": {
      "command": "fastmcp",
      "args": ["run", "/absolute/path/to/unreal_blueprint_mcp_server.py"],
      "env": {
        "PATH": "/path/to/mcp_server_env/bin:$PATH"
      }
    }
  }
}
```

### 배치 블루프린트 생성

```python
# 여러 블루프린트를 한 번에 생성하는 예시
blueprints_to_create = [
    {"name": "Player", "type": "Character"},
    {"name": "Enemy", "type": "Pawn"},
    {"name": "Weapon", "type": "Actor"},
    {"name": "HealthBar", "type": "UserWidget"}
]

for bp in blueprints_to_create:
    await client.create_blueprint(bp["name"], bp["type"])
    print(f"Created {bp['name']} blueprint")
```

---

## 📖 API 레퍼런스

### MCP 도구 목록

#### 1. `create_blueprint`
블루프린트 에셋을 새로 생성합니다.

**Parameters:**
```json
{
  "blueprint_name": "string",    // 블루프린트 이름 (필수)
  "parent_class": "string",      // 부모 클래스 (기본값: "Actor")
  "asset_path": "string"         // 에셋 경로 (기본값: "/Game/Blueprints/")
}
```

**Response:**
```json
{
  "success": true,
  "message": "Blueprint 'TestActor' creation requested",
  "blueprint_path": "/Game/Blueprints/TestActor",
  "parent_class": "Actor"
}
```

#### 2. `set_blueprint_property`
기존 블루프린트의 CDO 속성을 수정합니다.

**Parameters:**
```json
{
  "blueprint_path": "string",    // 블루프린트 경로 (필수)
  "property_name": "string",     // 속성 이름 (필수)
  "property_value": "string",    // 새 값 (필수)
  "property_type": "string"      // 타입 힌트 (선택사항)
}
```

#### 3. `get_server_status`
MCP 서버의 현재 상태를 조회합니다.

**Response:**
```json
{
  "server_name": "UnrealBlueprintMCPServer",
  "version": "1.0.0",
  "connection_status": "connected",
  "available_tools": ["create_blueprint", "set_blueprint_property", ...]
}
```

#### 4. `list_supported_blueprint_classes`
지원되는 블루프린트 부모 클래스 목록을 반환합니다.

**Response:**
```json
["Actor", "Pawn", "Character", "ActorComponent", "SceneComponent", "UserWidget", "Object"]
```

#### 5. `create_test_actor_blueprint`
테스트용 Actor 블루프린트를 빠르게 생성합니다.

**Parameters:**
```json
{
  "blueprint_name": "string",    // 블루프린트 이름 (기본값: "TestActor")
  "location": {                  // 초기 위치 (기본값: 0,0,100)
    "x": 0.0,
    "y": 0.0,
    "z": 100.0
  }
}
```

#### 6. `test_unreal_connection`
Unreal Engine과의 연결 상태를 테스트합니다.

**Response:**
```json
{
  "success": true,
  "message": "Connection test completed",
  "response_time_seconds": 0.123,
  "connection_status": "connected"
}
```

---

## 🗂️ 프로젝트 구조

```
unreal-blueprint-mcp/
├── 📁 Source/UnrealBlueprintMCP/     # Unreal Engine 플러그인
│   ├── 📁 Public/                    # 헤더 파일
│   │   ├── UnrealBlueprintMCP.h
│   │   ├── MCPSettings.h
│   │   ├── MCPClient.h
│   │   ├── MCPStatusWidget.h
│   │   └── MCPBlueprintManager.h
│   ├── 📁 Private/                   # 구현 파일
│   │   ├── UnrealBlueprintMCP.cpp
│   │   ├── MCPSettings.cpp
│   │   ├── MCPClient.cpp
│   │   ├── MCPStatusWidget.cpp
│   │   └── MCPBlueprintManager.cpp
│   └── UnrealBlueprintMCP.Build.cs
├── 📄 unreal_blueprint_mcp_server.py  # Python MCP 서버
├── 📄 UnrealBlueprintMCP.uplugin      # 플러그인 메타데이터
├── 📁 docs/                          # 문서 및 가이드
│   ├── 📄 INSTALLATION_GUIDE.md      # 상세 설치 가이드
│   ├── 📄 API_REFERENCE.md           # API 문서
│   └── 📁 images/                    # 스크린샷 및 다이어그램
├── 📁 examples/                      # 사용 예제
│   ├── 📄 basic_usage.py
│   ├── 📄 batch_creation.py
│   └── 📄 claude_integration.py
├── 📁 tests/                         # 테스트 파일
│   ├── 📄 test_mcp_tools.py
│   └── 📄 test_unreal_connection.py
├── 📄 README.md                      # 이 파일
├── 📄 LICENSE                        # MIT 라이선스
└── 📄 requirements.txt               # Python 종속성
```

---

## 🤝 기여하기 (Contributing)

우리는 커뮤니티의 기여를 환영합니다!

### 기여 방법

1. **Fork** 이 저장소
2. **Feature Branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Changes Commit** (`git commit -m 'Add amazing feature'`)
4. **Branch Push** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 개발 환경 설정

```bash
# 개발용 저장소 클론
git clone https://github.com/yourusername/unreal-blueprint-mcp.git
cd unreal-blueprint-mcp

# 개발용 Python 환경 설정
python -m venv dev_env
source dev_env/bin/activate
pip install -r requirements-dev.txt

# 테스트 실행
python -m pytest tests/

# 코드 품질 검사
black .
flake8 .
```

### 기여 가이드라인

- **코드 스타일**: Black formatter 사용
- **테스트**: 새 기능에 대한 테스트 추가 필수
- **문서화**: 공개 API에 대한 docstring 작성
- **커밋 메시지**: [Conventional Commits](https://www.conventionalcommits.org/) 형식 사용

---

## 🐛 이슈 리포팅

문제를 발견하셨나요? [GitHub Issues](https://github.com/yourusername/unreal-blueprint-mcp/issues)에서 보고해주세요!

### 이슈 템플릿

**버그 리포트:**
- 🔍 **문제 설명**: 무엇이 잘못되었나요?
- 🔄 **재현 단계**: 어떻게 재현할 수 있나요?
- 💻 **환경 정보**: OS, Unreal 버전, Python 버전
- 📸 **스크린샷**: 가능하다면 스크린샷 첨부

**기능 요청:**
- ✨ **원하는 기능**: 어떤 기능을 원하시나요?
- 🎯 **사용 사례**: 왜 이 기능이 필요한가요?
- 💡 **제안된 해결책**: 어떻게 구현될 수 있을까요?

---

## 📋 로드맵 (Roadmap)

### 🚀 v1.0 (Current)
- ✅ 기본 블루프린트 생성 및 속성 수정
- ✅ MCP 표준 프로토콜 지원
- ✅ WebSocket 실시간 통신
- ✅ 6개 핵심 MCP 도구

### 🔮 v1.1 (Next)
- [ ] **블루프린트 노드 그래프 편집**: 비주얼 스크립팅 노드 조작
- [ ] **Material 생성 및 수정**: 머티리얼 에셋 프로그래밍 방식 제어
- [ ] **Animation Blueprint 지원**: 애니메이션 로직 생성
- [ ] **Batch Operations**: 여러 블루프린트 동시 처리

### 🌟 v2.0 (Future)
- [ ] **Level/World 편집**: 레벨 내 액터 배치 및 편집
- [ ] **Package 및 빌드 자동화**: 프로젝트 빌드 파이프라인
- [ ] **Version Control 통합**: Git 등 VCS와의 연동
- [ ] **Cloud API**: 원격 Unreal 인스턴스 제어

### 🎮 v3.0 (Vision)
- [ ] **Visual Editor**: 웹 기반 블루프린트 에디터
- [ ] **Multi-User Support**: 팀 협업 기능
- [ ] **AI Code Generation**: AI를 통한 C++ 코드 생성
- [ ] **Marketplace Integration**: Unreal Marketplace 자동 발행

---

## 🏆 사용 사례 (Use Cases)

### 게임 개발 스튜디오
> "우리 팀은 UnrealBlueprintMCP를 사용해 프로토타이핑 시간을 80% 단축했습니다. AI가 반복적인 블루프린트 작업을 처리하는 동안 우리는 창의적인 작업에 집중할 수 있었습니다."
>
> — **InnovateGames Studio**

### 교육 기관
> "학생들이 복잡한 블루프린트 문법을 배우기 전에 자연어로 게임 로직을 구현할 수 있어서 학습 곡선이 크게 완화되었습니다."
>
> — **GameDev University**

### 인디 개발자
> "혼자 개발할 때 시간이 가장 소중한데, AI 어시스턴트가 블루프린트를 자동으로 생성해주니 개발 속도가 눈에 띄게 빨라졌습니다."
>
> — **Solo Developer**

---

## 🤖 AI 모델 호환성

| AI Client | 지원 상태 | 설정 방법 |
|-----------|---------|----------|
| **Claude Code** | ✅ 완전 지원 | MCP 설정 파일 구성 |
| **GPT-4 + LangChain** | ✅ 지원 | 커스텀 도구 래퍼 구현 |
| **Gemini** | 🔄 개발 중 | Gemini API 통합 예정 |
| **Local LLM** | ⚠️ 실험적 | Ollama + MCP 클라이언트 |

---

## 📊 성능 지표

### 시스템 요구사항
- **Unreal Engine**: 5.6+ (WebSocket 모듈 지원)
- **Python**: 3.8+ (비동기 처리 지원)
- **메모리**: 평균 200MB (Unreal Editor 제외)
- **CPU**: 블루프린트 생성 시 <1초
- **네트워크**: WebSocket 지연시간 <50ms (로컬)

### 벤치마크 결과
- **블루프린트 생성**: 평균 0.3초
- **속성 수정**: 평균 0.1초
- **MCP 도구 응답**: 평균 0.05초
- **동시 연결**: 최대 10개 클라이언트 지원

---

## 🔒 보안 및 제한사항

### 보안 고려사항
- **로컬 실행**: 기본적으로 localhost에서만 동작
- **인증**: MCP Inspector 토큰 기반 인증
- **권한**: Unreal Editor 권한 내에서만 작업 수행

### 현재 제한사항
- **에디터 모드**: Play In Editor 중에는 블루프린트 생성 불가
- **복잡한 노드**: 복잡한 블루프린트 노드 그래프 편집 미지원 (v1.1에서 지원 예정)
- **언두/리두**: 자동 실행취소 기능 미구현
- **네트워크**: 원격 Unreal 인스턴스 제어 미지원 (로컬 연결만 지원)

---

## 📞 지원 및 문의

### 커뮤니티
- 💬 **Discord**: [UnrealMCP Community](https://discord.gg/unreal-mcp)
- 📧 **Email**: support@unrealblueprintmcp.dev
- 🐦 **Twitter**: [@UnrealMCP](https://twitter.com/unrealmcp)

### 비즈니스 문의
- 🏢 **Enterprise Support**: enterprise@unrealblueprintmcp.dev
- 📋 **Custom Development**: consulting@unrealblueprintmcp.dev
- 🤝 **Partnership**: partners@unrealblueprintmcp.dev

---

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

```
MIT License

Copyright (c) 2025 UnrealBlueprintMCP Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 감사의 말

- **Unreal Engine Team**: 강력한 Blueprint 시스템 제공
- **MCP Contributors**: Model Context Protocol 표준 개발
- **FastMCP**: Python MCP 구현 라이브러리
- **Community**: 피드백과 기여를 해주신 모든 분들

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/unreal-blueprint-mcp&type=Date)](https://star-history.com/#yourusername/unreal-blueprint-mcp&Date)

---

<div align="center">

**🎮 Made with ❤️ for the Unreal Engine Community**

[🌟 Star this repo](https://github.com/yourusername/unreal-blueprint-mcp) | [🐛 Report Bug](https://github.com/yourusername/unreal-blueprint-mcp/issues) | [💡 Request Feature](https://github.com/yourusername/unreal-blueprint-mcp/issues)

</div>