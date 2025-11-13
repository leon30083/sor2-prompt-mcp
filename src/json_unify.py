from typing import List, Dict, Optional


def _safe_int_seconds(val) -> int:
    try:
        s = int(str(val))
    except Exception:
        s = 1
    return max(1, s)


def unify_shots_to_script_model(shots: List[Dict], meta: Optional[Dict] = None) -> Dict:
    """
    将内部 shots 列表统一为“剧本模型”结构（JSON 1 风格）。
    设计目标：
    - 保持字段单一职责与可直接访问的数据类型（duration 为数值秒）。
    - 不改变镜头数量与构图，仅映射字段并规范时长类型。
    - 可选附带原始元信息（meta）。

    返回示例结构：
    {
      "version": "sora2-script-model",
      "shots_count": 3,
      "total_duration": 12,
      "shots_list": [
        {
          "id": 1,
          "duration": 4,
          "description": "……",
          "cinematography": { … },
          "performance": { … },
          "dialogue": { "character": "旁白", "line": "……", "tone": "……" }
        }
      ],
      "meta": { … }  # 可选
    }
    """
    shots_list: List[Dict] = []
    total = 0
    for idx, shot in enumerate(shots, start=1):
        # 规范 id
        sid = shot.get("shot_id")
        try:
            sid = int(sid)
        except Exception:
            sid = idx
        # 规范时长为整数秒，至少 1
        seconds_val = _safe_int_seconds(shot.get("api_call", {}).get("seconds", 1))
        total += seconds_val
        shots_list.append({
            "id": sid,
            "duration": seconds_val,
            "description": shot.get("description", ""),
            "cinematography": shot.get("cinematography", {}),
            "performance": shot.get("performance", {}),
            "dialogue": shot.get("dialogue")
        })

    result: Dict = {
        "version": "sora2-script-model",
        "shots_count": len(shots_list),
        "total_duration": total,
        "shots_list": shots_list,
    }
    if isinstance(meta, dict):
        result["meta"] = meta
    return result