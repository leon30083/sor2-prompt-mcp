import json
from typing import Dict, List
from .sora2_agent import generate_sora2_instructions, to_json, detect_mode, summarize_text
from .script_format import format_script, fit_segment_time
from .json_unify import unify_shots_to_script_model
from .user_style_adapter import map_shots_to_user_style


def generate(payload: Dict) -> Dict:
    """
    MCP 工具入口：/sora2/agent.generate

    参数:
    - payload: { "text": str, "default_seconds": str, "narration_limit": str|int, "mode": str, "composition_policy"?: str }

    返回:
    - { "shots": List[Dict] }
    """
    text = payload.get("text", "")
    # 调整默认镜头秒数为 3（旧为 4），更贴近单镜头轻量时长，避免溢出
    default_seconds = payload.get("default_seconds", "3")
    narration_limit = payload.get("narration_limit", 3)
    composition_policy = str(payload.get("composition_policy", "neutral")).lower()
    mode = str(payload.get("mode", "auto")).lower()
    # 新增可选参数（向后兼容）
    format_enabled = payload.get("format", True)
    # 默认分段时长改为 12s；并在后续对齐时强制不超过 15s
    segment_seconds_raw = payload.get("segment_seconds", 12)
    time_fit_strategy = str(payload.get("time_fit_strategy", "scale")).lower()
    try:
        narration_limit = int(narration_limit)
    except Exception:
        narration_limit = 3
    try:
        segment_seconds = int(segment_seconds_raw)
    except Exception:
        segment_seconds = 12
    # 强制上限 15s，避免溢出
    if segment_seconds > 15:
        segment_seconds = 15
    if not isinstance(text, str) or not text.strip():
        return {"error": {"code": "INVALID_INPUT", "message": "text 不能为空"}}
    chosen_mode = "narration" if mode == "narration" else detect_mode(text)

    # 将 default_seconds 解析为整数用于时长对齐
    try:
        default_sec_int = int(str(default_seconds))
    except Exception:
        default_sec_int = 4

    if format_enabled:
        segments = format_script(text)
        all_shots: List[Dict] = []
        seg_meta: List[Dict] = []
        for seg in segments:
            seg_shots = generate_sora2_instructions(seg.get("content", ""), default_seconds, narration_limit, mode, composition_policy=composition_policy)
            seg_shots_fitted = fit_segment_time(seg_shots, segment_seconds, time_fit_strategy, default_sec_int)
            all_shots.extend(seg_shots_fitted)
            # 计算该分段总时长（镜头秒数之和），用于测试与审查
            seg_total = 0
            for sh in seg_shots_fitted:
                try:
                    seg_total += int(str((sh.get("api_call", {}) or {}).get("seconds")))
                except Exception:
                    seg_total += max(1, default_sec_int)
            seg_meta.append({
                "title": seg.get("title", "片段"),
                "shots_count": len(seg_shots_fitted),
                "total_duration": seg_total
            })
        summary = summarize_text(text)
        return {
            "shots": all_shots,
            "meta": {
                "chosen_mode": chosen_mode,
                "shots_count": len(all_shots),
                "segments": seg_meta,
                "segment_seconds": segment_seconds,
                "time_fit_strategy": time_fit_strategy,
                "parse_summary": summary
            }
        }
    else:
        shots = generate_sora2_instructions(text, default_seconds, narration_limit, mode, composition_policy=composition_policy)
        # 若未开启格式化但给了 segment_seconds，则将整段按该秒数对齐
        shots_fitted = fit_segment_time(shots, segment_seconds, time_fit_strategy, default_sec_int) if segment_seconds else shots
        summary = summarize_text(text)
        return {
            "shots": shots_fitted,
            "meta": {
                "chosen_mode": chosen_mode,
                "shots_count": len(shots_fitted),
                "segment_seconds": segment_seconds,
                "time_fit_strategy": time_fit_strategy,
                "parse_summary": summary
            }
        }


def format_only(payload: Dict) -> Dict:
    """独立格式化工具：返回分段与标题，不生成镜头。"""
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return {"error": {"code": "INVALID_INPUT", "message": "text 不能为空"}}
    segments = format_script(text)
    return {"segments": segments, "segments_count": len(segments)}


def generate_script_model(payload: Dict) -> Dict:
    """
    统一 JSON 输出：将 /sora2/agent.generate 的结果转换为“剧本模型”结构。
    - 输入参数与 generate 相同，保持向后兼容。
    - 仅映射字段与时长类型，不更改镜头数量或构图。
    """
    res = generate(payload)
    if isinstance(res, dict) and "error" in res:
        return res
    shots = res.get("shots", [])
    meta = res.get("meta", {})
    unified = unify_shots_to_script_model(shots, meta)
    return {"script_model": unified}


def generate_user_style_model(payload: Dict) -> Dict:
    """
    用户示例样式输出：字段名为 shot_type、frame_content、sound_effect、camera_movement。
    - 输入参数与 generate 相同。
    - 保持镜头数量与时长不变，仅字段映射。
    - 分段时长默认 12s，且强制不超过 15s（在 generate 内已处理）。
    """
    res = generate(payload)
    if isinstance(res, dict) and "error" in res:
        return res
    shots = res.get("shots", [])
    meta = res.get("meta", {})
    mapped = map_shots_to_user_style(shots)
    # 附带 meta，便于查看分段统计与模式
    mapped["meta"] = meta
    return {"user_script": mapped}


if __name__ == "__main__":
    # 简易命令行测试：python -m src.mcp_tool '{"text": "李四说：“到这边！”"}'
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else '{"text": "王强压低声音说：“别出声。”"}'
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"text": raw}
    print(json.dumps(generate(payload), ensure_ascii=False, indent=2))