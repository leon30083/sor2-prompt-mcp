"""
LLM 并列工具调用与标签注入测试模板

使用说明：
- 该模板示例演示直接调用工具层（src.mcp_tool.tool_generate）进行检测；
- 你也可以改为通过 JSON-RPC 或 NDJSON 发送请求并断言返回；
"""

import json
from typing import Dict

try:
    from src.mcp_tool import generate as tool_generate
except Exception:
    # 兼容非包结构的导入
    from mcp_tool import generate as tool_generate


def inject_stitch_tags(meta: Dict) -> Dict:
    """按 docs/LLM_INSTRUCTION.md 的规范计算标签。"""
    parse = meta.get("parse_summary") or {}
    total = parse.get("total_sentences") or 0
    dialogue_count = parse.get("dialogue_count") or 0
    narration_count = parse.get("narration_count") or 0
    chosen = meta.get("chosen_mode") or "dialogue"

    def norm(x, t):
        if not t:
            return 0
        return round((x / t) * 100)

    tags = {
        "audio_type": "voice_over" if chosen == "narration" else "dialogue",
        "vo_priority": norm(narration_count, total),
        "dialogue_priority": norm(dialogue_count, total),
    }
    return tags


def test_auto_dialogue_case():
    payload = {"text": "张三说：“快跑！”", "mode": "auto", "default_seconds": "3"}
    res = tool_generate(payload)
    assert "meta" in res and isinstance(res["meta"], dict)
    meta = res["meta"]
    assert meta.get("chosen_mode") == "dialogue"
    tags = inject_stitch_tags(meta)
    assert tags["audio_type"] == "dialogue"
    assert tags["dialogue_priority"] >= 50


def test_narration_case():
    payload = {"text": "雨夜里，路灯残影在水面摇晃。", "mode": "narration", "narration_limit": "3"}
    res = tool_generate(payload)
    assert "meta" in res and isinstance(res["meta"], dict)
    meta = res["meta"]
    assert meta.get("chosen_mode") == "narration"
    tags = inject_stitch_tags(meta)
    assert tags["audio_type"] == "voice_over"
    assert tags["vo_priority"] >= 50


if __name__ == "__main__":
    # 手动运行示例
    cases = [
        {"text": "张三说：“快跑！”", "mode": "auto", "default_seconds": "3"},
        {"text": "雨夜里，路灯残影在水面摇晃。", "mode": "narration", "narration_limit": "3"},
    ]
    for i, p in enumerate(cases, 1):
        res = tool_generate(p)
        meta = res.get("meta", {})
        tags = inject_stitch_tags(meta)
        print(f"Case {i} meta:", json.dumps(meta, ensure_ascii=False))
        print(f"Case {i} tags:", json.dumps(tags, ensure_ascii=False))