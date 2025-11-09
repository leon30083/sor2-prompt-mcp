import json
from typing import Dict
from .sora2_agent import generate_sora2_instructions, to_json, detect_mode, summarize_text


def generate(payload: Dict) -> Dict:
    """
    MCP 工具入口：/sora2/agent.generate

    参数:
    - payload: { "text": str, "default_seconds": str, "narration_limit": str|int, "mode": str }

    返回:
    - { "shots": List[Dict] }
    """
    text = payload.get("text", "")
    default_seconds = payload.get("default_seconds", "4")
    narration_limit = payload.get("narration_limit", 3)
    mode = str(payload.get("mode", "auto")).lower()
    try:
        narration_limit = int(narration_limit)
    except Exception:
        narration_limit = 3
    if not isinstance(text, str) or not text.strip():
        return {"error": {"code": "INVALID_INPUT", "message": "text 不能为空"}}
    chosen_mode = "narration" if mode == "narration" else detect_mode(text)
    shots = generate_sora2_instructions(text, default_seconds, narration_limit, mode)
    summary = summarize_text(text)
    return {
        "shots": shots,
        "meta": {
            "chosen_mode": chosen_mode,
            "shots_count": len(shots),
            "parse_summary": summary
        }
    }


if __name__ == "__main__":
    # 简易命令行测试：python -m src.mcp_tool '{"text": "李四说：“到这边！”"}'
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else '{"text": "王强压低声音说：“别出声。”"}'
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"text": raw}
    print(json.dumps(generate(payload), ensure_ascii=False, indent=2))