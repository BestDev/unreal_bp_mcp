# MCP 클라이언트 설정 가이드 (MCP Client Setup Guide)

> **목적**: AI 클라이언트를 UnrealBlueprintMCP 서버에 연결하는 상세 가이드
> **대상**: AI 개발자, 통합 담당자, 고급 사용자

## 📋 목차

1. [Claude Code 연동](#claude-code-연동)
2. [커스텀 Python 클라이언트](#커스텀-python-클라이언트)
3. [LangChain 통합](#langchain-통합)
4. [REST API 클라이언트](#rest-api-클라이언트)
5. [웹 클라이언트 (JavaScript)](#웹-클라이언트-javascript)
6. [문제 해결](#문제-해결)

---

## 🤖 Claude Code 연동

### 1단계: MCP 설정 파일 생성

Claude Code는 MCP 서버를 `mcp.json` 설정 파일을 통해 관리합니다.

#### Linux/macOS
```bash
# 설정 디렉토리 생성
mkdir -p ~/.config/claude-code

# MCP 설정 파일 생성
cat > ~/.config/claude-code/mcp.json << 'EOF'
{
  "servers": {
    "unreal_blueprint": {
      "command": "fastmcp",
      "args": ["run", "/absolute/path/to/unreal_blueprint_mcp_server.py"],
      "env": {
        "PATH": "/absolute/path/to/mcp_server_env/bin:$PATH",
        "PYTHONPATH": "/absolute/path/to/unreal_bp_mcp"
      }
    }
  }
}
EOF
```

#### Windows
```powershell
# 설정 디렉토리 생성
New-Item -ItemType Directory -Force -Path "$env:APPDATA\claude-code"

# MCP 설정 파일 생성 (PowerShell)
@"
{
  "servers": {
    "unreal_blueprint": {
      "command": "fastmcp",
      "args": ["run", "C:\\absolute\\path\\to\\unreal_blueprint_mcp_server.py"],
      "env": {
        "PATH": "C:\\absolute\\path\\to\\mcp_server_env\\Scripts;%PATH%",
        "PYTHONPATH": "C:\\absolute\\path\\to\\unreal_bp_mcp"
      }
    }
  }
}
"@ | Out-File -FilePath "$env:APPDATA\claude-code\mcp.json" -Encoding UTF8
```

### 2단계: 경로 설정 확인

**중요**: 절대 경로를 사용해야 합니다!

```bash
# 1. 현재 프로젝트 경로 확인
pwd
# 예: /home/user/projects/unreal_bp_mcp

# 2. Python 가상환경 경로 확인
which python  # 가상환경 활성화 후
# 예: /home/user/projects/unreal_bp_mcp/mcp_server_env/bin/python

# 3. 설정 파일에서 경로 업데이트
# "/absolute/path/to" 부분을 실제 경로로 변경
```

### 3단계: Claude Code에서 테스트

```bash
# 1. Claude Code 실행
claude-code

# 2. 새 대화 시작 후 다음 명령어 테스트:
"Show me the available Unreal Blueprint tools"
"Create an Actor blueprint called TestActor"
"List supported blueprint classes"
```

### 4단계: 연결 확인

Claude Code에서 MCP 서버 상태 확인:

```bash
# Claude Code 대화에서:
"Check the MCP server status"
"What tools are available for Unreal Engine?"

# 예상 응답:
# - 6개 도구 목록 표시
# - create_blueprint, set_blueprint_property 등
```

---

## 🐍 커스텀 Python 클라이언트

### 기본 MCP 클라이언트 구현

```python
#!/usr/bin/env python3
"""
Custom MCP Client for UnrealBlueprintMCP
Direct WebSocket connection to MCP server
"""

import asyncio
import websockets
import json
from typing import Dict, Any, Optional
import logging

class UnrealBlueprintMCPClient:
    def __init__(self, server_url: str = "ws://localhost:6277"):
        """
        UnrealBlueprintMCP 클라이언트 초기화

        Args:
            server_url: MCP 서버 WebSocket URL
        """
        self.server_url = server_url
        self.request_id = 0
        self.logger = logging.getLogger(__name__)

    def _get_next_id(self) -> int:
        """다음 요청 ID 생성"""
        self.request_id += 1
        return self.request_id

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 도구 호출

        Args:
            tool_name: 호출할 도구 이름
            arguments: 도구에 전달할 인자들

        Returns:
            도구 실행 결과
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            async with websockets.connect(self.server_url) as websocket:
                # 요청 전송
                await websocket.send(json.dumps(request))
                self.logger.info(f"Tool called: {tool_name}")

                # 응답 수신
                response = await websocket.recv()
                result = json.loads(response)

                if "error" in result:
                    raise Exception(f"MCP Error: {result['error']}")

                return result.get("result", {})

        except Exception as e:
            self.logger.error(f"Tool call failed: {e}")
            raise

    async def list_tools(self) -> list:
        """사용 가능한 도구 목록 조회"""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list"
        }

        async with websockets.connect(self.server_url) as websocket:
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            result = json.loads(response)
            return result.get("result", {}).get("tools", [])

    # === Unreal Blueprint 전용 메서드 ===

    async def create_blueprint(
        self,
        name: str,
        parent_class: str = "Actor",
        asset_path: str = "/Game/Blueprints/"
    ) -> Dict[str, Any]:
        """블루프린트 생성"""
        return await self.call_tool("create_blueprint", {
            "blueprint_name": name,
            "parent_class": parent_class,
            "asset_path": asset_path
        })

    async def set_blueprint_property(
        self,
        blueprint_path: str,
        property_name: str,
        property_value: str,
        property_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """블루프린트 속성 설정"""
        args = {
            "blueprint_path": blueprint_path,
            "property_name": property_name,
            "property_value": property_value
        }
        if property_type:
            args["property_type"] = property_type

        return await self.call_tool("set_blueprint_property", args)

    async def get_server_status(self) -> Dict[str, Any]:
        """서버 상태 조회"""
        return await self.call_tool("get_server_status", {})

    async def list_supported_classes(self) -> list:
        """지원되는 블루프린트 클래스 목록"""
        result = await self.call_tool("list_supported_blueprint_classes", {})
        return result.get("classes", [])

    async def create_test_actor(
        self,
        name: str = "TestActor",
        x: float = 0.0,
        y: float = 0.0,
        z: float = 100.0
    ) -> Dict[str, Any]:
        """테스트 액터 블루프린트 생성"""
        return await self.call_tool("create_test_actor_blueprint", {
            "blueprint_name": name,
            "location": {"x": x, "y": y, "z": z}
        })

    async def test_connection(self) -> Dict[str, Any]:
        """Unreal Engine 연결 테스트"""
        return await self.call_tool("test_unreal_connection", {})


# === 사용 예제 ===

async def main():
    """기본 사용 예제"""
    client = UnrealBlueprintMCPClient()

    try:
        # 1. 서버 상태 확인
        print("=== Server Status ===")
        status = await client.get_server_status()
        print(f"Server: {status.get('server_name')}")
        print(f"Version: {status.get('version')}")

        # 2. 사용 가능한 도구 목록
        print("\n=== Available Tools ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.get('name')}: {tool.get('description', 'No description')}")

        # 3. 지원되는 블루프린트 클래스
        print("\n=== Supported Classes ===")
        classes = await client.list_supported_classes()
        print(f"Classes: {', '.join(classes)}")

        # 4. 블루프린트 생성
        print("\n=== Creating Blueprint ===")
        result = await client.create_blueprint("MyCustomActor", "Actor")
        print(f"Blueprint created: {result.get('success')}")
        print(f"Path: {result.get('blueprint_path')}")

        # 5. 속성 설정
        print("\n=== Setting Property ===")
        prop_result = await client.set_blueprint_property(
            result.get('blueprint_path'),
            "RootComponent",
            "100.0,200.0,300.0",
            "Vector"
        )
        print(f"Property set: {prop_result.get('success')}")

        # 6. 연결 테스트
        print("\n=== Connection Test ===")
        conn_test = await client.test_connection()
        print(f"Connection: {conn_test.get('success')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 비동기 실행
    asyncio.run(main())
```

### 고급 사용 예제

```python
# advanced_usage.py
import asyncio
from unreal_mcp_client import UnrealBlueprintMCPClient

async def batch_blueprint_creation():
    """여러 블루프린트를 배치로 생성"""
    client = UnrealBlueprintMCPClient()

    blueprints = [
        {"name": "Player", "class": "Character"},
        {"name": "Enemy", "class": "Pawn"},
        {"name": "Weapon", "class": "Actor"},
        {"name": "PowerUp", "class": "Actor"},
        {"name": "HealthBar", "class": "UserWidget"}
    ]

    results = []
    for bp in blueprints:
        try:
            result = await client.create_blueprint(bp["name"], bp["class"])
            results.append({
                "name": bp["name"],
                "success": result.get("success"),
                "path": result.get("blueprint_path")
            })
            print(f"✅ Created {bp['name']} ({bp['class']})")
        except Exception as e:
            print(f"❌ Failed to create {bp['name']}: {e}")
            results.append({
                "name": bp["name"],
                "success": False,
                "error": str(e)
            })

    return results

async def setup_game_objects():
    """게임 오브젝트 설정 자동화"""
    client = UnrealBlueprintMCPClient()

    # 1. 플레이어 캐릭터 생성
    player_result = await client.create_blueprint("PlayerCharacter", "Character")

    if player_result.get("success"):
        # 플레이어 속성 설정
        await client.set_blueprint_property(
            player_result["blueprint_path"],
            "Health", "100", "int"
        )
        await client.set_blueprint_property(
            player_result["blueprint_path"],
            "Speed", "600.0", "float"
        )

    # 2. 적 AI 생성
    enemy_result = await client.create_blueprint("EnemyAI", "Pawn")

    if enemy_result.get("success"):
        # 적 속성 설정
        await client.set_blueprint_property(
            enemy_result["blueprint_path"],
            "Health", "50", "int"
        )
        await client.set_blueprint_property(
            enemy_result["blueprint_path"],
            "AttackDamage", "25", "int"
        )

    print("Game objects setup completed!")

# 실행 예제
if __name__ == "__main__":
    asyncio.run(batch_blueprint_creation())
    asyncio.run(setup_game_objects())
```

---

## 🔗 LangChain 통합

### LangChain Tool 래퍼 구현

```python
# langchain_unreal_tools.py
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import asyncio
from unreal_mcp_client import UnrealBlueprintMCPClient

class CreateBlueprintInput(BaseModel):
    """Blueprint 생성 도구 입력 스키마"""
    blueprint_name: str = Field(description="블루프린트 이름")
    parent_class: str = Field(default="Actor", description="부모 클래스")
    asset_path: str = Field(default="/Game/Blueprints/", description="에셋 경로")

class CreateBlueprintTool(BaseTool):
    """LangChain용 Blueprint 생성 도구"""
    name = "create_unreal_blueprint"
    description = "Unreal Engine에서 새로운 블루프린트를 생성합니다"
    args_schema: Type[BaseModel] = CreateBlueprintInput

    def __init__(self):
        super().__init__()
        self.client = UnrealBlueprintMCPClient()

    def _run(
        self,
        blueprint_name: str,
        parent_class: str = "Actor",
        asset_path: str = "/Game/Blueprints/"
    ) -> str:
        """동기 실행 (LangChain 호환)"""
        async def _async_run():
            result = await self.client.create_blueprint(
                blueprint_name, parent_class, asset_path
            )
            return f"Blueprint '{blueprint_name}' created: {result.get('success')}"

        return asyncio.run(_async_run())

    async def _arun(
        self,
        blueprint_name: str,
        parent_class: str = "Actor",
        asset_path: str = "/Game/Blueprints/"
    ) -> str:
        """비동기 실행"""
        result = await self.client.create_blueprint(
            blueprint_name, parent_class, asset_path
        )
        return f"Blueprint '{blueprint_name}' created: {result.get('success')}"

class SetBlueprintPropertyInput(BaseModel):
    """Blueprint 속성 설정 도구 입력 스키마"""
    blueprint_path: str = Field(description="블루프린트 경로")
    property_name: str = Field(description="속성 이름")
    property_value: str = Field(description="속성 값")
    property_type: Optional[str] = Field(default=None, description="속성 타입")

class SetBlueprintPropertyTool(BaseTool):
    """LangChain용 Blueprint 속성 설정 도구"""
    name = "set_unreal_blueprint_property"
    description = "Unreal Engine 블루프린트의 속성을 설정합니다"
    args_schema: Type[BaseModel] = SetBlueprintPropertyInput

    def __init__(self):
        super().__init__()
        self.client = UnrealBlueprintMCPClient()

    def _run(
        self,
        blueprint_path: str,
        property_name: str,
        property_value: str,
        property_type: Optional[str] = None
    ) -> str:
        """동기 실행"""
        async def _async_run():
            result = await self.client.set_blueprint_property(
                blueprint_path, property_name, property_value, property_type
            )
            return f"Property '{property_name}' set: {result.get('success')}"

        return asyncio.run(_async_run())

# === LangChain Agent 사용 예제 ===

from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI  # 또는 다른 LLM
from langchain.memory import ConversationBufferMemory

def create_unreal_agent():
    """Unreal Engine 제어 가능한 LangChain Agent 생성"""

    # 도구 목록
    tools = [
        CreateBlueprintTool(),
        SetBlueprintPropertyTool()
    ]

    # LLM 초기화 (OpenAI GPT-4 사용 예시)
    llm = OpenAI(temperature=0, model_name="gpt-4")

    # 메모리 설정
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # Agent 초기화
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )

    return agent

# 사용 예제
if __name__ == "__main__":
    agent = create_unreal_agent()

    # 자연어로 블루프린트 생성 요청
    response = agent.run(
        "Create a Character blueprint named 'MainPlayer' and set its health to 150"
    )
    print(response)
```

---

## 🌐 REST API 클라이언트

### HTTP 프록시 서버 구현

```python
# http_proxy_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import uvicorn
from unreal_mcp_client import UnrealBlueprintMCPClient

app = FastAPI(title="UnrealBlueprintMCP HTTP API", version="1.0.0")

# 전역 MCP 클라이언트
mcp_client = UnrealBlueprintMCPClient()

# === Pydantic 모델 ===

class CreateBlueprintRequest(BaseModel):
    blueprint_name: str
    parent_class: str = "Actor"
    asset_path: str = "/Game/Blueprints/"

class SetPropertyRequest(BaseModel):
    blueprint_path: str
    property_name: str
    property_value: str
    property_type: Optional[str] = None

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# === API 엔드포인트 ===

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "UnrealBlueprintMCP HTTP API"}

@app.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록"""
    try:
        tools = await mcp_client.list_tools()
        return APIResponse(success=True, data={"tools": tools})
    except Exception as e:
        return APIResponse(success=False, error=str(e))

@app.post("/blueprints")
async def create_blueprint(request: CreateBlueprintRequest):
    """블루프린트 생성"""
    try:
        result = await mcp_client.create_blueprint(
            request.blueprint_name,
            request.parent_class,
            request.asset_path
        )
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/blueprints/properties")
async def set_blueprint_property(request: SetPropertyRequest):
    """블루프린트 속성 설정"""
    try:
        result = await mcp_client.set_blueprint_property(
            request.blueprint_path,
            request.property_name,
            request.property_value,
            request.property_type
        )
        return APIResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/server/status")
async def get_server_status():
    """MCP 서버 상태"""
    try:
        status = await mcp_client.get_server_status()
        return APIResponse(success=True, data=status)
    except Exception as e:
        return APIResponse(success=False, error=str(e))

@app.get("/blueprints/classes")
async def list_blueprint_classes():
    """지원되는 블루프린트 클래스"""
    try:
        classes = await mcp_client.list_supported_classes()
        return APIResponse(success=True, data={"classes": classes})
    except Exception as e:
        return APIResponse(success=False, error=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### HTTP 클라이언트 사용 예제

```python
# http_client_example.py
import requests
import json

class UnrealHTTPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_blueprint(self, name: str, parent_class: str = "Actor") -> dict:
        """HTTP를 통한 블루프린트 생성"""
        response = requests.post(f"{self.base_url}/blueprints", json={
            "blueprint_name": name,
            "parent_class": parent_class
        })
        response.raise_for_status()
        return response.json()

    def set_property(self, blueprint_path: str, prop_name: str, value: str) -> dict:
        """HTTP를 통한 속성 설정"""
        response = requests.put(f"{self.base_url}/blueprints/properties", json={
            "blueprint_path": blueprint_path,
            "property_name": prop_name,
            "property_value": value
        })
        response.raise_for_status()
        return response.json()

    def get_status(self) -> dict:
        """서버 상태 조회"""
        response = requests.get(f"{self.base_url}/server/status")
        response.raise_for_status()
        return response.json()

# 사용 예제
if __name__ == "__main__":
    client = UnrealHTTPClient()

    # 블루프린트 생성
    result = client.create_blueprint("HTTPTestActor")
    print(f"Created: {result}")

    # 속성 설정
    if result["success"]:
        blueprint_path = result["data"]["blueprint_path"]
        prop_result = client.set_property(blueprint_path, "Health", "75")
        print(f"Property set: {prop_result}")

    # 서버 상태
    status = client.get_status()
    print(f"Server status: {status}")
```

---

## 💻 웹 클라이언트 (JavaScript)

### HTML + JavaScript 인터페이스

```html
<!-- unreal_blueprint_web_client.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UnrealBlueprintMCP Web Client</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background: #007cba;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background: #005a8b;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .status {
            background: #e2e3e5;
            border: 1px solid #d6d8db;
            color: #383d41;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 UnrealBlueprintMCP Web Client</h1>

        <!-- 서버 연결 설정 -->
        <div class="form-group">
            <label for="serverUrl">MCP Server URL:</label>
            <input type="text" id="serverUrl" value="http://localhost:8000" placeholder="http://localhost:8000">
            <button onclick="testConnection()">연결 테스트</button>
        </div>

        <!-- 블루프린트 생성 -->
        <h2>블루프린트 생성</h2>
        <div class="form-group">
            <label for="blueprintName">블루프린트 이름:</label>
            <input type="text" id="blueprintName" placeholder="예: MyTestActor">
        </div>
        <div class="form-group">
            <label for="parentClass">부모 클래스:</label>
            <select id="parentClass">
                <option value="Actor">Actor</option>
                <option value="Pawn">Pawn</option>
                <option value="Character">Character</option>
                <option value="ActorComponent">ActorComponent</option>
                <option value="SceneComponent">SceneComponent</option>
                <option value="UserWidget">UserWidget</option>
                <option value="Object">Object</option>
            </select>
        </div>
        <div class="form-group">
            <label for="assetPath">에셋 경로:</label>
            <input type="text" id="assetPath" value="/Game/Blueprints/" placeholder="/Game/Blueprints/">
        </div>
        <button onclick="createBlueprint()">블루프린트 생성</button>

        <!-- 속성 설정 -->
        <h2>속성 설정</h2>
        <div class="form-group">
            <label for="blueprintPath">블루프린트 경로:</label>
            <input type="text" id="blueprintPath" placeholder="예: /Game/Blueprints/MyTestActor">
        </div>
        <div class="form-group">
            <label for="propertyName">속성 이름:</label>
            <input type="text" id="propertyName" placeholder="예: Health, RootComponent">
        </div>
        <div class="form-group">
            <label for="propertyValue">속성 값:</label>
            <input type="text" id="propertyValue" placeholder="예: 100, 1.5, true, Hello">
        </div>
        <div class="form-group">
            <label for="propertyType">속성 타입 (선택사항):</label>
            <select id="propertyType">
                <option value="">자동 감지</option>
                <option value="int">int</option>
                <option value="float">float</option>
                <option value="bool">bool</option>
                <option value="string">string</option>
                <option value="Vector">Vector</option>
                <option value="Rotator">Rotator</option>
            </select>
        </div>
        <button onclick="setProperty()">속성 설정</button>

        <!-- 결과 표시 -->
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        const API_BASE = () => document.getElementById('serverUrl').value;

        // 결과 표시 함수
        function showResult(data, type = 'status') {
            const resultDiv = document.getElementById('result');
            resultDiv.className = `result ${type}`;
            resultDiv.textContent = JSON.stringify(data, null, 2);
            resultDiv.style.display = 'block';
        }

        // 연결 테스트
        async function testConnection() {
            try {
                const response = await fetch(`${API_BASE()}/health`);
                const data = await response.json();
                showResult(data, 'success');
            } catch (error) {
                showResult({error: error.message}, 'error');
            }
        }

        // 블루프린트 생성
        async function createBlueprint() {
            const name = document.getElementById('blueprintName').value;
            const parentClass = document.getElementById('parentClass').value;
            const assetPath = document.getElementById('assetPath').value;

            if (!name) {
                alert('블루프린트 이름을 입력해주세요.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE()}/blueprints`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        blueprint_name: name,
                        parent_class: parentClass,
                        asset_path: assetPath
                    })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    showResult(data, 'success');
                    // 생성된 블루프린트 경로를 속성 설정 필드에 자동 입력
                    if (data.data && data.data.blueprint_path) {
                        document.getElementById('blueprintPath').value = data.data.blueprint_path;
                    }
                } else {
                    showResult(data, 'error');
                }
            } catch (error) {
                showResult({error: error.message}, 'error');
            }
        }

        // 속성 설정
        async function setProperty() {
            const blueprintPath = document.getElementById('blueprintPath').value;
            const propertyName = document.getElementById('propertyName').value;
            const propertyValue = document.getElementById('propertyValue').value;
            const propertyType = document.getElementById('propertyType').value;

            if (!blueprintPath || !propertyName || !propertyValue) {
                alert('모든 필수 필드를 입력해주세요.');
                return;
            }

            try {
                const requestBody = {
                    blueprint_path: blueprintPath,
                    property_name: propertyName,
                    property_value: propertyValue
                };

                if (propertyType) {
                    requestBody.property_type = propertyType;
                }

                const response = await fetch(`${API_BASE()}/blueprints/properties`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    showResult(data, 'success');
                } else {
                    showResult(data, 'error');
                }
            } catch (error) {
                showResult({error: error.message}, 'error');
            }
        }

        // 페이지 로드 시 연결 테스트
        window.onload = function() {
            testConnection();
        };
    </script>
</body>
</html>
```

---

## 🔧 문제 해결

### 일반적인 연결 문제

#### 1. Claude Code에서 "Server not found" 오류

```bash
# 문제: MCP 서버를 찾을 수 없음
# 해결방법:

# 1. 경로 확인
pwd  # 현재 경로 확인
which fastmcp  # fastmcp 실행 파일 위치 확인

# 2. 절대 경로로 설정 파일 수정
{
  "servers": {
    "unreal_blueprint": {
      "command": "/absolute/path/to/mcp_server_env/bin/fastmcp",
      "args": ["run", "/absolute/path/to/unreal_blueprint_mcp_server.py"]
    }
  }
}

# 3. 환경 변수 설정 확인
export PATH="/path/to/mcp_server_env/bin:$PATH"
```

#### 2. WebSocket 연결 실패

```python
# 문제: ConnectionRefusedError
# 해결방법:

# 1. MCP 서버가 실행 중인지 확인
# 터미널에서:
fastmcp dev unreal_blueprint_mcp_server.py

# 2. 포트 충돌 확인
# Linux/macOS:
lsof -i :6277
# Windows:
netstat -an | findstr 6277

# 3. 방화벽 설정 확인 (Windows)
# Windows Defender 방화벽에서 포트 6277 허용
```

#### 3. 인증 토큰 오류

```bash
# 문제: MCP Inspector 접속 시 인증 실패
# 해결방법:

# 1. 새 토큰 확인
# MCP 서버 실행 로그에서 새로운 토큰 복사
🔑 Session token: abc123...

# 2. 브라우저 캐시 클리어 후 새 URL로 접속
http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<새_토큰>

# 3. 인증 비활성화 (개발 환경에서만)
export DANGEROUSLY_OMIT_AUTH=true
fastmcp dev unreal_blueprint_mcp_server.py
```

### 클라이언트별 디버깅

#### Python 클라이언트 디버깅

```python
# 디버깅 로그 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# WebSocket 연결 테스트
import websockets
import asyncio

async def test_connection():
    try:
        async with websockets.connect("ws://localhost:6277") as ws:
            print("✅ Connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test_connection())
```

#### HTTP 클라이언트 디버깅

```bash
# cURL을 사용한 직접 테스트
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/server/status

# 블루프린트 생성 테스트
curl -X POST http://localhost:8000/blueprints \
  -H "Content-Type: application/json" \
  -d '{"blueprint_name": "TestActor", "parent_class": "Actor"}'
```

### 성능 최적화

#### 연결 풀링

```python
# 여러 요청을 위한 연결 재사용
import asyncio
import websockets

class PooledMCPClient:
    def __init__(self, server_url: str, pool_size: int = 5):
        self.server_url = server_url
        self.pool_size = pool_size
        self._pool = asyncio.Queue(maxsize=pool_size)
        self._initialized = False

    async def _init_pool(self):
        """연결 풀 초기화"""
        if self._initialized:
            return

        for _ in range(self.pool_size):
            conn = await websockets.connect(self.server_url)
            await self._pool.put(conn)

        self._initialized = True

    async def execute(self, request: dict):
        """풀링된 연결로 요청 실행"""
        await self._init_pool()

        conn = await self._pool.get()
        try:
            await conn.send(json.dumps(request))
            response = await conn.recv()
            return json.loads(response)
        finally:
            await self._pool.put(conn)
```

---

## 📚 추가 리소스

### 예제 프로젝트
- `examples/python_client/`: Python 클라이언트 예제
- `examples/langchain_integration/`: LangChain 통합 예제
- `examples/web_client/`: 웹 클라이언트 예제
- `examples/batch_operations/`: 배치 작업 예제

### 커뮤니티 클라이언트
- **Rust 클라이언트**: [unreal-mcp-rust](https://github.com/community/unreal-mcp-rust)
- **Go 클라이언트**: [unreal-mcp-go](https://github.com/community/unreal-mcp-go)
- **C# 클라이언트**: [unreal-mcp-csharp](https://github.com/community/unreal-mcp-csharp)

### 디버깅 도구
- **MCP Inspector**: 웹 기반 디버깅 인터페이스
- **Postman Collection**: REST API 테스트용 컬렉션
- **WebSocket Test Tool**: 실시간 WebSocket 테스트

---

**🎮 Happy Coding with UnrealBlueprintMCP! 🚀**