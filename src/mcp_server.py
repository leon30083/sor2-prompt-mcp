import json
import sys
import uuid
from typing import Any, Dict, List
from .mcp_tool import generate as tool_generate
from .version import SERVER_NAME, SERVER_VERSION

# JSON-RPC 2.0 错误码映射
ERROR_CODES = {
    "BAD_JSON": -32700,      # Parse error
    "BAD_REQUEST": -32600,   # Invalid Request
    "NOT_FOUND": -32601,     # Method not found
    "SCHEMA_ERROR": -32602,  # Invalid params
    "INVALID_INPUT": -32000  # Application-defined
}

# 初始化状态标记（遵循 MCP 生命周期：初始化前仅允许 ping）
IS_INITIALIZED = False


def list_tools_ndjson() -> Dict[str, Any]:
    """旧版 NDJSON 列表，兼容本地管道测试"""
    return {
        "tools": [
            {
                "id": "/sora2/agent.generate",
                "description": "根据中文剧本文本生成 Sora2 指令（shots 数组）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "default_seconds": {"type": "string"},
                        "narration_limit": {"type": "string"}
                    },
                    "required": ["text"]
                }
            }
        ]
    }


def tools_list() -> Dict[str, Any]:
    """MCP 规范：tools/list 响应结构"""
    return {
        "tools": [
            {
                "name": "sora2.agent.generate",
                "title": "Sora2 指令生成",
                "description": "将中文剧本文本解析为 shots JSON",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "中文剧本文本"},
                        "default_seconds": {"type": "string", "description": "每镜头默认时长，字符串"},
                        "narration_limit": {"type": "string", "description": "无对话时旁白镜头数量上限，默认 3"}
                    },
                    "required": ["text"]
                }
            }
        ],
        # 说明：兼容严格校验客户端，返回空字符串表示“无后续分页”
        "nextCursor": ""
    }


def get_manifest() -> Dict[str, Any]:
    """返回服务器清单与工具能力说明"""
    tools = list_tools_ndjson()["tools"]
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "description": "MCP stdin/stdout (NDJSON) 服务器，提供 /sora2/agent.generate",
        "tools": tools,
        "errors": {
            "NOT_FOUND": "未知工具",
            "BAD_JSON": "JSON 解析失败",
            "BAD_REQUEST": "请求格式错误",
            "SCHEMA_ERROR": "输入结构不符合要求",
            "INVALID_INPUT": "输入校验失败"
        }
    }


def initialize() -> Dict[str, Any]:
    """初始化会话，返回基本能力与会话ID"""
    global IS_INITIALIZED
    IS_INITIALIZED = True
    return {
        # MCP / Trae 期望字段
        "protocolVersion": "2024-11-05",
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "capabilities": {
            "tools": {"listChanged": False}
        },
        # 保留原有字段，增强兼容
        "session_id": str(uuid.uuid4()),
        "server": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "defaults": {"seconds": "4", "language": "zh-CN"},
        "features": {"os_keywords": True, "vo_keywords": True}
    }


def version() -> Dict[str, Any]:
    return {"name": SERVER_NAME, "version": SERVER_VERSION}


def ping() -> Dict[str, Any]:
    return {"ok": True}


def handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """NDJSON 自定义协议处理：{'tool': str, 'input': object}
    返回 {'ok': bool, 'data'?: object, 'error'?: {code: str, message: str}}
    """
    tool = req.get("tool")
    payload = req.get("input", {})
    if tool == "/sora2/agent.generate":
        if not isinstance(payload, dict):
            return {"ok": False, "error": {"code": "SCHEMA_ERROR", "message": "input 必须为对象"}}
        if "text" not in payload:
            return {"ok": False, "error": {"code": "SCHEMA_ERROR", "message": "缺少必填字段: text"}}
        res = tool_generate(payload)
        if isinstance(res, dict) and "error" in res:
            return {"ok": False, "error": res["error"]}
        return {"ok": True, "data": res}
    elif tool == "list_tools":
        return {"ok": True, "data": list_tools_ndjson()}
    elif tool == "get_manifest":
        return {"ok": True, "data": get_manifest()}
    elif tool == "initialize":
        return {"ok": True, "data": initialize()}
    elif tool == "version":
        return {"ok": True, "data": version()}
    elif tool == "ping":
        return {"ok": True, "data": ping()}
    return {"ok": False, "error": {"code": "NOT_FOUND", "message": f"未知工具: {tool}"}}


def to_jsonrpc_success(id_val, result_obj):
    return {"jsonrpc": "2.0", "id": id_val, "result": result_obj}


def to_jsonrpc_error(id_val, code_num, message, data=None):
    err = {"code": code_num, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_val, "error": err}


def handle_jsonrpc(req: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-RPC 2.0 处理：{jsonrpc:"2.0", id, method, params}
    返回标准 JSON-RPC 响应。
    """
    id_val = req.get("id")
    method = req.get("method")
    params = req.get("params", {})
    # 基本校验
    if req.get("jsonrpc") != "2.0":
        return to_jsonrpc_error(id_val, ERROR_CODES["BAD_REQUEST"], "jsonrpc 必须为 '2.0'")
    if method is None:
        return to_jsonrpc_error(id_val, ERROR_CODES["BAD_REQUEST"], "缺少 method")

    try:
        # 初始化与生命周期
        if method == "initialize":
            return to_jsonrpc_success(id_val, initialize())
        if method == "notifications/initialized":
            # 作为通知，无需响应；为兼容简单返回 success
            global IS_INITIALIZED
            IS_INITIALIZED = True
            return to_jsonrpc_success(id_val, {"ok": True})

        # 初始化前仅允许 ping
        if not IS_INITIALIZED and method != "ping":
            return to_jsonrpc_error(id_val, ERROR_CODES["BAD_REQUEST"], "未初始化：仅允许 ping 与 initialize")

        # 基础信息
        if method == "get_manifest":
            return to_jsonrpc_success(id_val, get_manifest())
        if method == "version":
            return to_jsonrpc_success(id_val, version())
        if method == "ping":
            return to_jsonrpc_success(id_val, ping())

        # MCP 规范方法：tools/list
        if method == "tools/list":
            return to_jsonrpc_success(id_val, tools_list())

        # MCP 规范方法：tools/call
        if method == "tools/call":
            if not isinstance(params, dict):
                return to_jsonrpc_error(id_val, ERROR_CODES["SCHEMA_ERROR"], "params 必须为对象")
            name = params.get("name")
            arguments = params.get("arguments", {})
            if name == "sora2.agent.generate":
                if not isinstance(arguments, dict):
                    return to_jsonrpc_error(id_val, ERROR_CODES["SCHEMA_ERROR"], "arguments 必须为对象")
                if "text" not in arguments:
                    return to_jsonrpc_error(id_val, ERROR_CODES["SCHEMA_ERROR"], "缺少必填字段: text")
                res = tool_generate(arguments)
                if isinstance(res, dict) and "error" in res:
                    err = res["error"]
                    code = ERROR_CODES.get(err.get("code"), ERROR_CODES["BAD_REQUEST"]) if isinstance(err, dict) else ERROR_CODES["BAD_REQUEST"]
                    msg = err.get("message", "工具执行错误") if isinstance(err, dict) else str(err)
                    return to_jsonrpc_success(id_val, {"content": [{"type": "text", "text": msg}], "isError": True})
                # 将结构化结果以文本形式返回，兼容 MCP content
                text_out = json.dumps(res, ensure_ascii=False)
                return to_jsonrpc_success(id_val, {"content": [{"type": "text", "text": text_out}], "isError": False})

        # 兼容旧法：直接调用方法名
        if method == "/sora2/agent.generate":
            payload = params if isinstance(params, dict) else {}
            if not isinstance(payload, dict):
                return to_jsonrpc_error(id_val, ERROR_CODES["SCHEMA_ERROR"], "params 必须为对象")
            if "text" not in payload:
                return to_jsonrpc_error(id_val, ERROR_CODES["SCHEMA_ERROR"], "缺少必填字段: text")
            res = tool_generate(payload)
            if isinstance(res, dict) and "error" in res:
                err = res["error"]
                code = ERROR_CODES.get(err.get("code"), ERROR_CODES["BAD_REQUEST"]) if isinstance(err, dict) else ERROR_CODES["BAD_REQUEST"]
                msg = err.get("message", "工具执行错误") if isinstance(err, dict) else str(err)
                return to_jsonrpc_error(id_val, code, msg)
            return to_jsonrpc_success(id_val, res)

        # 未知方法
        return to_jsonrpc_error(id_val, ERROR_CODES["NOT_FOUND"], f"未知方法: {method}")
    except Exception as e:
        return to_jsonrpc_error(id_val, ERROR_CODES["BAD_REQUEST"], str(e))


if __name__ == "__main__":
    # 支持两种输入：
    # 1) NDJSON 自定义：{"tool":"list_tools"}
    # 2) JSON-RPC 2.0：{"jsonrpc":"2.0","id":1,"method":"list_tools","params":{}}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            # JSON-RPC 规范：Parse error -32700
            resp = to_jsonrpc_error(None, ERROR_CODES["BAD_JSON"], str(e))
        else:
            # 路由到 JSON-RPC 或 NDJSON
            if isinstance(req, dict) and req.get("jsonrpc") == "2.0":
                resp = handle_jsonrpc(req)
            else:
                try:
                    nd = handle_request(req)
                    # 将 NDJSON 响应包装为 JSON-RPC 风格（无 id 的通知）以兼容 Trae
                    if nd.get("ok"):
                        resp = to_jsonrpc_success(None, nd.get("data"))
                    else:
                        err = nd.get("error", {})
                        code = ERROR_CODES.get(err.get("code"), ERROR_CODES["BAD_REQUEST"]) if isinstance(err, dict) else ERROR_CODES["BAD_REQUEST"]
                        msg = err.get("message", "错误") if isinstance(err, dict) else str(err)
                        resp = to_jsonrpc_error(None, code, msg)
                except Exception as e:
                    resp = to_jsonrpc_error(None, ERROR_CODES["BAD_REQUEST"], str(e))
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()