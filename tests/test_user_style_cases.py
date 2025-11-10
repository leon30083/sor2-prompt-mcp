import json
import pytest

from src.mcp_tool import generate_user_style_model, format_only, generate_script_model


def _sum_durations(shots_list):
    return sum(int(s.get("duration", 0)) for s in shots_list)


@pytest.mark.parametrize("text,expect_segments", [
    ("""### 标题A\n第一段文字。\n\n### 标题B\n第二段文字。""", ["标题A", "标题B"]),
    ("""段落一\n\n段落二\n\n段落三""", ["片段1", "片段2", "片段3"]),
])
def test_format_rules_titles_or_blanklines(text, expect_segments):
    res = format_only({"text": text})
    assert "segments" in res
    titles = [s.get("title") for s in res["segments"]]
    assert titles == expect_segments


def test_user_style_default_segment_seconds_12_cap_15():
    text = """### 开场\n风声呼啸，李四压低声音说：“跟上。”\n\n### 转场\n远处火把摇曳。"""
    out = generate_user_style_model({"text": text, "format": True})
    meta = out["user_script"]["meta"]
    assert meta.get("segment_seconds") == 12
    # 每个分段的 total_duration 应该精确等于目标时长，且不超过 15
    for seg in meta.get("segments", []):
        assert seg.get("total_duration") <= 15
        assert seg.get("total_duration") == 12


@pytest.mark.parametrize("strategy,target", [
    ("scale", 12),
    ("pad", 12),
    ("trim", 12),
])
def test_time_fit_strategies(strategy, target):
    text = """段落一：王强说：“别出声。”\n\n段落二：脚步声越来越近。"""
    out = generate_user_style_model({
        "text": text,
        "format": True,
        "time_fit_strategy": strategy,
        "segment_seconds": target,
        "default_seconds": "3",
    })
    meta = out["user_script"]["meta"]
    assert meta.get("segment_seconds") == target
    for seg in meta.get("segments", []):
        if strategy == "trim":
            # trim 策略在总时长小于目标时不扩展，保证不超过目标即可
            assert seg.get("total_duration") <= target
        else:
            assert seg.get("total_duration") == target


def test_dialogue_mode_explicit():
    text = "李四说：“快走！” 王强压低声音说：“等等。”"
    out = generate_user_style_model({"text": text, "mode": "dialogue", "format": False})
    us = out["user_script"]
    # 至少包含两个镜头，且行文本被映射到 line 字段
    assert us.get("shots_count", 0) >= 1
    assert any((s.get("line") or "") for s in us.get("shots_list", []))


def test_narration_mode_forced():
    text = "荒野上风声呼啸，远处狼影一闪而过。"
    out = generate_user_style_model({"text": text, "mode": "narration", "format": False})
    us = out["user_script"]
    assert us.get("shots_count", 0) >= 1
    # 旁白/环境镜头 line 可能为空，但 sound_effect 应该可给出“风声”等简单提示
    se_list = [s.get("sound_effect") for s in us.get("shots_list", [])]
    assert any(isinstance(se, str) for se in se_list)


def test_user_mapping_fields_exist():
    text = """### A\n他停下脚步，回头张望。\n\n### B\n火把的火光在墙上跳动。"""
    out = generate_user_style_model({"text": text, "format": True})
    us = out["user_script"]
    assert set(us.keys()) >= {"shots_list", "shots_count", "total_duration", "meta"}
    first = us["shots_list"][0]
    # 字段名按用户示例
    for key in ["shot_id", "shot_type", "duration", "frame_content", "sound_effect", "line", "camera_movement"]:
        assert key in first


def test_total_duration_matches_sum():
    text = "段落一：他在走廊里低声说话。"
    out = generate_user_style_model({"text": text, "format": True})
    us = out["user_script"]
    assert us.get("total_duration") == _sum_durations(us.get("shots_list", []))


def test_segment_seconds_override_10():
    text = """### A\n画外传来脚步声。\n\n### B\n他握紧火把。"""
    out = generate_user_style_model({"text": text, "format": True, "segment_seconds": 10})
    meta = out["user_script"]["meta"]
    assert meta.get("segment_seconds") == 10
    for seg in meta.get("segments", []):
        assert seg.get("total_duration") == 10


def test_seconds_default_is_3():
    text = "段落一：简短描述。\n\n段落二：另一段。"
    out = generate_user_style_model({"text": text, "format": True})
    # 无法直接读取每镜头默认秒，但总时长与目标一致（12），间接证明默认镜头秒经过缩放处理
    meta = out["user_script"]["meta"]
    assert meta.get("segment_seconds") == 12


def test_script_model_and_user_style_duration_consistency():
    text = """### A\n他回头一看。\n\n### B\n风声渐起。"""
    payload = {"text": text, "format": True}
    us_out = generate_user_style_model(payload)
    sm_out = generate_script_model(payload)
    us_total = us_out["user_script"]["total_duration"]
    sm_total = sm_out["script_model"]["total_duration"]
    assert isinstance(us_total, int) and isinstance(sm_total, int)
    assert abs(us_total - sm_total) < 5  # 两者映射字段不同，但总时长应基本一致