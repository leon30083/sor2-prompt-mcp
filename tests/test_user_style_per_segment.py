import pytest

from src.mcp_tool import generate_user_style_per_segment
from src.mcp_tool import format_only


def test_preview_markdown_and_user_scripts_count():
    text = """段落一：他说：“快跑！”

段落二：海面起涌，旁白描述。

段落三：他们回到山谷。"""
    res = generate_user_style_per_segment({"text": text, "format": True})
    assert "preview_markdown" in res
    assert res["preview_markdown"].startswith("### 片段1：")
    # 分段数量与 user_scripts 数量一致
    segs = format_only({"text": text})["segments"]
    assert len(res.get("user_scripts", [])) == len(segs)

    # 校验 shot_id 规范：segNN_shotMM
    first_us = res["user_scripts"][0]["user_script"]
    sid = first_us["shots_list"][0]["shot_id"]
    assert isinstance(sid, str) and sid.startswith("seg01_shot")


@pytest.mark.parametrize("strategy,target", [
    ("scale", 12),
    ("pad", 12),
    ("trim", 12),
])
def test_each_segment_has_meta_and_duration(strategy, target):
    text = """### A\n他停下脚步，回头张望。\n\n### B\n火把在墙上映出跳动光影。"""
    res = generate_user_style_per_segment({
        "text": text,
        "format": True,
        "time_fit_strategy": strategy,
        "segment_seconds": target
    })
    scripts = res.get("user_scripts", [])
    assert len(scripts) == 2
    for item in scripts:
        us = item.get("user_script", {})
        assert set(us.keys()) >= {"shots_list", "shots_count", "total_duration", "meta"}
        meta = us.get("meta", {})
        assert meta.get("segment_seconds") == target
        segs = meta.get("segments", [])
        assert len(segs) == 1
        if strategy == "trim":
            # trim 不扩展不足的时长，但不超过目标
            assert segs[0].get("total_duration") <= target
        else:
            assert segs[0].get("total_duration") == target


def test_narration_mode_forced_all_segments():
    text = """第一段：夜色下风声呼啸。

第二段：旁白继续描述场景。"""
    res = generate_user_style_per_segment({"text": text, "format": True, "mode": "narration"})
    for item in res.get("user_scripts", []):
        meta = item.get("user_script", {}).get("meta", {})
        assert meta.get("chosen_mode") == "narration"
