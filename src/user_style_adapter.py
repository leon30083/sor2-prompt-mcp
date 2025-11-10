from typing import List, Dict


def _shot_type_from_cine(cine: str) -> str:
    c = (cine or "").lower()
    # 依据常见英文摄影机术语映射到中文类型
    if "extreme wide" in c or "wide shot" in c or "wide" in c:
        return "全景"
    if "medium close-up" in c or "mcu" in c or "medium close up" in c:
        return "近景"
    if "close-up" in c or "extreme close-up" in c:
        return "特写"
    if "medium shot" in c or "medium" in c:
        return "中景"
    # 旁白/B-roll默认给中景，以便通用
    if "b-roll" in c or "montage" in c:
        return "中景"
    return "中景"


def _camera_movement_from_cine(cine: str) -> str:
    c = (cine or "").lower()
    if "static" in c or "locked-off" in c:
        return "固定"
    if "slow lateral pan" in c or "pan" in c:
        return "平移"
    if "slow push-in" in c or "push in" in c or "push-in" in c:
        return "缓慢推进"
    if "handheld" in c:
        return "轻微晃动"
    if "tilt" in c:
        return "上/下摇"
    if "tracking" in c or "follow" in c:
        return "跟拍"
    return "固定"


def _sound_effect_from_tone_perf_desc(tone: str, performance: str, description: str) -> str:
    t = (tone or "").lower()
    p = (performance or "").lower()
    d = (description or "")
    # 简易启发式：尽量不复杂化，保持可读
    if "voice-over" in t:
        return "旁白"
    if "off-screen" in t:
        return "画外声"
    if "whispers" in p or "hushed" in t or "低声" in d or "压低" in d:
        return "低声"
    if "urgent" in t or "emphatic" in t or "急促" in d:
        return "急促"
    # 基本环境音提示（根据常见词）
    if "风" in d:
        return "风声"
    if "心跳" in d:
        return "心跳声"
    if "火把" in d:
        return "火把噼啪声"
    return "无"


def map_shots_to_user_style(shots: List[Dict]) -> Dict:
    """
    将内部镜头结构映射到用户示例的字段名：
    - shot_id, shot_type, duration, frame_content, sound_effect, line, camera_movement
    仅做字段重命名与轻量规则映射，不改变镜头数量与时长。
    """
    out_list: List[Dict] = []
    total = 0
    for idx, sh in enumerate(shots, start=1):
        # 原始 id 与时长
        sid = sh.get("shot_id", idx)
        try:
            shot_id = int(sid)
        except Exception:
            shot_id = idx
        sec_str = (sh.get("api_call", {}) or {}).get("seconds")
        try:
            duration = max(1, int(str(sec_str)))
        except Exception:
            duration = 1
        total += duration
        # 字段映射
        description = sh.get("description", "")
        cine = sh.get("cinematography") or ""
        perf = sh.get("performance") or ""
        dlg = sh.get("dialogue") or {}
        line = dlg.get("line") or ""
        tone = dlg.get("tone") or ""
        out_list.append({
            "shot_id": shot_id,
            "shot_type": _shot_type_from_cine(cine),
            "duration": duration,
            "frame_content": description,
            "sound_effect": _sound_effect_from_tone_perf_desc(tone, perf, description),
            "line": line,
            "camera_movement": _camera_movement_from_cine(cine)
        })
    return {
        "shots_list": out_list,
        "shots_count": len(out_list),
        "total_duration": total
    }