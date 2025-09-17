# UnrealBlueprintMCP API Reference

> **Version**: 1.0.0
> **Protocol**: JSON-RPC 2.0 via WebSocket
> **Standard**: Model Context Protocol (MCP)

## 📋 목차

1. [개요](#개요)
2. [연결 및 인증](#연결-및-인증)
3. [MCP 도구 목록](#mcp-도구-목록)
4. [요청/응답 형식](#요청응답-형식)
5. [오류 처리](#오류-처리)
6. [데이터 타입](#데이터-타입)
7. [사용 예제](#사용-예제)

---

## 🔍 개요

UnrealBlueprintMCP는 Model Context Protocol을 통해 6개의 핵심 도구를 제공합니다. 모든 통신은 JSON-RPC 2.0 프로토콜을 사용하며, WebSocket을 통해 실시간 양방향 통신을 지원합니다.

### 기본 정보
- **서버 주소**: `ws://localhost:6277` (프록시 서버)
- **프로토콜**: WebSocket + JSON-RPC 2.0
- **인증**: 세션 토큰 기반
- **문자 인코딩**: UTF-8

---

## 🔐 연결 및 인증

### WebSocket 연결

```javascript
// JavaScript 예시
const ws = new WebSocket('ws://localhost:6277');

// 인증이 필요한 경우
const ws = new WebSocket('ws://localhost:6277', {
  headers: {
    'Authorization': 'Bearer YOUR_SESSION_TOKEN'
  }
});
```

### 세션 토큰

MCP 서버 시작 시 생성되는 토큰을 사용합니다:

```bash
# 서버 시작 시 출력되는 토큰
🔑 Session token: 98378ccaa878e45b8c80b02f6ffb1e3277cef595707a0464d54a79fd04c90d41
```

---

## 🛠️ MCP 도구 목록

### 1. create_blueprint

새로운 블루프린트 에셋을 생성합니다.

#### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "method": "tools/call",
  "params": {
    "name": "create_blueprint",
    "arguments": {
      "blueprint_name": "string",
      "parent_class": "string",
      "asset_path": "string"
    }
  }
}
```

#### 매개변수

| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `blueprint_name` | string | ✅ | - | 생성할 블루프린트의 이름 |
| `parent_class` | string | ❌ | "Actor" | 부모 클래스 (Actor, Pawn, Character 등) |
| `asset_path` | string | ❌ | "/Game/Blueprints/" | 블루프린트를 생성할 경로 |

#### 지원되는 부모 클래스
- `Actor` - 기본 게임 오브젝트
- `Pawn` - 제어 가능한 엔티티
- `Character` - 플레이어/NPC 캐릭터
- `ActorComponent` - 재사용 가능한 컴포넌트
- `SceneComponent` - 변환 기반 컴포넌트
- `UserWidget` - UI 위젯 클래스
- `Object` - 기본 UObject 클래스

#### 응답 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "result": {
    "success": true,
    "message": "Blueprint 'TestActor' creation requested",
    "blueprint_path": "/Game/Blueprints/TestActor",
    "parent_class": "Actor",
    "unreal_response": {
      "success": true,
      "message": "Command 'create_blueprint' executed successfully",
      "timestamp": "2025-09-17T03:45:00.000Z"
    }
  }
}
```

#### 오류 응답
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "result": {
    "success": false,
    "error": "Invalid parent class: NonExistentClass",
    "message": "Failed to create blueprint 'TestActor'"
  }
}
```

---

### 2. set_blueprint_property

기존 블루프린트의 CDO(Class Default Object) 속성을 수정합니다.

#### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_002",
  "method": "tools/call",
  "params": {
    "name": "set_blueprint_property",
    "arguments": {
      "blueprint_path": "string",
      "property_name": "string",
      "property_value": "string",
      "property_type": "string"
    }
  }
}
```

#### 매개변수

| 매개변수 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `blueprint_path` | string | ✅ | 블루프린트의 전체 에셋 경로 |
| `property_name` | string | ✅ | 수정할 속성의 이름 |
| `property_value` | string | ✅ | 새로운 속성 값 (문자열로 표현) |
| `property_type` | string | ❌ | 속성 타입 힌트 (자동 감지 시 생략 가능) |

#### 지원되는 속성 타입

| 타입 | 형식 예시 | 설명 |
|------|----------|------|
| `int` | `"100"` | 32비트 정수 |
| `float` | `"3.14"` | 단정밀도 실수 |
| `bool` | `"true"` or `"false"` | 불린 값 |
| `string` | `"Hello World"` | 문자열 |
| `Vector` | `"100.0,200.0,300.0"` | 3D 벡터 (X,Y,Z) |
| `Rotator` | `"0.0,90.0,0.0"` | 3D 회전 (Pitch,Yaw,Roll) |

#### 응답 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_002",
  "result": {
    "success": true,
    "message": "Property 'Health' modification requested",
    "blueprint_path": "/Game/Blueprints/TestActor",
    "property_name": "Health",
    "property_value": "100",
    "property_type": "int",
    "unreal_response": {
      "success": true,
      "message": "Command 'set_property' executed successfully"
    }
  }
}
```

---

### 3. get_server_status

MCP 서버의 현재 상태와 연결 정보를 조회합니다.

#### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_003",
  "method": "tools/call",
  "params": {
    "name": "get_server_status",
    "arguments": {}
  }
}
```

#### 응답 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_003",
  "result": {
    "server_name": "UnrealBlueprintMCPServer",
    "version": "1.0.0",
    "connection_status": "simulated_success",
    "unreal_websocket_url": "ws://localhost:8080",
    "last_connection_attempt": "2025-09-17T03:45:00.000Z",
    "timestamp": "2025-09-17T03:45:30.000Z",
    "available_tools": [
      "create_blueprint",
      "set_blueprint_property",
      "list_supported_blueprint_classes",
      "create_test_actor_blueprint"
    ]
  }
}
```

---

### 4. list_supported_blueprint_classes

지원되는 블루프린트 부모 클래스 목록을 반환합니다.

#### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_004",
  "method": "tools/call",
  "params": {
    "name": "list_supported_blueprint_classes",
    "arguments": {}
  }
}
```

#### 응답 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_004",
  "result": [
    "Actor",
    "Pawn",
    "Character",
    "ActorComponent",
    "SceneComponent",
    "UserWidget",
    "Object"
  ]
}
```

---

### 5. create_test_actor_blueprint

테스트용 Actor 블루프린트를 빠르게 생성하고 초기 위치를 설정합니다.

#### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_005",
  "method": "tools/call",
  "params": {
    "name": "create_test_actor_blueprint",
    "arguments": {
      "blueprint_name": "string",
      "location": {
        "x": 0.0,
        "y": 0.0,
        "z": 100.0
      }
    }
  }
}
```

#### 매개변수

| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `blueprint_name` | string | ❌ | "TestActor" | 테스트 블루프린트 이름 |
| `location` | Vector3D | ❌ | `{x:0, y:0, z:100}` | 초기 월드 위치 |

#### 응답 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_005",
  "result": {
    "success": true,
    "message": "Test actor blueprint 'MyTestActor' created successfully with location {100.0, 200.0, 300.0}",
    "blueprint_creation": {
      "success": true,
      "blueprint_path": "/Game/Blueprints/MyTestActor"
    },
    "property_setting": {
      "success": true,
      "property_name": "RootComponent"
    },
    "final_blueprint_path": "/Game/Blueprints/MyTestActor",
    "location": {
      "x": 100.0,
      "y": 200.0,
      "z": 300.0
    }
  }
}
```

---

### 6. test_unreal_connection

Unreal Engine과의 WebSocket 연결 상태를 테스트합니다.

#### 요청 형식
```json
{
  "jsonrpc": "2.0",
  "id": "req_006",
  "method": "tools/call",
  "params": {
    "name": "test_unreal_connection",
    "arguments": {}
  }
}
```

#### 응답 형식 (성공)
```json
{
  "jsonrpc": "2.0",
  "id": "req_006",
  "result": {
    "success": true,
    "message": "Connection test completed",
    "response_time_seconds": 0.123,
    "unreal_response": {
      "success": true,
      "message": "Command 'ping' executed successfully"
    },
    "connection_status": "simulated_success"
  }
}
```

#### 응답 형식 (실패)
```json
{
  "jsonrpc": "2.0",
  "id": "req_006",
  "result": {
    "success": false,
    "error": "Connection timeout",
    "message": "Failed to connect to Unreal Engine"
  }
}
```

---

## 📨 요청/응답 형식

### 기본 요청 구조

모든 MCP 도구 호출은 다음 형식을 따릅니다:

```json
{
  "jsonrpc": "2.0",
  "id": "unique_request_id",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

### 기본 응답 구조

```json
{
  "jsonrpc": "2.0",
  "id": "unique_request_id",
  "result": {
    // 도구별 응답 데이터
  }
}
```

### 오류 응답 구조

```json
{
  "jsonrpc": "2.0",
  "id": "unique_request_id",
  "error": {
    "code": -32000,
    "message": "Tool execution failed",
    "data": {
      "tool_name": "create_blueprint",
      "error_details": "Invalid blueprint name"
    }
  }
}
```

---

## ❌ 오류 처리

### 표준 JSON-RPC 오류 코드

| 코드 | 이름 | 설명 |
|------|------|------|
| -32700 | Parse error | JSON 파싱 오류 |
| -32600 | Invalid Request | 잘못된 요청 형식 |
| -32601 | Method not found | 존재하지 않는 메서드 |
| -32602 | Invalid params | 잘못된 매개변수 |
| -32603 | Internal error | 내부 서버 오류 |

### UnrealBlueprintMCP 특정 오류

| 코드 | 설명 | 해결 방법 |
|------|------|----------|
| -32000 | Tool execution failed | 도구 실행 중 오류 발생 |
| -32001 | Blueprint creation failed | 블루프린트 생성 실패 |
| -32002 | Property setting failed | 속성 설정 실패 |
| -32003 | Unreal connection failed | Unreal Engine 연결 실패 |
| -32004 | Invalid blueprint path | 잘못된 블루프린트 경로 |
| -32005 | Unsupported property type | 지원되지 않는 속성 타입 |

### 오류 응답 예시

```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "error": {
    "code": -32001,
    "message": "Blueprint creation failed",
    "data": {
      "tool_name": "create_blueprint",
      "blueprint_name": "Invalid@Name",
      "error_details": "Blueprint name contains invalid characters"
    }
  }
}
```

---

## 🔢 데이터 타입

### Vector3D

3차원 벡터를 나타내는 구조체:

```json
{
  "x": 100.0,
  "y": 200.0,
  "z": 300.0
}
```

**문자열 형식**: `"100.0,200.0,300.0"`

### BlueprintCreateParams

블루프린트 생성을 위한 매개변수:

```json
{
  "blueprint_name": "MyActor",
  "parent_class": "Actor",
  "asset_path": "/Game/Blueprints/"
}
```

### BlueprintPropertyParams

블루프린트 속성 설정을 위한 매개변수:

```json
{
  "blueprint_path": "/Game/Blueprints/MyActor",
  "property_name": "Health",
  "property_value": "100",
  "property_type": "int"
}
```

---

## 💡 사용 예제

### 예제 1: 기본 블루프린트 생성

```javascript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:6277');

// 블루프린트 생성 요청
const createRequest = {
  "jsonrpc": "2.0",
  "id": "bp_create_001",
  "method": "tools/call",
  "params": {
    "name": "create_blueprint",
    "arguments": {
      "blueprint_name": "PlayerCharacter",
      "parent_class": "Character",
      "asset_path": "/Game/Characters/"
    }
  }
};

ws.send(JSON.stringify(createRequest));

// 응답 처리
ws.onmessage = function(event) {
  const response = JSON.parse(event.data);
  if (response.id === "bp_create_001") {
    if (response.result.success) {
      console.log("블루프린트 생성 성공:", response.result.blueprint_path);
    } else {
      console.error("블루프린트 생성 실패:", response.result.error);
    }
  }
};
```

### 예제 2: 속성 설정 체인

```python
import asyncio
import websockets
import json

async def setup_character():
    uri = "ws://localhost:6277"

    async with websockets.connect(uri) as websocket:
        # 1. 캐릭터 블루프린트 생성
        create_msg = {
            "jsonrpc": "2.0",
            "id": "create_char",
            "method": "tools/call",
            "params": {
                "name": "create_blueprint",
                "arguments": {
                    "blueprint_name": "GameCharacter",
                    "parent_class": "Character"
                }
            }
        }

        await websocket.send(json.dumps(create_msg))
        response = await websocket.recv()
        result = json.loads(response)

        if result["result"]["success"]:
            blueprint_path = result["result"]["blueprint_path"]

            # 2. 체력 설정
            health_msg = {
                "jsonrpc": "2.0",
                "id": "set_health",
                "method": "tools/call",
                "params": {
                    "name": "set_blueprint_property",
                    "arguments": {
                        "blueprint_path": blueprint_path,
                        "property_name": "Health",
                        "property_value": "100",
                        "property_type": "int"
                    }
                }
            }

            await websocket.send(json.dumps(health_msg))
            health_response = await websocket.recv()

            # 3. 이동 속도 설정
            speed_msg = {
                "jsonrpc": "2.0",
                "id": "set_speed",
                "method": "tools/call",
                "params": {
                    "name": "set_blueprint_property",
                    "arguments": {
                        "blueprint_path": blueprint_path,
                        "property_name": "MovementSpeed",
                        "property_value": "600.0",
                        "property_type": "float"
                    }
                }
            }

            await websocket.send(json.dumps(speed_msg))
            speed_response = await websocket.recv()

            print("캐릭터 설정 완료!")

# 실행
asyncio.run(setup_character())
```

### 예제 3: 배치 생성

```python
async def create_game_objects():
    """게임 오브젝트들을 배치로 생성"""

    objects_to_create = [
        {"name": "Player", "class": "Character", "path": "/Game/Characters/"},
        {"name": "Enemy", "class": "Pawn", "path": "/Game/Enemies/"},
        {"name": "Weapon", "class": "Actor", "path": "/Game/Weapons/"},
        {"name": "PowerUp", "class": "Actor", "path": "/Game/Items/"},
        {"name": "MainMenu", "class": "UserWidget", "path": "/Game/UI/"}
    ]

    uri = "ws://localhost:6277"
    async with websockets.connect(uri) as websocket:

        for i, obj in enumerate(objects_to_create):
            request = {
                "jsonrpc": "2.0",
                "id": f"batch_create_{i}",
                "method": "tools/call",
                "params": {
                    "name": "create_blueprint",
                    "arguments": {
                        "blueprint_name": obj["name"],
                        "parent_class": obj["class"],
                        "asset_path": obj["path"]
                    }
                }
            }

            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            result = json.loads(response)

            if result["result"]["success"]:
                print(f"✅ {obj['name']} 생성 완료")
            else:
                print(f"❌ {obj['name']} 생성 실패: {result['result'].get('error')}")

asyncio.run(create_game_objects())
```

---

## 🔄 비동기 처리

### 여러 요청 동시 처리

```python
import asyncio
import websockets
import json

async def concurrent_operations():
    """여러 작업을 동시에 실행"""

    uri = "ws://localhost:6277"

    async def create_blueprint(name, parent_class):
        async with websockets.connect(uri) as ws:
            request = {
                "jsonrpc": "2.0",
                "id": f"create_{name}",
                "method": "tools/call",
                "params": {
                    "name": "create_blueprint",
                    "arguments": {
                        "blueprint_name": name,
                        "parent_class": parent_class
                    }
                }
            }
            await ws.send(json.dumps(request))
            response = await ws.recv()
            return json.loads(response)

    # 동시 실행
    tasks = [
        create_blueprint("Actor1", "Actor"),
        create_blueprint("Actor2", "Actor"),
        create_blueprint("Player", "Character"),
        create_blueprint("Enemy", "Pawn")
    ]

    results = await asyncio.gather(*tasks)

    for result in results:
        blueprint_name = result["result"].get("blueprint_path", "Unknown")
        success = result["result"].get("success", False)
        print(f"{'✅' if success else '❌'} {blueprint_name}")

asyncio.run(concurrent_operations())
```

---

## 📚 SDK 및 래퍼

### Python SDK

```python
# SDK를 통한 간편한 사용
from unreal_blueprint_sdk import UnrealBlueprintClient

client = UnrealBlueprintClient()

# 블루프린트 생성
await client.create_blueprint("MyActor", "Actor")

# 속성 설정
await client.set_property("MyActor", "Health", 100)
```

### TypeScript/JavaScript SDK

```typescript
import { UnrealBlueprintClient } from 'unreal-blueprint-mcp-client';

const client = new UnrealBlueprintClient('ws://localhost:6277');

// 블루프린트 생성
const result = await client.createBlueprint({
  blueprintName: 'MyActor',
  parentClass: 'Actor'
});

// 속성 설정
await client.setProperty({
  blueprintPath: result.blueprintPath,
  propertyName: 'Health',
  propertyValue: '100',
  propertyType: 'int'
});
```

---

**📚 이 API 레퍼런스는 UnrealBlueprintMCP v1.0.0 기준으로 작성되었습니다.**

**🔄 최신 정보는 [GitHub Repository](https://github.com/yourusername/unreal-blueprint-mcp)에서 확인하세요.**